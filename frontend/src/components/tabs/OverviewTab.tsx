import React from 'react';
import { motion } from 'motion/react';
import type { EvidencePackage, NetworkSummaryStats } from '@/types/forensics';
import { CanvasGraphHUD } from '@/components/landing/CanvasGraphHUD';
import { MetricCards } from '@/components/landing/MetricCards';
import { TriageStream } from '@/components/landing/TriageStream';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { BarChart3, Globe, PieChart, ShieldCheck } from 'lucide-react';

interface OverviewTabProps {
  evidenceList: EvidencePackage[];
  stats: NetworkSummaryStats;
  onInspect: (pkg: EvidencePackage) => void;
  onNavigateToQueue?: () => void;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({ evidenceList, stats, onInspect, onNavigateToQueue }) => {
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
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* 1. Canvas Network HUD Animation */}
      <CanvasGraphHUD />

      {/* 2. Headline Metric Gauges */}
      <MetricCards stats={stats} />

      {/* 3. Live High-Risk Triage Stream */}
      <Card className="p-5 shadow-card border-border/80">
        <TriageStream evidenceList={evidenceList} onInspect={onInspect} onNavigateToQueue={onNavigateToQueue} />
      </Card>

      {/* 4. Deep Analytical Distribution Charts */}
      <div className="space-y-4 pt-2">
        <div className="flex flex-col space-y-1 pb-3 border-b border-border/80">
          <div className="flex items-center gap-2">
            <h3 className="font-serif text-lg sm:text-xl font-bold text-foreground">
              Statistical Risk & Behavioral Distributions
            </h3>
          </div>
          <p className="text-xs text-muted-foreground">
            Aggregate empirical distribution profiles across flagged transaction subgraphs and broadcast entities
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Chart 1: Risk Score Histogram */}
          <Card className="shadow-card border-border/80">
            <CardHeader className="p-4 pb-2 border-b border-border/60">
              <CardTitle className="text-sm font-serif font-bold flex items-center gap-2 text-foreground">
                <BarChart3 className="h-4 w-4 text-accent" />
                Risk Score Distribution Histogram
              </CardTitle>
            </CardHeader>

            <CardContent className="p-4">
              <div className="flex items-end h-36 gap-3 pt-4 border-b border-border">
                {['0–19', '20–39', '40–59', '60–79', '80–100'].map((label, idx) => {
                  const count = scoreBins[idx];
                  const heightPct = Math.max(10, (count / maxBin) * 100);
                  const barColors = [
                    'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.3)]',
                    'bg-teal-500 shadow-[0_0_8px_rgba(20,184,166,0.3)]',
                    'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.3)]',
                    'bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.3)]',
                    'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.3)]',
                  ];

                  return (
                    <div key={idx} className="flex-1 flex flex-col items-center justify-end h-full group">
                      <span className="font-mono text-[11px] text-foreground font-semibold mb-1 opacity-80 group-hover:opacity-100">
                        {count}
                      </span>
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: `${heightPct}%` }}
                        transition={{ duration: 0.5, delay: idx * 0.08 }}
                        className={`w-full rounded-t-sm transition-all ${barColors[idx]}`}
                      />
                      <span className="font-mono text-[10px] text-muted-foreground mt-2">
                        {label}
                      </span>
                    </div>
                  );
                })}
              </div>
              <div className="text-[11px] text-muted-foreground mt-2 text-center">
                Score Ranges (Low to Critical Severity Bands)
              </div>
            </CardContent>
          </Card>

          {/* Chart 2: Behavioral Patterns */}
          <Card className="shadow-card border-border/80">
            <CardHeader className="p-4 pb-2 border-b border-border/60">
              <CardTitle className="text-sm font-serif font-bold flex items-center gap-2 text-foreground">
                <PieChart className="h-4 w-4 text-accent" />
                Behavioral Pattern Frequency
              </CardTitle>
            </CardHeader>

            <CardContent className="p-4 space-y-3">
              {patternEntries.length === 0 ? (
                <div className="text-xs text-muted-foreground py-6 text-center">No patterns recorded.</div>
              ) : (
                patternEntries.map(([pat, count], idx) => {
                  const widthPct = Math.max(8, (count / maxPattern) * 100);
                  return (
                    <div key={pat} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-mono text-foreground font-medium">{pat}</span>
                        <span className="font-mono text-accent font-semibold text-xs">{count} entities</span>
                      </div>
                      <div className="h-2 w-full bg-card-raised rounded-full overflow-hidden border border-border/50">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${widthPct}%` }}
                          transition={{ duration: 0.5, delay: idx * 0.05 }}
                          className="h-full bg-accent rounded-full"
                        />
                      </div>
                    </div>
                  );
                })
              )}
            </CardContent>
          </Card>

          {/* Chart 3: Flagged Jurisdictions */}
          <Card className="shadow-card border-border/80">
            <CardHeader className="p-4 pb-2 border-b border-border/60">
              <CardTitle className="text-sm font-serif font-bold flex items-center gap-2 text-foreground">
                <Globe className="h-4 w-4 text-risk-high" />
                Flagged Jurisdictions & Broadcast Nodes
              </CardTitle>
            </CardHeader>

            <CardContent className="p-4 space-y-3">
              {countryEntries.length === 0 ? (
                <div className="text-xs text-muted-foreground py-6 text-center">
                  No geographic broadcast records found in current evidence.
                </div>
              ) : (
                countryEntries.map(([country, count], idx) => {
                  const widthPct = Math.max(10, (count / maxCountry) * 100);
                  return (
                    <div key={country} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-foreground font-medium">{country}</span>
                        <span className="font-mono text-risk-high font-semibold text-xs">{count} nodes</span>
                      </div>
                      <div className="h-2 w-full bg-card-raised rounded-full overflow-hidden border border-border/50">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${widthPct}%` }}
                          transition={{ duration: 0.5, delay: idx * 0.05 }}
                          className="h-full bg-risk-high rounded-full"
                        />
                      </div>
                    </div>
                  );
                })
              )}
            </CardContent>
          </Card>

          {/* Chart 4: Severity Band Breakdown */}
          <Card className="shadow-card border-border/80">
            <CardHeader className="p-4 pb-2 border-b border-border/60">
              <CardTitle className="text-sm font-serif font-bold flex items-center gap-2 text-foreground">
                <ShieldCheck className="h-4 w-4 text-risk-critical" />
                Severity Band Breakdown
              </CardTitle>
            </CardHeader>

            <CardContent className="p-4 space-y-3">
              {[
                { label: 'Critical (≥90)', count: stats.critical_count, color: 'bg-red-500', text: 'text-red-500' },
                { label: 'High (70–89)', count: stats.high_count, color: 'bg-orange-500', text: 'text-orange-500' },
                { label: 'Medium (40–69)', count: stats.medium_count, color: 'bg-amber-500', text: 'text-amber-500' },
                { label: 'Low (<40)', count: stats.low_count, color: 'bg-emerald-500', text: 'text-emerald-500' },
              ].map((band, idx) => {
                const total = Math.max(1, stats.total_wallets);
                const pct = Math.round((band.count / total) * 100);
                return (
                  <div key={band.label} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-foreground font-medium">{band.label}</span>
                      <span className={`font-mono font-bold text-xs ${band.text}`}>
                        {band.count} ({pct}%)
                      </span>
                    </div>
                    <div className="h-2 w-full bg-card-raised rounded-full overflow-hidden border border-border/50">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.5, delay: idx * 0.06 }}
                        className={`h-full rounded-full ${band.color}`}
                      />
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </div>
      </div>
    </motion.div>
  );
};
