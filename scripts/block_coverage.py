#!/usr/bin/env python3
"""Estimate diagnostic coverage per block from results.csv.

Input CSV must include:
  fault_class, detected

Default mapping:
  control -> CPU
  interconnect -> interconnect
  memory -> memory

Usage:
  python3 scripts/block_coverage.py results.csv --out block_coverage.csv
  python3 scripts/block_coverage.py results.csv --out block_coverage.csv --config scripts/fusa_config.json
"""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Optional

TRUTHY = {"1", "y", "yes", "true", "t"}

DEFAULT_MAP = {
    "control": "CPU",
    "interconnect": "interconnect",
    "memory": "memory",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("input", help="results.csv with fault_class,detected")
    p.add_argument("--out", required=True, help="output CSV path")
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


def main() -> int:
    args = parse_args()
    in_path = Path(args.input)
    out_path = Path(args.out)

    if not in_path.exists():
        print(f"Input not found: {in_path}")
        return 1

    cfg = load_config(args.config).get("block_coverage", {})
    block_map = cfg.get("block_map", DEFAULT_MAP)

    total = defaultdict(int)
    detected = defaultdict(int)

    with in_path.open(newline="") as f:
        reader = csv.DictReader(f)
        required = {"fault_class", "detected"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            print(f"Missing required columns: {', '.join(sorted(missing))}")
            return 2

        for row in reader:
            fc = (row.get("fault_class") or "").strip() or "other"
            block = block_map.get(fc, "other")
            total[block] += 1
            det = (row.get("detected") or "").strip().lower() in TRUTHY
            detected[block] += 1 if det else 0

    rows = []
    for block in sorted(total.keys()):
        t = total[block]
        d = detected[block]
        dc = 0.0 if t == 0 else (d / t) * 100.0
        rows.append(
            {
                "block": block,
                "detected": d,
                "total": t,
                "dc_percent": f"{dc:.1f}",
            }
        )

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["block", "detected", "total", "dc_percent"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
