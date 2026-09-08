import React, { useState } from 'react';
import type { EvidencePackage } from '../../types/forensics';
import { RiskPill } from '../common/RiskPill';
import { getRiskSeverityBand } from '../../data/evidenceData';
import { Download, ArrowUpDown, Eye, ExternalLink } from 'lucide-react';

interface AlertQueueTabProps {
  evidenceList: EvidencePackage[];
  onInspect: (pkg: EvidencePackage) => void;
  onSelectEntity: (walletId: string) => void;
}

export const AlertQueueTab: React.FC<AlertQueueTabProps> = ({
  evidenceList,
  onInspect,
  onSelectEntity,
}) => {
  const [sortField, setSortField] = useState<'score' | 'wallet' | 'pattern'>('score');
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  const sortedList = [...evidenceList].sort((a, b) => {
    if (sortField === 'score') {
      const sA = Number(a.final_risk_score) || 0;
      const sB = Number(b.final_risk_score) || 0;
      return sortAsc ? sA - sB : sB - sA;
    } else if (sortField === 'wallet') {
      return sortAsc ? a.wallet_id.localeCompare(b.wallet_id) : b.wallet_id.localeCompare(a.wallet_id);
    } else {
      const pA = a.pattern_hint || '';
      const pB = b.pattern_hint || '';
      return sortAsc ? pA.localeCompare(pB) : pB.localeCompare(pA);
    }
  });

  const toggleSort = (field: 'score' | 'wallet' | 'pattern') => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const handleExportCSV = () => {
    if (evidenceList.length === 0) return;

    const headers = ['wallet_id', 'final_risk_score', 'severity_band', 'confidence_label', 'pattern_hint', 'reason_sentence'];
    const rows = sortedList.map((item) => [
      item.wallet_id,
      Number(item.final_risk_score).toFixed(2),
      getRiskSeverityBand(Number(item.final_risk_score)),
      item.confidence_label || 'Normal',
      item.pattern_hint || 'unknown',
      `"${(item.reason_sentence || '').replace(/"/g, '""')}"`,
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'forensic_alert_queue.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <h2 className="font-serif" style={{ fontSize: '1.4rem', color: 'var(--text)' }}>
            🚨 Ranked Forensic Alert Queue
          </h2>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            Showing {sortedList.length} prioritized entities matching active sidebar filter criteria
          </p>
        </div>

        <button className="btn btn-accent" onClick={handleExportCSV}>
          <Download size={15} /> Export Alert Queue (.csv)
        </button>
      </div>

      {sortedList.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
          No entities match the active filters. Adjust your score threshold or pattern criteria in the sidebar.
        </div>
      ) : (
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th onClick={() => toggleSort('wallet')} style={{ cursor: 'pointer' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    Target Wallet ID <ArrowUpDown size={12} />
                  </div>
                </th>
                <th onClick={() => toggleSort('score')} style={{ cursor: 'pointer' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    Risk Score <ArrowUpDown size={12} />
                  </div>
                </th>
                <th>Severity Band</th>
                <th>Confidence</th>
                <th onClick={() => toggleSort('pattern')} style={{ cursor: 'pointer' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    Pattern Signature <ArrowUpDown size={12} />
                  </div>
                </th>
                <th>Forensic Finding Summary</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sortedList.map((item) => {
                const score = Number(item.final_risk_score) || 0;
                return (
                  <tr key={item.wallet_id} onClick={() => onInspect(item)}>
                    <td className="font-mono" style={{ fontWeight: 600, color: 'var(--text)' }}>
                      {item.wallet_id.substring(0, 18)}...
                    </td>
                    <td className="font-mono" style={{ fontWeight: 700, color: 'var(--text)' }}>
                      {score.toFixed(1)}
                    </td>
                    <td>
                      <RiskPill score={score} showScore={false} />
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {item.confidence_label || 'Normal'}
                      </span>
                    </td>
                    <td className="font-mono" style={{ fontSize: '0.8rem', color: 'var(--accent)' }}>
                      {item.pattern_hint || 'unknown'}
                    </td>
                    <td style={{ fontSize: '0.82rem', color: 'var(--text-muted)', maxWidth: '380px' }}>
                      <span
                        style={{
                          display: '-webkit-box',
                          WebkitLineClamp: 1,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                        }}
                      >
                        {item.reason_sentence}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '6px' }}>
                        <button
                          className="btn btn-sm"
                          title="Inspect Dossier"
                          onClick={(e) => {
                            e.stopPropagation();
                            onInspect(item);
                          }}
                        >
                          <Eye size={13} />
                        </button>
                        <button
                          className="btn btn-sm btn-accent"
                          title="Open Case Detail View"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectEntity(item.wallet_id);
                          }}
                        >
                          <ExternalLink size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
