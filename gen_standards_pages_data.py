"""Derive architecture-standards.json, technical-governance.json,
architecture-standards-industry.json, technical-governance-process.json, and
component-governance.json (the data files the stub-page loader fetches at
runtime) from docs/spec-content.json's governance_standards (§7.1.1 +
§7.1.2), industry_standards (§7.1.3), technical_governance_process (§7.2),
and component_governance_process (§7.3).

Run this right after build_site.py (which regenerates spec-content.json from
the PDF) and before/after gen_stub_pages.py — order between those two doesn't
matter, since the stub HTML is a static shell that fetches its JSON at
runtime rather than baking data in at generation time.

Usage:
    python3 gen_standards_pages_data.py --out-dir .
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec-json", default="docs/spec-content.json")
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()

    spec = json.loads(Path(args.spec_json).read_text(encoding="utf-8"))
    rows = spec.get("governance_standards", [])
    industry_rows = spec.get("industry_standards", [])
    tech_process = spec.get("technical_governance_process", [])
    component_process = spec.get("component_governance_process", [])

    arch = [r for r in rows if r.get("section") == "7.1.1"]
    tech = [r for r in rows if r.get("section") == "7.1.2"]

    def to_docs(rows: list[dict]) -> list[dict]:
        return [{"Standard": r["name"], "Requirements": r["requirement"]} for r in rows]

    def industry_to_docs(rows: list[dict]) -> list[dict]:
        return [
            {
                "Category": r.get("category", ""),
                "Standard / Body": r.get("standard", ""),
                "Applies To": r.get("applies_to", ""),
                "Note": r.get("note", ""),
            }
            for r in rows
        ]

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    arch_payload = {"source": f"{spec.get('sourcePdf', '')} §7.1.1", "docs": to_docs(arch)}
    tech_payload = {"source": f"{spec.get('sourcePdf', '')} §7.1.2", "docs": to_docs(tech)}
    industry_payload = {"source": f"{spec.get('sourcePdf', '')} §7.1.3", "docs": industry_to_docs(industry_rows)}
    tech_process_payload = {"source": f"{spec.get('sourcePdf', '')} §7.2", "docs": tech_process}
    component_process_payload = {"source": f"{spec.get('sourcePdf', '')} §7.3", "docs": component_process}

    (out_dir / "architecture-standards.json").write_text(
        json.dumps(arch_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "technical-governance.json").write_text(
        json.dumps(tech_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "architecture-standards-industry.json").write_text(
        json.dumps(industry_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "technical-governance-process.json").write_text(
        json.dumps(tech_process_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "component-governance.json").write_text(
        json.dumps(component_process_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote architecture-standards.json ({len(arch)} entries)")
    print(f"Wrote technical-governance.json ({len(tech)} entries)")
    print(f"Wrote architecture-standards-industry.json ({len(industry_rows)} entries)")
    print(f"Wrote technical-governance-process.json ({len(tech_process)} sections)")
    print(f"Wrote component-governance.json ({len(component_process)} sections)")


if __name__ == "__main__":
    main()
