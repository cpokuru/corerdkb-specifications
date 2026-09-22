"""Extract §3-7 of the RDKB High Level API Spec (the "North Bound Interface"
document) into north-bound-specification.json, for the "sections" render
mode gen_stub_pages.py already supports (heading + paragraph/bullet/table/
code blocks, same mechanism used for the Core spec's §7.2/§7.3).

This is a different PDF from the main Core RDK spec — only one level of
heading numbering (1, 1.1, 2, 3, 4.1 ... not 7.1.1.2-deep), no repeating
"§X.Y.Z." governance boilerplate, a JSON template block (§6) that must be
kept verbatim rather than reflowed into prose, and a real bordered table
(§7, spanning two pages) — so it gets its own small extractor rather than
reusing extract_spec_content.py's section-7.2/7.3 logic.

Usage:
    python3 extract_nbi_spec.py "docs/hlspec/RDKB High Level API Spec 2026-August-11_v1.pdf" --out north-bound-specification.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pdfplumber

_BOILERPLATE_RE = re.compile(r"^(Core RDK — RDKB High Level API|CONFIDENTIAL — Internal \| Page \d+ of \d+)$")
_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)?)\.?\s+([A-Za-z][^\n]{1,80})$")
_BULLET_RE = re.compile(r"^[•]\s*|^-\s+")
_TERM_RE = re.compile(r"^[A-Z][A-Za-z0-9 /&]{2,60}:\s")
_PSEUDO_HEADING_BODY_RE = re.compile(r"^[A-Za-z0-9 /&\-]+$")
_PSEUDO_HEADING_STOPWORDS = ("a ", "an ", "the ", "this ", "for ", "note", "example", "suppose", "these ", "supported ")


def is_pseudo_heading(txt: str) -> bool:
    """A handful of section-5 sub-topics (OBJECT NAMES:, ELEMENT NAMES:,
    NON-STANDARD NAMES, DATA MODEL OPERATIONS:, ...) act as sub-headings in
    the source but aren't numbered like §4.1 etc — just a short standalone
    label line, sometimes ALL CAPS, sometimes Title Case with a trailing
    colon. Distinguished from ordinary lead-in phrases like "For example:"
    or "Supported operations include:" by excluding sentence-starter words."""
    body = txt.rstrip(":").strip()
    if not body or not body[0].isupper() or len(txt) > 58:
        return False
    if body.lower().startswith(_PSEUDO_HEADING_STOPWORDS):
        return False
    if not _PSEUDO_HEADING_BODY_RE.match(body):
        return False
    is_all_caps = body == body.upper() and any(c.isalpha() for c in body)
    return is_all_caps or txt.endswith(":")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def find_page_with(pdf, needle: str, start: int = 3) -> int:
    """start=3 skips the cover/executive-summary/TOC pages (0-2), which would
    otherwise false-positive match section heading text appearing in the
    Table of Contents itself."""
    for i, page in enumerate(pdf.pages):
        if i < start:
            continue
        if needle in (page.extract_text() or ""):
            return i
    raise SystemExit(f"Heading {needle!r} not found in PDF")


def extract_sections(pdf) -> list[dict]:
    start = find_page_with(pdf, "3. Definitions")
    stop_page = find_page_with(pdf, "7. Interface Inventory")

    sections: list[dict] = []
    current: dict | None = None
    in_json_template = False  # true once inside §6's code block
    pending_json_section = False  # true after §6's heading, before its "{" starts
    json_lines: list[str] = []

    def flush_json_block():
        nonlocal json_lines
        if current is not None and json_lines:
            current["blocks"].append({"type": "pre", "text": "\n".join(json_lines)})
        json_lines = []

    p = start
    while p <= stop_page + 2:  # §7's table spans 2 pages past its heading page
        if p >= len(pdf.pages):
            break
        page = pdf.pages[p]
        table_ranges = [(t.bbox[1], t.bbox[3]) for t in page.find_tables()]

        def in_table(top: float) -> bool:
            return any(t0 - 2 <= top <= t1 + 2 for t0, t1 in table_ranges)

        for line in page.extract_text_lines():
            txt = line["text"].strip()
            if not txt or _BOILERPLATE_RE.match(txt) or in_table(line["top"]):
                continue

            m = _HEADING_RE.match(txt)
            # Only treat as a heading if it's a KNOWN top-level or §4.x heading —
            # avoids false positives on body text and the many inline
            # "Device.WiFi.Radio.2." style dotted paths in §5.
            is_real_heading = bool(m) and (
                m.group(1) in ("3", "4", "5", "6", "7") or m.group(1).startswith("4.")
            )
            if is_real_heading:
                flush_json_block()
                in_json_template = False
                if current is not None:
                    sections.append(current)
                num, title = m.group(1), m.group(2).strip()
                current = {"number": num, "title": title, "level": num.count(".") + 2, "blocks": []}
                if num == "6":
                    pending_json_section = True
                continue

            if current is None:
                continue

            if in_json_template:
                json_lines.append(txt)
                continue

            if pending_json_section and txt.startswith("{"):
                # Section 6's intro paragraph (prose) precedes the actual
                # JSON template — only start the verbatim code block once we
                # hit its real opening brace, so the intro stays normal prose.
                pending_json_section = False
                in_json_template = True
                json_lines.append(txt)
                continue

            bullet_m = _BULLET_RE.match(txt)
            if is_pseudo_heading(txt):
                current["blocks"].append({"type": "h", "text": txt.rstrip(":")})
            elif bullet_m:
                current["blocks"].append({"type": "li", "text": txt[bullet_m.end():].strip()})
            elif _TERM_RE.match(txt):
                # Unbulleted "Term: definition" entries (§3 Definitions) —
                # each term starts a fresh list item rather than merging
                # into whatever came before.
                current["blocks"].append({"type": "li", "text": txt})
            else:
                prev = current["blocks"][-1] if current["blocks"] else None
                if prev and prev["type"] in ("p", "li"):
                    prev["text"] += " " + txt
                else:
                    current["blocks"].append({"type": "p", "text": txt})

        p += 1

    flush_json_block()
    if current is not None:
        sections.append(current)

    _attach_interface_table(pdf, sections, stop_page)
    return sections


def _attach_interface_table(pdf, sections: list[dict], start_page: int) -> None:
    """§7's Interface Inventory / API Coverage table spans two pages with
    slightly different column layouts (page 1 has extra empty columns from a
    merged header cell); normalize both into one (name, status) row list and
    attach as a single table block on the §7 section."""
    section7 = next((s for s in sections if s["number"] == "7"), None)
    if section7 is None:
        return
    rows: list[list[str]] = []
    for p in (start_page, start_page + 1):
        if p >= len(pdf.pages):
            continue
        for t in pdf.pages[p].find_tables():
            for row in t.extract():
                cells = [norm(c or "") for c in row if norm(c or "")]
                if len(cells) >= 2 and cells[0] != "Interface Inventory":
                    rows.append([cells[0], cells[1]])
    if rows:
        section7["blocks"].append({"type": "table", "headers": ["Interface Inventory", "API Coverage Report"], "rows": rows})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--out", default="north-bound-specification.json")
    args = ap.parse_args()

    path = Path(args.pdf)
    with pdfplumber.open(path) as pdf:
        sections = extract_sections(pdf)

    payload = {"source": f"{path.name} §3-7", "docs": sections}
    Path(args.out).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {args.out} ({len(sections)} sections)")


if __name__ == "__main__":
    main()
