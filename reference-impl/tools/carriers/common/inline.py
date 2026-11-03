"""Inline markup of explainer/1 text fields — one parser for every carrier.

Grammar (nothing else is markup; everything else is literal text):
  **bold**          -> ("bold", text)
  [[g:<id>]]        -> ("gloss", id)   glossary term; the carrier shows the term and its gloss on demand
  [[r:<id>]]        -> ("ref", id)     reference; the carrier shows its label
  [[s:<id>]]        -> ("sec", id)     cross-link to a section
A carrier renders tokens; it never re-parses the raw string.
"""
import re

_TOKEN = re.compile(r"\*\*(.+?)\*\*|\[\[([grs]):([a-z0-9][a-z0-9-]*)\]\]")
_KIND = {"g": "gloss", "r": "ref", "s": "sec"}


def tokens(text):
    out, pos = [], 0
    for m in _TOKEN.finditer(text):
        if m.start() > pos:
            out.append(("text", text[pos:m.start()]))
        if m.group(1) is not None:
            out.append(("bold", m.group(1)))
        else:
            out.append((_KIND[m.group(2)], m.group(3)))
        pos = m.end()
    if pos < len(text):
        out.append(("text", text[pos:]))
    return out


def markers(text):
    """(kind letter, id) for every [[x:id]] marker in text."""
    return [(m.group(2), m.group(3)) for m in _TOKEN.finditer(text) if m.group(2)]


def plain(text, glossary=None, refs=None, sections=None):
    """Text with markup resolved to plain words (for carriers or fields that cannot style)."""
    glossary, refs, sections = glossary or {}, refs or {}, sections or {}
    parts = []
    for kind, val in tokens(text):
        if kind in ("text", "bold"):
            parts.append(val)
        elif kind == "gloss":
            parts.append(glossary.get(val, val))
        elif kind == "ref":
            parts.append(refs.get(val, val))
        else:
            parts.append(sections.get(val, val))
    return "".join(parts)
