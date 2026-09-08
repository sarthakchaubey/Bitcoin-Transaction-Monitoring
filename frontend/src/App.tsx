import { useState, useMemo } from 'react';
import type { EvidencePackage, FilterState, TabId } from './types/forensics';
import { evidencePackages, computeSummaryStats, getRiskSeverityBand } from './data/evidenceData';
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';
import { OverviewTab } from './components/tabs/OverviewTab';
import { AlertQueueTab } from './components/tabs/AlertQueueTab';
import { CaseDetailTab } from './components/tabs/CaseDetailTab';
import { NetworkTab } from './components/tabs/NetworkTab';
import { ModelInsightsTab } from './components/tabs/ModelInsightsTab';
import { ModalDossier } from './components/common/ModalDossier';

export function App() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [selectedWalletId, setSelectedWalletId] = useState<string>(
    evidencePackages[0]?.wallet_id || ''
  );
  const [modalPkg, setModalPkg] = useState<EvidencePackage | null>(null);

  // Available unique patterns
  const availablePatterns = useMemo(() => {
    const set = new Set<string>();
    evidencePackages.forEach((e) => {
      if (e.pattern_hint) set.add(e.pattern_hint);
    });
    return Array.from(set).sort();
  }, []);

  // Filter state
  const [filters, setFilters] = useState<FilterState>({
    minRiskScore: 0,
    selectedSeverities: ['Critical', 'High', 'Medium', 'Low'],
    selectedPatterns: availablePatterns,
    searchQuery: '',
  });

  // Filtered evidence packages
  const filteredEvidence = useMemo(() => {
    return evidencePackages.filter((pkg) => {
      const score = Number(pkg.final_risk_score) || 0;
      if (score < filters.minRiskScore) return false;

      const band = getRiskSeverityBand(score);
      if (!filters.selectedSeverities.includes(band)) return false;

      const pat = pkg.pattern_hint || 'unknown';
      if (filters.selectedPatterns.length > 0 && !filters.selectedPatterns.includes(pat)) {
        return false;
      }

      if (filters.searchQuery.trim()) {
        const q = filters.searchQuery.toLowerCase().trim();
        const matchesId = pkg.wallet_id?.toLowerCase().includes(q);
        const matchesPat = pkg.pattern_hint?.toLowerCase().includes(q);
        const matchesReason = pkg.reason_sentence?.toLowerCase().includes(q);
        if (!matchesId && !matchesPat && !matchesReason) return false;
      }

      return true;
    });
  }, [filters, availablePatterns]);

  // Overall summary stats
  const summaryStats = useMemo(() => {
    return computeSummaryStats(filteredEvidence.length > 0 ? filteredEvidence : evidencePackages);
  }, [filteredEvidence]);

  const handleInspectEntity = (pkg: EvidencePackage) => {
    setModalPkg(pkg);
  };

  const handleSelectEntityFromQueue = (walletId: string) => {
    setSelectedWalletId(walletId);
    setActiveTab('detail');
  };

  const handleNavigateToNetwork = (walletId: string) => {
    setSelectedWalletId(walletId);
    setActiveTab('network');
  };

  return (
    <div className="app-layout">
      {/* Navbar Header */}
      <Navbar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        alertCount={filteredEvidence.length}
      />

      {/* Main Investigation Workspace */}
      <div className="main-container">
        {/* Sidebar Filters (visible on Queue, Overview, and Detail) */}
        {activeTab !== 'models' && (
          <Sidebar
            filters={filters}
            onFilterChange={setFilters}
            availablePatterns={availablePatterns}
            totalRecords={evidencePackages.length}
            filteredRecords={filteredEvidence.length}
          />
        )}

        {/* Dynamic Tab Content View */}
        <main className="content-area">
          {activeTab === 'overview' && (
            <OverviewTab
              evidenceList={filteredEvidence}
              stats={summaryStats}
              onInspect={handleInspectEntity}
            />
          )}

          {activeTab === 'queue' && (
            <AlertQueueTab
              evidenceList={filteredEvidence}
              onInspect={handleInspectEntity}
              onSelectEntity={handleSelectEntityFromQueue}
            />
          )}

          {activeTab === 'detail' && (
            <CaseDetailTab
              evidenceList={filteredEvidence.length > 0 ? filteredEvidence : evidencePackages}
              selectedWalletId={selectedWalletId}
              onSelectWallet={setSelectedWalletId}
              onNavigateToNetwork={handleNavigateToNetwork}
            />
          )}

          {activeTab === 'network' && (
            <NetworkTab
              evidenceList={filteredEvidence.length > 0 ? filteredEvidence : evidencePackages}
              selectedWalletId={selectedWalletId}
              onSelectWallet={setSelectedWalletId}
            />
          )}

          {activeTab === 'models' && (
            <ModelInsightsTab evidenceList={evidencePackages} />
          )}
        </main>
      </div>

      {/* Quick Dossier Modal */}
      <ModalDossier
        pkg={modalPkg}
        onClose={() => setModalPkg(null)}
        onNavigateToDetail={handleSelectEntityFromQueue}
      />
    </div>
  );
}

export default App;
