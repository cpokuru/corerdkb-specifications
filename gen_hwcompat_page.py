"""One-time generator for hardware-compatibility.html.

Unlike the other stub pages, this one reads a small set of static local
files rather than fetching anything client-side: one JSON file per RDK-B
device profile (docs/*.json, matching docs/hw-compat.schema.json), published
per Core-RDK-Broadband-Hardware-Compatibility-Spec_v3.docx section 3.2.
Everything is rendered server-side at generation time.

Two of the seven profiles (EthWAN WiFi Router, EXT EasyMesh) are actually
in scope for this spec revision and carry real CPU/RAM/flash/peripheral
data; the other five are defined in the RDK-B Component List 2026 but not
yet covered -- their JSON files are present with every field set to "n/a"
(see hw-compat.schema.json's own description) and are rendered as a
compact "not yet covered" list rather than full detail cards.

PROFILE_DEFINITIONS below is the one piece of narrative text that isn't in
the JSON schema (the spec's own one-line profile definitions, per Table 1
of the .docx) -- kept here as a small static lookup since it rarely
changes and isn't worth its own data file for seven short lines.

Usage:
    python3 gen_hwcompat_page.py --profiles-dir docs --out-dir .
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from layout import esc, render_hero, render_page

# From Table 1 of Core-RDK-Broadband-Hardware-Compatibility-Spec_v3.docx --
# the RDK-B Component List 2026's one-line definition of each of the seven
# profiles. Order here also sets display order (in-scope profiles first).
PROFILE_DEFINITIONS: dict[str, str] = {
    "ethwan-wifi-router": "IPv4/IPv6 router with Ethernet WAN and Wi-Fi AP features. EasyMesh features are optional.",
    "ext-easymesh": "Wi-Fi extender device based on EasyMesh Agent technology; supports Wi-Fi AP fronthaul and Wi-Fi/Ethernet backhaul.",
    "modem-onu": "Managed or unmanaged bridge from a WAN access technology to an Ethernet LAN port(s); may provide WAN configuration and diagnostics data. Does not include routing or Wi-Fi AP features.",
    "gw": "IPv4/IPv6 router with one or more WAN access technologies and Wi-Fi AP features.",
    "gw-opensync": "IPv4/IPv6 router with one or more WAN access technologies and OpenSync Mesh Wi-Fi features.",
    "gw-easymesh": "IPv4/IPv6 router with one or more WAN access technologies and EasyMesh Wi-Fi controller + agent features.",
    "ext-opensync": "Wi-Fi extender device based on OpenSync technology; supports Wi-Fi AP fronthaul and Wi-Fi/Ethernet backhaul.",
}

STATUS_STYLE = {
    "validated": {"bg": "#d1fae5", "fg": "#065f46", "label": "Validated"},
    "partial": {"bg": "#fef3c7", "fg": "#92400e", "label": "Partial"},
    "not-started": {"bg": "#e5e7eb", "fg": "#374151", "label": "Not started"},
}

# From Table 26 (Section 9.6) of Core-RDK-Broadband-Hardware-Compatibility-
# Spec_v13.docx -- the full set of target markets for eventual regional
# certification, all "Not started" as of v13 except wherever a detailed
# regionalRefs file exists (currently just US, shown in full above this
# summary table -- see render_regional_section). Applies generally across
# in-scope profiles per Section 9.6, not itemized per profile in the source.
TARGET_REGIONS: list[tuple[str, str]] = [
    ("North America (US)", "FCC (Part 15, equipment authorization)"),
    ("Canada", "ISED, ICES"),
    ("European Union / EEA", "RED, CE marking, RoHS, REACH, WEEE"),
    ("United Kingdom", "UK Radio Equipment Regulations, UKCA, PSTI"),
    ("India", "TEC/MTCTE, WPC ETA, BIS"),
    ("Japan", "Radio Law / TELEC, JATE, VCCI, PSE"),
    ("South Korea", "KC certification"),
    ("Australia / New Zealand", "RCM, ACMA"),
    ("Brazil", "ANATEL"),
    ("Other operator-selected markets", "Per operator requirement"),
]


def load_profiles(profiles_dir: Path) -> list[dict]:
    profiles = []
    for path in sorted(profiles_dir.glob("*.json")):
        if path.name == "hw-compat.schema.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if "profileId" not in data:
            continue
        profiles.append(data)
    order = {pid: i for i, pid in enumerate(PROFILE_DEFINITIONS)}
    profiles.sort(key=lambda p: order.get(p["profileId"], 999))
    return profiles


def status_pill(status: str) -> str:
    s = STATUS_STYLE.get(status, STATUS_STYLE["not-started"])
    return f'<span class="pill" style="background:{s["bg"]};color:{s["fg"]};border-radius:999px;">{esc(s["label"])}</span>'


def render_coverage_table(profiles: list[dict]) -> str:
    # Every profile shows as not-covered here -- nothing is validated
    # against an operationalized Core RDK Broadband build yet. Two
    # profiles (EthWAN WiFi Router, EXT EasyMesh) do have RDK8-based
    # target data, shown further down in "Minimum CPU, Memory, and Flash
    # Storage (based on RDK8)" and "Profile Details (based on RDK8)" --
    # but target data isn't the same as this-revision validation, so this
    # table doesn't call them "in scope".
    rows = []
    for p in profiles:
        definition = PROFILE_DEFINITIONS.get(p["profileId"], "")
        rows.append(
            "<tr><td>" + esc(p["profileName"]) + "</td><td>Defined \u2014 not covered in this revision</td><td>"
            + esc(definition) + "</td></tr>"
        )
    return (
        '<table class="def-table"><thead><tr><th>Device Profile</th><th>Coverage in this Spec</th>'
        "<th>Definition</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )


def _load_ref_json(p: dict, key: str, profiles_dir: Path) -> dict | None:
    ref = p.get(key)
    if not ref:
        return None
    path = profiles_dir / ref
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def render_flash_details_section(profiles_dir: Path) -> str:
    """Generic, platform-level flash definitions -- partition classes,
    supported storage technologies, valid filesystem pairings. Not tied
    to any one profile's measured layout (that's tracked separately and
    added later); the same content applies across every profile.
    flash-details.json lives at the top level of docs/, alongside
    hw-compat.schema.json, not inside a per-profile subfolder."""
    path = profiles_dir / "flash-details.json"
    if not path.exists():
        return ""
    data = json.loads(path.read_text(encoding="utf-8"))

    flc_rows = "".join(
        f'<tr><td class="mono">{esc(c["id"])}</td><td><strong>{esc(c["title"])}</strong></td>'
        f'<td>{esc(c["purpose"])}</td><td>{esc(c["otaTreatment"])}</td><td>{esc(c["owner"])}</td></tr>'
        for c in data.get("partitionClasses", [])
    )
    flc_table = (
        '<table class="def-table"><thead><tr><th>ID</th><th>Partition Class</th><th>Purpose</th>'
        "<th>OTA Treatment</th><th>Owner</th></tr></thead><tbody>" + flc_rows + "</tbody></table>"
    )

    tech_rows = "".join(
        f'<tr><td><strong>{esc(t["technology"])}</strong></td><td>{esc(t["whatItIs"])}</td>'
        f'<td>{esc(t["managedBy"])}</td></tr>'
        for t in data.get("storageTechnologies", [])
    )
    tech_table = (
        '<table class="def-table"><thead><tr><th>Technology</th><th>What It Is</th>'
        "<th>Managed By</th></tr></thead><tbody>" + tech_rows + "</tbody></table>"
    )

    fs_rows = "".join(
        f'<tr><td><strong>{esc(m["storageType"])}</strong></td><td>{esc(m["validFilesystems"])}</td>'
        f'<td>{esc(m["why"])}</td></tr>'
        for m in data.get("filesystemMapping", [])
    )
    fs_table = (
        '<table class="def-table"><thead><tr><th>Storage Type</th><th>Valid Filesystem(s)</th>'
        "<th>Why</th></tr></thead><tbody>" + fs_rows + "</tbody></table>"
    )

    layout = data.get("layout", {})
    layout_html = ""
    if layout.get("status") == "tbd":
        layout_html = (
            '<div style="background:var(--cloud-bg); border-radius:8px; padding:14px 18px; margin-top:18px;">'
            '<strong style="color:var(--cloud-fg);">Partition-level layout: TBD</strong>'
            f'<p style="color:var(--ink); font-size:0.86rem; margin:6px 0 0;">{esc(layout.get("note",""))}</p>'
            "</div>"
        )
    elif layout.get("status") == "reference-available":
        part_rows = "".join(
            f'<tr><td class="mono">{esc(p["partition"])}</td><td><strong>{esc(p["gptLabel"])}</strong></td>'
            f'<td>{esc(p["allocated"])}</td><td>{esc(p["filesystem"])}</td><td>{esc(p["used"])}</td>'
            f'<td>{esc(p["purpose"])}</td></tr>'
            for p in layout.get("partitions", [])
        )
        total = layout.get("totalAllocated", "")
        layout_html = f"""
  <div style="margin-top:18px;">
    <strong style="color:var(--ink); font-size:0.9rem;">Partition-level layout (reference: {esc(layout.get("referenceDevice",""))})</strong>
    <p style="color:var(--muted); font-size:0.82rem; margin:4px 0 10px;">{esc(layout.get("note",""))}</p>
    <table class="def-table"><thead><tr><th>#</th><th>Partition</th><th>Allocated</th><th>Filesystem</th>
    <th>Used</th><th>Purpose</th></tr></thead><tbody>{part_rows}</tbody></table>
    <p style="color:var(--muted); font-size:0.8rem; margin:8px 0 0;"><strong>Total allocated:</strong> {esc(total)}</p>
  </div>
