"""Generator for the sidebar pages that don't have their own dedicated
generator script (architecture-standards.html, industry-standards.html,
technical-governance.html, north-bound-specification.html).

Each page ships with a generic loader (render_stub_page in layout.py) that
tries <slug>.json then <slug>.xml (same folder) at runtime and renders
whatever it finds; until one of those data files exists, the page shows a
clean "no data yet" empty state instead of breaking.

For a page that needs its own dedicated script (its own JSON schema, its
own fetch-from-GitHub logic, etc.) -- like component-registry.html -- write
a small standalone script that imports render_stub_page from layout.py
directly, the same way this file does. See gen_component_registry_page.py.

Usage:
    python3 gen_stub_pages.py --out-dir .
"""
from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import quote

from layout import esc, render_hero, render_page, render_stub_page

PAGES = [
    {
        "active_id": "architecture-standards",
        "slug": "architecture-standards",
        "eyebrow": "Architecture Standards",
        "title": "Architecture Standards",
        "lede": "Architectural rules every new or refactored component follows — "
                "modularity, IPC, dependency management, and data model documentation (§7.1.1).",
    },
    {
        "active_id": "industry-standards",
        "slug": "industry-standards",
        "eyebrow": "Industry Conformance Standards",
        "title": "Industry Conformance Standards",
        "lede": "Where RDK-B functionality overlaps an established external standards "
                "body, tracked by category (§7.1.3).",
        "tables": [
            {"slug": "architecture-standards-industry"},
        ],
    },
    {
        "active_id": "technical-governance",
        "slug": "technical-governance",
        "eyebrow": "Development Standards",
        "title": "Development Standards",
        "lede": "Process, implementation, and coding standards every new or refactored "
                "component is held to.",
        "tables": [
            {"slug": "technical-governance"},
            {
                "slug": "technical-governance-process",
                "kind": "sections",
                "heading": "Technical Governance Process",
                "blurb": "How a change moves from proposal to merge — classification, entry "
                         "criteria, architecture review, testing, and release governance (§7.2).",
            },
            {
                "slug": "component-governance",
                "kind": "sections",
                "heading": "Component Governance Process",
                "blurb": "How components are registered, owned, health-reviewed, deprecated, "
                         "and how interface stability is tagged over their lifecycle (§7.3).",
            },
        ],
    },
    {
        "active_id": "nbi-spec",
        "slug": "north-bound-specification",
        "eyebrow": "North Bound APIs",
        "title": "North Bound Specification",
        "lede": "The RDK-B High Level API Specification — the northbound protocol and "
                "data-model contract (TR-069, TR-369/USP, WebPA, TR-181).",
        "tables": [
            {"slug": "north-bound-specification", "kind": "sections"},
        ],
    },
    {
        "active_id": "sbi-spec",
        "slug": "south-bound-specification",
        "eyebrow": "South Bound APIs",
        "title": "South Bound Specification",
        "lede": "The vendor- and SoC-facing contract RDK-B exposes downward — HAL "
                "interfaces and OSS southbound delegation between middleware and the BSP.",
        "tables": [
            {"slug": "south-bound-specification", "kind": "sections"},
        ],
    },
]


def build_pdf_page(page: dict) -> str:
    """A PDF-embed page (e.g. North Bound Specification): no JSON loader,
    just an <iframe> pointing at the PDF already checked into the repo, plus
    a plain-link fallback for browsers/mobile viewers that force a download
    instead of rendering the iframe inline."""
    pdf_src = quote(page["pdf"], safe="/")
    body = render_hero(page["eyebrow"], page["title"], page["lede"], compact=True, visual_key=page["active_id"]) + f'''
<section class="tight-top">
  <div class="pdf-embed-wrap">
    <iframe src="{esc(pdf_src)}" title="{esc(page["title"])}" loading="lazy"></iframe>
  </div>
  <p style="margin-top:14px; font-size:0.86rem;">
    Viewer not loading? <a href="{esc(pdf_src)}" target="_blank" rel="noopener">Open the PDF directly ↗</a>
  </p>
</section>
'''
    head_extra = f"<title>{page['title']} — RDK-B Core Broadband</title>\n" + \
        '<style>.pdf-embed-wrap{border:1px solid var(--border);border-radius:12px;overflow:hidden;' \
        'box-shadow:var(--shadow-sm);height:82vh;min-height:520px;}' \
        '.pdf-embed-wrap iframe{width:100%;height:100%;border:none;display:block;}</style>'
    return render_page(page["active_id"], head_extra, body)



def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for page in PAGES:
        path = out_dir / f"{page['slug']}.html"
        html = build_pdf_page(page) if "pdf" in page else render_stub_page(page)
        path.write_text(html, encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
