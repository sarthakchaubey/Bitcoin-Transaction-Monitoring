# AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic

## Problem Statement
Build an offline Bitcoin forensics pipeline that monitors and analyzes transaction traffic for suspicious activity.

## Architecture Overview

The project is planned as the following pipeline stages:

1. **Phase 0 — Project scaffolding:** establish the offline Python project structure and environment.
2. **Phase 1 — Synthetic dataset generation:** create representative Bitcoin transaction traffic and evaluation labels.
3. **Phase 2 — Data ingestion:** parse CSV, JSON, and XML transaction sources.
4. **Phase 3 — GeoIP enrichment:** map relevant network information using GeoLite2-City.
5. **Phase 4 — Graph construction:** build entity and transaction graphs.
6. **Phase 5 — Feature engineering:** derive graph, transaction, and temporal features.
7. **Phase 6 — Modeling:** apply Isolation Forest, GraphSAGE, and Louvain methods.
8. **Phase 7 — Explainability:** generate SHAP-based explanations for model findings.
9. **Phase 8 — Dashboard:** present results in a Streamlit application.

## Setup Instructions

Run the setup script from the project root:

```bash
./setup.sh
```

The script creates a virtual environment and installs the dependencies in `requirements.txt`. A free MaxMind account is required to download `GeoLite2-City.mmdb`; place the downloaded database in `geoip/`.

## How to Run

From a fresh clone, run the following sequence:

### 1. Create the environment

```bash
./setup.sh
source .venv/bin/activate
```

On Windows, activate with `.venv\\Scripts\\activate` after creating the environment with the platform-equivalent venv command.

### 2. Add required local data

Download `GeoLite2-City.mmdb` from MaxMind using a free account and place it at `geoip/GeoLite2-City.mmdb`. Place the Phase 1 generated transaction files under `data/raw/` and `ground_truth.csv` at `data/ground_truth/ground_truth.csv`.

This checkout does not currently include the Phase 1 generator or generated datasets, so the exact data-generation command cannot be truthfully documented yet. `data/generate_evidence.py` creates dashboard demonstration evidence only; it is not a substitute for the hidden-label transaction generator.

### 3. Run the full forensic pipeline

```bash
python main.py
```

This generates `data/evidence_packages.json` with ranked wallet alerts, forensic reason sentences, SHAP feature breakdowns, and transaction/IP neighborhood subgraphs.

### 4. Run final evaluation and generate plots

```bash
python -m evaluation.run_full_evaluation
python -m evaluation.generate_plots
```

These commands create `data/evaluation_report.txt`, `data/pipeline_timing.json`, `data/error_analysis.json`, and PNG charts under `data/plots/`.

### 5. Launch the dashboard

```bash
streamlit run dashboard/app.py
```

Or:

```bash
python -m streamlit run dashboard/app.py
```

The dashboard allows investigators to:
- Filter alerts by risk score threshold (0–100), confidence level (High, Medium, Low), behavioral patterns, and wallet ID search.
- View key triage metrics (analyzed wallets, flagged alerts, severity breakdown).
- Inspect forensic reasoning findings and SHAP feature contribution charts.
- Interactively explore local transaction and broadcast IP subgraphs rendered via Pyvis.

## Team Name

_To be decided._
