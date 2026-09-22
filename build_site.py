"""Single entry point for the whole CoreRDK-Broadband-Specification site.

Regenerates the landing page and every *.json data file from source (the
spec PDF and the component xlsx). components/index.html and
components/full-list.html are static templates, committed once — they load
their data at runtime in the browser instead of having it baked in at build
time. This script never rewrites either of them.

Order of operations (each step's output feeds the next):

  1. docs/*.pdf   --(extract_spec_content.py)-->  docs/spec-content.json
  2. docs/spec-content.json  --(gen_base_page.py)-->  index.html (About Core RDK Broadband —
                                                       About comes from docs/about-content.json,
                                                       Architecture comes from spec-content.json)
  3. docs/*.xlsx  --(gen_html.py --sync-only)-->  components/RDK-B_Component_List_2026.xlsx
                                                   (a synced copy — full-list.html loads THIS xlsx
                                                    directly client-side via SheetJS, same-directory
                                                    fetch, so the file has to physically sit next to it)
  4. docs/*.xlsx  --(extract_components.py)-->  components/<profile>-components.json
                                                 one file per device profile column in the xlsx (see
                                                 ALL_PROFILES below) -- ethwan-router-components.json
                                                 is fetched at runtime by the static components/index.html;
                                                 the rest feed gen_hwcompat_page.py's per-profile
                                                 "Memory Footprint by Process" tables and anything else
                                                 that wants a per-profile component list.

Both source files (the spec PDF and the component xlsx) live together in
docs/. components/ holds the generator scripts, the two static HTML
templates, and the synced xlsx + generated JSON — no hand-maintained data.

Usage:
    python3 build_site.py
    python3 build_site.py --skip-pdf               # reuse existing docs/spec-content.json
    python3 build_site.py --skip-xlsx               # reuse existing components/* data
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
COMPONENTS = ROOT / "components"

# Every device-profile column in RDK-B_Component_List_2026.xlsx, and the
# output filename each becomes under components/. Column names with an
# embedded newline (xlsx header-wrap artifacts, e.g. "GW\nOpenSync") are
# required verbatim here for the exact-match lookup in extract_components.py
# -- that script normalizes them for display text on its own.
#
# ethwan-router-components.json keeps its existing name since
# components/index.html and components/gen_components_page.py already
# depend on it by that exact filename; every other profile follows the
# <profile-id>-components.json pattern already used by
# gen_hwcompat_page.py's PROFILE_COMPONENTS_FILE.
ALL_PROFILES: list[tuple[str, str]] = [
    ("Modem\n/ONU", "modem-onu-components.json"),
    ("EthWAN WiFi Router", "ethwan-router-components.json"),
    ("GW", "gw-components.json"),
    ("GW\nOpenSync", "gw-opensync-components.json"),
    ("GW\nEasyMesh", "gw-easymesh-components.json"),
    ("EXT\nOpenSync", "ext-opensync-components.json"),
    ("EXT\nEasyMesh", "ext-easymesh-components.json"),
]


def find_one(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.glob(pattern))
    if not matches:
        raise SystemExit(f"No file matching {pattern!r} found in {directory}/")
    if len(matches) > 1:
        print(f"  note: multiple matches for {pattern!r} in {directory}/, using the newest: "
              f"{max(matches, key=lambda p: p.stat().st_mtime).name}")
        return max(matches, key=lambda p: p.stat().st_mtime)
    return matches[0]


def run(cmd: list[str], cwd: Path) -> None:
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    subprocess.run([sys.executable if cmd[0] == "python3" else cmd[0], *cmd[1:]], cwd=cwd, check=True)


def step_pdf_to_json() -> None:
    print("\n[1/4] Spec PDF -> docs/spec-content.json")
    pdf = find_one(DOCS, "*.pdf")
    run(["python3", "extract_spec_content.py", str(pdf.relative_to(ROOT)), "--out", "docs/spec-content.json"], cwd=ROOT)


def step_json_to_base_html() -> None:
    print("\n[2/4] docs/spec-content.json -> index.html")
    run(["python3", "gen_base_page.py", "docs/spec-content.json", "docs/about-content.json", "--out-dir", "."], cwd=ROOT)


def step_sync_workbook_for_full_list() -> None:
    print("\n[3/4] Component xlsx -> components/RDK-B_Component_List_2026.xlsx (synced copy for full-list.html)")
    run(["python3", "gen_html.py", "--sync-only"], cwd=COMPONENTS)


def step_xlsx_to_all_profile_json() -> None:
    xlsx = find_one(DOCS, "*.xlsx")
    xlsx_rel_from_components = Path("..") / xlsx.relative_to(ROOT)
    for profile, out_name in ALL_PROFILES:
        print(f"\n[4/5] Component xlsx -> components/{out_name} (profile: {profile!r})")
        run([
            "python3", "extract_components.py", "profile", profile,
            "--xlsx", str(xlsx_rel_from_components),
            "--out", out_name,
            "--show-core",
        ], cwd=COMPONENTS)


def step_xlsx_to_all_components_json() -> None:
    print("\n[5/5] Component xlsx -> components/all-components.json (every component, any profile -- feeds north-bound-apis.html)")
    xlsx = find_one(DOCS, "*.xlsx")
    xlsx_rel_from_components = Path("..") / xlsx.relative_to(ROOT)
    run([
        "python3", "extract_components.py", "all-components",
        "--xlsx", str(xlsx_rel_from_components),
        "--out", "all-components.json",
    ], cwd=COMPONENTS)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-pdf", action="store_true", help="Reuse existing docs/spec-content.json instead of re-parsing the PDF")
    ap.add_argument("--skip-xlsx", action="store_true", help="Skip both xlsx-driven steps")
    args = ap.parse_args()

    print("Building CoreRDK-Broadband-Docs-Base")
    print("=" * 40)

    if not args.skip_pdf:
        step_pdf_to_json()
    else:
        print("\n[1/5] Skipped (--skip-pdf) — reusing docs/spec-content.json")
    step_json_to_base_html()

    if not args.skip_xlsx:
        step_sync_workbook_for_full_list()
        step_xlsx_to_all_profile_json()
        step_xlsx_to_all_components_json()
    else:
        print("\n[3/5], [4/5], and [5/5] Skipped (--skip-xlsx)")

    print("\nDone. Generated:")
    print("  index.html")
    print("  docs/spec-content.json")
    if not args.skip_xlsx:
        print("  components/RDK-B_Component_List_2026.xlsx  (synced copy, read by full-list.html)")
        for _, out_name in ALL_PROFILES:
            print(f"  components/{out_name}")
        print("  components/all-components.json  (read by north-bound-apis.html)")
    print("\ncomponents/full-list.html is static — not touched by this script.")
    print("Regenerate it with plain 'python3 gen_html.py' (no --sync-only)")
    print("only if the page design itself changes, not the data.")
    print("\ncomponents/index.html IS generated — from ethwan-router-components.json,")
    print("via 'python3 components/gen_components_page.py'. Run that after this")
    print("script (step 4 above regenerates the JSON it reads from).")


if __name__ == "__main__":
    main()
