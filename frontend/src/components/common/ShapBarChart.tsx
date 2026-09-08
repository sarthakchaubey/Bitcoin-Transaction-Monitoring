import type { SHAPExplanation } from '../../types/forensics';

interface ShapBarChartProps {
  explanations: SHAPExplanation[];
}

export const ShapBarChart: React.FC<ShapBarChartProps> = ({ explanations }) => {
  if (!explanations || explanations.length === 0) {
    return <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No SHAP explanations available.</div>;
  }

  const maxVal = Math.max(...explanations.map((e) => Math.abs(Number(e.shap_value) || 0)), 0.01);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {explanations.map((item, idx) => {
        const val = Number(item.shap_value) || 0;
        const absVal = Math.abs(val);
        const widthPct = Math.min(100, Math.max(6, (absVal / maxVal) * 100));
        const isRisk = item.direction === 'increases_risk' || val > 0;
        const barColor = isRisk ? 'var(--risk-high)' : 'var(--risk-low)';

        return (
          <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
              <span className="font-mono" style={{ color: 'var(--text)', fontWeight: 600 }}>
                {item.feature}
              </span>
              <span className="font-mono" style={{ color: barColor }}>
                {val >= 0 ? '+' : ''}
                {val.toFixed(4)} ({item.direction === 'increases_risk' ? '▲ Risk' : '▼ Mitigates'})
              </span>
            </div>
            <div
              style={{
                width: '100%',
                height: '8px',
                backgroundColor: 'var(--surface-raised)',
                borderRadius: '4px',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${widthPct}%`,
                  height: '100%',
                  backgroundColor: barColor,
                  borderRadius: '4px',
                  transition: 'width 0.4s ease',
                }}
              />
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
              <span>Raw feature value: <strong className="font-mono" style={{ color: 'var(--text)' }}>{String(item.raw_value)}</strong></span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
