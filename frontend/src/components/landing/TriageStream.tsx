import React, { useState } from 'react';
import type { EvidencePackage } from '../../types/forensics';
import { RiskPill } from '../common/RiskPill';
import { Search, ArrowRight, Tag } from 'lucide-react';

interface TriageStreamProps {
  evidenceList: EvidencePackage[];
  onInspect: (pkg: EvidencePackage) => void;
}

export const TriageStream: React.FC<TriageStreamProps> = ({ evidenceList, onInspect }) => {
  const [query, setQuery] = useState('');

  const filtered = evidenceList.filter((item) => {
    const q = query.toLowerCase().trim();
    if (!q) return true;
    return (
      (item.wallet_id && item.wallet_id.toLowerCase().includes(q)) ||
      (item.pattern_hint && item.pattern_hint.toLowerCase().includes(q)) ||
      (item.reason_sentence && item.reason_sentence.toLowerCase().includes(q))
    );
  });

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
          borderBottom: '1px solid var(--border)',
          paddingBottom: '10px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <h3 className="font-serif" style={{ fontSize: '1.2rem', color: 'var(--text)' }}>
            ⚡ High-Risk Entity Triage Stream
          </h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Live triage feed ranked by composite multivariate anomaly score
          </p>
        </div>

        <div style={{ position: 'relative', width: '280px' }}>
          <input
            type="text"
            className="search-input"
            placeholder="Search address or pattern..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <Search
            size={14}
            style={{
              position: 'absolute',
              right: '10px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)',
              pointerEvents: 'none',
            }}
          />
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '30px' }}>
          No entities matched the search filter "{query}".
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: '14px',
          }}
        >
          {filtered.map((item) => {
            const shaps = (item.shap_explanation || []).slice(0, 2);
            return (
              <div
                key={item.wallet_id}
                className="card"
                onClick={() => onInspect(item)}
                style={{
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'all 0.2s ease',
                  margin: 0,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--surface-raised)';
                  e.currentTarget.style.borderColor = 'var(--accent)';
                  e.currentTarget.style.boxShadow = '0 6px 16px rgba(0,0,0,0.4)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--surface)';
                  e.currentTarget.style.borderColor = 'var(--border)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                    <span className="font-mono" style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text)' }}>
                      {item.wallet_id.substring(0, 14)}...
                    </span>
                    <RiskPill score={Number(item.final_risk_score)} />
                  </div>

                  <div
                    className="font-mono"
                    style={{
                      fontSize: '0.74rem',
                      color: 'var(--accent)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      marginBottom: '8px',
                    }}
                  >
                    <Tag size={12} /> {item.pattern_hint || 'unknown'}
                  </div>

                  <p
                    style={{
                      fontSize: '0.82rem',
                      color: 'var(--text-muted)',
                      lineHeight: 1.4,
                      marginBottom: '10px',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                    }}
                  >
                    {item.reason_sentence || 'Anomalous network transaction signature detected.'}
                  </p>

                  {/* Inline Mini SHAP Bars */}
                  {shaps.length > 0 && (
                    <div
                      style={{
                        borderTop: '1px solid var(--border-light)',
                        paddingTop: '8px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '4px',
                      }}
                    >
                      {shaps.map((s, idx) => {
                        const val = Math.abs(Number(s.shap_value) || 0);
                        const width = Math.min(100, Math.round(val * 180));
                        const isRisk = s.direction === 'increases_risk' || Number(s.shap_value) > 0;
                        const barColor = isRisk ? 'var(--risk-high)' : 'var(--risk-low)';

                        return (
                          <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.72rem' }}>
                            <span
                              className="font-mono"
                              style={{ width: '110px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text-muted)' }}
                              title={s.feature}
                            >
                              {s.feature}
                            </span>
                            <div style={{ flex: 1, height: '4px', backgroundColor: 'var(--surface-raised)', borderRadius: '2px', overflow: 'hidden' }}>
                              <div style={{ width: `${width}%`, height: '100%', backgroundColor: barColor, borderRadius: '2px' }} />
                            </div>
                            <span className="font-mono" style={{ color: 'var(--text)', fontSize: '0.7rem' }}>
                              {Number(s.shap_value).toFixed(2)}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginTop: '12px',
                    paddingTop: '8px',
                    borderTop: '1px solid var(--border)',
                    fontSize: '0.74rem',
                    color: 'var(--text-muted)',
                  }}
                >
                  <span>
                    Confidence: <strong style={{ color: 'var(--text)' }}>{item.confidence_label || 'Normal'}</strong>
                  </span>
                  <span style={{ color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
                    Inspect <ArrowRight size={13} />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