"""

    why = data.get("whyTwoBanks", {})
    why_html = ""
    if why:
        why_html = f"""
  <h3 style="font-size:0.98rem; margin:22px 0 8px;">Why 4 GB? Two banks, not one</h3>
  <p style="color:var(--ink); font-size:0.9rem; line-height:1.55; margin:0 0 10px;">{esc(why.get("summary",""))}</p>
  <p style="color:var(--ink); font-size:0.86rem; line-height:1.55; margin:0 0 10px;">{esc(why.get("scope",""))}</p>
  <div style="background:var(--card-bg); border:1px solid var(--border); border-left:3px solid var(--middleware); border-radius:8px; padding:12px 16px; margin-bottom:10px;">
    <strong style="color:var(--ink); font-size:0.84rem;">Measured evidence:</strong>
    <p style="color:var(--muted); font-size:0.82rem; line-height:1.5; margin:4px 0 0;">{esc(why.get("measuredEvidence",""))}</p>
  </div>
  <p style="color:var(--muted); font-size:0.82rem; line-height:1.5; margin:0 0 18px;">{esc(why.get("singleBankAlternative",""))}</p>
"""

    generic = data.get("genericReferenceDesign", {})
    generic_design_html = ""
    if generic:
        entries = generic.get("entries", [])
        generic_rows = "".join(
            f'<tr><td class="mono">{esc(e["num"])}</td><td>{esc(e["partitionName"])}</td>'
            f'<td>{esc(e["purpose"])}</td><td>{esc(e["referenceAllocation"])}</td></tr>'
            for e in entries
        )
        generic_design_html = f"""
  <details style="margin-top:22px; border:1px solid var(--border); border-radius:8px; padding:2px 16px;">
    <summary style="cursor:pointer; padding:12px 0; font-weight:600; color:var(--ink); font-size:0.9rem;">
      Generic RDKM reference design ({len(entries)} entries, not device-specific) -- click to expand
    </summary>
    <p style="color:var(--muted); font-size:0.82rem; line-height:1.5; margin:0 0 12px;">{esc(generic.get("note",""))}</p>
    <table class="def-table"><thead><tr><th>#</th><th>Partition Name</th><th>Purpose</th>
    <th>Reference Allocation</th></tr></thead><tbody>{generic_rows}</tbody></table>
  </details>
