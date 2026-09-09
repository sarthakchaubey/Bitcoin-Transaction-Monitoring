import React, { useState } from 'react';
import type { EvidencePackage } from '../../types/forensics';
import { RiskPill } from '../common/RiskPill';
import { Search, ArrowRight, Tag, ChevronDown, ChevronUp, ExternalLink, ShieldAlert, SlidersHorizontal } from 'lucide-react';

interface TriageStreamProps {
  evidenceList: EvidencePackage[];
  onInspect: (pkg: EvidencePackage) => void;
  onNavigateToQueue?: () => void;
}

export const TriageStream: React.FC<TriageStreamProps> = ({ evidenceList, onInspect, onNavigateToQueue }) => {
  const [query, setQuery] = useState('');
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const [limit, setLimit] = useState<number>(6);

  const filtered = evidenceList.filter((item) => {
    const q = query.toLowerCase().trim();
    if (!q) return true;
    return (
      (item.wallet_id && item.wallet_id.toLowerCase().includes(q)) ||
      (item.pattern_hint && item.pattern_hint.toLowerCase().includes(q)) ||
      (item.reason_sentence && item.reason_sentence.toLowerCase().includes(q))
    );
  });

  const displayedList = limit === -1 ? filtered : filtered.slice(0, limit);

  return (
    <div>
      {/* Header Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: isMinimized ? 0 : '16px',
          borderBottom: isMinimized ? 'none' : '1px solid var(--border)',
          paddingBottom: isMinimized ? 0 : '12px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              backgroundColor: 'var(--surface-raised)',
              border: '1px solid var(--border)',
              color: 'var(--risk-critical)',
            }}
          >
            <ShieldAlert size={18} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 className="font-serif" style={{ fontSize: '1.15rem', color: 'var(--text)', margin: 0 }}>
                High-Risk Priority Triage Feed
              </h3>
              <span
                style={{
                  backgroundColor: 'var(--surface-raised)',
                  border: '1px solid var(--border)',
                  borderRadius: '10px',
                  padding: '2px 8px',
                  fontSize: '0.72rem',
                  fontFamily: 'IBM Plex Mono, monospace',
                  color: 'var(--accent)',
                }}
              >
                {filtered.length} Entities
              </span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
              {isMinimized
                ? 'Section minimized. Click expand or jump to the dedicated Alert Queue page.'
                : `Displaying top ${displayedList.length} of ${filtered.length} ranked critical targets`}
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {!isMinimized && (
            <>
              {/* Limit Pill Selector */}
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  backgroundColor: 'var(--surface-raised)',
                  border: '1px solid var(--border)',
                  borderRadius: '6px',
                  padding: '2px',
                  gap: '2px',
                }}
              >
                <SlidersHorizontal size={13} style={{ marginLeft: '6px', marginRight: '2px', color: 'var(--text-muted)' }} />
                {[
                  { label: 'Top 6', val: 6 },
                  { label: 'Top 12', val: 12 },
                  { label: 'All', val: -1 },
                ].map((opt) => (
                  <button
                    key={opt.val}
                    className={`btn btn-sm ${limit === opt.val ? 'btn-accent' : ''}`}
                    style={{
                      padding: '3px 8px',
                      fontSize: '0.72rem',
                      height: '24px',
                      minHeight: '24px',
                      background: limit === opt.val ? 'var(--accent)' : 'transparent',
                      color: limit === opt.val ? '#0c1017' : 'var(--text-muted)',
                      border: 'none',
                    }}
                    onClick={() => setLimit(opt.val)}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>

              {/* Search Box */}
              <div style={{ position: 'relative', width: '210px' }}>
                <input
                  type="text"
                  className="search-input"
                  style={{ height: '30px', fontSize: '0.78rem', paddingRight: '28px' }}
                  placeholder="Filter addresses..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
                <Search
                  size={13}
                  style={{
                    position: 'absolute',
                    right: '8px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text-muted)',
                    pointerEvents: 'none',
                  }}
                />
              </div>
            </>
          )}

          {/* Jump to Alert Queue Tab */}
          {onNavigateToQueue && (
            <button
              className="btn btn-sm btn-accent"
              onClick={onNavigateToQueue}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontSize: '0.75rem', height: '30px' }}
              title="Open full dedicated Alert Queue page with table, sorting, and CSV export"
            >
              <ExternalLink size={13} /> Open Alert Queue Page ({filtered.length})
            </button>
          )}

          {/* Minimize / Expand Toggle */}
          <button
            className="btn btn-sm"
            onClick={() => setIsMinimized(!isMinimized)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.75rem',
              height: '30px',
              color: 'var(--text)',
            }}
            title={isMinimized ? 'Expand Triage Feed' : 'Minimize Triage Feed'}
          >
            {isMinimized ? (
              <>
                <ChevronDown size={14} /> Expand Feed
              </>
            ) : (
              <>
                <ChevronUp size={14} /> Minimize
              </>
            )}
          </button>
        </div>
      </div>

      {/* Collapsible Content */}
      {!isMinimized && (
        <>
          {displayedList.length === 0 ? (
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
              {displayedList.map((item) => {
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

          {/* Footer Navigation Bar when limited */}
          {limit > 0 && filtered.length > limit && (
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginTop: '16px',
                paddingTop: '12px',
                borderTop: '1px solid var(--border)',
                fontSize: '0.8rem',
                color: 'var(--text-muted)',
              }}
            >
              <span>
                Showing <strong>{displayedList.length}</strong> of <strong>{filtered.length}</strong> prioritized alerts.
              </span>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  className="btn btn-sm"
                  onClick={() => setLimit(limit === 6 ? 12 : -1)}
                  style={{ fontSize: '0.75rem' }}
                >
                  {limit === 6 ? 'Show Next 6 (+6)' : 'Show All'}
                </button>
                {onNavigateToQueue && (
                  <button
                    className="btn btn-sm btn-accent"
                    onClick={onNavigateToQueue}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem' }}
                  >
                    View All {filtered.length} In Full Alert Queue <ArrowRight size={13} />
                  </button>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
