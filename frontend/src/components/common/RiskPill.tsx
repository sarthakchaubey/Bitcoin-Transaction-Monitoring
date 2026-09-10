import React from 'react';
import { getRiskSeverityBand } from '@/data/evidenceData';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface RiskPillProps {
  score: number;
  showScore?: boolean;
  className?: string;
}

export const RiskPill: React.FC<RiskPillProps> = ({ score, showScore = true, className = '' }) => {
  const band = getRiskSeverityBand(score);
  const variant = band.toLowerCase() as 'critical' | 'high' | 'medium' | 'low';

  const dotColors = {
    critical: 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.7)]',
    high: 'bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.7)]',
    medium: 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.7)]',
    low: 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.7)]',
  };

  return (
    <Badge
      variant={variant}
      className={cn('inline-flex items-center gap-1.5 px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wider', className)}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full animate-pulse', dotColors[variant])} />
      <span>{band}</span>
      {showScore && <span className="opacity-90 font-mono font-normal">| {score.toFixed(1)}</span>}
    </Badge>
  );
};
