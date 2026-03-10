#!/usr/bin/env python3
"""Compute high-risk latent fault exposure indicators.

Input CSV must include:
  fault_class, detected, status, location

Heuristic indicators:
  - undetected_rate by fault_class and block
  - top undetected locations
  - flags any group above threshold (default 20%)

Usage:
  python3 scripts/latent_risk.py results.csv --out latent_risk.csv
  python3 scripts/latent_risk.py results.csv --out latent_risk.csv --config scripts/fusa_config.json
"""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Optional

TRUTHY = {"1", "y", "yes", "true", "t"}

BLOCK_MAP = {
    "control": "CPU",
    "interconnect": "interconnect",
    "memory": "memory",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("input", help="results.csv with fault_class,detected,status,location")
    p.add_argument("--out", required=True, help="output CSV path")
    p.add_argument("--threshold", type=float, default=20.0, help="undetected rate percent threshold")
    p.add_argument("--top", type=int, default=10, help="top undetected locations to report")
    p.add_argument("--config", help="JSON config file")
    return p.parse_args()


def load_config(path: Optional[str]):
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {p}")
    with p.open() as f:
        return json.load(f)


def is_detected(val: str) -> bool:
    return (val or "").strip().lower() in TRUTHY


def main() -> int:
    args = parse_args()
    in_path = Path(args.input)
    out_path = Path(args.out)

    if not in_path.exists():
        print(f"Input not found: {in_path}")
        return 1

    cfg = load_config(args.config).get("latent_risk", {})
    block_map = cfg.get("block_map", BLOCK_MAP)
    threshold = cfg.get("threshold_percent", args.threshold)
    top_n = cfg.get("top_locations", args.top)

    req = {"fault_class", "detected", "status", "location"}
    by_class = defaultdict(lambda: [0, 0])  # total, undetected
    by_block = defaultdict(lambda: [0, 0])  # total, undetected
    undet_loc = defaultdict(int)

    with in_path.open(newline="") as f:
        reader = csv.DictReader(f)
        missing = req - set(reader.fieldnames or [])
        if missing:
            print(f"Missing required columns: {', '.join(sorted(missing))}")
            return 2

        for row in reader:
            fc = (row.get("fault_class") or "").strip() or "other"
            block = block_map.get(fc, "other")
            det = is_detected(row.get("detected"))
            loc = (row.get("location") or "").strip() or "(unknown)"

            by_class[fc][0] += 1
            by_block[block][0] += 1
            if not det:
                by_class[fc][1] += 1
                by_block[block][1] += 1
                undet_loc[loc] += 1

    def rate(undet, total):
        return 0.0 if total == 0 else (undet / total) * 100.0

    rows = []
    for fc, (total, undet) in sorted(by_class.items()):
        r = rate(undet, total)
        rows.append(
            {
                "indicator_type": "fault_class",
                "name": fc,
                "undetected": undet,
                "total": total,
                "undetected_rate_percent": f"{r:.1f}",
                "high_risk": "Y" if r >= threshold else "N",
            }
        )

    for blk, (total, undet) in sorted(by_block.items()):
        r = rate(undet, total)
        rows.append(
            {
                "indicator_type": "block",
                "name": blk,
                "undetected": undet,
                "total": total,
                "undetected_rate_percent": f"{r:.1f}",
                "high_risk": "Y" if r >= threshold else "N",
            }
        )

    for loc, cnt in sorted(undet_loc.items(), key=lambda x: x[1], reverse=True)[: top_n]:
        rows.append(
            {
                "indicator_type": "location",
                "name": loc,
                "undetected": cnt,
                "total": "",
                "undetected_rate_percent": "",
                "high_risk": "Y",
            }
        )

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "indicator_type",
                "name",
                "undetected",
                "total",
                "undetected_rate_percent",
                "high_risk",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} indicators to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
