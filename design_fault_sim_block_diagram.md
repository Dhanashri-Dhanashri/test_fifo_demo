# FIFO Safety Demo: Design + Fault Injection + Safety Mechanisms

## 1) Complete Design Block Diagram (Safety Design Enabled)

```mermaid
flowchart LR
    TB["fifo_tb.v (testbench)<br/>Stimulus: +test1 / +test2"] --> DUT["FIFO (fifo_sm.v)<br/>Top DUT"]

    DUT --> CTRL["Control Path<br/>DoRead / DoWrite gating"]
    DUT --> RED["Redundancy Monitors<br/>FL_IF vs FL_SM<br/>RP_IF vs RP_SM<br/>WP_IF vs WP_SM"]
    DUT --> MEMTOP["SDPRAM_TOP (sdpram.v)"]

    MEMTOP --> ENC["ECC_8BIT_ENC<br/>8b -> 12b encoded"]
    ENC --> RAM["SDPRAM mem_array<br/>stored word width = DATA+4"]
    RAM --> DEC["ECC_8BIT_DEC<br/>syndrome + correction"]
    DEC --> OUT["DataOut + EccError"]

    RED --> ERR["Error Aggregation<br/>FlagError | ReadError | WriteError"]
    OUT --> ERR2["EccError"]
    ERR --> EOUT["DUT Error output"]
    ERR2 --> EOUT
```

## 2) Fault Injection and Simulation Flow

```mermaid
flowchart TD
    A["RTL + testbench compile (VCS)"] --> B["Fault campaign setup<br/>COLLATERAL/FCM/fcm.tcl"]
    B --> C["Fault generation from SFF<br/>config.sff + faults.sff"]
    C --> D["Run testcases (test1, test2)"]
    D --> E["Fault simulation (fsim)"]
    E --> F["Coverage report: fsim_v.rpt"]
    E --> G["Optional FM waveform dump<br/>FID 130 -> fm_fid130_test1.fsdb"]
    F --> H["analyze_report.py + fusa_config.json"]
    H --> I["CSV outputs:<br/>fault_class_vs_detection_summary.csv<br/>estimated_block_diagnostic_coverage.csv<br/>latent_risk_by_block.csv<br/>top_latent_locations.csv"]
```

## 3) Safety Mechanisms Used Here (Mapped to Analysis)

```mermaid
flowchart LR
    F1["Injected Fault Classes<br/>PORT permanent faults"] --> M1["Memory-related locations"]
    F1 --> M2["Control-related locations"]
    F1 --> M3["Unmapped/other"]

    M1 --> S1["ECC syndrome detection/correction<br/>(ECC_8BIT_ENC/DEC + EccError)"]
    M2 --> S2["Redundant compare<br/>(duplicate FLAGS / pointers)"]
    M2 --> S3["Functional checks<br/>(ReadEn/WriteEn/clock/data path checks)"]
    M3 --> S4["Unknown mechanism"]

    S1 --> R1["Observed DC: 23.44% (memory)"]
    S2 --> R2["Observed DC: 90.79% (control, redundant_compare)"]
    S3 --> R3["Observed DC: 25.00% (control, functional_check)"]
    S4 --> R4["Observed DC: 30.00% (other)"]
```

## Notes
- Diagram reflects `+define+USE_SAFETY_DESIGN` and `+define+USE_SDPRAM_TOP` from `rtl.f`.
- Detection/coverage labels are based on your current generated CSVs in `fsim_analysis_out/`.
