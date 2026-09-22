"""Builds search-index.json — a flat, searchable list combining content from
all three data sources already in this repo:

  - docs/about-content.json                    (definition, goals, RDK Ready, benefits)
  - docs/spec-content.json                      (five-tier model, test suites,
                                                   governance standards, industry standards)
  - components/ethwan-router-components.json    (61 components)

This powers the floating search chatbox (see layout.py's CHATBOX_SCRIPT) on
every page. It's a plain keyword search, not a real AI — no API key, no
backend, works entirely client-side on GitHub Pages. Answers are shown
directly in the chat panel from the matched text, since some of this data
(governance/industry standards) doesn't have a live page to link to yet —
see architecture-standards.html / technical-governance.html, which are still
empty stubs waiting for their own JSON.

Rerun this after regenerating docs/spec-content.json, docs/about-content.json,
or components/ethwan-router-components.json, so the index stays current.

Usage:
    python3 build_search_index.py --out-dir .
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_index(about: dict, spec: dict, components: dict) -> list[dict]:
    docs = []

    # ---- about-content.json ----
    docs.append({
        "title": "What is RDKB Core?",
        "text": about["definition"],
        "category": "About",
        "url": "index.html#",
    })
    for g in about["goals"]:
        docs.append({
            "title": g["title"],
            "text": f'Goal — {g["goal"]} Challenge — {g["challenge"]}',
            "category": "Why RDKB Core",
            "url": f'index.html#{_slug(g["title"])}',
        })
    for r in about["rdk_ready"]:
        docs.append({
            "title": r["title"],
            "text": r["body"],
            "category": "RDK Ready",
            "url": "index.html#",
        })
    for b in about["benefits"]:
        docs.append({
            "title": b["category"],
            "text": "; ".join(b["items"]),
            "category": "Benefits & uses",
            "url": "index.html#",
        })

    # ---- spec-content.json ----
    for t in spec["five_tier"]:
        if "split" in t:
            text = " ".join(f'{c["title"]}: {c["text"]}' for c in t["split"])
        else:
            text = t["description"]
        docs.append({
            "title": f'Tier {t["tier"]} — {t["layer"]}',
            "text": text,
            "category": "Architecture — five-tier model",
            "url": "index.html#",
        })
    for ts in spec["test_suites"]:
        docs.append({
            "title": ts["name"],
            "text": f'{ts["definition"]} Owner: {ts["owner"]}.',
            "category": "Architecture — test suites",
            "url": "index.html#",
        })
    for gs in spec["governance_standards"]:
        docs.append({
            "title": gs["name"],
            "text": gs["requirement"],
            "category": "Technical Governance",
            "url": "technical-governance.html",
        })
    for ind in spec["industry_standards"]:
        docs.append({
            "title": ind["standard"],
            "text": f'Applies to: {ind["applies_to"]}. {ind["note"]}'.strip(),
            "category": f'Architecture Standards — {ind["category"] or "Other"}',
            "url": "architecture-standards.html",
        })

    # ---- components/ethwan-router-components.json ----
    for c in components["components"]:
        docs.append({
            "title": c["name"],
            "text": f'{c["category"] or "Uncategorized"} · {c["tier"]} tier for the EthWAN WiFi Router profile.',
            "category": "Components",
            "url": "components/",
        })

    return docs


def _slug(text: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()
    root = Path(args.out_dir)

    about = load(root / "docs" / "about-content.json")
    spec = load(root / "docs" / "spec-content.json")
    components = load(root / "components" / "ethwan-router-components.json")

    index = build_index(about, spec, components)
    out_path = root / "search-index.json"
    out_path.write_text(json.dumps({"docs": index}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_path} ({len(index)} searchable entries)")


if __name__ == "__main__":
    main()
