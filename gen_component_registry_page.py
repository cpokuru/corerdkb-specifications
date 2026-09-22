"""One-purpose generator for component-registry.html.

Two parts, in order:

1. A condensed "policy at a glance" panel -- paraphrased, high-level
   terminology (not verbatim spec text) covering what the Component
   Registry is, what it must track, and the four lifecycle states, still
   cited back to sections 7.3.2 / 7.3.2.1 / 7.3.2.2 / 7.3.3 / 7.3.3.1 of
   the Core RDK Broadband Specification for traceability. This panel's
   copy is hand-written and lives in this file (POLICY below) -- it is a
   summary, not a rendering of component-governance.json, so there's
   nothing to keep in sync if the wording here drifts slightly from the
   source spec language; go back to component-governance.json directly
   (also used by technical-governance.html) if the exact legal text is
   ever needed.

2. The catalog itself -- every component across every device profile, one
   row each, from components/all-components.json. Sortable by column,
   filterable by tier and category, with summary stat cards. Field set is
   still narrower than the full 7.3.2.1 mandatory list (only
   name/category/tier/repo, from the existing extraction pipeline) --
   owner, lifecycle state, HAL contract, TR-181 model, and dependency
   fields still need their own data source before they can render here.

Usage:
    python3 gen_component_registry_page.py --data components/all-components.json --out-dir .
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from layout import esc, render_hero, render_page

PAGE = {
    "active_id": "component-registry",
    "eyebrow": "Component Registry",
    "title": "Component Registry",
    "lede": "The authoritative record of every RDK-B component -- registration, lifecycle "
            "state, and ownership, per §7.3.2 of the Core RDK Broadband Specification.",
}

# ---------- condensed policy panel (paraphrased, not verbatim spec text) ----------

LIFECYCLE_STATES = [
    {"name": "Active", "note": "Active development. New features and fixes accepted."},
    {"name": "Stable", "note": "Interface frozen. Critical/security fixes only."},
    {"name": "Deprecated", "note": "Scheduled for removal. Migration path published."},
    {"name": "Removed", "note": "No longer part of RDK-B. Repository archived."},
]

FIELD_GROUPS = [
    {"title": "Identity", "items": "Name, repositories, per-profile classification (CORE / Required / Optional)"},
    {"title": "Ownership", "items": "Primary and secondary owner, name and organization"},
    {"title": "Interfaces", "items": "RBUS / HAL, HAL contract reference, TR-181 data model"},
    {"title": "Dependencies", "items": "Dependent RDKB components and non-RDKB open source components"},
    {"title": "Health", "items": "Last validated release, open critical issues, distro flags"},
]

MAINTENANCE_RULES = [
    "Updated at every release; any owner, state, or interface change must trigger an update",
    "RTAB owns registry accuracy and the registry must stay publicly accessible",
]

NEW_COMPONENT_DEFINITION = (
    "A new component is any new open source repo or group of repos adding new RDK-B features or "
    "services. It must be organized as one logically self-contained, includable/excludable unit -- "
    "not a grab-bag of unrelated functionality."
)

PROPOSAL_GROUPS = [
    {"title": "Scope & ownership", "items": "Problem statement, functional scope, ownership, which profiles it applies to"},
    {"title": "Interfaces & data", "items": "Data models provided and consumed, HAL APIs used, build/runtime dependencies"},
    {"title": "Impact", "items": "Security, telemetry, logging, memory/CPU, boot-time, restart/recovery behavior"},
    {"title": "Delivery", "items": "Test plan, platform portability, release target, rollback plan"},
]

REGISTRATION_FLOW = [
    "Propose -- open an architecture proposal ticket and identify an owner",
    "Define -- interfaces, dependencies, HAL/OSS usage, and every data model provided or consumed",
    "Build -- implement, run unit tests, validate on the reference platform",
    "Submit -- open a PR, pass CI, complete peer review (and RTAB review if required)",
    "Merge -- attach test evidence; merge only after a sanity pass against run-time data model auto-discovery",
    "Register -- entered into this registry at merge time; track through the next release",
]


def render_policy_panel() -> str:
    field_cards = "".join(
        f'<div class="cr-field-card"><h4>{esc(g["title"])}</h4><p>{esc(g["items"])}</p></div>'
        for g in FIELD_GROUPS
    )
    proposal_cards = "".join(
        f'<div class="cr-field-card"><h4>{esc(g["title"])}</h4><p>{esc(g["items"])}</p></div>'
        for g in PROPOSAL_GROUPS
    )
    flow_items = "".join(
        f'<div class="tl-item"><div class="tl-year">Step {i}</div><p>{esc(step)}</p></div>'
        for i, step in enumerate(REGISTRATION_FLOW, start=1)
    )
    lifecycle_strip = "".join(
        f'<div class="cr-lc-step"><span class="cr-lc-name">{esc(s["name"])}</span>'
        f'<span class="cr-lc-note">{esc(s["note"])}</span></div>'
        for s in LIFECYCLE_STATES
    )
    maintenance = "".join(f"<li>{esc(r)}</li>" for r in MAINTENANCE_RULES)

    return f'''
<section class="tight-top">
  <div class="section-head">
    <span class="eyebrow-lt">Registry policy · §7.3.2 &amp; §7.3.3</span>
    <h2>What "registered" means</h2>
    <p>Every component merged into RDK-B is entered here at merge time. This is a summary of the
      governing rules, not the full spec text -- see the Component Governance section of
      <a href="technical-governance.html">Development Standards</a> for the complete wording.</p>
  </div>

  <div class="callout">
    <strong>Catalog schema &amp; controlled vocabulary</strong>
    <p>The fields, identifiers, lifecycle states, classification rules, and profile-applicability
      model below are the schema every entry must follow -- decided once, here, before components
      are loaded, so a catalog that grows past today's 78 entries doesn't end up classified
      inconsistently by whoever happens to be filling it in. Tier and category are the controlled
      vocabulary: a fixed, pre-designated set of classification values -- profile applicability,
      core/non-core status, category -- applied the same way to every component, not chosen freely
      per entry.</p>
  </div>

  <div class="subhead" style="margin-top:32px;">Registering a new component · §7.2.3.1 &amp; §7.2.4.1</div>
  <p class="cr-catalog-note" style="margin-bottom:14px;">{esc(NEW_COMPONENT_DEFINITION)}</p>
  <div class="cr-field-grid">{proposal_cards}</div>

  <div class="subhead" style="margin-top:32px;">The flow · §7.2.8.1</div>
  <div class="timeline" style="margin-top:14px;">{flow_items}</div>

  <div class="subhead" style="margin-top:36px;">What the registry itself tracks · §7.3.2.1</div>
  <div class="cr-field-grid">{field_cards}</div>

  <div class="subhead" style="margin-top:32px;">Lifecycle states · §7.3.3</div>
  <div class="cr-lc-strip">{lifecycle_strip}</div>
  <p class="cr-catalog-note" style="margin-top:10px;">
    Each forward transition requires architecture-owner or RTAB approval; deprecation requires a
    published migration path before a component can move to Removed.
  </p>

  <div class="subhead" style="margin-top:28px;">Maintenance · §7.3.2.2</div>
  <ul class="cr-maint-list">{maintenance}</ul>
</section>
'''


# ---------- catalog table ----------

SCRIPT_TEMPLATE = r"""
<script>
const DATA_URL = {data_url_json};

