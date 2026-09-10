import React, { useState } from 'react';
import { motion } from 'motion/react';
import type { EvidencePackage } from '@/types/forensics';
import { RiskPill } from '@/components/common/RiskPill';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { getRiskSeverityBand } from '@/data/evidenceData';
import { Download, ArrowUpDown, Eye, ExternalLink, AlertOctagon, ShieldAlert } from 'lucide-react';

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
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-4"
    >
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-2">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="font-serif text-xl sm:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <AlertOctagon className="h-6 w-6 text-risk-critical" />
              Ranked Forensic Alert Queue
            </h2>
            <Badge variant="accent" className="font-mono text-xs">
              {sortedList.length} Active Alerts
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Showing {sortedList.length} prioritized entities matching active sidebar filter criteria
          </p>
        </div>

        <Button
          variant="accent"
          size="sm"
          onClick={handleExportCSV}
          className="text-xs h-9"
        >
          <Download className="h-4 w-4" />
          Export Alert Queue (.csv)
        </Button>
      </div>

      {sortedList.length === 0 ? (
        <Card className="text-center py-16 px-4">
          <ShieldAlert className="h-12 w-12 text-muted-foreground mx-auto mb-3 opacity-40" />
          <h3 className="font-serif text-base font-bold text-foreground mb-1">
            No Flagged Entities Match Active Filters
          </h3>
          <p className="text-xs text-muted-foreground max-w-md mx-auto">
            Try adjusting your minimum risk score threshold or enabling more behavioral pattern categories in the sidebar.
          </p>
        </Card>
      ) : (
        <Card className="shadow-card border-border/80 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-card-raised/80 border-b border-border text-muted-foreground uppercase tracking-wider font-semibold text-[11px]">
                  <th
                    onClick={() => toggleSort('wallet')}
                    className="p-3.5 pl-4 cursor-pointer hover:text-foreground transition-colors select-none"
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Target Wallet ID</span>
                      <ArrowUpDown className="h-3 w-3" />
                    </div>
                  </th>
                  <th
                    onClick={() => toggleSort('score')}
                    className="p-3.5 cursor-pointer hover:text-foreground transition-colors select-none"
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Risk Score</span>
                      <ArrowUpDown className="h-3 w-3" />
                    </div>
                  </th>
                  <th className="p-3.5">Severity Band</th>
                  <th className="p-3.5">Confidence</th>
                  <th
                    onClick={() => toggleSort('pattern')}
                    className="p-3.5 cursor-pointer hover:text-foreground transition-colors select-none"
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Pattern Signature</span>
                      <ArrowUpDown className="h-3 w-3" />
                    </div>
                  </th>
                  <th className="p-3.5 max-w-xs">Forensic Finding Summary</th>
                  <th className="p-3.5 pr-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60 font-sans">
                {sortedList.map((item) => {
                  const score = Number(item.final_risk_score) || 0;
                  return (
                    <tr
                      key={item.wallet_id}
                      onClick={() => onInspect(item)}
                      className="hover:bg-card-raised/60 transition-colors cursor-pointer group"
                    >
                      <td className="p-3.5 pl-4 font-mono font-bold text-foreground group-hover:text-accent transition-colors">
                        {item.wallet_id.substring(0, 18)}...
                      </td>
                      <td className="p-3.5 font-mono font-bold text-foreground text-sm">
                        {score.toFixed(1)}
                      </td>
                      <td className="p-3.5">
                        <RiskPill score={score} showScore={false} />
                      </td>
                      <td className="p-3.5 text-muted-foreground text-xs font-mono">
                        {item.confidence_label || 'Normal'}
                      </td>
                      <td className="p-3.5">
                        <Badge variant="outline" className="font-mono text-[11px] text-accent border-accent/30 bg-accent/5">
                          {item.pattern_hint || 'unknown'}
                        </Badge>
                      </td>
                      <td className="p-3.5 text-muted-foreground max-w-sm">
                        <span className="line-clamp-1 text-xs">
                          {item.reason_sentence}
                        </span>
                      </td>
                      <td className="p-3.5 pr-4 text-right">
                        <div className="inline-flex items-center gap-1.5">
                          <Button
                            variant="outline"
                            size="icon-sm"
                            title="Inspect Dossier"
                            onClick={(e) => {
                              e.stopPropagation();
                              onInspect(item);
                            }}
                            className="h-7 w-7"
                          >
                            <Eye className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            variant="accent"
                            size="icon-sm"
                            title="Open Case Detail View"
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectEntity(item.wallet_id);
                            }}
                            className="h-7 w-7"
                          >
                            <ExternalLink className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </motion.div>
  );
};
