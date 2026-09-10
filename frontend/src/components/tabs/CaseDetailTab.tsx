import React, { useState } from 'react';
import { motion } from 'motion/react';
import type { EvidencePackage } from '@/types/forensics';
import { RiskPill } from '@/components/common/RiskPill';
import { ShapBarChart } from '@/components/common/ShapBarChart';
import { generateMarkdownDossier } from '@/data/evidenceData';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ShieldAlert, Download, Copy, Code, Check, Network, Layers, Sparkles, Tag, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { cn } from '@/lib/utils';

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
      <Card className="text-center py-16 px-4">
        <ShieldAlert className="h-12 w-12 text-muted-foreground mx-auto mb-3 opacity-40" />
        <h3 className="font-serif text-base font-bold text-foreground">No case records available</h3>
      </Card>
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
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-5"
    >
      {/* Wallet Selector Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-2">
        <div>
          <h2 className="font-serif text-xl sm:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <span>📁 Forensic Case Dossier</span>
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Comprehensive Explainable AI signal breakdown & topological graph evidence
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <div className="relative">
            <select
              className="h-9 px-3 py-1 text-xs font-mono rounded-md border border-input bg-card-raised text-foreground focus:outline-none focus:ring-1 focus:ring-accent max-w-xs sm:max-w-sm cursor-pointer shadow-sm"
              value={currentPkg.wallet_id}
              onChange={(e) => onSelectWallet(e.target.value)}
            >
              {evidenceList.map((e) => (
                <option key={e.wallet_id} value={e.wallet_id} className="bg-card text-foreground">
                  {e.wallet_id.substring(0, 16)}... (Score: {Number(e.final_risk_score).toFixed(1)})
                </option>
              ))}
            </select>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleDownloadDossier}
            className="text-xs h-9"
          >
            <Download className="h-4 w-4 text-accent" />
            Export (.md)
          </Button>
        </div>
      </div>

      {/* Target Entity Overview Card */}
      <Card className="border-t-2 border-t-accent shadow-card border-border/80">
        <CardContent className="p-5 sm:p-6 space-y-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                Target Entity Wallet ID
              </div>
              <div className="font-mono text-base sm:text-xl font-bold text-foreground break-all mt-1 select-all">
                {currentPkg.wallet_id}
              </div>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <RiskPill score={score} />
              <Badge variant="accent" className="font-mono text-xs flex items-center gap-1">
                <Tag className="h-3 w-3" />
                {currentPkg.pattern_hint || 'unknown'}
              </Badge>
            </div>
          </div>

          {/* Reason Centerpiece Callout */}
          <div className="p-4 rounded-lg bg-card-raised border-l-4 border-accent border border-border/60 shadow-inner">
            <div className="flex items-center gap-1.5 text-xs font-bold text-accent uppercase tracking-wider mb-1.5">
              <ShieldAlert className="h-4 w-4" />
              Forensic Finding & Anomaly Narrative
            </div>
            <p className="text-sm sm:text-base text-foreground leading-relaxed">
              {currentPkg.reason_sentence}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Two Column Layout: SHAP Explanations & Topology */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* SHAP Feature Contribution Card */}
        <Card className="shadow-card border-border/80">
          <CardHeader className="p-4 sm:p-5 pb-3 border-b border-border/60">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm sm:text-base font-serif font-bold text-foreground flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-accent" />
                Explainable AI (SHAP) Drivers
              </CardTitle>
              <span className="text-[11px] text-muted-foreground font-mono">Directional Impact</span>
            </div>
          </CardHeader>

          <CardContent className="p-4 sm:p-5 space-y-4">
            <ShapBarChart explanations={currentPkg.shap_explanation} />

            {/* Attribution Matrix Table */}
            <div className="pt-3 border-t border-border/70 space-y-2">
              <div className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                Attribution Value Matrix
              </div>
              <div className="overflow-x-auto rounded-md border border-border/60">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-card-raised/80 border-b border-border text-muted-foreground text-[10px] uppercase">
                      <th className="p-2.5 pl-3">Feature Name</th>
                      <th className="p-2.5">SHAP Value</th>
                      <th className="p-2.5">Direction</th>
                      <th className="p-2.5 pr-3">Observed</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60 font-sans">
                    {(currentPkg.shap_explanation || []).map((s, idx) => (
                      <tr key={idx} className="hover:bg-card-raised/40">
                        <td className="p-2.5 pl-3 font-mono font-medium text-foreground">{s.feature}</td>
                        <td
                          className={cn(
                            'p-2.5 font-mono font-bold',
                            s.direction === 'increases_risk' ? 'text-risk-high' : 'text-risk-low'
                          )}
                        >
                          {Number(s.shap_value) >= 0 ? '+' : ''}
                          {Number(s.shap_value).toFixed(4)}
                        </td>
                        <td className="p-2.5">
                          <span
                            className={cn(
                              'inline-flex items-center gap-1 text-[11px] font-semibold',
                              s.direction === 'increases_risk' ? 'text-risk-high' : 'text-risk-low'
                            )}
                          >
                            {s.direction === 'increases_risk' ? (
                              <ArrowUpRight className="h-3 w-3" />
                            ) : (
                              <ArrowDownRight className="h-3 w-3" />
                            )}
                            {s.direction === 'increases_risk' ? 'Risk' : 'Mitigating'}
                          </span>
                        </td>
                        <td className="p-2.5 pr-3 font-mono text-muted-foreground">{String(s.raw_value)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Behavioral Pattern Topology & Subgraph Summary */}
        <Card className="shadow-card border-border/80">
          <CardHeader className="p-4 sm:p-5 pb-3 border-b border-border/60">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm sm:text-base font-serif font-bold text-foreground flex items-center gap-2">
                <Layers className="h-4 w-4 text-accent" />
                Topology & Neighborhood Metrics
              </CardTitle>
              {onNavigateToNetwork && (
                <Button
                  variant="accent"
                  size="sm"
                  onClick={() => onNavigateToNetwork(currentPkg.wallet_id)}
                  className="text-xs h-7 gap-1.5"
                >
                  <Network className="h-3.5 w-3.5" />
                  View Graph
                </Button>
              )}
            </div>
          </CardHeader>

          <CardContent className="p-4 sm:p-5 space-y-4">
            {/* Stat Counters */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3.5 rounded-lg bg-card-raised border border-border/60">
                <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                  Connected Nodes
                </div>
                <div className="font-mono text-2xl font-bold text-foreground mt-1">
                  {nodes.length}
                </div>
              </div>
              <div className="p-3.5 rounded-lg bg-card-raised border border-border/60">
                <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                  Transaction Edges
                </div>
                <div className="font-mono text-2xl font-bold text-accent mt-1">
                  {edges.length}
                </div>
              </div>
            </div>

            {/* Behavioral Pattern Explanation */}
            <div className="p-3.5 rounded-lg bg-card-raised/50 border border-border/60 text-xs leading-relaxed text-muted-foreground">
              <strong className="text-foreground block mb-1">
                Behavioral Signature Pattern:
              </strong>
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
            <div className="pt-2 border-t border-border/70">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowJsonDrawer(!showJsonDrawer)}
                className="w-full text-xs"
              >
                <Code className="h-3.5 w-3.5" />
                {showJsonDrawer ? 'Hide Raw Evidence JSON' : 'Inspect Raw Evidence JSON'}
              </Button>

              {showJsonDrawer && (
                <div className="mt-3 relative rounded-lg border border-border bg-background p-3">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCopyJson}
                    className="absolute right-2.5 top-2.5 text-[11px] h-6 px-2"
                  >
                    {copiedJson ? (
                      <Check className="h-3 w-3 text-emerald-500 mr-1" />
                    ) : (
                      <Copy className="h-3 w-3 mr-1" />
                    )}
                    {copiedJson ? 'Copied' : 'Copy'}
                  </Button>
                  <pre className="font-mono text-[11px] text-muted-foreground max-h-60 overflow-y-auto pt-4 leading-normal">
                    {JSON.stringify(currentPkg, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </motion.div>
  );
};
