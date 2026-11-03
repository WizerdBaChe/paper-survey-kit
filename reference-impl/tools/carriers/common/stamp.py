"""Generator stamp: proves an output was produced by a registered carrier from a given content file.

The stamp lives INSIDE the output (no sidecar receipt — small-file budget):
  .html  <meta name="carrier-stamp" content="{json}">  in <head>
  .pptx  core properties: content_status = "carrier-stamp", identifier = content_sha256,
         category = body_sha256, comments = {json of the other fields} (255-char cap per property)
Stamp fields: carrier, version, schema, content_sha256, body_sha256, built_at.

body_sha256 covers the whole output AND every other stamp field:
  html  the file text with the stamp meta neutralised, line endings normalised;
  pptx  every package part except docProps/core.xml, plus core.xml's own elements minus the four
        stamp elements and the save-time bookkeeping (modified, lastModifiedBy, revision);
  both  + the canonical JSON of the stamp fields other than body_sha256.
So a hand edit anywhere — text, a core property such as the title, or the stamp's own carrier /
version / content fields — reads `edited`. content_sha256 against the current content digest
(common/content.py digest(): canonical JSON + figure bytes) tells whether the output is behind its
content (`stale`). A stamp that cannot be parsed reads `edited`, never a traceback.
"""
import hashlib
import html
import io
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

HTML_META = re.compile(r'<meta name="carrier-stamp" content="([^"]*)">')
PLACEHOLDER = '<meta name="carrier-stamp" content="">'
PPTX_STATUS = "carrier-stamp"
PPTX_CORE = "docProps/core.xml"
PPTX_SPLIT = ("content_sha256", "body_sha256")
_NS = {"cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
       "dc": "http://purl.org/dc/elements/1.1/",
       "dcterms": "http://purl.org/dc/terms/"}
# stamp carriers (identifier, category, description=comments, contentStatus) and save-time bookkeeping
_CORE_EXCLUDED = {f"{{{_NS['dc']}}}identifier", f"{{{_NS['cp']}}}category", f"{{{_NS['dc']}}}description",
                  f"{{{_NS['cp']}}}contentStatus", f"{{{_NS['dcterms']}}}modified", f"{{{_NS['cp']}}}lastModifiedBy",
                  f"{{{_NS['cp']}}}revision"}


def _fields_blob(stamp):
    return json.dumps({k: v for k, v in stamp.items() if k != "body_sha256"},
                      ensure_ascii=False, sort_keys=True).encode("utf-8")


def _html_body_sha(text, stamp):
    neutral = HTML_META.sub(PLACEHOLDER, text, count=1).replace("\r\n", "\n")
    return hashlib.sha256(neutral.encode("utf-8") + b"\0" + _fields_blob(stamp)).hexdigest()


def _core_canonical(xml_bytes):
    root = ET.fromstring(xml_bytes)
    items = sorted((el.tag, (el.text or "").strip()) for el in root if el.tag not in _CORE_EXCLUDED)
    return json.dumps(items, ensure_ascii=False).encode("utf-8")


def _pptx_body_sha(data, stamp):
    h = hashlib.sha256()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in sorted(z.namelist()):
            part = z.read(name)
            if name == PPTX_CORE:
                part = _core_canonical(part)
            h.update(name.encode("utf-8") + b"\0" + part + b"\0")
    h.update(_fields_blob(stamp))
    return h.hexdigest()


def apply(out_path, fields):
    """Write the stamp into an already rendered output. fields: carrier, version, schema, content_sha256, built_at."""
    out_path = Path(out_path)
    stamp = dict(fields)
    if out_path.suffix.lower() in (".html", ".htm"):
        text = out_path.read_text(encoding="utf-8")
        if not HTML_META.search(text):
            if "</head>" not in text:
                raise ValueError(f"{out_path}: no </head> to place the stamp in")
            text = text.replace("</head>", PLACEHOLDER + "\n</head>", 1)
        stamp["body_sha256"] = _html_body_sha(text, stamp)
        meta = '<meta name="carrier-stamp" content="%s">' % html.escape(json.dumps(stamp, ensure_ascii=False, sort_keys=True), quote=True)
        out_path.write_text(HTML_META.sub(lambda _m: meta, text, count=1), encoding="utf-8", newline="\n")
        return stamp
    if out_path.suffix.lower() == ".pptx":
        from pptx import Presentation

        def _write(st):
            prs = Presentation(str(out_path))
            cp = prs.core_properties
            cp.content_status = PPTX_STATUS
            cp.identifier = st["content_sha256"]
            cp.category = st["body_sha256"]
            cp.comments = json.dumps({k: v for k, v in st.items() if k not in PPTX_SPLIT}, ensure_ascii=False, sort_keys=True)
            prs.save(str(out_path))

        stamp["body_sha256"] = "0" * 64
        _write(stamp)                       # first save rewrites every part
        stamp["body_sha256"] = _pptx_body_sha(out_path.read_bytes(), stamp)
        _write(stamp)                       # changes only excluded core elements
        if _pptx_body_sha(out_path.read_bytes(), stamp) != stamp["body_sha256"]:
            raise RuntimeError(f"{out_path}: pptx body hash not stable across a core-properties save")
        return stamp
    raise ValueError(f"{out_path}: no stamp format for suffix {out_path.suffix}")


class StampUnreadable(Exception):
    pass


def read(out_path):
    """-> (stamp dict or None, recomputed body sha or None). Raises StampUnreadable when a stamp is present but broken."""
    out_path = Path(out_path)
    suf = out_path.suffix.lower()
    if suf in (".html", ".htm"):
        text = out_path.read_text(encoding="utf-8", errors="replace")
        m = HTML_META.search(text)
        if not m or not m.group(1):
            return None, None
        try:
            stamp = json.loads(html.unescape(m.group(1)))
        except ValueError as e:
            raise StampUnreadable(f"stamp meta is not valid JSON: {e}") from e
        return stamp, _html_body_sha(text, stamp)
    if suf == ".pptx":
        from pptx import Presentation
        cp = Presentation(str(out_path)).core_properties
        if cp.content_status != PPTX_STATUS:
            return None, None
        try:
            stamp = json.loads(cp.comments)
        except (TypeError, ValueError) as e:
            raise StampUnreadable(f"stamp in core property 'comments' is not valid JSON: {e}") from e
        stamp.update(content_sha256=cp.identifier, body_sha256=cp.category)
        return stamp, _pptx_body_sha(out_path.read_bytes(), stamp)
    return None, None


def check(out_path, content_sha=None):
    """-> (verdict, detail). verdict: ok | unstamped | edited | stale."""
    try:
        stamp, body = read(out_path)
    except StampUnreadable as e:
        return "edited", f"{out_path}: {e}; rebuild from content"
    if stamp is None:
        return "unstamped", f"{out_path}: no carrier stamp"
    if stamp.get("body_sha256") != body:
        return "edited", f"{out_path}: changed after the build (body sha {body[:12]} != stamped {str(stamp.get('body_sha256'))[:12]}); rebuild from content, never hand-edit"
    if content_sha is not None and stamp.get("content_sha256") != content_sha:
        return "stale", f"{out_path}: built from content {str(stamp.get('content_sha256'))[:12]}, content is now {content_sha[:12]}; rebuild"
    tail = "" if content_sha is not None else " (content not compared: pass --content to detect stale)"
    return "ok", f"{out_path}: {stamp.get('carrier')}@{stamp.get('version')} from content {str(stamp.get('content_sha256'))[:12]}{tail}"
