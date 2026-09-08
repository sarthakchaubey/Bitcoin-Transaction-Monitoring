import React from 'react';
import type { NetworkSummaryStats } from '../../types/forensics';
import { ShieldAlert, Users, TrendingUp, AlertTriangle, Coins } from 'lucide-react';

interface MetricCardsProps {
  stats: NetworkSummaryStats;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ stats }) => {
  const cards = [
    {
      title: 'Monitored Entities',
      value: stats.total_wallets.toString(),
      hint: 'Cluster-aggregated wallets',
      color: 'var(--accent)',
      icon: <Users size={16} color="var(--accent)" />,
    },
    {
      title: 'Mean Network Risk',
      value: `${stats.avg_risk_score.toFixed(1)} / 100`,
      hint: 'Composite anomaly score',
      color: 'var(--accent)',
      icon: <TrendingUp size={16} color="var(--accent)" />,
    },
    {
      title: 'Critical / High Alerts',
      value: (stats.critical_count + stats.high_count).toString(),
      hint: 'Priority triage backlog',
      color: 'var(--risk-critical)',
      icon: <ShieldAlert size={16} color="var(--risk-critical)" />,
    },
    {
      title: 'Medium Risk Backlog',
      value: stats.medium_count.toString(),
      hint: 'Requires secondary review',
      color: 'var(--risk-medium)',
      icon: <AlertTriangle size={16} color="var(--risk-medium)" />,
    },
    {
      title: 'Flagged Volume',
      value: `${stats.total_flagged_volume_btc.toFixed(2)} ₿`,
      hint: 'Total ingress subgraph sum',
      color: 'var(--accent)',
      icon: <Coins size={16} color="var(--accent)" />,
    },
  ];

  return (
    <div className="stats-grid">
      {cards.map((card, idx) => (
        <div
          key={idx}
          className="stat-card"
          style={{ '--card-color': card.color } as React.CSSProperties}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="stat-title">{card.title}</div>
            {card.icon}
          </div>
          <div className="stat-number">{card.value}</div>
          <div className="stat-hint">{card.hint}</div>
        </div>
      ))}
    </div>
  );
};
