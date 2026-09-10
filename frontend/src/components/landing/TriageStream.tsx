import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import type { EvidencePackage } from '@/types/forensics';
import { RiskPill } from '@/components/common/RiskPill';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Search, ArrowRight, Tag, ChevronDown, ChevronUp, ExternalLink, ShieldAlert, SlidersHorizontal } from 'lucide-react';
import { cn } from '@/lib/utils';

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
    <div className="space-y-4">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-border/80">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-risk-critical-bg border border-risk-critical-border text-risk-critical">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-serif text-base sm:text-lg font-bold text-foreground">
                High-Risk Priority Triage Feed
              </h3>
              <Badge variant="accent" className="font-mono text-[10px]">
                {filtered.length} Entities
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              {isMinimized
                ? 'Section minimized. Click expand or jump to the dedicated Alert Queue page.'
                : `Displaying top ${displayedList.length} of ${filtered.length} ranked critical targets`}
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          {!isMinimized && (
            <>
              {/* Limit Pill Selector */}
              <div className="inline-flex items-center bg-card-raised border border-border rounded-lg p-0.5 gap-1">
                <SlidersHorizontal className="h-3.5 w-3.5 ml-2 mr-1 text-muted-foreground" />
                {[
                  { label: 'Top 6', val: 6 },
                  { label: 'Top 12', val: 12 },
                  { label: 'All', val: -1 },
                ].map((opt) => (
                  <button
                    key={opt.val}
                    className={cn(
                      'px-2.5 py-1 text-xs rounded-md transition-all font-medium',
                      limit === opt.val
                        ? 'bg-accent text-accent-foreground font-semibold shadow-sm'
                        : 'text-muted-foreground hover:text-foreground'
                    )}
                    onClick={() => setLimit(opt.val)}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>

              {/* Search Box */}
              <div className="relative w-44 sm:w-52">
                <Input
                  type="text"
                  placeholder="Filter targets..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="h-8 text-xs pr-7"
                />
                <Search className="absolute right-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
              </div>
            </>
          )}

          {/* Jump to Alert Queue Tab */}
          {onNavigateToQueue && (
            <Button
              variant="accent"
              size="sm"
              onClick={onNavigateToQueue}
              className="text-xs h-8"
              title="Open full dedicated Alert Queue page with table, sorting, and CSV export"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              Alert Queue ({filtered.length})
            </Button>
          )}

          {/* Minimize / Expand Toggle */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsMinimized(!isMinimized)}
            className="text-xs h-8"
            title={isMinimized ? 'Expand Triage Feed' : 'Minimize Triage Feed'}
          >
            {isMinimized ? (
              <>
                <ChevronDown className="h-3.5 w-3.5" /> Expand
              </>
            ) : (
              <>
                <ChevronUp className="h-3.5 w-3.5" /> Minimize
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Collapsible Content */}
      <AnimatePresence>
        {!isMinimized && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
            className="space-y-4"
          >
            {displayedList.length === 0 ? (
              <Card className="text-center py-10 text-muted-foreground text-xs">
                No entities matched the search filter "{query}".
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
                {displayedList.map((item, index) => {
                  const shaps = (item.shap_explanation || []).slice(0, 2);
                  return (
                    <motion.div
                      key={item.wallet_id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.2, delay: index * 0.03 }}
                    >
                      <Card
                        onClick={() => onInspect(item)}
                        className="group flex flex-col justify-between h-full p-4 cursor-pointer hover:border-accent hover:bg-card-raised/70 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card"
                      >
                        <div>
                          {/* Wallet Header & Risk Pill */}
                          <div className="flex items-start justify-between gap-2 mb-2">
                            <span className="font-mono text-xs font-bold text-foreground group-hover:text-accent transition-colors truncate">
                              {item.wallet_id.substring(0, 16)}...
                            </span>
                            <RiskPill score={Number(item.final_risk_score)} />
                          </div>

                          {/* Pattern Tag */}
                          <div className="flex items-center gap-1 text-[11px] font-mono text-accent mb-2">
                            <Tag className="h-3 w-3" />
                            <span>{item.pattern_hint || 'unknown'}</span>
                          </div>

                          {/* Reason Sentence */}
                          <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed mb-3">
                            {item.reason_sentence || 'Anomalous network transaction signature detected.'}
                          </p>

                          {/* Inline Mini SHAP Bars */}
                          {shaps.length > 0 && (
                            <div className="pt-2 border-t border-border/60 space-y-1.5">
                              {shaps.map((s, idx) => {
                                const val = Math.abs(Number(s.shap_value) || 0);
                                const width = Math.min(100, Math.round(val * 180));
                                const isRisk = s.direction === 'increases_risk' || Number(s.shap_value) > 0;
                                const barColor = isRisk ? 'bg-risk-high' : 'bg-risk-low';

                                return (
                                  <div key={idx} className="flex items-center gap-2 text-[11px]">
                                    <span
                                      className="font-mono text-muted-foreground w-24 truncate"
                                      title={s.feature}
                                    >
                                      {s.feature}
                                    </span>
                                    <div className="flex-1 h-1.5 bg-muted/60 rounded-full overflow-hidden">
                                      <div
                                        className={cn('h-full rounded-full', barColor)}
                                        style={{ width: `${width}%` }}
                                      />
                                    </div>
                                    <span className="font-mono text-[10px] text-foreground font-semibold">
                                      {Number(s.shap_value).toFixed(2)}
                                    </span>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>

                        {/* Card Footer */}
                        <div className="flex items-center justify-between pt-3 mt-3 border-t border-border/60 text-xs text-muted-foreground">
                          <span>
                            Confidence: <strong className="text-foreground">{item.confidence_label || 'Normal'}</strong>
                          </span>
                          <span className="text-accent font-semibold flex items-center gap-1 text-[11px] group-hover:translate-x-0.5 transition-transform">
                            Inspect <ArrowRight className="h-3 w-3" />
                          </span>
                        </div>
                      </Card>
                    </motion.div>
                  );
                })}
              </div>
            )}

            {/* Footer Pagination Controls */}
            {limit > 0 && filtered.length > limit && (
              <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-border/80 text-xs text-muted-foreground">
                <span>
                  Showing <strong className="text-foreground">{displayedList.length}</strong> of{' '}
                  <strong className="text-foreground">{filtered.length}</strong> prioritized alerts.
                </span>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setLimit(limit === 6 ? 12 : -1)}
                    className="text-xs h-7"
                  >
                    {limit === 6 ? 'Show Next 6 (+6)' : 'Show All'}
                  </Button>
                  {onNavigateToQueue && (
                    <Button
                      variant="accent"
                      size="sm"
                      onClick={onNavigateToQueue}
                      className="text-xs h-7 flex items-center gap-1"
                    >
                      View All in Queue <ArrowRight className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
