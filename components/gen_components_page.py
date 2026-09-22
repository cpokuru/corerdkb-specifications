"""Generate components/index.html from ethwan-router-components.json, using
the same shared site shell (topnav + hero banner) as every other page —
unlike full-list.html or the other gen_*.py outputs in this folder, this one
now goes through layout.py's render_page()/render_hero()/render_topnav()
instead of a standalone hand-authored <style> block.

components/index.html sits one directory below the repo root, so this script
passes path_prefix="../" to render_page() — that's what makes the logo, nav
links, and search index fetch resolve correctly from inside components/.

Usage:
    python3 gen_components_page.py --json ethwan-router-components.json --out index.html

Run this whenever ethwan-router-components.json changes (i.e. after
extract_components.py / build_site.py step 4), so the page stays in sync
with the .xlsx it's derived from.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from layout import render_hero, render_page  # noqa: E402

FULL_DETAILS_URL = "full-list.html"

# Same fixed/rotating palettes as gen_simple_html.py, kept in sync so the
# tier/category pill colors look identical to the rest of the components
# tooling (full-list.html, any other gen_simple_html.py output).
TIER_COLORS = {
    "gold":  {"bg": "#fef3c7", "fg": "#92400e"},
    "blue":  {"bg": "#dbeafe", "fg": "#1e40af"},
    "gray":  {"bg": "#f3f4f6", "fg": "#374151"},
    "green": {"bg": "#d1fae5", "fg": "#065f46"},
}
CATEGORY_PALETTE = [
    {"bg": "#d1fae5", "fg": "#065f46"},
    {"bg": "#fde2e2", "fg": "#991b1b"},
    {"bg": "#fef3c7", "fg": "#92400e"},
    {"bg": "#dbeafe", "fg": "#1e40af"},
    {"bg": "#ede9fe", "fg": "#5b21b6"},
    {"bg": "#e0f2fe", "fg": "#075985"},
    {"bg": "#fce7f3", "fg": "#9d174d"},
    {"bg": "#e5e7eb", "fg": "#374151"},
]


def category_color(category: str) -> dict:
    idx = int(hashlib.md5(category.encode("utf-8")).hexdigest(), 16) % len(CATEGORY_PALETTE)
    return CATEGORY_PALETTE[idx]


def esc(s) -> str:
    return html.escape("" if s is None else str(s))


def build_body(data: dict) -> str:
    subtitle = data.get("subtitle", "")
    schema_version = data["schemaVersion"]
    generated_at = data["generatedAt"]
    tiers = {t["id"]: t for t in data.get("tiers", [])}
    components = sorted(data["components"], key=lambda c: (c["tier"] != "common-core", c["name"].lower()))

    legend_html = "".join(
        f'<span class="pill" style="background:{TIER_COLORS[t["color"]]["bg"]};color:{TIER_COLORS[t["color"]]["fg"]}">{esc(t["label"])}</span>'
        for t in tiers.values()
    )

    rows_html = []
    for c in components:
        tier = tiers.get(c["tier"], {"label": c["tier"], "color": "gray"})
        tier_style = TIER_COLORS[tier["color"]]
        cat_style = category_color(c["category"] or "Uncategorized")
        url = c.get("url")
        repos = [u for u in [url, *c.get("supportingUrls", [])] if u]
        if repos:
            url_cell = '<div style="display:flex;flex-direction:column;gap:4px;">' + "".join(
                f'<a href="{esc(u)}" target="_blank" rel="noopener" style="font-size:0.86rem;">{esc(u)}</a>'
                for u in repos
            ) + '</div>'
        else:
            url_cell = '<span class="muted">—</span>'
        rows_html.append(f'''<tr>
          <td>{esc(c["name"])}</td>
          <td><span class="pill" style="background:{cat_style["bg"]};color:{cat_style["fg"]};border-radius:8px;line-height:1.5;">{esc(c["category"] or "Uncategorized")}</span></td>
          <td><span class="pill" style="background:{tier_style["bg"]};color:{tier_style["fg"]}">{esc(tier["label"])}</span></td>
          <td>{url_cell}</td>
        </tr>''')

    lede = subtitle or "Every RDK-B component for this device profile — repo, category, and tier."
    return f'''
{render_hero("Core RDK Components", "RDK-B EthWAN WiFi Router Components", lede, compact=True, visual_key="components")}

<section class="tight-top">
  <p style="color:var(--muted); font-size:0.85rem; margin:0 0 14px;">
    Schema version: {esc(schema_version)} &nbsp;|&nbsp; Generated: {esc(generated_at)}
  </p>
  <div style="margin-bottom:18px;">{legend_html}</div>
  <table class="def-table">
    <thead><tr><th>Name</th><th>Category</th><th>Tier</th><th>Repositories</th></tr></thead>
    <tbody>{"".join(rows_html)}</tbody>
  </table>
  <p style="margin-top:18px; font-size:0.86rem;">
    For the full interactive workbook view, see the <a href="{FULL_DETAILS_URL}">detailed version</a>.
  </p>
</section>
'''


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="ethwan-router-components.json")
    ap.add_argument("--out", default="index.html")
    args = ap.parse_args()

    data = json.loads(Path(args.json).read_text(encoding="utf-8"))
    body = build_body(data)
    head_extra = f"<title>{esc(data['title'])} — RDK-B Core Broadband</title>"
    html_out = render_page("components", head_extra, body, path_prefix="../")
    Path(args.out).write_text(html_out, encoding="utf-8")
    print(f"Wrote {args.out} ({len(data['components'])} components)")


if __name__ == "__main__":
    main()
