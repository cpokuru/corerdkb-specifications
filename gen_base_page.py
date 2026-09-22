"""Render index.html (About Core RDK Broadband) for CoreRDK-Broadband-Specification.

Two source files, two different sections of the same page:

  - docs/about-content.json  -> the About section (definition, goals/challenges,
    RDK Ready program, benefits). Hand-curated from the Core RDK Broadband
    deck (a slide layout, not a structured doc, so — like FIVE_TIER below —
    it isn't a good fit for automatic extraction). Update this file by hand
    when the deck changes.

  - docs/spec-content.json   -> the Architecture section (five-tier model,
    production/vendor-test layering, test suite ownership). Unchanged from
    before — still produced by extract_spec_content.py from the spec PDF.

architecture-standards.html and technical-governance.html are separate,
empty static stub pages (see gen_stub_pages.py) — not touched by this script.

Usage:
    python3 gen_base_page.py docs/spec-content.json docs/about-content.json --out-dir .
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from layout import esc, render_hero, render_page, render_quicklinks, render_tabs, TABS_SCRIPT, ICONS

COMPONENTS_URL = "components/"
COMPONENTS_FULL_URL = "components/full-list.html"
SPEC_WIKI_URL = "https://wiki.rdkcentral.com/spaces/RDK/pages/498925914/RDK9+Core+RDK+Broadband+Specification+Approved+by+TAB"

FOOTER = """
<footer>
  <div class="footer-links">
    <a href="{components_url}">Components — profiles<span>Required / optional components per device profile</span></a>
    <a href="{components_full_url}">Components — full workbook<span>Interactive component list, all profiles</span></a>
    <a href="{spec_wiki_url}">RDK9 Core RDK Broadband Spec<span>TAB-approved specification (wiki)</span></a>
    <a href="https://github.com/rdkcentral">rdkcentral on GitHub<span>Component source repositories</span></a>
  </div>
  <div class="footer-meta">
    RDKM · © 2026 RDK Central. All rights reserved. Generated from {source_pdf}.
  </div>
