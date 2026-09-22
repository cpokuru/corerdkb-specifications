"""One-shot: RDK-B_Component_List_2026.xlsx -> JSON -> HTML, in a single command.

Wraps extract_components.py + gen_simple_html.py so a new simple page (Core,
or any device profile) is one call instead of two. Both scripts must sit in
the same folder as this one.

Usage:
    python3 build_simple_page.py core \
        --xlsx RDK-B_Component_List_2026.xlsx \
        --json-out core-b-components.json \
        --html-out core-components.html

    python3 build_simple_page.py profile "GW" \
        --xlsx RDK-B_Component_List_2026.xlsx \
        --json-out gw-components.json \
        --html-out gw-components.html

If --json-out / --html-out are omitted, sensible filenames are derived
automatically (core-b-components.* , or a slugified profile name).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from extract_components import build_payload, extract_core, extract_profile, PROFILE_COLUMNS
import openpyxl

from gen_simple_html import build_html


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="mode", required=True)

    core_p = sub.add_parser("core")
    core_p.add_argument("--xlsx", default="RDK-B_Component_List_2026.xlsx")
    core_p.add_argument("--json-out", default=None)
    core_p.add_argument("--html-out", default=None)

    prof_p = sub.add_parser("profile")
    prof_p.add_argument("profile", help='e.g. "EthWAN WiFi Router"')
    prof_p.add_argument("--xlsx", default="RDK-B_Component_List_2026.xlsx")
    prof_p.add_argument("--json-out", default=None)
    prof_p.add_argument("--html-out", default=None)
    prof_p.add_argument("--required-only", action="store_true", help="Omit Optional components; show only Required.")
    prof_p.add_argument("--show-core", action="store_true", help="Tag CORE components as 'Common Core' instead of Required/Optional.")

    args = p.parse_args()
    wb = openpyxl.load_workbook(Path(args.xlsx), data_only=True)
    ws = wb["Components"]

    if args.mode == "core":
        components = extract_core(ws)
        payload = build_payload(
            components,
            title="Core RDK-B Components",
            subtitle="Components common to every RDK-B device profile, or required wherever they apply.",
            tier_ids=["common-core", "required"],
        )
        json_out = args.json_out or "core-b-components.json"
        html_out = args.html_out or "core-components.html"
    else:
        components = extract_profile(ws, args.profile, required_only=args.required_only, show_core=args.show_core)
        if args.required_only:
            tier_ids = ["required"]
        elif args.show_core:
            tier_ids = ["common-core", "required", "optional"]
        else:
            tier_ids = ["required", "optional"]
        subtitle = f"Components required for the {args.profile} device profile." if args.required_only \
            else f"Components for the {args.profile} device profile: Common Core, Required, and Optional." if args.show_core \
            else f"Components that apply to the {args.profile} device profile."
        payload = build_payload(
            components,
            title=f"RDK-B {args.profile} Components",
            subtitle=subtitle,
            tier_ids=tier_ids,
        )
        slug = slugify(args.profile)
        json_out = args.json_out or f"{slug}-components.json"
        html_out = args.html_out or f"{slug}-components.html"

    Path(json_out).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    Path(html_out).write_text(build_html(payload), encoding="utf-8")

    print(f"Wrote {json_out} ({len(components)} components)")
    print(f"Wrote {html_out}")


if __name__ == "__main__":
    main()
