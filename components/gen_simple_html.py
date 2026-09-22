"""Generate a simple static HTML page from a rdk-b-simple-components.schema.json file.

Usage:
    python3 gen_simple_html.py core-b-components.json core-components.html
    python3 gen_simple_html.py ethwan-router-components.json ethwan-router-components.html
"""
import hashlib
import html
import json
import sys
from pathlib import Path

FULL_DETAILS_URL = "full-list.html"

# Fixed palette for tier badges (id -> css color values), matches schema's color enum.
TIER_COLORS = {
    "gold":  {"bg": "#fef3c7", "fg": "#92400e"},
    "blue":  {"bg": "#dbeafe", "fg": "#1e40af"},
    "gray":  {"bg": "#f3f4f6", "fg": "#374151"},
    "green": {"bg": "#d1fae5", "fg": "#065f46"},
}

# Rotating palette for category pills, picked deterministically per category name
# (same idea as the video page: each category gets a stable, distinct color).
CATEGORY_PALETTE = [
    {"bg": "#d1fae5", "fg": "#065f46"},  # green
    {"bg": "#fde2e2", "fg": "#991b1b"},  # red
    {"bg": "#fef3c7", "fg": "#92400e"},  # amber
    {"bg": "#dbeafe", "fg": "#1e40af"},  # blue
    {"bg": "#ede9fe", "fg": "#5b21b6"},  # violet
    {"bg": "#e0f2fe", "fg": "#075985"},  # sky
    {"bg": "#fce7f3", "fg": "#9d174d"},  # pink
    {"bg": "#e5e7eb", "fg": "#374151"},  # gray
]


def category_color(category: str) -> dict:
    idx = int(hashlib.md5(category.encode("utf-8")).hexdigest(), 16) % len(CATEGORY_PALETTE)
    return CATEGORY_PALETTE[idx]


def esc(s) -> str:
    return html.escape("" if s is None else str(s))


def build_html(data: dict) -> str:
    title = data["title"]
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
        url_cell = f'<a href="{esc(url)}">{esc(url)}</a>' if url else '<span class="muted">—</span>'
        rows_html.append(f'''
        <tr>
          <td>{esc(c["name"])}</td>
          <td><span class="pill" style="background:{cat_style["bg"]};color:{cat_style["fg"]}">{esc(c["category"] or "Uncategorized")}</span></td>
          <td><span class="pill" style="background:{tier_style["bg"]};color:{tier_style["fg"]}">{esc(tier["label"])}</span></td>
          <td>{url_cell}</td>
        </tr>''')

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{esc(title)}</title>
<style>
  :root {{ font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
  body {{ margin: 40px; color: #111827; }}
  h1 {{ font-size: 2rem; margin: 0 0 8px; }}
  .meta {{ color: #6b7280; font-size: 0.9rem; margin-bottom: 4px; }}
  .subtitle {{ color: #374151; margin-bottom: 16px; }}
  .legend {{ margin-bottom: 20px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ text-align: left; padding: 10px 14px; border-bottom: 1px solid #e5e7eb; }}
  th {{ background: #f5f5f5; font-size: 0.9rem; }}
  .pill {{ display: inline-block; padding: 3px 10px; border-radius: 9999px; font-size: 0.85rem; font-weight: 600; }}
  a {{ color: #1d4ed8; text-decoration: underline; }}
  .muted {{ color: #9ca3af; }}
  .footer-link {{ margin-top: 28px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 0.9rem; }}
</style>
</head>
<body>
  <h1>{esc(title)}</h1>
  <div class="meta">Schema version: {esc(schema_version)} | Generated: {esc(generated_at)}</div>
  {f'<div class="subtitle">{esc(subtitle)}</div>' if subtitle else ''}
  <div class="legend">{legend_html}</div>
  <table>
    <thead><tr><th>Name</th><th>Category</th><th>Tier</th><th>URL</th></tr></thead>
    <tbody>{''.join(rows_html)}</tbody>
  </table>
  <div class="footer-link">For the full interactive workbook view, see the <a href="{FULL_DETAILS_URL}">detailed version</a>.</div>
</body>
</html>
'''


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: gen_simple_html.py <input.json> <output.html>")
    src, dest = Path(sys.argv[1]), Path(sys.argv[2])
    data = json.loads(src.read_text(encoding="utf-8"))
    dest.write_text(build_html(data), encoding="utf-8")
    print(f"Wrote {dest} ({len(data['components'])} components)")


if __name__ == "__main__":
    main()
