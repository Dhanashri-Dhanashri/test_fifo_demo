# `analyze_report.py` Safety Analysis Summary

## What the script calculates
- Parses each fault record from `fsim_v.rpt` using configurable regex rules.
- Classifies each fault into:
  - `fault_class` (e.g., control/data/state/other)
  - `detection_mechanism` (e.g., parity/ECC/watchdog/unknown)
  - `block` (via config mapping, e.g., CPU/interconnect/memory)
- Determines `detected` as a boolean from configured detected status values.

## Core metrics and formulas
- For each `(fault_class, block, detection_mechanism)`:
  - `total_faults = count`
  - `detected_faults = sum(detected)`
  - `latent_faults = total_faults - detected_faults`
  - `estimated_dc_percent = 100 * detected_faults / total_faults`
- For each `block`:
  - Same totals + `estimated_dc_percent`
- Latent risk:
  - `latent_percent = 100 * latent_faults / total_faults`
  - `high_risk = latent_percent >= threshold_percent` (from config)
  - Top latent locations ranked by `latent_count`

## Outputs generated
- `parsed_faults.csv`
- `fault_class_vs_detection_summary.csv`
- `estimated_block_diagnostic_coverage.csv`
- `latent_risk_by_block.csv`
- `top_latent_locations.csv`

## What problems this solves
- Replaces manual fault-log review with repeatable, configuration-driven analysis.
- Quantifies diagnostic coverage by architecture block for functional safety tracking.
- Exposes latent-fault hot spots and high-risk blocks early for targeted mitigation.
- Produces auditable CSV evidence for safety reviews and closure planning.

## Diagram companion
- Detailed block diagrams are in `design_fault_sim_block_diagram.md`:
  - Complete RTL safety design
  - Fault injection + simulation flow
  - Safety mechanisms mapped to measured diagnostic coverage
