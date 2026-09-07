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

_To be filled in during later implementation phases._

## Team Name

_To be decided._
