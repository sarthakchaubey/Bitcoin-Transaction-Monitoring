import React from 'react';
import type { EvidencePackage } from '../../types/forensics';
import { Cpu, TrendingUp, Sparkles } from 'lucide-react';

interface ModelInsightsTabProps {
  evidenceList: EvidencePackage[];
}

export const ModelInsightsTab: React.FC<ModelInsightsTabProps> = ({ evidenceList }) => {
  // Aggregate global SHAP feature impacts
  const featureImpactMap: Record<string, number> = {};

  evidenceList.forEach((pkg) => {
    (pkg.shap_explanation || []).forEach((s) => {
      const feat = s.feature || 'unknown';
      const absVal = Math.abs(Number(s.shap_value) || 0);
      featureImpactMap[feat] = (featureImpactMap[feat] || 0) + absVal;
    });
  });

  const sortedFeatures = Object.entries(featureImpactMap)
    .map(([feature, impact]) => ({ feature, impact: impact / Math.max(1, evidenceList.length) }))
    .sort((a, b) => b.impact - a.impact);

  const maxImpact = Math.max(...sortedFeatures.map((f) => f.impact), 0.01);

  // Group risk scores by pattern
  const patternScores: Record<string, number[]> = {};
  evidenceList.forEach((pkg) => {
    const pat = pkg.pattern_hint || 'unknown';
    const score = Number(pkg.final_risk_score) || 0;
    if (!patternScores[pat]) patternScores[pat] = [];
    patternScores[pat].push(score);
  });

  return (
    <div>
      <div style={{ marginBottom: '20px', borderBottom: '1px solid var(--border)', paddingBottom: '10px' }}>
        <h2 className="font-serif" style={{ fontSize: '1.4rem', color: 'var(--text)' }}>
          🧠 Model Insights & Ensemble Signals
        </h2>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          Global explainability rankings, feature impact distributions, and community risk decomposition
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px' }}>
        {/* Global SHAP Impact Ranking */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', borderBottom: '1px solid var(--border)', paddingBottom: '8px' }}>
            <Sparkles size={17} color="var(--accent)" />
            <h3 className="font-serif" style={{ fontSize: '1.1rem', color: 'var(--text)' }}>
              ⚡ Global Feature Impact Ranking (Mean |SHAP|)
            </h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {sortedFeatures.map((item, idx) => {
              const widthPct = Math.max(8, (item.impact / maxImpact) * 100);
              return (
                <div key={item.feature} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                    <span className="font-mono" style={{ color: 'var(--text)', fontWeight: 600 }}>
                      #{idx + 1} {item.feature}
                    </span>
                    <span className="font-mono" style={{ color: 'var(--accent)', fontWeight: 700 }}>
                      {item.impact.toFixed(4)}
                    </span>
                  </div>
                  <div style={{ height: '8px', backgroundColor: 'var(--surface-raised)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${widthPct}%`,
                        height: '100%',
                        backgroundColor: 'var(--accent)',
                        borderRadius: '4px',
                        transition: 'width 0.4s ease',
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Pattern Risk Distributions */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', borderBottom: '1px solid var(--border)', paddingBottom: '8px' }}>
            <TrendingUp size={17} color="var(--risk-high)" />
            <h3 className="font-serif" style={{ fontSize: '1.1rem', color: 'var(--text)' }}>
              📈 Risk Score Mean by Pattern Signature
            </h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {Object.entries(patternScores).map(([pat, scores]) => {
              const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
              const min = Math.min(...scores);
              const max = Math.max(...scores);
              const widthPct = Math.min(100, Math.max(10, avg));

              return (
                <div key={pat} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                    <span className="font-mono" style={{ color: 'var(--text)', fontWeight: 600 }}>
                      {pat} ({scores.length} entities)
                    </span>
                    <span className="font-mono" style={{ color: 'var(--risk-high)', fontWeight: 700 }}>
                      Avg: {avg.toFixed(1)} / 100
                    </span>
                  </div>
                  <div style={{ height: '8px', backgroundColor: 'var(--surface-raised)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${widthPct}%`,
                        height: '100%',
                        backgroundColor: 'var(--risk-high)',
                        borderRadius: '4px',
                      }}
                    />
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', display: 'flex', justifyContent: 'space-between' }}>
                    <span>Min: {min.toFixed(1)}</span>
                    <span>Max: {max.toFixed(1)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Model Ensemble Architecture Section */}
      <div className="card" style={{ marginTop: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <Cpu size={18} color="var(--accent)" />
          <h3 className="font-serif" style={{ fontSize: '1.1rem', color: 'var(--text)' }}>
            🛡️ Dual-Engine Forensic Scoring Pipeline
          </h3>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
          The final composite risk score ($0–100$) integrates a multivariate <strong>Isolation Forest</strong> unsupervised anomaly detector trained on temporal burstiness, round-number ratios, and fee-to-amount distributions, fused with a <strong>Louvain community modularity</strong> projection score. Feature attributions are rendered through exact <strong>SHAP TreeExplainer</strong> values to provide human-auditable explanations for every flagged transaction cluster.
        </p>
      </div>
    </div>
  );
};
