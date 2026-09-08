import React, { useState } from 'react';
import type { EvidencePackage } from '../../types/forensics';
import { RiskPill } from '../common/RiskPill';
import { ShapBarChart } from '../common/ShapBarChart';
import { generateMarkdownDossier } from '../../data/evidenceData';
import { ShieldAlert, Download, Copy, Code, Check, Network, Layers, Sparkles } from 'lucide-react';

interface CaseDetailTabProps {
  evidenceList: EvidencePackage[];
  selectedWalletId: string;
  onSelectWallet: (walletId: string) => void;
  onNavigateToNetwork?: (walletId: string) => void;
}

export const CaseDetailTab: React.FC<CaseDetailTabProps> = ({
  evidenceList,
  selectedWalletId,
  onSelectWallet,
  onNavigateToNetwork,
}) => {
  const [copiedJson, setCopiedJson] = useState(false);
  const [showJsonDrawer, setShowJsonDrawer] = useState(false);

  const currentPkg =
    evidenceList.find((e) => e.wallet_id === selectedWalletId) ||
    evidenceList[0] ||
    null;

  if (!currentPkg) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
        No case records available.
      </div>
    );
  }

  const handleDownloadDossier = () => {
    const mdContent = generateMarkdownDossier(currentPkg);
    const blob = new Blob([mdContent], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `case_dossier_${currentPkg.wallet_id.substring(0, 10)}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(currentPkg, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  const score = Number(currentPkg.final_risk_score) || 0;
  const nodes = currentPkg.subgraph?.nodes || [];
  const edges = currentPkg.subgraph?.edges || [];

  return (
    <div>
      {/* Wallet Selector Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <h2 className="font-serif" style={{ fontSize: '1.4rem', color: 'var(--text)' }}>
            📁 Forensic Case-File Dossier
          </h2>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            Comprehensive Explainable AI signal breakdown & topological evidence
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <select
            className="search-input"
            value={currentPkg.wallet_id}
            onChange={(e) => onSelectWallet(e.target.value)}
            style={{ width: '320px', cursor: 'pointer' }}
          >
            {evidenceList.map((e) => (
              <option key={e.wallet_id} value={e.wallet_id}>
                {e.wallet_id.substring(0, 16)}... ({Number(e.final_risk_score).toFixed(1)} / 100)
              </option>
            ))}
          </select>

          <button className="btn" onClick={handleDownloadDossier}>
            <Download size={15} /> Export (.md)
          </button>
        </div>
      </div>

      {/* Target Entity Overview Card */}
      <div className="card" style={{ borderTop: '3px solid var(--accent)', marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)' }}>
              Target Entity Wallet ID
            </div>
            <div className="font-mono" style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text)', wordBreak: 'break-all', marginTop: '2px' }}>
              {currentPkg.wallet_id}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <RiskPill score={score} />
            <div
              className="font-mono"
              style={{
                backgroundColor: 'var(--surface-raised)',
                border: '1px solid var(--border)',
                padding: '4px 10px',
                borderRadius: '4px',
                fontSize: '0.8rem',
                color: 'var(--accent)',
              }}
            >
              🏷️ {currentPkg.pattern_hint || 'unknown'}
            </div>
          </div>
        </div>

        {/* Reason Centerpiece Callout */}
        <div
          style={{
            backgroundColor: 'var(--surface-raised)',
            borderLeft: '4px solid var(--accent)',
            borderRadius: '4px',
            padding: '16px',
            marginTop: '18px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '0.76rem',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              color: 'var(--accent)',
              fontWeight: 700,
              marginBottom: '6px',
            }}
          >
            <ShieldAlert size={16} /> Forensic Finding & Anomaly Narrative
          </div>
          <div style={{ fontSize: '0.98rem', color: 'var(--text)', lineHeight: 1.6 }}>
            {currentPkg.reason_sentence}
          </div>
        </div>
      </div>

      {/* Two Column Layout: SHAP Explanations & Behavioral Topology */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px', marginBottom: '20px' }}>
        {/* SHAP Feature Contribution Card */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', borderBottom: '1px solid var(--border)', paddingBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={16} color="var(--accent)" />
              <h3 className="font-serif" style={{ fontSize: '1.05rem', color: 'var(--text)' }}>
                Explainable AI (SHAP) Drivers
              </h3>
            </div>
            <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Directional Impact</span>
          </div>

          <ShapBarChart explanations={currentPkg.shap_explanation} />

          {/* Structured Feature Value Table */}
          <div style={{ marginTop: '18px', borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
            <div style={{ fontSize: '0.76rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
              Attribution Value Matrix
            </div>
            <div className="data-table-container">
              <table className="data-table" style={{ fontSize: '0.78rem' }}>
                <thead>
                  <tr>
                    <th>Feature Name</th>
                    <th>SHAP Value</th>
                    <th>Direction</th>
                    <th>Raw Observed</th>
                  </tr>
                </thead>
                <tbody>
                  {(currentPkg.shap_explanation || []).map((s, idx) => (
                    <tr key={idx}>
                      <td className="font-mono">{s.feature}</td>
                      <td
                        className="font-mono"
                        style={{ color: s.direction === 'increases_risk' ? 'var(--risk-high)' : 'var(--risk-low)', fontWeight: 600 }}
                      >
                        {Number(s.shap_value) >= 0 ? '+' : ''}
                        {Number(s.shap_value).toFixed(4)}
                      </td>
                      <td>{s.direction === 'increases_risk' ? '▲ Risk' : '▼ Mitigating'}</td>
                      <td className="font-mono">{String(s.raw_value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Behavioral Pattern Topology & Subgraph Summary */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', borderBottom: '1px solid var(--border)', paddingBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={16} color="var(--accent)" />
              <h3 className="font-serif" style={{ fontSize: '1.05rem', color: 'var(--text)' }}>
                Topology & Neighborhood Metrics
              </h3>
            </div>
            {onNavigateToNetwork && (
              <button
                className="btn btn-sm btn-accent"
                onClick={() => onNavigateToNetwork(currentPkg.wallet_id)}
              >
                <Network size={13} /> View in Graph
              </button>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', marginBottom: '16px' }}>
            <div style={{ backgroundColor: 'var(--surface-raised)', padding: '12px', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Connected Nodes</div>
              <div className="font-mono" style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text)' }}>
                {nodes.length}
              </div>
            </div>
            <div style={{ backgroundColor: 'var(--surface-raised)', padding: '12px', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Transaction Edges</div>
              <div className="font-mono" style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--accent)' }}>
                {edges.length}
              </div>
            </div>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '16px' }}>
            <strong style={{ color: 'var(--text)' }}>Behavioral Signature Explanation:</strong>{' '}
            {currentPkg.pattern_hint === 'peeling_chain' &&
              'Sequential transaction sequence where an address moves value incrementally through rapid consecutive change outputs.'}
            {currentPkg.pattern_hint === 'mixing_service' &&
              'High entropy transaction topology involving multiple aggregated inputs and split outputs designed to obfuscate origin.'}
            {currentPkg.pattern_hint === 'rapid_burst' &&
              'Sudden high-velocity transaction bursts concentrated within short temporal windows.'}
            {currentPkg.pattern_hint === 'high_risk_jurisdiction' &&
              'Broadcast transaction initiated from known high-risk sanctions-flagged or proxy IP networks.'}
            {currentPkg.pattern_hint === 'structuring' &&
              'Multiple sub-threshold round-amount transactions executed to evade detection filters.'}
            {!['peeling_chain', 'mixing_service', 'rapid_burst', 'high_risk_jurisdiction', 'structuring'].includes(
              currentPkg.pattern_hint
            ) && 'Statistical multivariate outlier identified across temporal, volumetric, and topological graph dimensions.'}
          </div>

          {/* Raw JSON Inspect Toggle */}
          <div style={{ borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
            <button
              className="btn btn-sm"
              onClick={() => setShowJsonDrawer(!showJsonDrawer)}
              style={{ width: '100%', justifyContent: 'center' }}
            >
              <Code size={14} /> {showJsonDrawer ? 'Hide Raw Evidence JSON' : 'Inspect Raw Evidence JSON'}
            </button>

            {showJsonDrawer && (
              <div style={{ marginTop: '12px', position: 'relative' }}>
                <button
                  className="btn btn-sm"
                  onClick={handleCopyJson}
                  style={{ position: 'absolute', right: '10px', top: '10px', zIndex: 10 }}
                >
                  {copiedJson ? <Check size={12} color="#48BB78" /> : <Copy size={12} />}
                  {copiedJson ? 'Copied' : 'Copy'}
                </button>
                <pre
                  className="font-mono"
                  style={{
                    backgroundColor: 'var(--bg)',
                    border: '1px solid var(--border)',
                    borderRadius: '4px',
                    padding: '12px',
                    fontSize: '0.74rem',
                    color: '#A0AEC0',
                    maxHeight: '260px',
                    overflowY: 'auto',
                  }}
                >
                  {JSON.stringify(currentPkg, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