function esc(s) {{
  const d = document.createElement('div');
  d.textContent = s ?? '';
  return d.innerHTML;
}}

let ALL = [];
let TIERS = [];
let activeTier = null;
let activeCategory = '';
let sortKey = 'name';
let sortDir = 1;

function tierMeta(id) {{
  return TIERS.find(t => t.id === id) || {{ id, label: id, color: 'gray' }};
}}

function renderStats() {{
  const el = document.getElementById('cr-stats');
  const cats = new Set(ALL.map(c => c.category)).size;
  const cards = [
    {{ label: 'Registered components', value: ALL.length }},
    {{ label: 'Categories', value: cats }},
    ...TIERS.map(t => ({{ label: t.label, value: ALL.filter(c => c.tier === t.id).length }})),
  ];
  el.innerHTML = cards.map(c => `<div class="cr-stat"><div class="cr-stat-num">${{c.value}}</div><div class="cr-stat-lbl">${{esc(c.label)}}</div></div>`).join('');
}}

function renderLegend() {{
  const el = document.getElementById('cr-legend');
  el.innerHTML = TIERS.map(t => {{
    const count = ALL.filter(c => c.tier === t.id).length;
    const active = activeTier === t.id ? ' active' : '';
    return `<button class="cr-chip cr-chip-${{esc(t.color)}}${{active}}" data-tier="${{esc(t.id)}}">` +
      `${{esc(t.label)}} <span class="cr-chip-count">${{count}}</span></button>`;
  }}).join('') +
  `<button class="cr-chip cr-chip-all${{activeTier === null ? ' active' : ''}}" data-tier="">All <span class="cr-chip-count">${{ALL.length}}</span></button>`;
  el.querySelectorAll('.cr-chip').forEach(btn => {{
    btn.addEventListener('click', () => {{
      activeTier = btn.dataset.tier || null;
      renderLegend();
      renderTable();
    }});
  }});
}}

