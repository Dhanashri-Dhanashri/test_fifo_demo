#!/usr/bin/env python3
"""
Generate three safety-analysis summaries from a VC Z01X fsim report:

1) Fault class vs detection mechanism mapping summary
2) Estimated diagnostic coverage per block (CPU / interconnect / memory)
3) High-risk latent fault exposure indicators

Usage:
    python analyze_fsim.py --report fsim_v.rpt --config fault_mapping_config.json

Optional:
    python analyze_fsim.py --report fsim_v.rpt --config fault_mapping_config.json --outdir results

Expected config structure matches the JSON you shared.
"""

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from typing import Tuple

import pandas as pd


def load_config(config_path: str) -> dict:
    with open(config_path, "r") as f:
        return json.load(f)


def compile_rules(cfg: dict):
    parse_cfg = cfg["parse_fsim_rpt"]
    fault_line_regex = re.compile(parse_cfg["fault_line_regex"])
    detected_status = set(parse_cfg["detected_status"])
    rules = []
    for rule in parse_cfg["rules"]:
        rules.append(
            {
                "pattern": re.compile(rule["regex"]),
                "fault_class": rule["fault_class"],
                "detection_mechanism": rule["detection_mechanism"],
            }
        )
    default_fault_class = parse_cfg.get("default_fault_class", "other")
    default_detection_mechanism = parse_cfg.get("default_detection_mechanism", "unknown")
    return fault_line_regex, detected_status, rules, default_fault_class, default_detection_mechanism


def classify_location(
    location: str,
    rules: list,
    default_fault_class: str,
    default_detection_mechanism: str,
):
    for rule in rules:
        if rule["pattern"].search(location):
            return rule["fault_class"], rule["detection_mechanism"]
    return default_fault_class, default_detection_mechanism


def parse_fsim_report(
    report_path: str,
    fault_line_regex,
    rules,
    detected_status,
    default_fault_class: str,
    default_detection_mechanism: str,
) -> pd.DataFrame:
    records = []

    with open(report_path, "r", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            match = fault_line_regex.search(line)
            if not match:
                continue

            status = match.group(1)
            location = match.group(2)

            fault_class, detection_mechanism = classify_location(
                location,
                rules,
                default_fault_class,
                default_detection_mechanism,
            )

            records.append(
                {
                    "location": location,
                    "status": status,
                    "fault_class": fault_class,
                    "detection_mechanism": detection_mechanism,
                    "detected": status in detected_status,
                }
            )

    if not records:
        raise ValueError("No fault entries were parsed from the report. Check the regex and report format.")

    df = pd.DataFrame(records)
    return df


def add_block_mapping(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    block_map = cfg["block_coverage"]["block_map"]
    df = df.copy()
    df["block"] = df["fault_class"].map(block_map).fillna("other")
    return df


def compute_fault_class_vs_detection_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["fault_class", "block", "detection_mechanism"], dropna=False)
        .agg(
            total_faults=("location", "count"),
            detected_faults=("detected", "sum"),
        )
        .reset_index()
    )
    summary["latent_faults"] = summary["total_faults"] - summary["detected_faults"]
    summary["estimated_dc_percent"] = (
        100.0 * summary["detected_faults"] / summary["total_faults"]
    ).round(2)
    summary = summary.sort_values(
        by=["block", "fault_class", "detection_mechanism"]
    ).reset_index(drop=True)
    return summary


def compute_block_coverage(df: pd.DataFrame) -> pd.DataFrame:
    coverage = (
        df.groupby("block", dropna=False)
        .agg(
            total_faults=("location", "count"),
            detected_faults=("detected", "sum"),
        )
        .reset_index()
    )
    coverage["latent_faults"] = coverage["total_faults"] - coverage["detected_faults"]
    coverage["estimated_dc_percent"] = (
        100.0 * coverage["detected_faults"] / coverage["total_faults"]
    ).round(2)
    coverage = coverage.sort_values(by="block").reset_index(drop=True)
    return coverage