"""

    return f"""
<section class="tight-top">
  <div class="section-head"><h2>Flash Details</h2>
    <p>Why the flash floor is what it is, what every profile's layout must provide, and the
    storage technologies this specification recognizes -- generic across all profiles.</p>
  </div>
  {why_html}
  <h3 style="font-size:0.98rem; margin:18px 0 8px;">Logical Partition Classes</h3>
  {flc_table}
  <h3 style="font-size:0.98rem; margin:22px 0 8px;">Storage Technologies</h3>
  {tech_table}
  <h3 style="font-size:0.98rem; margin:22px 0 8px;">Valid Filesystem Pairings</h3>
  {fs_table}
  {layout_html}
  {generic_design_html}
</section>
"""


def render_minimums_table(in_scope: list[dict], profiles_dir: Path) -> str:
    rows = []
    partial_notes = []
    for p in in_scope:
        cpu, mem, sto, ref = p["cpu"], p["memory"], p["requiredStorage"], p["referenceDevice"]
        cpu_txt = f'{esc(cpu["architecture"])}, \u2265 {esc(cpu["minClockGHz"])} GHz'
        cores_txt = str(cpu["minCores"]) + (f' ({esc(cpu["coreTopology"])})' if cpu.get("coreTopology") else "")
        ref_txt = esc(ref["name"]) + (f', {esc(ref["soc"])}' if ref.get("soc") else "")

        mem_data = _load_ref_json(p, "memoryFootprintRef", profiles_dir)
        cpu_data = _load_ref_json(p, "cpuUtilizationRef", profiles_dir)

        measured_ram = "\u2014"
        if mem_data and mem_data.get("measured"):
            if mem_data.get("usedMemoryMB") is not None:
                # System-level used RAM (MemTotal - MemAvailable) -- the
                # correct figure to compare against minRamMB. Preferred
                # over totalRssMB, which double-counts shared pages across
                # processes and is not directly comparable to a RAM floor.
                measured_ram = f'{esc(mem_data["usedMemoryMB"])} MB'
            elif mem_data.get("totalRssMB") is not None:
                # Older captures without usedMemoryMB yet -- fall back to
                # gross RSS, flagged so it isn't mistaken for the same
                # thing as system-used RAM.
                n_proc = len(mem_data.get("processes", []))
                partial = n_proc > 0 and n_proc < 10
                star = "*" if partial else "\u2020"
                measured_ram = f'{esc(mem_data["totalRssMB"])} MB{star}'
                if partial:
                    partial_notes.append(
                        f'* {esc(p["profileName"])}: measured RSS covers only {n_proc} Wi-Fi/EasyMesh-specific '
                        f'processes, not a full-system total \u2014 see Memory Footprint by Process below.'
                    )
                else:
                    partial_notes.append(
                        f'\u2020 {esc(p["profileName"])}: figure shown is gross RSS (sum of per-process RSS, '
                        f'which double-counts shared pages), not system-level used RAM \u2014 see Memory '
                        f'Footprint by Process below for the correct used-RAM figure.'
                    )

        measured_cpu = "\u2014"
        if cpu_data and cpu_data.get("measured") and cpu_data.get("totalCpuPercent") is not None:
            measured_cpu = f'{esc(cpu_data["totalCpuPercent"])}%'

        rows.append(
            "<tr><td>" + esc(p["profileName"]) + "</td><td class=\"mono\">" + cpu_txt + "</td><td>" + cores_txt +
            "</td><td>" + esc(mem["minRamMB"]) + " MB</td><td>" + esc(sto["minFlashMB"]) +
            " MB</td><td class=\"mono\">" + measured_ram + "</td><td class=\"mono\">" + measured_cpu +
            "</td><td>" + ref_txt + "</td></tr>"
        )

    footnote = f'<p style="font-size:0.78rem; color:var(--muted); margin:8px 0 0;">{"<br>".join(partial_notes)}</p>' if partial_notes else ""

    return (
        '<table class="def-table"><thead><tr><th>Profile</th><th>CPU (min.)</th><th>Cores</th>'
        "<th>RAM (min.)</th><th>Flash (min.)</th><th>RAM Used</th><th>Measured CPU</th>"
        "<th>Reference Device</th></tr></thead><tbody>"
        + "".join(rows) + "</tbody></table>" + footnote
    )


STATUS_COLORS = {
    "required": {"bg": "#d1fae5", "fg": "#065f46"},
    "applicable": {"bg": "#d1fae5", "fg": "#065f46"},
    "optional": {"bg": "#fef3c7", "fg": "#92400e"},
    "recommended": {"bg": "#dbeafe", "fg": "#1e40af"},
    "not required": {"bg": "#e5e7eb", "fg": "#374151"},
    "not applicable": {"bg": "#e5e7eb", "fg": "#374151"},
}


def mini_pill(text: str) -> str:
    c = STATUS_COLORS.get(text.lower(), {"bg": "#e5e7eb", "fg": "#374151"})
    return (
        f'<span style="display:inline-block;background:{c["bg"]};color:{c["fg"]};border-radius:999px;'
        f'font-size:0.72rem;font-weight:600;padding:2px 10px;white-space:nowrap;">{esc(text)}</span>'
    )


def status_text(value) -> str:
    if isinstance(value, bool):
        return "Required" if value else "Not required"
    text = str(value).strip()
    if not text or text.lower() == "n/a":
        return "Not applicable"
    return text.replace("-", " ").capitalize()


def render_peripheral_block(block: dict) -> str:
    """Render one self-describing peripherals-array block (see
    peripherals.schema.json). Fully data-driven: a new block, or a new
    detail field within an existing block, needs only a JSON change --
    this function never special-cases a field name.

    Typographic hierarchy, darkest/most prominent to lightest:
      1. title            -- bold, ink
      2. requirement       -- ink, the primary content (explicitly NOT
                              inheriting the page's muted default <p> color)
      3. detail lines      -- ink values, muted labels
      4. referenceImplementation -- small tag, clearly marked as an example
      5. notes             -- smallest, muted, tertiary/supplementary

    requirement and referenceImplementation are kept visually distinct:
    requirement is the generic, chip-agnostic capability every compatible
    device must provide; referenceImplementation is one example (the
    reference device's actual component), never presented as a mandate."""
    pills = []
    for pill in block.get("statusPills", []):
        pill_html = mini_pill(status_text(pill.get("value")))
        label = pill.get("label")
        pills.append(f'<span style="font-size:0.74rem;color:var(--muted);">{esc(label)}:</span> {pill_html}' if label else pill_html)

    requirement = block.get("requirement")
    requirement_html = (
        f'<p style="color:var(--ink); font-size:0.9rem; line-height:1.5; margin:0 0 10px;">{esc(requirement)}</p>'
        if requirement and requirement != "n/a" else ""
    )

    meta_lines = []
    for item in block.get("detail", []):
        label = item.get("label", "")
        val = item.get("value")
        if val in (None, "", [], "n/a"):
            continue
        text = ", ".join(str(v) for v in val) if isinstance(val, list) else str(val)
        if text and text.lower() != "n/a":
            meta_lines.append(
                f'<div style="font-size:0.86rem; line-height:1.5; margin-bottom:4px;">'
                f'<span style="color:var(--muted);">{esc(label)}:</span> '
                f'<span style="color:var(--ink);">{esc(text)}</span></div>'
            )
    meta_html = f'<div style="margin-bottom:10px;">{"".join(meta_lines)}</div>' if meta_lines else ""

    ref_impl = block.get("referenceImplementation")
    ref_impl_html = (
        f'<div style="display:inline-block; background:var(--cloud-bg); color:var(--cloud-fg); '
        f'font-size:0.74rem; font-weight:600; border-radius:6px; padding:3px 9px; margin-bottom:10px;">'
        f'Reference: {esc(ref_impl)}</div><br>'
        if ref_impl else ""
    )

    notes = block.get("notes")
    notes_html = (
        f'<p style="color:var(--muted); font-size:0.78rem; line-height:1.5; margin:0;">{esc(notes)}</p>'
        if notes and notes != "n/a" else ""
    )
    title = block.get("title", "")

    return (
        '<div style="background:var(--card-bg); border:1px solid var(--border); '
        'border-left:3px solid var(--middleware); border-radius:10px; padding:16px 18px; '
        'box-shadow:var(--shadow-sm);">'
        f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">'
        f'<span style="font-weight:700; font-size:0.98rem; color:var(--ink);">{esc(title)}</span>{"".join(pills)}</div>'
        f'{requirement_html}{meta_html}{ref_impl_html}{notes_html}'
        '</div>'
    )


def render_memory_footprint_table(p: dict, profiles_dir: Path) -> str:
    ref = p.get("memoryFootprintRef")
    header = '<div class="subhead" style="margin-top:18px;">Memory Footprint by Process</div>'
    if not ref:
        return header + '<p style="font-size:0.82rem; color:var(--muted); margin:0;">Arriving soon &mdash; per-process RSS measurements from the RDK8 Broadband Release will be added here once available.</p>'

    path = profiles_dir / ref
    if not path.exists():
        return header + '<p style="font-size:0.82rem; color:var(--muted); margin:0;">Arriving soon &mdash; per-process RSS measurements from the RDK8 Broadband Release will be added here once available.</p>'

    data = json.loads(path.read_text(encoding="utf-8"))
    notes = data.get("notes", "")

    if not data.get("measured") or not data.get("processes"):
        # e.g. EXT EasyMesh today: file exists, explains why it's pending
        # (references the EthWAN measurement as context) via its own notes.
        note_html = f'<p style="font-size:0.82rem; color:var(--muted); margin:0;">{esc(notes)}</p>' if notes else \
            '<p style="font-size:0.82rem; color:var(--muted); margin:0;">Arriving soon &mdash; per-process RSS measurements from the RDK8 Broadband Release will be added here once available.</p>'
        return header + note_html

    processes = sorted(data["processes"], key=lambda pr: (isinstance(pr["rssMB"], str), -(pr["rssMB"] if isinstance(pr["rssMB"], (int, float)) else 0)))
    row_parts = []
    for pr in processes:
        rss = pr["rssMB"]
        rss_display = rss if isinstance(rss, str) else f"{rss:.1f} MB"
        row_parts.append(f'<tr><td>{esc(pr["process"])}</td><td class="mono" style="color:var(--muted);">{esc(rss_display)}</td></tr>')
    rows = "".join(row_parts)
    others = data.get("othersRssMB")
    if others is not None:
        rows += f'<tr><td style="color:var(--muted);font-style:italic;">Others (below reporting threshold, base OS/kernel)</td><td class="mono" style="color:var(--muted);">{others:.1f} MB</td></tr>'

    meta_bits = []
    if data.get("referenceDevice"):
        meta_bits.append(f'<strong>Reference device:</strong> {esc(data["referenceDevice"])}')
    if data.get("lastMeasured"):
        meta_bits.append(f'<strong>Last measured:</strong> {esc(data["lastMeasured"])}')
    if data.get("totalRssMB") is not None:
        meta_bits.append(f'<strong>Total RSS:</strong> {esc(data["totalRssMB"])} MB')
    meta_html = f'<div class="hwcompat-summary" style="margin:0 0 10px;">{" ".join(f"<span>{b}</span>" for b in meta_bits)}</div>' if meta_bits else ""

    note_html = f'<p class="hwc-notes" style="margin-top:10px;">{esc(notes)}</p>' if notes else ""

    return (
        header + meta_html +
        '<table class="def-table"><thead><tr><th>Process</th><th>RSS</th></tr></thead><tbody>' + rows + '</tbody></table>' +
        note_html
    )


def render_cpu_utilization_table(p: dict, profiles_dir: Path) -> str:
    ref = p.get("cpuUtilizationRef")
    header = '<div class="subhead" style="margin-top:18px;">CPU Utilization by Process</div>'
    fallback = header + '<p style="font-size:0.82rem; color:var(--muted); margin:0;">Arriving soon &mdash; per-process CPU utilization from the RDK8 Broadband Release will be added here once available.</p>'
    if not ref:
        return fallback

    path = profiles_dir / ref
    if not path.exists():
        return fallback

    data = json.loads(path.read_text(encoding="utf-8"))
    notes = data.get("notes", "")

    if not data.get("measured"):
        note_html = f'<p style="font-size:0.82rem; color:var(--muted); margin:0;">{esc(notes)}</p>' if notes else fallback[len(header):]
        return header + note_html

    meta_bits = []
    if data.get("referenceDevice"):
        meta_bits.append(f'<strong>Reference device:</strong> {esc(data["referenceDevice"])}')
    if data.get("measurementCondition"):
        meta_bits.append(f'<strong>Condition:</strong> {esc(data["measurementCondition"])}')
    if data.get("lastMeasured"):
        meta_bits.append(f'<strong>Last measured:</strong> {esc(data["lastMeasured"])}')
    if data.get("totalCpuPercent") is not None:
        meta_bits.append(f'<strong>Total CPU:</strong> {esc(data["totalCpuPercent"])}%')
    meta_html = f'<div class="hwcompat-summary" style="margin:0 0 10px;">{" ".join(f"<span>{b}</span>" for b in meta_bits)}</div>' if meta_bits else ""

    note_html = f'<p class="hwc-notes" style="margin-top:10px;">{esc(notes)}</p>' if notes else ""

    if not data.get("processes"):
        # e.g. only an aggregate /proc/stat sample was captured, no
        # per-process breakdown yet -- show the aggregate + notes, no table.
        return header + meta_html + note_html

    processes = sorted(data["processes"], key=lambda pr: (isinstance(pr["cpuPercent"], str), -(pr["cpuPercent"] if isinstance(pr["cpuPercent"], (int, float)) else 0)))
    row_parts = []
    for pr in processes:
        cpu_val = pr["cpuPercent"]
        cpu_display = cpu_val if isinstance(cpu_val, str) else f"{cpu_val:.1f}%"
        row_parts.append(f'<tr><td>{esc(pr["process"])}</td><td class="mono" style="color:var(--muted);">{esc(cpu_display)}</td></tr>')
    rows = "".join(row_parts)
    others = data.get("othersCpuPercent")
    if others is not None:
        rows += f'<tr><td style="color:var(--muted);font-style:italic;">Others (below reporting threshold)</td><td class="mono" style="color:var(--muted);">{others:.1f}%</td></tr>'

    return (
        header + meta_html +
        '<table class="def-table"><thead><tr><th>Process</th><th>CPU</th></tr></thead><tbody>' + rows + '</tbody></table>' +
        note_html
    )


def render_regional_section(p: dict, profiles_dir: Path) -> str:
    refs = p.get("regionalRefs") or []
    header = '<div class="subhead" style="margin-top:18px;">Regional Applicability</div>'
    if not refs:
        return header + '<p style="font-size:0.82rem; color:var(--muted); margin:0;">Arriving soon &mdash; regional radio/power configuration and compliance status will be added here once available.</p>'

    blocks = []
    detailed_region_names = set()
    for ref in refs:
        path = profiles_dir / ref
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        region_label = data.get("regionName") or data.get("regionId", "")

        radio_lines = []
        radios = data.get("radios", {})
        for key, label in [("wifi24GHz", "2.4 GHz"), ("wifi5GHz", "5 GHz"), ("wifi6GHz", "6 GHz")]:
            r = radios.get(key)
            if not r:
                continue
            bits = ["Supported" if r.get("supported") else "Not supported"]
            if r.get("dfsRequired"):
                bits.append("DFS required")
            if r.get("operatingModes"):
                bits.append(", ".join(r["operatingModes"]))
            if r.get("afcRequired"):
                bits.append("AFC required")
            radio_lines.append(f'<div><strong>{esc(label)}:</strong> {esc(", ".join(bits))}</div>')
        radio_html = f'<div style="font-size:0.85rem; color:var(--muted); line-height:1.7; margin-bottom:8px;">{"".join(radio_lines)}</div>' if radio_lines else ""

        compliance_rows = []
        for c in data.get("compliance", []):
            status = c["status"]
            pill_colors = {"certified": ("#d1fae5", "#065f46"), "pre-compliance": ("#fef3c7", "#92400e"), "not-tested": ("#e5e7eb", "#374151")}
            bg, fg = pill_colors.get(status, ("#e5e7eb", "#374151"))
            status_label = status.replace("-", " ").capitalize()
            pill = f'<span style="display:inline-block;background:{bg};color:{fg};border-radius:999px;font-size:0.72rem;font-weight:600;padding:2px 10px;">{esc(status_label)}</span>'
            cert = esc(c["certificateId"]) if c.get("certificateId") else "\u2014"
            compliance_rows.append(f'<tr><td>{esc(c["scheme"])}</td><td>{pill}</td><td class="mono" style="color:var(--muted);">{cert}</td></tr>')
        compliance_html = ""
        if compliance_rows:
            compliance_html = (
                '<table class="def-table" style="font-size:0.85rem; margin-bottom:8px;">'
                '<thead><tr><th>Scheme</th><th>Status</th><th>Certificate</th></tr></thead><tbody>'
                + "".join(compliance_rows) + '</tbody></table>'
            )

        notes = data.get("notes", "")
        note_html = f'<p class="hwc-notes" style="margin:0;">{esc(notes)}</p>' if notes else ""

        blocks.append(
            f'<div class="hwc-block" style="margin-bottom:10px;">'
            f'<div class="hwc-block-head"><span class="hwc-block-title">{esc(region_label)}</span>'
            f'<span style="font-size:0.74rem; color:var(--muted);">{esc(data.get("regulatoryDomain", ""))}</span></div>'
            f'{radio_html}{compliance_html}{note_html}'
            f'</div>'
        )
        detailed_region_names.add(region_label)

    target_rows = []
    for region, scheme in TARGET_REGIONS:
        if region in detailed_region_names:
            status_html = '<span style="display:inline-block;background:#dbeafe;color:#1e40af;border-radius:999px;font-size:0.72rem;font-weight:600;padding:2px 10px;">See detail above</span>'
        else:
            status_html = '<span style="display:inline-block;background:#e5e7eb;color:#374151;border-radius:999px;font-size:0.72rem;font-weight:600;padding:2px 10px;">Not started</span>'
        target_rows.append(f'<tr><td>{esc(region)}</td><td style="color:var(--muted);">{esc(scheme)}</td><td>{status_html}</td></tr>')
    target_table = (
        '<div style="font-weight:600; font-size:0.85rem; margin:14px 0 6px;">Planned Regional Coverage</div>'
        '<table class="def-table" style="font-size:0.85rem;">'
        '<thead><tr><th>Region</th><th>Primary Regulatory Scheme(s)</th><th>Status</th></tr></thead>'
        '<tbody>' + "".join(target_rows) + '</tbody></table>'
    )

    return header + "".join(blocks) + target_table


def render_profile_card(p: dict, profiles_dir: Path) -> str:
    cpu, mem, sto, ref = p["cpu"], p["memory"], p["requiredStorage"], p["referenceDevice"]

    peripheral_blocks = _load_ref_json(p, "peripheralsRef", profiles_dir) or []
    peripheral_blocks = sorted(peripheral_blocks, key=lambda b: b.get("order", 999))
    blocks = [render_peripheral_block(b) for b in peripheral_blocks]

    last_validated = ""
    if p.get("lastValidated") and p["lastValidated"] != "n/a":
        last_validated = f'last validated {esc(p["lastValidated"])}'

    ref_line = esc(ref["name"])
    if ref.get("soc"):
        ref_line += f' ({esc(ref["soc"])})'

    return (
        '<div class="card" style="max-width:none; margin-bottom:20px;">'
        '<div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:10px;">'
        f'<h3 style="margin:0;">{esc(p["profileName"])}</h3>'
        f'{status_pill(p["validationStatus"])}'
        f'<span style="font-size:0.78rem; color:var(--muted);">{last_validated}</span>'
        '</div>'
        '<div class="hwcompat-summary">'
        f'<span><strong>CPU:</strong> {esc(cpu["architecture"])}, \u2265 {esc(cpu["minClockGHz"])} GHz, {esc(cpu["minCores"])} cores (reference: {esc(cpu["family"])})</span>'
        f'<span><strong>RAM:</strong> {esc(mem["minRamMB"])} MB</span>'
        f'<span><strong>Flash:</strong> {esc(sto["minFlashMB"])} MB</span>'
        f'<span><strong>Reference device:</strong> {ref_line}</span>'
        '</div>'
        '<div class="subhead" style="margin-top:18px;">Peripheral Requirements</div>'
        '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:16px;">'
        + "".join(blocks) +
        '</div>'
        + render_memory_footprint_table(p, profiles_dir) +
        render_cpu_utilization_table(p, profiles_dir) +
        render_regional_section(p, profiles_dir) +
        '</div>'
    )


def render_not_covered_list(profiles: list[dict]) -> str:
    rows = []
    for p in profiles:
        if p.get("coverageNote"):
            status = p["coverageNote"]
        elif p["validationStatus"] != "not-started":
            status = "RDK8-based target values available \u2014 see Profile Details (based on RDK8) below."
        else:
            status = ""
        rows.append(
            "<tr><td>" + esc(p["profileName"]) + "</td><td>" + esc(PROFILE_DEFINITIONS.get(p["profileId"], ""))
            + "</td><td>" + esc(status) + "</td></tr>"
        )
    return (
        '<table class="def-table"><thead><tr><th>Device Profile</th><th>Definition</th>'
        "<th>Status</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )


EXTRA_CSS = """
<style>
  .hwcompat-summary { display: flex; flex-wrap: wrap; gap: 8px 22px; font-size: 0.85rem; color: var(--muted); }
  .hwcompat-summary strong { color: var(--ink); font-weight: 600; }
  .hwc-block { border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; background: #fff; }
  .hwc-block-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
  .hwc-block-title { font-weight: 700; font-size: 0.85rem; color: var(--ink); margin-right: 2px; }
  .hwc-block-meta { font-size: 0.8rem; color: var(--muted); line-height: 1.7; }
  .hwc-block-meta strong { color: var(--ink); font-weight: 600; }
  .hwc-notes { font-size: 0.78rem; color: #9aa1ad; line-height: 1.55; margin: 8px 0 0; }
</style>
"""


def build_page(profiles_dir: Path, repo_root: Path = None) -> str:
    profiles = load_profiles(profiles_dir)
    # rdk8_data: the 2 profiles with real (RDK8-based target) CPU/RAM/flash
    # and peripheral data -- still shown in their own detail sections below,
    # just not called "in scope" anymore (see render_coverage_table).
    rdk8_data = [p for p in profiles if p["validationStatus"] != "not-started"]

    body = f'''
{render_hero("Hardware Compatibility", "Hardware Compatibility Spec",
    "Minimum CPU, RAM, flash, and required peripheral hardware per RDK-B device profile, "
    "validated against a BPI-R4 (MT7988/Filogic) reference platform.",
    compact=True, visual_key="hwcompat")}

<section class="tight-top">
  <div class="callout">
    <strong>Values are current design targets</strong>
    <p>CPU/RAM/flash minimums and peripheral requirements below reflect design intent and reference
    the existing RDK8 Broadband Release. Memory Footprint by Process is intentionally TBD for every
    component &mdash; per-process RSS can only be measured once Core RDK Broadband is operationalized
    on the reference platform. Fine-tuned, measured values will replace these targets as that
    validation completes.</p>
  </div>
</section>

<section class="tight-top">
  <div class="section-head"><h2>Device Profile Coverage</h2>
    <p>The RDK-B Component List 2026 defines seven device profiles. None are validated against an
    operationalized Core RDK Broadband build in this revision; two have RDK8-based target values
    available below.</p>
  </div>
  {render_coverage_table(profiles)}
</section>

<section class="tight-top">
  <div class="section-head"><h2>Minimum CPU, Memory, and Flash Storage (based on RDK8)</h2></div>
  {render_minimums_table(rdk8_data, profiles_dir)}
</section>

{render_flash_details_section(profiles_dir)}

<section class="tight-top">
  <div class="section-head"><h2>Profile Details (based on RDK8)</h2>
    <p>Full CPU/memory/flash minimums and peripheral requirements, from the RDK8 Broadband Release,
    for the two profiles with target data available.</p>
  </div>
  {"".join(render_profile_card(p, profiles_dir) for p in rdk8_data)}
</section>

<section class="tight-top">
  <div class="section-head"><h2>Not Yet Covered</h2>
    <p>Defined in the RDK-B Component List 2026; not yet validated against an operationalized
    Core RDK Broadband build in this revision.</p>
  </div>
  {render_not_covered_list(profiles)}
</section>
'''
    head_extra = "<title>Hardware Compatibility Spec \u2014 RDK-B Core Broadband</title>\n" + EXTRA_CSS
    return render_page("hwcompat", head_extra, body)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profiles-dir", default="docs")
    ap.add_argument("--repo-root", default=".", help="Unused (kept for backward compatibility with older invocations)")
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "hardware-compatibility.html"
    path.write_text(build_page(Path(args.profiles_dir), Path(args.repo_root)), encoding="utf-8")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
