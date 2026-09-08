import React from 'react';
import { X, Copy, Download, ShieldAlert, Check } from 'lucide-react';
import type { EvidencePackage } from '../../types/forensics';
import { RiskPill } from './RiskPill';
import { ShapBarChart } from './ShapBarChart';
import { generateMarkdownDossier } from '../../data/evidenceData';

interface ModalDossierProps {
  pkg: EvidencePackage | null;
  onClose: () => void;
  onNavigateToDetail?: (walletId: string) => void;
}

export const ModalDossier: React.FC<ModalDossierProps> = ({ pkg, onClose, onNavigateToDetail }) => {
  const [copied, setCopied] = React.useState(false);

  if (!pkg) return null;

  const handleCopyWallet = () => {
    navigator.clipboard.writeText(pkg.wallet_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadDossier = () => {
    const mdContent = generateMarkdownDossier(pkg);
    const blob = new Blob([mdContent], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `forensic_dossier_${pkg.wallet_id.substring(0, 10)}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border)', paddingBottom: '14px', marginBottom: '16px' }}>
          <div>
            <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>
              Target Entity Forensic Dossier
            </div>
            <div className="font-mono" style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text)', wordBreak: 'break-all', marginTop: '4px' }}>
              {pkg.wallet_id}
            </div>
          </div>
          <button className="btn btn-sm" onClick={onClose} style={{ padding: '6px' }}>
            <X size={18} />
          </button>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <RiskPill score={Number(pkg.final_risk_score)} />
          <div className="font-mono" style={{ fontSize: '0.85rem', color: 'var(--accent)' }}>
            🏷️ {pkg.pattern_hint || 'unknown'}
          </div>
        </div>

        <div
          style={{
            backgroundColor: 'var(--surface-raised)',
            borderLeft: '3px solid var(--accent)',
            padding: '14px',
            borderRadius: '4px',
            marginBottom: '20px',
            fontSize: '0.92rem',
            lineHeight: 1.5,
          }}
        >
          <div style={{ fontWeight: 600, color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <ShieldAlert size={14} color="var(--accent)" /> Forensic Finding
          </div>
          <div style={{ color: 'var(--text)' }}>{pkg.reason_sentence}</div>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '10px' }}>
            Top Model Explainability Drivers (SHAP)
          </div>
          <ShapBarChart explanations={pkg.shap_explanation} />
        </div>

        <div style={{ display: 'flex', gap: '10px', marginTop: '20px', borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
          <button className="btn" onClick={handleCopyWallet} style={{ flex: 1 }}>
            {copied ? <Check size={16} color="#48BB78" /> : <Copy size={16} />}
            {copied ? 'Copied Address!' : 'Copy Wallet ID'}
          </button>
          <button className="btn" onClick={handleDownloadDossier} style={{ flex: 1 }}>
            <Download size={16} /> Export Dossier (.md)
          </button>
          {onNavigateToDetail && (
            <button
              className="btn btn-accent"
              onClick={() => {
                onNavigateToDetail(pkg.wallet_id);
                onClose();
              }}
              style={{ flex: 1 }}
            >
              Full Case Detail →
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
