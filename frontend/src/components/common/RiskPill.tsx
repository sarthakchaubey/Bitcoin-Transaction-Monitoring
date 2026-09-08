import React from 'react';
import { getRiskSeverityBand } from '../../data/evidenceData';

interface RiskPillProps {
  score: number;
  showScore?: boolean;
  className?: string;
}

export const RiskPill: React.FC<RiskPillProps> = ({ score, showScore = true, className = '' }) => {
  const band = getRiskSeverityBand(score);
  const pillClass = band.toLowerCase();

  return (
    <span className={`risk-pill ${pillClass} ${className}`}>
      {band.toUpperCase()} {showScore ? `• ${score.toFixed(1)}` : ''}
    </span>
  );
};