</footer>
""".format(components_url=COMPONENTS_URL, components_full_url=COMPONENTS_FULL_URL,
           spec_wiki_url=SPEC_WIKI_URL, source_pdf="{source_pdf}")


# ---------- About section renderers (from about-content.json) ----------

def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def render_goals(goals: list[dict]) -> str:
    out = []
    for g in goals:
        anchor = slugify(g["title"])
        out.append(f'''
    <div class="card" id="{anchor}" style="margin-bottom:16px; scroll-margin-top:140px;">
      <h3>{esc(g["title"])}</h3>
      <p><strong style="color:var(--ink);">Goal —</strong> {esc(g["goal"])}</p>
      <p style="margin-bottom:0;"><strong style="color:var(--amber-fg);">Challenge —</strong> {esc(g["challenge"])}</p>
    </div>''')
    return "\n".join(out)


def render_rdk_ready(items: list[dict]) -> str:
    out = []
    for it in items:
        out.append(f'''
    <div class="card">
      <h3>{esc(it["title"])}</h3>
      <p style="margin-bottom:0;">{esc(it["body"])}</p>
    </div>''')
    return f'<div class="two-col">{"".join(out)}</div>'


def render_benefits(groups: list[dict]) -> str:
    cols = []
    for g in groups:
        items_html = "".join(f'<li>{esc(i)}</li>' for i in g["items"])
        cols.append(f'''
    <div class="card" style="height:100%; box-sizing:border-box;">
      <h3>{esc(g["category"])}</h3>
      <ul style="margin:0; padding-left:18px; font-size:0.92rem; color:var(--muted);">{items_html}</ul>
    </div>''')
    return f'<div style="display:flex; gap:20px; flex-wrap:wrap; align-items:stretch;">' + \
        "".join(f'<div style="flex:1; min-width:220px;">{c}</div>' for c in cols) + '</div>'


# ---------- Architecture section renderers (from spec-content.json, unchanged) ----------

def render_five_tier(tiers: list[dict]) -> str:
    out = []
    for t in sorted(tiers, key=lambda x: -x["tier"]):
        if "split" in t:
            cols = "".join(
                f'<div class="split-col"><h4>{esc(c["title"])}</h4><p>{esc(c["text"])}</p></div>'
                for c in t["split"]
            )
            body = f'<div class="body body-split">{cols}</div>'
        else:
            body = f'<div class="body"><h4>{esc(t["layer"])}</h4><p>{esc(t["description"])}</p></div>'
        out.append(f'''
    <div class="tier t{t["tier"]}">
      <div class="num">{t["tier"]}</div>
      {body}
    </div>''')
    return "\n".join(out)


def render_test_suites(rows: list[dict]) -> str:
    out = []
    for r in rows:
        out.append(f'<tr><td class="mono">{esc(r["name"])}</td><td>{esc(r["definition"])}</td><td>{esc(r["owner"])}</td></tr>')
    return "\n".join(out)


# ---------- page: About Core RDK Broadband ----------

def build_about_page(spec: dict, about: dict) -> str:
    hero_badges = (
        '<span class="badge">26 features</span>'
        '<span class="badge">7 device profiles</span>'
        '<span class="badge">Five-tier system</span>'
        '<span class="badge">Apache-2.0 / LGPL-2.1</span>'
    )
    tabs = [
        {"id": "overview", "label": "Overview"},
        {"id": "why", "label": "Why Core RDK"},
        {"id": "ready", "label": "RDK Ready"},
        {"id": "architecture", "label": "Architecture"},
        {"id": "testing", "label": "Testing"},
    ]

    body = f'''
{render_hero("Core RDK Broadband", "Core RDK Broadband Platform", about["definition"], hero_badges, visual_key="about")}

<div class="stats">
  <div class="stat"><span class="stat-icon">{ICONS["share"]}</span><div class="num">Operators</div></div>
  <div class="stat"><span class="stat-icon">{ICONS["cpu"]}</span><div class="num">SoCs</div></div>
  <div class="stat"><span class="stat-icon">{ICONS["monitor"]}</span><div class="num">OEMs</div></div>
  <div class="stat"><span class="stat-icon">{ICONS["cubes"]}</span><div class="num">System Integrators</div></div>
  <div class="stat"><span class="stat-icon">{ICONS["puzzle"]}</span><div class="num">Third Parties</div></div>
</div>

{render_tabs(tabs)}

<div class="tab-panel active" id="tab-overview">
<section class="tight-top">
  <div class="section-head">
    <span class="eyebrow-lt">About</span>
    <h2>A common foundation for broadband</h2>
  </div>

  <div class="feature-band">
  {render_quicklinks([
        {"icon": "recycle", "title": "Component reuse", "desc": "Leverage proven, portable components across devices and use cases.", "href": "#easier-component-reuse", "color": "#29b6e8"},
        {"icon": "layers", "title": "Build-time modularity", "desc": "Compose the right features for each product with flexible build options.", "href": "#modularity-build-time-dependencies", "color": "#7ac943"},
        {"icon": "cpu", "title": "Run-time modularity", "desc": "Enable dynamic features and service flexibility across deployments.", "href": "#modularity-run-time-dependencies", "color": "#f5a623"},
        {"icon": "check-list", "title": "Reduced code size", "desc": "Optimized components help deliver efficient, smaller footprints.", "href": "#reduced-code-size", "color": "#f0653e"},
        {"icon": "shield-check", "title": "Consistent interfaces", "desc": "Common APIs and data models across broadband devices and services.", "href": "#consistent-interface-definitions", "color": "#2a5cf0"},
    ], variant="grid")}
  </div>

  <div class="callout" style="margin-top:28px;">
    <strong>Platform definition</strong>
    <p>{esc(about["definition"])}</p>
  </div>

  <div class="callout" style="margin-top:24px;">
    <strong>Value proposition</strong>
    <p>{esc(about["value_proposition"])}</p>
  </div>
</section>
</div>

<div class="tab-panel" id="tab-why">
<section class="tight-top">
  <div class="section-tint tint-blue">
    <div class="subhead" style="margin-top:0;">Why RDKB Core</div>
    {render_goals(about["goals"])}
  </div>
</section>
</div>

<div class="tab-panel" id="tab-ready">
<section class="tight-top">
  <div class="section-tint tint-green">
    <div class="subhead" style="margin-top:0;">RDK Ready — a test and certification program for vendors</div>
    {render_rdk_ready(about["rdk_ready"])}
  </div>

  <div class="section-tint tint-amber">
    <div class="subhead" style="margin-top:0;">Benefits &amp; uses</div>
    {render_benefits(about["benefits"])}
  </div>
</section>
</div>

<div class="tab-panel" id="tab-architecture">
<section style="background:#fff;">
  <div class="section-head">
    <span class="eyebrow-lt">Architecture</span>
    <h2>System Diagram</h2>
    <p>RDK-B's architecture reads like a cross-section: cloud-facing management at the
      top, silicon at the base, with the RDK-B middleware — the platform's largest tier —
      doing the work in between.</p>
  </div>

  <div class="tier-diagram">
    {render_five_tier(spec["five_tier"])}
  </div>
  <div class="tier-caption">Tier 1 is owned by vendors and certified via RDK Ready. Tiers 2, 3 and 4 are where RDK-B feature development happens. Tier 5 is cloud or back-office software that is out of the scope for RDK-B.</div>

  <div class="two-col" style="margin-top:44px;">
    <div>
      <div class="subhead" style="margin-top:0;">Production software builds</div>
      <div class="layer-stack">
        <div class="layer-box top">RDK-B Components</div>
        <div class="layer-box mid">Hardware Abstraction Layer</div>
        <div class="layer-box bot">Vendor Layer — hardware-dependent implementation</div>
      </div>
    </div>
    <div>
      <div class="subhead" style="margin-top:0;">Vendor test software builds</div>
      <div class="layer-stack">
        <div class="layer-box top">RDK Ready — Vendor Test Software</div>
        <div class="layer-box mid">Hardware Abstraction Layer</div>
        <div class="layer-box bot">Vendor Layer — hardware-dependent implementation</div>
      </div>
    </div>
  </div>
</section>
</div>

<div class="tab-panel" id="tab-testing">
<section style="background:#fff;">
  <div class="section-head">
    <span class="eyebrow-lt">Testing</span>
    <h2>Test suite ownership</h2>
  </div>
  <table class="def-table">
    <thead><tr><th>Test suite</th><th>Definition</th><th>Owner</th></tr></thead>
    <tbody>
      {render_test_suites(spec["test_suites"])}
    </tbody>
  </table>
</section>
</div>

{FOOTER.format(source_pdf=esc(spec["sourcePdf"]))}
'''
    return render_page("about", "<title>About &amp; Architecture — RDK-B Core Broadband</title>", body, script=TABS_SCRIPT)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec_json", help="spec-content.json (drives the Architecture section)")
    ap.add_argument("about_json", help="about-content.json (drives the About section)")
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()

    spec = json.loads(Path(args.spec_json).read_text(encoding="utf-8"))
    about = json.loads(Path(args.about_json).read_text(encoding="utf-8"))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "index.html").write_text(build_about_page(spec, about), encoding="utf-8")
    print(f"Wrote {out_dir / 'index.html'}")


if __name__ == "__main__":
    main()
