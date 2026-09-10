import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import type { EvidencePackage, FilterState, TabId } from '@/types/forensics';
import { evidencePackages, computeSummaryStats, getRiskSeverityBand } from '@/data/evidenceData';
import { ThemeProvider } from '@/context/ThemeContext';
import { LenisProvider } from '@/components/common/LenisProvider';
import { Navbar } from '@/components/layout/Navbar';
import { Sidebar } from '@/components/layout/Sidebar';
import { OverviewTab } from '@/components/tabs/OverviewTab';
import { AlertQueueTab } from '@/components/tabs/AlertQueueTab';
import { CaseDetailTab } from '@/components/tabs/CaseDetailTab';
import { NetworkTab } from '@/components/tabs/NetworkTab';
import { ModelInsightsTab } from '@/components/tabs/ModelInsightsTab';
import { ModalDossier } from '@/components/common/ModalDossier';

export function AppContent() {
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
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans transition-colors duration-200 selection:bg-accent selection:text-accent-foreground">
      {/* Navbar Header */}
      <Navbar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        alertCount={filteredEvidence.length}
      />

      {/* Main Investigation Workspace */}
      <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar Filters (visible on Queue, Overview, Detail, and Network) */}
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
          <main className="flex-1 min-w-0">
            <AnimatePresence mode="wait">
              {activeTab === 'overview' && (
                <motion.div
                  key="overview"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.2 }}
                >
                  <OverviewTab
                    evidenceList={filteredEvidence}
                    stats={summaryStats}
                    onInspect={handleInspectEntity}
                    onNavigateToQueue={() => setActiveTab('queue')}
                  />
                </motion.div>
              )}

              {activeTab === 'queue' && (
                <motion.div
                  key="queue"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.2 }}
                >
                  <AlertQueueTab
                    evidenceList={filteredEvidence}
                    onInspect={handleInspectEntity}
                    onSelectEntity={handleSelectEntityFromQueue}
                  />
                </motion.div>
              )}

              {activeTab === 'detail' && (
                <motion.div
                  key="detail"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.2 }}
                >
                  <CaseDetailTab
                    evidenceList={filteredEvidence.length > 0 ? filteredEvidence : evidencePackages}
                    selectedWalletId={selectedWalletId}
                    onSelectWallet={setSelectedWalletId}
                    onNavigateToNetwork={handleNavigateToNetwork}
                  />
                </motion.div>
              )}

              {activeTab === 'network' && (
                <motion.div
                  key="network"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.2 }}
                >
                  <NetworkTab
                    evidenceList={filteredEvidence.length > 0 ? filteredEvidence : evidencePackages}
                    selectedWalletId={selectedWalletId}
                    onSelectWallet={setSelectedWalletId}
                  />
                </motion.div>
              )}

              {activeTab === 'models' && (
                <motion.div
                  key="models"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.2 }}
                >
                  <ModelInsightsTab evidenceList={evidencePackages} />
                </motion.div>
              )}
            </AnimatePresence>
          </main>
        </div>
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

export function App() {
  return (
    <ThemeProvider defaultTheme="dark">
      <LenisProvider>
        <AppContent />
      </LenisProvider>
    </ThemeProvider>
  );
}

export default App;
