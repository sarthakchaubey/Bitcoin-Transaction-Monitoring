import React from 'react';
import type { TabId } from '../../types/forensics';
import { Shield, LayoutDashboard, AlertOctagon, FileText, Share2, Brain } from 'lucide-react';

interface NavbarProps {
  activeTab: TabId;
  onSelectTab: (tab: TabId) => void;
  alertCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onSelectTab, alertCount }) => {
  const tabs: { id: TabId; label: string; icon: React.ReactNode; badge?: number }[] = [
    { id: 'overview', label: 'Overview', icon: <LayoutDashboard size={17} /> },
    { id: 'queue', label: 'Alert Queue', icon: <AlertOctagon size={17} />, badge: alertCount },
    { id: 'detail', label: 'Case Detail', icon: <FileText size={17} /> },
    { id: 'network', label: 'Network', icon: <Share2 size={17} /> },
    { id: 'models', label: 'Model Insights', icon: <Brain size={17} /> },
  ];

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <div className="brand-section">
          <div className="brand-icon">
            <Shield size={22} color="var(--accent)" />
          </div>
          <div>
            <h1 className="brand-title">Bitcoin Forensics Case Console</h1>
            <p className="brand-subtitle">
              Offline Transaction Monitoring, Community Risk Scoring & Explainable AI Case Investigation
            </p>
          </div>
        </div>

        <div className="mode-badge">
          <div className="beacon-dot" />
          OFFLINE FORENSICS MODE
        </div>
      </div>

      <div style={{ maxWidth: '1600px', margin: '0 auto', padding: '0 20px' }}>
        <nav className="tab-nav" style={{ marginBottom: 0 }}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => onSelectTab(tab.id)}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.badge !== undefined && (
                <span
                  style={{
                    backgroundColor: 'var(--surface-raised)',
                    border: '1px solid var(--border)',
                    borderRadius: '10px',
                    padding: '1px 6px',
                    fontSize: '0.72rem',
                    fontFamily: 'IBM Plex Mono, monospace',
                    color: 'var(--accent)',
                  }}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>
    </header>
  );
};
