import React from 'react';
import { motion } from 'motion/react';
import type { EvidencePackage } from '@/types/forensics';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Cpu, TrendingUp, Sparkles, Brain } from 'lucide-react';

interface ModelInsightsTabProps {
  evidenceList: EvidencePackage[];
}

export const ModelInsightsTab: React.FC<ModelInsightsTabProps> = ({ evidenceList }) => {
  // Aggregate global SHAP feature impacts
  const featureImpactMap: Record<string, number> = {};

  evidenceList.forEach((pkg) => {
    (pkg.shap_explanation || []).forEach((s) => {
      const feat = s.feature || 'unknown';
      const absVal = Math.abs(Number(s.shap_value) || 0);
      featureImpactMap[feat] = (featureImpactMap[feat] || 0) + absVal;
    });
  });

  const sortedFeatures = Object.entries(featureImpactMap)
    .map(([feature, impact]) => ({ feature, impact: impact / Math.max(1, evidenceList.length) }))
    .sort((a, b) => b.impact - a.impact);

  const maxImpact = Math.max(...sortedFeatures.map((f) => f.impact), 0.01);

  // Group risk scores by pattern
  const patternScores: Record<string, number[]> = {};
  evidenceList.forEach((pkg) => {
    const pat = pkg.pattern_hint || 'unknown';
    const score = Number(pkg.final_risk_score) || 0;
    if (!patternScores[pat]) patternScores[pat] = [];
    patternScores[pat].push(score);
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      <div className="pb-2 border-b border-border/80">
        <h2 className="font-serif text-xl sm:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
          <Brain className="h-6 w-6 text-accent" />
          Model Insights & Ensemble Signals
        </h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          Global explainability rankings, feature impact distributions, and community risk decomposition
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Global SHAP Impact Ranking */}
        <Card className="shadow-card border-border/80">
          <CardHeader className="p-4 sm:p-5 pb-3 border-b border-border/60">
            <CardTitle className="text-sm sm:text-base font-serif font-bold text-foreground flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-accent" />
              Global Feature Impact Ranking (Mean |SHAP|)
            </CardTitle>
          </CardHeader>

          <CardContent className="p-4 sm:p-5 space-y-3.5">
            {sortedFeatures.map((item, idx) => {
              const widthPct = Math.max(8, (item.impact / maxImpact) * 100);
              return (
                <div key={item.feature} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-foreground font-semibold flex items-center gap-2">
                      <Badge variant="outline" className="text-[10px] h-5 px-1.5 font-mono">
                        #{idx + 1}
                      </Badge>
                      {item.feature}
                    </span>
                    <span className="font-mono text-accent font-bold text-xs">
                      {item.impact.toFixed(4)}
                    </span>
                  </div>
                  <div className="h-2 w-full bg-card-raised rounded-full overflow-hidden border border-border/50">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${widthPct}%` }}
                      transition={{ duration: 0.5, delay: idx * 0.04 }}
                      className="h-full bg-gradient-to-r from-amber-600 to-accent rounded-full shadow-[0_0_8px_rgba(200,151,59,0.4)]"
                    />
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Pattern Risk Distributions */}
        <Card className="shadow-card border-border/80">
          <CardHeader className="p-4 sm:p-5 pb-3 border-b border-border/60">
            <CardTitle className="text-sm sm:text-base font-serif font-bold text-foreground flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-risk-high" />
              Risk Score Mean by Pattern Signature
            </CardTitle>
          </CardHeader>

          <CardContent className="p-4 sm:p-5 space-y-4">
            {Object.entries(patternScores).map(([pat, scores], idx) => {
              const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
              const min = Math.min(...scores);
              const max = Math.max(...scores);
              const widthPct = Math.min(100, Math.max(10, avg));

              return (
                <div key={pat} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-foreground font-semibold">
                      {pat}{' '}
                      <span className="text-muted-foreground font-normal font-sans">
                        ({scores.length} entities)
                      </span>
                    </span>
                    <span className="font-mono text-risk-high font-bold text-xs">
                      Avg: {avg.toFixed(1)} / 100
                    </span>
                  </div>
                  <div className="h-2 w-full bg-card-raised rounded-full overflow-hidden border border-border/50">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${widthPct}%` }}
                      transition={{ duration: 0.5, delay: idx * 0.05 }}
                      className="h-full bg-gradient-to-r from-orange-600 to-risk-high rounded-full"
                    />
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground font-mono">
                    <span>Min Score: {min.toFixed(1)}</span>
                    <span>Max Score: {max.toFixed(1)}</span>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>

      {/* Model Ensemble Architecture Section */}
      <Card className="shadow-card border-border/80 border-t-2 border-t-accent p-5 sm:p-6">
        <div className="flex items-center gap-2 mb-2">
          <Cpu className="h-5 w-5 text-accent" />
          <h3 className="font-serif text-base sm:text-lg font-bold text-foreground">
            Dual-Engine Forensic Scoring Architecture
          </h3>
        </div>
        <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
          The final composite risk score ($0–100$) integrates a multivariate <strong>Isolation Forest</strong> unsupervised anomaly detector trained on temporal burstiness, round-number ratios, and fee-to-amount distributions, fused with a <strong>Louvain community modularity</strong> projection score. Feature attributions are rendered through exact <strong>SHAP TreeExplainer</strong> values to provide human-auditable explanations for every flagged transaction cluster.
        </p>
      </Card>
    </motion.div>
  );
};
