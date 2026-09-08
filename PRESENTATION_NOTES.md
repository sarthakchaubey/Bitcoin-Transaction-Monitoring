# Presentation Notes

## Opening line

“Bitcoin is transparent, but the challenge is turning millions of visible transactions into a short, explainable list of wallets an investigator can act on.”

## Suggested live demo flow

1. Start the Streamlit dashboard:

   ```bash
   streamlit run dashboard/app.py
   ```

2. Begin on the ranked alert table and point out the final risk score and confidence label.
3. Move the **Minimum Risk Score Threshold** slider to focus on High-confidence alerts.
4. Use the **Behavioral Pattern Hint** filter to show a specific pattern such as `peeling_chain` or `fan_in_fan_out`.
5. Select the highest-risk wallet from the alert table.
6. Read the generated reason sentence aloud, emphasizing the top contributing features and community risk score.
7. Show the SHAP contribution chart and explain that positive bars increase anomaly risk while negative bars reduce it.
8. Open the local graph view to show the wallet’s transaction, counterparty, and broadcast-IP neighborhood.
9. Close with the evaluation panel/report: precision@k, recall@k, F1, and pattern-level recall from `data/evaluation_report.txt`.
10. If demonstrating the current checkout, explicitly state that the Phase 1 dataset and ground truth are not present, so evaluation numbers are not available yet; do not present dashboard demo fixtures as measured model results.

## Anticipated judge questions

### How does this differ from rule-based flagging?

Rules are useful for transparent checks, but this system trains Isolation Forest on a multivariate feature matrix and combines that score with a Louvain-derived network signal. The SHAP layer makes the learned anomaly ranking inspectable without reducing the model to a fixed threshold rule.

### How would this scale to real Bitcoin volume?

The current baseline is intentionally offline and hackathon-sized: pandas, NetworkX, Isolation Forest, and cached GeoIP lookups. For production volume, transaction storage and graph traversal should move to Neo4j or a distributed graph/data platform, ingestion should become streaming, and feature/model computation should be incremental.

### How confident are you in the wallet clustering heuristic?

Common-input ownership is a standard forensic heuristic, but it is not universally correct. CoinJoin-like transactions, custodial services, shared wallets, change behavior, and address reuse can create false merges or missed merges. The system exposes cluster-based evidence while treating clustering as an uncertainty source, not ground truth.

### Why use both Isolation Forest and Louvain?

Isolation Forest captures unusual wallet behavior; Louvain captures relationships between wallets that may look ordinary individually but suspicious in context. Equal default ensemble weights provide a transparent starting point and should be tuned against a held-out validation set.

### Why is the high-risk geography signal not proof of wrongdoing?

Geography and ASN metadata are risk context only. The default list is illustrative and must be replaced by a reviewed, current intelligence source. A country or IP association alone is never a determination of illicit activity.

### Why not use GraphSAGE now?

GraphSAGE is a sensible future upgrade, but it adds training, validation, labeling, and deployment complexity. The current Louvain projection provides a fast, explainable graph baseline; GraphSAGE can be evaluated later using weak supervision from the hidden labels.

### How do you prevent ground-truth leakage?

Ground truth is loaded only by the evaluation layer after scoring. It is not included in the feature table, preprocessing pipeline, anomaly model, community model, or SHAP inputs.
