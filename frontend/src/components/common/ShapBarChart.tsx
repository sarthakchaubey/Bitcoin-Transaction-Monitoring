import React from 'react';
import { motion } from 'motion/react';
import type { SHAPExplanation } from '@/types/forensics';
import { cn } from '@/lib/utils';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface ShapBarChartProps {
  explanations: SHAPExplanation[];
}

export const ShapBarChart: React.FC<ShapBarChartProps> = ({ explanations }) => {
  if (!explanations || explanations.length === 0) {
    return (
      <div className="text-center py-6 text-xs text-muted-foreground">
        No SHAP explanations available for this entity.
      </div>
    );
  }

  const maxVal = Math.max(...explanations.map((e) => Math.abs(Number(e.shap_value) || 0)), 0.01);

  return (
    <div className="flex flex-col space-y-3.5">
      {explanations.map((item, idx) => {
        const val = Number(item.shap_value) || 0;
        const absVal = Math.abs(val);
        const widthPct = Math.min(100, Math.max(8, (absVal / maxVal) * 100));
        const isRisk = item.direction === 'increases_risk' || val > 0;

        return (
          <div key={idx} className="flex flex-col space-y-1.5 group">
            <div className="flex items-center justify-between text-xs">
              <span className="font-mono font-medium text-foreground tracking-tight flex items-center gap-1.5">
                {isRisk ? (
                  <ArrowUpRight className="h-3.5 w-3.5 text-risk-high stroke-[2.5]" />
                ) : (
                  <ArrowDownRight className="h-3.5 w-3.5 text-risk-low stroke-[2.5]" />
                )}
                {item.feature}
              </span>
              <span
                className={cn(
                  'font-mono font-semibold text-xs',
                  isRisk ? 'text-risk-high' : 'text-risk-low'
                )}
              >
                {val >= 0 ? '+' : ''}
                {val.toFixed(4)}
              </span>
            </div>

            {/* Bar Track */}
            <div className="h-2 w-full bg-card-raised rounded-full overflow-hidden p-0.5 border border-border/50">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${widthPct}%` }}
                transition={{ duration: 0.5, delay: idx * 0.06, ease: 'easeOut' }}
                className={cn(
                  'h-full rounded-full transition-all',
                  isRisk
                    ? 'bg-gradient-to-r from-orange-500 to-red-500 shadow-[0_0_8px_rgba(239,68,68,0.4)]'
                    : 'bg-gradient-to-r from-emerald-600 to-teal-400 shadow-[0_0_8px_rgba(16,185,129,0.4)]'
                )}
              />
            </div>

            <div className="flex items-center justify-between text-[11px] text-muted-foreground">
              <span>
                Raw observed:{' '}
                <strong className="font-mono text-foreground font-semibold">
                  {String(item.raw_value)}
                </strong>
              </span>
              <span className={cn('text-[10px] font-semibold uppercase tracking-wider', isRisk ? 'text-risk-high' : 'text-risk-low')}>
                {isRisk ? 'Risk Amplifier' : 'Risk Mitigator'}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
