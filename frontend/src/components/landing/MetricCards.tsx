import React from 'react';
import { motion } from 'motion/react';
import type { NetworkSummaryStats } from '@/types/forensics';
import { ShieldAlert, Users, TrendingUp, AlertTriangle, Coins } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface MetricCardsProps {
  stats: NetworkSummaryStats;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ stats }) => {
  const cards = [
    {
      title: 'Monitored Entities',
      value: stats.total_wallets.toString(),
      hint: 'Cluster-aggregated wallets',
      borderColor: 'border-t-accent',
      iconBg: 'bg-accent/15 text-accent',
      icon: <Users className="h-4 w-4" />,
    },
    {
      title: 'Mean Network Risk',
      value: `${stats.avg_risk_score.toFixed(1)} / 100`,
      hint: 'Composite anomaly score',
      borderColor: 'border-t-accent',
      iconBg: 'bg-accent/15 text-accent',
      icon: <TrendingUp className="h-4 w-4" />,
    },
    {
      title: 'Critical / High Alerts',
      value: (stats.critical_count + stats.high_count).toString(),
      hint: 'Priority triage backlog',
      borderColor: 'border-t-risk-critical',
      iconBg: 'bg-risk-critical-bg text-risk-critical',
      icon: <ShieldAlert className="h-4 w-4" />,
    },
    {
      title: 'Medium Risk Backlog',
      value: stats.medium_count.toString(),
      hint: 'Requires secondary review',
      borderColor: 'border-t-risk-medium',
      iconBg: 'bg-risk-medium-bg text-risk-medium',
      icon: <AlertTriangle className="h-4 w-4" />,
    },
    {
      title: 'Flagged Volume',
      value: `${stats.total_flagged_volume_btc.toFixed(2)} ₿`,
      hint: 'Total ingress subgraph sum',
      borderColor: 'border-t-accent',
      iconBg: 'bg-accent/15 text-accent',
      icon: <Coins className="h-4 w-4" />,
    },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.07 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3.5 mb-6"
    >
      {cards.map((card, idx) => (
        <motion.div key={idx} variants={itemVariants}>
          <Card
            className={cn(
              'border-t-2 p-4 flex flex-col justify-between h-full hover:-translate-y-0.5 hover:shadow-card transition-all duration-200 bg-card/90',
              card.borderColor
            )}
          >
            <div className="flex items-center justify-between gap-2 mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground truncate">
                {card.title}
              </span>
              <div className={cn('p-1.5 rounded-md flex items-center justify-center', card.iconBg)}>
                {card.icon}
              </div>
            </div>

            <div>
              <div className="font-mono text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                {card.value}
              </div>
              <p className="text-[11px] text-muted-foreground mt-1 truncate">
                {card.hint}
              </p>
            </div>
          </Card>
        </motion.div>
      ))}
    </motion.div>
  );
};