function renderCategoryOptions() {{
  const sel = document.getElementById('cr-category');
  const cats = [...new Set(ALL.map(c => c.category))].sort();
  sel.innerHTML = '<option value="">All categories</option>' +
    cats.map(c => `<option value="${{esc(c)}}">${{esc(c)}}</option>`).join('');
}}

function updateSortIndicators() {{
  document.querySelectorAll('.cr-table th[data-sort]').forEach(th => {{
    th.classList.toggle('sorted', th.dataset.sort === sortKey);
    th.querySelector('.cr-sort-arrow').textContent = th.dataset.sort === sortKey ? (sortDir === 1 ? '▲' : '▼') : '';
  }});
}}

function repoLabel(url) {{
  const parts = url.replace(/\/+$/, '').split('/');
  return parts[parts.length - 1] || url;
}}

function renderTable() {{
  const q = document.getElementById('cr-search').value.trim().toLowerCase();
  let rows = ALL.filter(c => {{
    if (activeTier && c.tier !== activeTier) return false;
    if (activeCategory && c.category !== activeCategory) return false;
    if (!q) return true;
    return c.name.toLowerCase().includes(q) || c.category.toLowerCase().includes(q);
  }});

  rows = rows.slice().sort((a, b) => {{
    let av = a[sortKey], bv = b[sortKey];
    if (sortKey === 'tier') {{ av = tierMeta(a.tier).label; bv = tierMeta(b.tier).label; }}
    return String(av).localeCompare(String(bv)) * sortDir;
  }});

  document.getElementById('cr-count').textContent =
    rows.length === ALL.length ? `${{ALL.length}} registered components` : `${{rows.length}} of ${{ALL.length}} registered components`;

  const body = document.getElementById('cr-tbody');
  if (!rows.length) {{
    body.innerHTML = `<tr><td colspan="4" class="cr-empty">No components match the current filters.</td></tr>`;
    updateSortIndicators();
    return;
  }}
  body.innerHTML = rows.map(c => {{
    const t = tierMeta(c.tier);
    const repos = [c.url, ...(c.supportingUrls || [])].filter(Boolean);
    const repoHtml = repos.length
      ? `<div class="cr-repo-list">` +
        repos.map((u, i) => `<a class="cr-repo-chip" href="${{esc(u)}}" target="_blank" rel="noopener" title="${{esc(u)}}">` +
          `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><path d="M15 3h6v6"/><path d="M10 14 21 3"/></svg>` +
          `${{esc(repoLabel(u))}}</a>`).join('') +
        `</div>`
      : '<span class="cr-empty-cell">—</span>';
    return `<tr>` +
      `<td>${{esc(c.name)}}</td>` +
      `<td class="cr-cat">${{esc(c.category)}}</td>` +
      `<td><span class="cr-badge cr-chip-${{esc(t.color)}}">${{esc(t.label)}}</span></td>` +
      `<td>${{repoHtml}}</td>` +
      `</tr>`;
  }}).join('');
  updateSortIndicators();
}}

