#!/usr/bin/env python3
"""Parse fsim_v.rpt FaultList into results CSV for mapping summary.

Outputs CSV with columns:
  fault_class, detection_mechanism, detected, status, location

Usage:
  python3 scripts/parse_fsim_rpt.py fsim_v.rpt --out results.csv
  python3 scripts/parse_fsim_rpt.py fsim_v.rpt --out results.csv --config scripts/fusa_config.json
"""

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Optional


DEFAULT_FAULT_LINE_REGEX = r'<\s*\d+>\s+([A-Z]{2})\s+\d+\s+\{PORT\s+"([^"]+)"\}'
DEFAULT_RULES = [
    (r"\.sdpram_i1\.|ECC_|R_DataOut|L_DataIn|DataOutEnc|DataInEnc", "memory", "ecc_syndrome"),
    (r"\.FL_|\.RP_|\.WP_", "control", "redundant_compare"),
    (r"\.ReadEn|\.WriteEn|\.ReadClk|\.WriteClk|\.DataIn\[|\.DataOut\[", "interconnect", "functional_check"),
]
DEFAULT_DETECTED_STATUS = {"ND", "OD", "PD", "AD"}
DEFAULT_FC = "other"
DEFAULT_DM = "unknown"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("input", help="fsim_v.rpt path")
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


def classify(location: str, rules, default_fc, default_dm):
    for regex, fclass, mech in rules:
        if regex.search(location):
            return fclass, mech
    return default_fc, default_dm


def main() -> int:
    args = parse_args()
    in_path = Path(args.input)
    out_path = Path(args.out)

    if not in_path.exists():
        print(f"Input not found: {in_path}")
        return 1

    cfg = load_config(args.config).get("parse_fsim_rpt", {})
    fault_line_regex = cfg.get("fault_line_regex", DEFAULT_FAULT_LINE_REGEX)
    detected_status = set(cfg.get("detected_status", list(DEFAULT_DETECTED_STATUS)))
    rules_cfg = cfg.get("rules", [])
    default_fc = cfg.get("default_fault_class", DEFAULT_FC)
    default_dm = cfg.get("default_detection_mechanism", DEFAULT_DM)

    rules = []
    if rules_cfg:
        for r in rules_cfg:
            rules.append((re.compile(r["regex"], re.IGNORECASE), r["fault_class"], r["detection_mechanism"]))
    else:
        for regex, fc, dm in DEFAULT_RULES:
            rules.append((re.compile(regex, re.IGNORECASE), fc, dm))

    fault_line_re = re.compile(fault_line_regex)

    rows = []
    in_fault_list = False

    with in_path.open() as f:
        for line in f:
            line = line.strip()
            if line.startswith("FaultList"):
                in_fault_list = True
                continue
            if in_fault_list and line.startswith("}"):
                break
            if not in_fault_list:
                continue

            m = fault_line_re.search(line)
            if not m:
                continue

            status = m.group(1)
            location = m.group(2)
            fclass, mech = classify(location, rules, default_fc, default_dm)
            detected = "Y" if status in detected_status else "N"

            rows.append(
                {
                    "fault_class": fclass,
                    "detection_mechanism": mech,
                    "detected": detected,
                    "status": status,
                    "location": location,
                }
            )

    if not rows:
        print("No faults parsed. Check format or regex.")
        return 2

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "fault_class",
                "detection_mechanism",
                "detected",
                "status",
                "location",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
