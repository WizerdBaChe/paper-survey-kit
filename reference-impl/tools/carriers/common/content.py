"""Load and validate an explainer/1 content file.

validate() runs the JSON Schema (schema/explainer-1.schema.json) and then the checks a schema
cannot express:
  * unique ids;
  * every string leaf of the content is walked: in a MARKUP field every [[g:]] / [[r:]] / [[s:]]
    marker resolves and no marker sits inside **bold** (the grammar cannot render it); a PLAIN field
    (PLAIN_FIELDS, rendered as literal text by every carrier) carries no markup at all — so the
    same content reads the same in every carrier;
  * every figure is a relative path that stays inside the content file's folder tree, exists, and has
    an extension every carrier can embed (FIGURE_SUFFIXES);
  * every table row has as many cells as columns; refs[].href uses an allowed scheme.
An empty list means the content is buildable by every carrier.

digest() is the content identity the stamp carries: sha256 over the canonical JSON (key order,
whitespace, BOM and line endings do not count) plus the bytes of every figure, so a changed figure
makes the output `stale` exactly like changed text.
"""
import hashlib
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match

from . import inline

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = {"explainer/1": ROOT / "schema" / "explainer-1.schema.json"}
FIGURE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif")   # the intersection of what html and pptx carriers embed
HREF_OK = re.compile(r"^(https?://|file:///|#|[^:]*$)", re.I)
# fields every carrier renders as literal text (no **bold**, no markers)
PLAIN_FIELDS = {("glossary", "term"), ("glossary", "en"), ("refs", "label"), ("refs", "href"),
                ("meta", "author"), ("meta", "lang"), ("meta", "date"), ("meta", "audience"),
                ("metrics", "value"), ("metrics", "unit")}
# keys whose strings are identifiers / enums / paths, never text
NON_TEXT_KEYS = {"schema", "id", "type", "kind", "src"}
_ANY_MARKUP = re.compile(r"\*\*|\[\[[grs]:")
_BOLD = re.compile(r"\*\*(.+?)\*\*")


def load(path):
    path = Path(path)
    data = json.loads(path.read_bytes().decode("utf-8-sig"))
    return data, digest(data, path.parent)


def digest(data, base_dir):
    h = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    for s in data.get("sections", []) if isinstance(data, dict) else []:
        for b in s.get("blocks", []):
            if isinstance(b, dict) and b.get("type") == "figure":
                p = Path(base_dir) / b.get("src", "")
                h.update(b"\0fig\0" + b.get("src", "").encode("utf-8") + b"\0")
                h.update(p.read_bytes() if p.is_file() else b"<missing>")
    return h.hexdigest()


def _leaves(node, where, owner):
    """Yield (where, owner, key, text) for every string leaf. owner = the container kind that fixes PLAIN_FIELDS."""
    if isinstance(node, dict):
        kind = node.get("type") if isinstance(node.get("type"), str) else owner
        for k, v in node.items():
            if k in NON_TEXT_KEYS:
                continue
            if isinstance(v, str):
                yield f"{where}.{k}", kind, k, v
            else:
                child_owner = k if k in ("glossary", "refs", "meta") else kind
                yield from _leaves(v, f"{where}.{k}", child_owner)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            if isinstance(v, str):
                yield f"{where}[{i}]", owner, None, v
            else:
                yield from _leaves(v, f"{where}[{i}]", owner)


def _schema_errors(content, schema):
    out = []
    for e in sorted(Draft202012Validator(schema).iter_errors(content), key=lambda e: list(e.path)):
        if e.context:  # oneOf / anyOf: report the most specific sub-error, not the whole instance
            e = best_match(e.context)
        loc = "/".join(str(p) for p in e.absolute_path) or "(root)"
        out.append(f"schema: {loc}: {e.message[:200]}")
    return out


def validate(content, base_dir=None):
    schema_id = content.get("schema") if isinstance(content, dict) else None
    if schema_id not in SCHEMAS:
        return [f"schema: unknown or missing ({schema_id!r}); known: {sorted(SCHEMAS)}"]
    errors = _schema_errors(content, json.loads(SCHEMAS[schema_id].read_text(encoding="utf-8")))
    if errors:
        return errors
    ids = {"g": [g["id"] for g in content.get("glossary", [])],
           "r": [r["id"] for r in content.get("refs", [])],
           "s": [s["id"] for s in content["sections"]]}
    for kind, lst in ids.items():
        dup = sorted({x for x in lst if lst.count(x) > 1})
        if dup:
            errors.append(f"ids: duplicate {kind}-ids {dup}")
    known = {k: set(v) for k, v in ids.items()}
    for where, owner, key, text in _leaves(content, "content", None):
        if (owner, key) in PLAIN_FIELDS:
            if _ANY_MARKUP.search(text):
                errors.append(f"plain: {where}: markup is not rendered in this field by every carrier; write it as plain text")
            continue
        for kind, ref in inline.markers(text):
            if ref not in known[kind]:
                errors.append(f"inline: {where}: [[{kind}:{ref}]] has no {kind}-entry")
        for m in _BOLD.finditer(text):
            if inline.markers(m.group(1)):
                errors.append(f"inline: {where}: a [[..]] marker inside **bold** cannot be rendered; move it outside the bold")
    for r in content.get("refs", []):
        if r.get("href") and not HREF_OK.match(r["href"]):
            errors.append(f"refs[{r['id']}].href: scheme not allowed ({r['href'][:40]!r}); use http(s)://, file:/// or a relative path")
    for s in content["sections"]:
        for bi, b in enumerate(s["blocks"]):
            if b["type"] == "table":
                n = len(b["columns"])
                for ri, row in enumerate(b["rows"]):
                    if len(row) != n:
                        errors.append(f"table: section[{s['id']}].blocks[{bi}].rows[{ri}] has {len(row)} cells, {n} columns")
            if b["type"] == "figure":
                errors += _figure_errors(f"section[{s['id']}].blocks[{bi}]", b["src"], base_dir)
    return errors


def _figure_errors(where, src, base_dir):
    p = Path(src)
    if p.is_absolute() or p.drive or src.startswith(("/", "\\")):
        return [f"figure: {where}: {src} is absolute; figures are paths relative to the content file"]
    if p.suffix.lower() not in FIGURE_SUFFIXES:
        return [f"figure: {where}: {src}: type {p.suffix!r} is not embeddable by every carrier; use one of {FIGURE_SUFFIXES}"]
    if base_dir is None:
        return []
    base = Path(base_dir).resolve()
    full = (base / p).resolve()
    if base != full and base not in full.parents:
        return [f"figure: {where}: {src} resolves outside the content file's folder ({base})"]
    if not full.is_file():
        return [f"figure: {where}: {src} not found under {base}"]
    return []