def compute_latent_risk(df: pd.DataFrame, cfg: dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    latent_cfg = cfg["latent_risk"]
    threshold_percent = float(latent_cfg.get("threshold_percent", 20.0))
    top_locations = int(latent_cfg.get("top_locations", 10))

    # Block-level latent exposure
    by_block = (
        df.groupby("block", dropna=False)
        .agg(
            total_faults=("location", "count"),
            latent_faults=("detected", lambda x: (~x).sum()),
        )
        .reset_index()
    )
    by_block["latent_percent"] = (
        100.0 * by_block["latent_faults"] / by_block["total_faults"]
    ).round(2)
    by_block["high_risk"] = by_block["latent_percent"] >= threshold_percent
    by_block = by_block.sort_values(
        by=["high_risk", "latent_percent", "latent_faults"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    # Location-level latent hot spots
    latent_only = df[~df["detected"]].copy()
    if latent_only.empty:
        top_latent = pd.DataFrame(
            columns=[
                "location",
                "block",
                "fault_class",
                "detection_mechanism",
                "latent_count",
                "statuses",
            ]
        )
    else:
        grouped = []
        for location, subdf in latent_only.groupby("location", dropna=False):
            grouped.append(
                {
                    "location": location,
                    "block": subdf["block"].iloc[0],
                    "fault_class": subdf["fault_class"].iloc[0],
                    "detection_mechanism": subdf["detection_mechanism"].iloc[0],
                    "latent_count": len(subdf),
                    "statuses": ",".join(sorted(Counter(subdf["status"]).keys())),
                }
            )
        top_latent = pd.DataFrame(grouped).sort_values(
            by=["latent_count", "block", "location"],
            ascending=[False, True, True],
        ).head(top_locations).reset_index(drop=True)

    return by_block, top_latent


def print_section(title: str):
    print("\n" + "=" * len(title))
    print(title)
    print("=" * len(title))


def print_dataframe(df: pd.DataFrame):
    if df.empty:
        print("(no rows)")
    else:
        print(df.to_string(index=False))


def ensure_outdir(path: str):
    os.makedirs(path, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Analyze VC Z01X fsim report for safety summaries.")
    parser.add_argument("--report", required=True, help="Path to fsim report, e.g. fsim_v.rpt")
    parser.add_argument("--config", required=True, help="Path to JSON config file")
    parser.add_argument("--outdir", default="fsim_analysis_out", help="Directory for CSV outputs")
    args = parser.parse_args()

    cfg = load_config(args.config)
    (
        fault_line_regex,
        detected_status,
        rules,
        default_fault_class,
        default_detection_mechanism,
    ) = compile_rules(cfg)

    df = parse_fsim_report(
        args.report,
        fault_line_regex,
        rules,
        detected_status,
        default_fault_class,
        default_detection_mechanism,
    )
    df = add_block_mapping(df, cfg)

    mapping_summary = compute_fault_class_vs_detection_summary(df)
    block_coverage = compute_block_coverage(df)
    latent_by_block, top_latent_locations = compute_latent_risk(df, cfg)

    ensure_outdir(args.outdir)

    raw_csv = os.path.join(args.outdir, "parsed_faults.csv")
    mapping_csv = os.path.join(args.outdir, "fault_class_vs_detection_summary.csv")
    block_csv = os.path.join(args.outdir, "estimated_block_diagnostic_coverage.csv")
    latent_block_csv = os.path.join(args.outdir, "latent_risk_by_block.csv")
    latent_locations_csv = os.path.join(args.outdir, "top_latent_locations.csv")

    df.to_csv(raw_csv, index=False)
    mapping_summary.to_csv(mapping_csv, index=False)
    block_coverage.to_csv(block_csv, index=False)
    latent_by_block.to_csv(latent_block_csv, index=False)
    top_latent_locations.to_csv(latent_locations_csv, index=False)

    print_section("Parsed Fault Summary")
    print(f"Total parsed faults: {len(df)}")
    print(f"Detected statuses used: {sorted(detected_status)}")
    print(f"Output directory: {os.path.abspath(args.outdir)}")

    print_section("1) Fault class vs detection mechanism mapping summary")
    print_dataframe(mapping_summary)

    print_section("2) Estimated diagnostic coverage per block")
    print_dataframe(block_coverage)

    print_section("3) High-risk latent fault exposure indicators")
    print("By block:")
    print_dataframe(latent_by_block)

    print("\nTop latent locations:")
    print_dataframe(top_latent_locations)

    print_section("Generated Files")
    print(raw_csv)
    print(mapping_csv)
    print(block_csv)
    print(latent_block_csv)
    print(latent_locations_csv)


if __name__ == "__main__":
    main()
