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

### 5. Launch the React + TypeScript Web Frontend (Recommended)

```bash
cd frontend
npm install
npm run dev
```

Open **`http://localhost:5173/`** to access the high-performance React + TypeScript investigation console featuring:
- **Canvas Particle HUD & Telemetry**: Live physics graph simulation with interactive mouse repulsion.
- **Dynamic Metric Cards & Triage Stream**: Instant client-side search across wallet IDs and pattern signatures.
- **Interactive SHAP Attribution**: Directional risk impact bars and exact delta values.
- **Topological Subgraph Explorer**: Force-directed multi-hop transaction flow and broadcast IP geolocations with zoom, pan, and dragging.
- **Model Insights & Export Tools**: Global feature rankings, pattern distributions, CSV export, and Markdown forensic dossier generation.

### 6. Deploy the Vercel API endpoint

The repository includes `vercel.json` configured to build the React/Vite investigation frontend from `frontend/` and publish `frontend/dist`. The API health endpoint remains available under `/api`; it has its own minimal `api/requirements.txt`, while `.vercelignore` excludes the heavyweight root ML requirements so PyTorch is not bundled into the serverless function.

Using the Vercel CLI:

```bash
npm install --global vercel
vercel login
vercel --prod
```

Or import the GitHub repository in the Vercel dashboard and deploy with the default settings. The deployed root URL serves the React investigation console. The `/api` endpoint returns JSON health metadata. The offline forensic pipeline remains a local/batch workflow and should not be executed inside a short-lived serverless request.

The Streamlit dashboard is not a native Vercel workload. Deploy it separately on Streamlit Community Cloud or another host that supports persistent Streamlit processes:

```bash
streamlit run dashboard/app.py
```

## Team Name

_To be decided._
