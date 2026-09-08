import React from 'react';
import type { EvidencePackage, NetworkSummaryStats } from '../../types/forensics';
import { CanvasGraphHUD } from '../landing/CanvasGraphHUD';
import { MetricCards } from '../landing/MetricCards';
import { TriageStream } from '../landing/TriageStream';
import { BarChart3, Globe, PieChart } from 'lucide-react';

interface OverviewTabProps {
  evidenceList: EvidencePackage[];
  stats: NetworkSummaryStats;
  onInspect: (pkg: EvidencePackage) => void;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({ evidenceList, stats, onInspect }) => {
  // Compute histogram bins for risk scores
  const scoreBins = Array(5).fill(0);
  evidenceList.forEach((e) => {
    const s = Number(e.final_risk_score) || 0;
    if (s < 20) scoreBins[0]++;
    else if (s < 40) scoreBins[1]++;
    else if (s < 60) scoreBins[2]++;
    else if (s < 80) scoreBins[3]++;
    else scoreBins[4]++;
  });
  const maxBin = Math.max(...scoreBins, 1);

  // Pattern data
  const patternEntries = Object.entries(stats.pattern_counts).sort((a, b) => b[1] - a[1]);
  const maxPattern = Math.max(...patternEntries.map((p) => p[1]), 1);

  // Geo data
  const countryEntries = Object.entries(stats.country_counts).sort((a, b) => b[1] - a[1]).slice(0, 6);
  const maxCountry = Math.max(...countryEntries.map((c) => c[1]), 1);

  return (
    <div>
      {/* 1. Canvas Network HUD Animation */}
      <CanvasGraphHUD />

      {/* 2. Headline Metric Gauges */}
      <MetricCards stats={stats} />

      {/* 3. Live High-Risk Triage Stream */}
      <div className="card" style={{ marginBottom: '28px' }}>
        <TriageStream evidenceList={evidenceList} onInspect={onInspect} />
      </div>

      {/* 4. Deep Analytical Distribution Charts */}
      <div>
        <div style={{ marginBottom: '16px', borderBottom: '1px solid var(--border)', paddingBottom: '8px' }}>
          <h3 className="font-serif" style={{ fontSize: '1.25rem', color: 'var(--text)' }}>
            📊 Network Risk & Behavioral Statistical Distributions
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Aggregate empirical distribution profiles across flagged transaction subgraphs and broadcast entities
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '16px' }}>
          {/* Chart 1: Risk Score Histogram */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <BarChart3 size={16} color="var(--accent)" />
              <h4 className="font-serif" style={{ fontSize: '1rem', color: 'var(--text)' }}>
                🎯 Risk Score Distribution
              </h4>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-end', height: '140px', gap: '14px', paddingTop: '16px', borderBottom: '1px solid var(--border)' }}>
              {['0–19', '20–39', '40–59', '60–79', '80–100'].map((label, idx) => {
                const count = scoreBins[idx];
                const heightPct = Math.max(8, (count / maxBin) * 100);
                const colors = ['var(--risk-low)', 'var(--risk-low)', 'var(--risk-medium)', 'var(--risk-high)', 'var(--risk-critical)'];

                return (
                  <div key={idx} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end' }}>
                    <span className="font-mono" style={{ fontSize: '0.72rem', color: 'var(--text)', marginBottom: '4px' }}>
                      {count}
                    </span>
                    <div
                      style={{
                        width: '100%',
                        height: `${heightPct}%`,
                        backgroundColor: colors[idx],
                        borderRadius: '3px 3px 0 0',
                        transition: 'height 0.3s ease',
                      }}
                    />
                    <span className="font-mono" style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '6px' }}>
                      {label}
                    </span>
                  </div>
                );
              })}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', marginTop: '8px', textAlign: 'center' }}>
              Score Ranges (Low to Critical Severity)
            </div>
          </div>

          {/* Chart 2: Behavioral Patterns */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <PieChart size={16} color="var(--accent)" />
              <h4 className="font-serif" style={{ fontSize: '1rem', color: 'var(--text)' }}>
                🔄 Behavioral Pattern Frequency
              </h4>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {patternEntries.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No patterns recorded.</div>
              ) : (
                patternEntries.map(([pat, count]) => {
                  const widthPct = Math.max(6, (count / maxPattern) * 100);
                  return (
                    <div key={pat} style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                        <span className="font-mono" style={{ color: 'var(--text)' }}>{pat}</span>
                        <span className="font-mono" style={{ color: 'var(--accent)', fontWeight: 600 }}>{count} entities</span>
                      </div>
                      <div style={{ height: '7px', width: '100%', backgroundColor: 'var(--surface-raised)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${widthPct}%`, height: '100%', backgroundColor: 'var(--accent)', borderRadius: '3px' }} />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Chart 3: Flagged Jurisdictions */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <Globe size={16} color="var(--risk-high)" />
              <h4 className="font-serif" style={{ fontSize: '1rem', color: 'var(--text)' }}>
                🌍 Flagged Jurisdictions & Broadcast IPs
              </h4>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {countryEntries.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                  No geographic broadcast records in evidence subgraphs.
                </div>
              ) : (
                countryEntries.map(([country, count]) => {
                  const widthPct = Math.max(8, (count / maxCountry) * 100);
                  return (
                    <div key={country} style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                        <span style={{ color: 'var(--text)' }}>{country}</span>
                        <span className="font-mono" style={{ color: 'var(--risk-high)' }}>{count} IPs</span>
                      </div>
                      <div style={{ height: '7px', width: '100%', backgroundColor: 'var(--surface-raised)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${widthPct}%`, height: '100%', backgroundColor: 'var(--risk-high)', borderRadius: '3px' }} />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Chart 4: Severity Band Breakdown */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <BarChart3 size={16} color="var(--risk-critical)" />
              <h4 className="font-serif" style={{ fontSize: '1rem', color: 'var(--text)' }}>
                🛡️ Severity Band Distribution
              </h4>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[
                { label: 'Critical (≥90)', count: stats.critical_count, color: 'var(--risk-critical)' },
                { label: 'High (70–89)', count: stats.high_count, color: 'var(--risk-high)' },
                { label: 'Medium (40–69)', count: stats.medium_count, color: 'var(--risk-medium)' },
                { label: 'Low (<40)', count: stats.low_count, color: 'var(--risk-low)' },
              ].map((band) => {
                const total = Math.max(1, stats.total_wallets);
                const pct = Math.round((band.count / total) * 100);
                return (
                  <div key={band.label} style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                      <span style={{ color: 'var(--text)' }}>{band.label}</span>
                      <span className="font-mono" style={{ color: band.color, fontWeight: 700 }}>
                        {band.count} ({pct}%)
                      </span>
                    </div>
                    <div style={{ height: '7px', width: '100%', backgroundColor: 'var(--surface-raised)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${pct}%`, height: '100%', backgroundColor: band.color, borderRadius: '3px' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