fetch(DATA_URL, {{ cache: 'no-store' }})
  .then(res => {{ if (!res.ok) throw new Error('HTTP ' + res.status); return res.json(); }})
  .then(data => {{
    ALL = data.components || [];
    TIERS = data.tiers || [];
    document.getElementById('cr-loading').style.display = 'none';
    document.getElementById('cr-content').style.display = '';
    renderStats();
    renderLegend();
    renderCategoryOptions();
    renderTable();
    document.getElementById('cr-search').addEventListener('input', renderTable);
    document.getElementById('cr-category').addEventListener('change', e => {{ activeCategory = e.target.value; renderTable(); }});
    document.querySelectorAll('.cr-table th[data-sort]').forEach(th => {{
      th.addEventListener('click', () => {{
        const key = th.dataset.sort;
        if (sortKey === key) {{ sortDir *= -1; }} else {{ sortKey = key; sortDir = 1; }}
        renderTable();
      }});
    }});
  }})
  .catch(err => {{
    document.getElementById('cr-loading').innerHTML =
      `<div class="empty-state"><div class="icon">📄</div><h3>Could not load the catalog</h3>` +
      `<p>${{esc(err.message)}} — expected data at <code>${{esc(DATA_URL)}}</code>.</p></div>`;
  }});

function crOpenRegister() {{
  const panel = document.getElementById('contact-panel');
  const msgField = document.getElementById('contact-message');
  if (!panel || !msgField) return;
  panel.classList.add('open');
  if (!msgField.value.trim()) {{
    msgField.value = "I'd like to register a new component in the Component Registry.\n\n" +
      "Component name:\nOwner:\nApplicable RDKB profile(s):\nRepository:\n";
  }}
  const nameField = document.getElementById('contact-name');
  if (nameField) nameField.focus();
}}
</script>
"""

STYLE = """
<style>
  .cr-field-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 14px; margin-top: 18px; }
  .cr-field-card { background: var(--card-bg); border: 1px solid var(--border); border-left: 3px solid var(--middleware);
    border-radius: 10px; padding: 14px 16px; }
  .cr-field-card h4 { font-size: 0.88rem; margin: 0 0 4px; }
  .cr-field-card p { font-size: 0.82rem; margin: 0; color: var(--muted); line-height: 1.5; }
  .cr-lc-strip { display: flex; gap: 0; margin-top: 14px; border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
  .cr-lc-step { flex: 1; padding: 14px 16px; border-right: 1px solid var(--border); }
  .cr-lc-step:last-child { border-right: none; }
  .cr-lc-step:nth-child(1) { background: #eef2ff; }
  .cr-lc-step:nth-child(2) { background: var(--cloud-bg); }
  .cr-lc-step:nth-child(3) { background: var(--amber-bg); }
  .cr-lc-step:nth-child(4) { background: #f1f3f9; }
  .cr-lc-name { display: block; font-weight: 700; font-size: 0.9rem; color: var(--ink); margin-bottom: 4px; }
  .cr-lc-note { display: block; font-size: 0.78rem; color: var(--muted); line-height: 1.45; }
  .cr-maint-list { margin: 10px 0 0; padding-left: 20px; color: var(--muted); font-size: 0.88rem; }
  .cr-maint-list li { margin-bottom: 5px; line-height: 1.55; }

  .cr-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-bottom: 22px; }
  .cr-stat { background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; }
  .cr-stat-num { font-family: "Space Grotesk", sans-serif; font-size: 1.4rem; font-weight: 700; color: var(--ink); }
  .cr-stat-lbl { font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; margin-top: 2px; }

  .cr-toolbar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; }
  .cr-search-input { flex: 1 1 220px; max-width: 300px; padding: 10px 14px; font-size: 0.92rem;
    border: 1px solid var(--border); border-radius: 10px; background: var(--card-bg); color: var(--ink); }
  .cr-category-select { padding: 10px 12px; font-size: 0.86rem; border: 1px solid var(--border); border-radius: 10px;
    background: var(--card-bg); color: var(--ink); max-width: 220px; }
  .cr-count { font-size: 0.82rem; color: var(--muted); white-space: nowrap; margin-left: auto; }
  .cr-legend { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 18px; }
  .cr-chip { border: 1px solid var(--border); background: var(--card-bg); color: var(--ink);
    border-radius: 999px; padding: 6px 14px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
    display: inline-flex; align-items: center; gap: 6px; transition: border-color 0.15s, background 0.15s; }
  .cr-chip:hover { border-color: var(--middleware); }
  .cr-chip.active { background: var(--ink); color: #fff; border-color: var(--ink); }
  .cr-chip-count { font-weight: 700; opacity: 0.65; font-size: 0.78rem; }
  .cr-chip-gold::before, .cr-badge.cr-chip-gold::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: #d97706; display: inline-block; }
  .cr-chip-blue::before, .cr-badge.cr-chip-blue::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: var(--middleware); display: inline-block; }
  .cr-chip-gray::before, .cr-badge.cr-chip-gray::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: #9ca3af; display: inline-block; }
  .cr-chip-all::before { display: none; }

  table.cr-table {
    width: 100%; border-collapse: separate; border-spacing: 0; font-size: 0.92rem;
    border: 1px solid var(--border); border-radius: 12px; overflow: hidden; box-shadow: var(--shadow-sm);
  }
  table.cr-table thead th {
    text-align: left; font-family: "Space Grotesk", sans-serif; font-size: 0.78rem; text-transform: uppercase;
    letter-spacing: 0.06em; font-weight: 700; color: rgba(255,255,255,0.85);
    background: linear-gradient(90deg, var(--hal), var(--middleware));
    padding: 14px 18px; border-bottom: none; cursor: pointer; user-select: none; white-space: nowrap;
  }
  table.cr-table thead th:first-child { border-top-left-radius: 12px; }
  table.cr-table thead th:last-child { border-top-right-radius: 12px; }
  table.cr-table thead th:hover { color: #fff; }
  table.cr-table thead th.sorted { color: #fff; text-decoration: underline; text-underline-offset: 3px; }
  .cr-sort-arrow { font-size: 0.65rem; margin-left: 4px; }
  table.cr-table tbody tr { border-bottom: 1px solid var(--border); }
  table.cr-table tbody tr:last-child { border-bottom: none; }
  table.cr-table tbody tr:nth-child(odd) { background: #fbfcff; }
  table.cr-table tbody tr:nth-child(even) { background: #fff; }
  table.cr-table tbody td { padding: 12px 16px; vertical-align: middle; color: var(--muted); line-height: 1.65; border-right: 1px solid var(--border); }
  table.cr-table tbody td:last-child { border-right: none; }
  table.cr-table tbody td:first-child {
    color: var(--ink); font-weight: 700; font-family: "Space Grotesk", sans-serif;
    border-left: 3px solid var(--rdk-blue); background: rgba(41,182,232,0.04);
  }
  table.cr-table tbody tr:hover { background: var(--cloud-bg); }
  table.cr-table a { font-weight: 600; text-decoration: none; display: inline-flex; align-items: center; gap: 5px; }
  table.cr-table a:hover { text-decoration: underline; }
  .cr-repo-list { display: flex; flex-direction: column; gap: 4px; align-items: flex-start; }
  .cr-repo-chip { font-weight: 500 !important; font-size: 0.82rem; color: var(--middleware) !important;
    display: inline-flex; align-items: center; gap: 5px; }
  .cr-repo-chip svg { flex: 0 0 auto; opacity: 0.6; }
  .cr-empty-cell { color: var(--muted); }
  .cr-cat { color: var(--muted); }
  .cr-badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px;
    font-size: 0.78rem; font-weight: 600; border: 1px solid var(--border); }
  .cr-empty { text-align: center; color: var(--muted); padding: 32px 16px !important; }
  .cr-catalog-note { font-size: 0.86rem; color: var(--muted); margin: -6px 0 20px; max-width: 720px; }
  .cr-register-btn { margin-top: 10px; background: var(--middleware); color: #fff; border: none;
    padding: 10px 18px; border-radius: 999px; font-size: 0.86rem; font-weight: 600; cursor: pointer;
    font-family: inherit; transition: filter 0.12s; }
  .cr-register-btn:hover { filter: brightness(1.1); }
</style>
"""


def build_page(data_rel_url: str) -> str:
    hero_badges = '<span class="badge">§7.3.2 Component Registry</span><span class="badge">§7.3.3 Lifecycle States</span>'
    body = render_hero(PAGE["eyebrow"], PAGE["title"], PAGE["lede"], hero_badges,
                        compact=True, visual_key=PAGE["active_id"]) \
        + render_policy_panel() + f'''
<section class="tight-top">
  <div class="section-head">
    <span class="eyebrow-lt">Registry data</span>
    <h2>Registered Components</h2>
  </div>
  <p class="cr-catalog-note">
    Currently populated fields: name, category, primary and supporting repositories, and
    per-profile classification tier. Owner, lifecycle state, HAL contract reference, TR-181 model,
    and dependency fields from §7.3.2.1 are not yet tracked in the pipeline that feeds this table.
  </p>
  <div id="cr-loading" class="empty-state"><p>Loading component catalog…</p></div>
  <div id="cr-content" style="display:none;">
    <div id="cr-stats" class="cr-stats"></div>
    <div class="cr-toolbar">
      <input id="cr-search" class="cr-search-input" type="text" placeholder="Search by name or category…" />
      <select id="cr-category" class="cr-category-select"></select>
      <span id="cr-count" class="cr-count"></span>
    </div>
    <div id="cr-legend" class="cr-legend"></div>
    <table class="cr-table">
      <thead><tr>
        <th data-sort="name">Component <span class="cr-sort-arrow"></span></th>
        <th data-sort="category">Category <span class="cr-sort-arrow"></span></th>
        <th data-sort="tier">Tier <span class="cr-sort-arrow"></span></th>
        <th>Repositories</th>
      </tr></thead>
      <tbody id="cr-tbody"></tbody>
    </table>
  </div>

  <div class="callout" style="margin-top:32px;">
    <strong>Don't see your component here?</strong>
    <p>If you're proposing a new component, or an existing one is missing or wrong in this
      registry, reach out and we'll get it registered -- have your component name, owner, and
      which RDKB profiles it applies to ready (see the proposal checklist above).</p>
    <button type="button" class="cr-register-btn" onclick="crOpenRegister()">Register a component</button>
  </div>
</section>
'''
    head_extra = f"<title>{PAGE['title']} — RDK-B Core Broadband</title>\n" + STYLE + \
        SCRIPT_TEMPLATE.format(data_url_json=json.dumps(data_rel_url))
    return render_page(PAGE["active_id"], head_extra, body)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="components/all-components.json",
                     help="Path (relative to the built site root) to the component catalog JSON.")
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    path = out_dir / "component-registry.html"
    path.write_text(build_page(args.data), encoding="utf-8")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
