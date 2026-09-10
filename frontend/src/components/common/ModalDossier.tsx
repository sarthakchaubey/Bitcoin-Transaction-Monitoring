import React, { useState } from 'react';
import { Copy, Download, ShieldAlert, Check, ArrowRight, Tag } from 'lucide-react';
import type { EvidencePackage } from '@/types/forensics';
import { RiskPill } from '@/components/common/RiskPill';
import { ShapBarChart } from '@/components/common/ShapBarChart';
import { generateMarkdownDossier } from '@/data/evidenceData';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface ModalDossierProps {
  pkg: EvidencePackage | null;
  onClose: () => void;
  onNavigateToDetail?: (walletId: string) => void;
}

export const ModalDossier: React.FC<ModalDossierProps> = ({ pkg, onClose, onNavigateToDetail }) => {
  const [copied, setCopied] = useState(false);

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
    <Dialog open={!!pkg} onOpenChange={(open) => { if (!open) onClose(); }}>
      <DialogContent onClose={onClose} className="max-w-xl">
        <DialogHeader>
          <div className="flex items-center gap-2 text-xs font-semibold text-accent uppercase tracking-wider">
            <ShieldAlert className="h-4 w-4" />
            Target Entity Forensic Dossier
          </div>
          <DialogTitle className="font-mono text-base sm:text-lg break-all text-foreground mt-1 select-all">
            {pkg.wallet_id}
          </DialogTitle>
          <DialogDescription>
            Offline transaction graph anomaly telemetry & explainability signature
          </DialogDescription>
        </DialogHeader>

        {/* Severity & Pattern Header */}
        <div className="flex flex-wrap items-center justify-between gap-2 p-3 bg-card-raised rounded-lg border border-border/80 mb-4">
          <RiskPill score={Number(pkg.final_risk_score)} />
          <Badge variant="accent" className="flex items-center gap-1">
            <Tag className="h-3 w-3" />
            {pkg.pattern_hint || 'unknown'}
          </Badge>
          <span className="text-xs text-muted-foreground font-mono">
            Confidence: <strong className="text-foreground">{pkg.confidence_label || 'Normal'}</strong>
          </span>
        </div>

        {/* Forensic Finding Narrative Banner */}
        <div className="p-4 rounded-lg bg-card-raised/80 border-l-4 border-accent border border-border/60 shadow-inner mb-4">
          <div className="flex items-center gap-1.5 text-xs font-bold text-accent uppercase tracking-wider mb-1.5">
            <ShieldAlert className="h-3.5 w-3.5" />
            Primary Forensic Finding
          </div>
          <p className="text-sm text-foreground/90 leading-relaxed font-sans">
            {pkg.reason_sentence || 'Anomalous network transaction signature detected across clustering pipelines.'}
          </p>
        </div>

        {/* SHAP Explainability Visualization */}
        <div className="space-y-2 mb-6">
          <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center justify-between">
            <span>Model Explainability Signals (SHAP)</span>
            <span className="text-[11px] font-normal text-muted-foreground">Impact on Risk</span>
          </div>
          <div className="p-3 bg-card-raised/50 rounded-lg border border-border/60">
            <ShapBarChart explanations={pkg.shap_explanation} />
          </div>
        </div>

        {/* Footer Actions */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-3 border-t border-border">
          <Button
            variant="outline"
            size="sm"
            onClick={handleCopyWallet}
            className="w-full text-xs"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? 'Copied ID!' : 'Copy Wallet ID'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDownloadDossier}
            className="w-full text-xs"
          >
            <Download className="h-3.5 w-3.5 text-accent" />
            Export (.md)
          </Button>
          {onNavigateToDetail && (
            <Button
              variant="accent"
              size="sm"
              onClick={() => {
                onNavigateToDetail(pkg.wallet_id);
                onClose();
              }}
              className="w-full text-xs"
            >
              Full Case Detail
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
