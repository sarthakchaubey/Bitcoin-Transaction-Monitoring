import React from 'react';
import type { FilterState } from '../../types/forensics';
import { SlidersHorizontal, RotateCcw, Search } from 'lucide-react';

interface SidebarProps {
  filters: FilterState;
  onFilterChange: (filters: FilterState) => void;
  availablePatterns: string[];
  totalRecords: number;
  filteredRecords: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  filters,
  onFilterChange,
  availablePatterns,
  totalRecords,
  filteredRecords,
}) => {
  const severities = ['Critical', 'High', 'Medium', 'Low'];

  const handleScoreChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({
      ...filters,
      minRiskScore: parseFloat(e.target.value) || 0,
    });
  };

  const handleSeverityToggle = (sev: string) => {
    const next = filters.selectedSeverities.includes(sev)
      ? filters.selectedSeverities.filter((s) => s !== sev)
      : [...filters.selectedSeverities, sev];
    onFilterChange({ ...filters, selectedSeverities: next });
  };

  const handlePatternToggle = (pat: string) => {
    const next = filters.selectedPatterns.includes(pat)
      ? filters.selectedPatterns.filter((p) => p !== pat)
      : [...filters.selectedPatterns, pat];
    onFilterChange({ ...filters, selectedPatterns: next });
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({ ...filters, searchQuery: e.target.value });
  };

  const handleReset = () => {
    onFilterChange({
      minRiskScore: 0,
      selectedSeverities: ['Critical', 'High', 'Medium', 'Low'],
      selectedPatterns: [...availablePatterns],
      searchQuery: '',
    });
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-title">
        <SlidersHorizontal size={18} />
        <span>Queue Filters</span>
      </div>

      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '14px' }}>
        Showing <strong style={{ color: 'var(--accent)' }}>{filteredRecords}</strong> of{' '}
        <strong style={{ color: 'var(--text)' }}>{totalRecords}</strong> entities
      </div>

      {/* Search Input */}
      <div className="filter-group">
        <label className="filter-label">Search Target Entity</label>
        <div style={{ position: 'relative' }}>
          <input
            type="text"
            className="search-input"
            placeholder="Search address or hash..."
            value={filters.searchQuery}
            onChange={handleSearchChange}
          />
          <Search
            size={14}
            style={{
              position: 'absolute',
              right: '10px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)',
              pointerEvents: 'none',
            }}
          />
        </div>
      </div>

      {/* Min Risk Score Slider */}
      <div className="filter-group">
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
          <label className="filter-label" style={{ margin: 0 }}>Min Risk Score</label>
          <span className="font-mono" style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--accent)' }}>
            {filters.minRiskScore.toFixed(0)} / 100
          </span>
        </div>
        <input
          type="range"
          min="0"
          max="100"
          step="1"
          value={filters.minRiskScore}
          onChange={handleScoreChange}
          className="range-slider"
        />
      </div>

      {/* Risk Severity Checkboxes */}
      <div className="filter-group">
        <label className="filter-label">Severity Confidence</label>
        <div className="checkbox-group">
          {severities.map((sev) => (
            <label key={sev} className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.selectedSeverities.includes(sev)}
                onChange={() => handleSeverityToggle(sev)}
                style={{ accentColor: 'var(--accent)', cursor: 'pointer' }}
              />
              <span>{sev}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Behavioral Pattern Hints */}
      {availablePatterns.length > 0 && (
        <div className="filter-group">
          <label className="filter-label">Behavioral Pattern</label>
          <div className="checkbox-group" style={{ maxHeight: '160px', overflowY: 'auto' }}>
            {availablePatterns.map((pat) => (
              <label key={pat} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={filters.selectedPatterns.includes(pat)}
                  onChange={() => handlePatternToggle(pat)}
                  style={{ accentColor: 'var(--accent)', cursor: 'pointer' }}
                />
                <span className="font-mono" style={{ fontSize: '0.78rem' }}>{pat}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      <button className="btn" onClick={handleReset} style={{ width: '100%', justifyContent: 'center' }}>
        <RotateCcw size={14} /> Reset Filters
      </button>
    </aside>
  );
};
