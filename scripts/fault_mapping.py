#!/usr/bin/env python3
"""Generate Fault Class vs Detection Mechanism mapping summary.

Input: CSV with at least these columns:
  fault_class, detection_mechanism, detected

Optional columns (kept for reference):
  injection, notes, block, time

Example row:
  memory_single_bit, ecc_syndrome, Y

Usage:
  python3 scripts/fault_mapping.py results.csv
  python3 scripts/fault_mapping.py results.csv --out summary.csv
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path

TRUTHY = {"1", "y", "yes", "true", "t"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("input", help="CSV with fault_class,detection_mechanism,detected")
    p.add_argument("--out", help="write summary CSV to this path")
    return p.parse_args()


def normalize_detected(val: str) -> int:
    if val is None:
        return 0
    return 1 if str(val).strip().lower() in TRUTHY else 0


def main() -> int:
    args = parse_args()
    in_path = Path(args.input)

    if not in_path.exists():
        print(f"Input not found: {in_path}")
        return 1

    # key: (fault_class, detection_mechanism) -> [detected_count, total]
    agg = defaultdict(lambda: [0, 0])

    with in_path.open(newline="") as f:
        reader = csv.DictReader(f)
        required = {"fault_class", "detection_mechanism", "detected"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            print(f"Missing required columns: {', '.join(sorted(missing))}")
            return 2

        for row in reader:
            fc = (row.get("fault_class") or "").strip() or "(unknown)"
            dm = (row.get("detection_mechanism") or "").strip() or "(none)"
            det = normalize_detected(row.get("detected"))
            agg[(fc, dm)][0] += det
            agg[(fc, dm)][1] += 1

    # Prepare rows
    out_rows = []
    for (fc, dm), (det_cnt, total) in sorted(agg.items()):
        dc = 0.0 if total == 0 else (det_cnt / total) * 100.0
        out_rows.append(
            {
                "fault_class": fc,
                "detection_mechanism": dm,
                "detected": det_cnt,
                "total": total,
                "dc_percent": f"{dc:.1f}",
            }
        )

    # Print table
    header = ["fault_class", "detection_mechanism", "detected", "total", "dc_percent"]
    print(",".join(header))
    for r in out_rows:
        print(",".join(
            [
                r["fault_class"],
                r["detection_mechanism"],
                str(r["detected"]),
                str(r["total"]),
                r["dc_percent"],
            ]
        ))

    if args.out:
        out_path = Path(args.out)
        with out_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            writer.writerows(out_rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
