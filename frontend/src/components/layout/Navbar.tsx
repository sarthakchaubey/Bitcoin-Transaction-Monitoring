import React, { useState } from 'react';
import { motion } from 'motion/react';
import type { TabId } from '@/types/forensics';
import { Shield, LayoutDashboard, AlertOctagon, FileText, Share2, Brain, Menu } from 'lucide-react';
import { ThemeToggle } from '@/components/common/ThemeToggle';
import { Sheet } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface NavbarProps {
  activeTab: TabId;
  onSelectTab: (tab: TabId) => void;
  alertCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onSelectTab, alertCount }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const tabs: { id: TabId; label: string; icon: React.ReactNode; badge?: number }[] = [
    { id: 'overview', label: 'Overview', icon: <LayoutDashboard className="h-4 w-4" /> },
    { id: 'queue', label: 'Alert Queue', icon: <AlertOctagon className="h-4 w-4" />, badge: alertCount },
    { id: 'detail', label: 'Case Detail', icon: <FileText className="h-4 w-4" /> },
    { id: 'network', label: 'Network', icon: <Share2 className="h-4 w-4" /> },
    { id: 'models', label: 'Model Insights', icon: <Brain className="h-4 w-4" /> },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-card/80 backdrop-blur-md">
      {/* Top Banner Row */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between gap-4">
          {/* Brand Info */}
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-accent/60 bg-gradient-to-br from-card-raised to-background shadow-glow">
              <Shield className="h-5 w-5 text-accent" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-serif text-lg sm:text-xl font-bold tracking-tight text-foreground">
                  Bitcoin Forensics Console
                </h1>
                <Badge variant="accent" className="hidden sm:inline-flex text-[10px] py-0 px-2">
                  AML Engine
                </Badge>
              </div>
              <p className="hidden md:block text-xs text-muted-foreground truncate max-w-md">
                Offline Transaction Monitoring, Community Risk Scoring & Explainable AI
              </p>
            </div>
          </div>

          {/* Right Controls: Mode Badge, Theme Toggle & Mobile Menu */}
          <div className="flex items-center gap-2.5">
            <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full border border-border bg-card-raised text-xs font-mono text-emerald-500 font-medium">
              <div className="beacon-dot" />
              <span className="text-[11px] tracking-wider uppercase">Offline Pipeline Synced</span>
            </div>

            <ThemeToggle />

            {/* Mobile Hamburger Button */}
            <Button
              variant="outline"
              size="icon-sm"
              className="lg:hidden"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open mobile navigation"
            >
              <Menu className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Desktop Navigation Tabs */}
      <div className="hidden lg:block border-t border-border/60 bg-card/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-1 py-1" aria-label="Tabs">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => onSelectTab(tab.id)}
                  className={cn(
                    'relative flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors whitespace-nowrap',
                    isActive
                      ? 'text-accent font-semibold'
                      : 'text-muted-foreground hover:text-foreground hover:bg-card-raised/50'
                  )}
                >
                  {tab.icon}
                  <span>{tab.label}</span>
                  {tab.badge !== undefined && (
                    <span
                      className={cn(
                        'ml-1 px-1.5 py-0.5 text-[11px] font-mono rounded-full border transition-colors',
                        isActive
                          ? 'border-accent/50 bg-accent/15 text-accent font-bold'
                          : 'border-border bg-card-raised text-muted-foreground'
                      )}
                    >
                      {tab.badge}
                    </span>
                  )}
                  {isActive && (
                    <motion.div
                      layoutId="activeNavTab"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent shadow-[0_0_8px_rgba(200,151,59,0.8)]"
                      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                    />
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Mobile Drawer Sheet */}
      <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen} side="left">
        <div className="flex flex-col h-full justify-between pt-4">
          <div>
            <div className="flex items-center gap-2.5 pb-5 border-b border-border mb-4">
              <div className="h-8 w-8 rounded-lg bg-accent/20 border border-accent flex items-center justify-center">
                <Shield className="h-4 w-4 text-accent" />
              </div>
              <div className="font-serif font-bold text-base text-foreground">
                Forensics Navigation
              </div>
            </div>

            <nav className="flex flex-col space-y-1">
              {tabs.map((tab) => {
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => {
                      onSelectTab(tab.id);
                      setMobileMenuOpen(false);
                    }}
                    className={cn(
                      'flex items-center justify-between w-full px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-left',
                      isActive
                        ? 'bg-accent/15 text-accent border border-accent/40 font-semibold'
                        : 'text-foreground hover:bg-card-raised'
                    )}
                  >
                    <div className="flex items-center gap-2.5">
                      {tab.icon}
                      <span>{tab.label}</span>
                    </div>
                    {tab.badge !== undefined && (
                      <Badge variant={isActive ? 'accent' : 'secondary'} className="text-[10px]">
                        {tab.badge}
                      </Badge>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="pt-4 border-t border-border text-xs text-muted-foreground flex items-center justify-between">
            <span className="font-mono">Offline Forensics v2.0</span>
            <div className="flex items-center gap-1.5 text-emerald-500 font-mono text-[11px]">
              <div className="beacon-dot" /> Live
            </div>
          </div>
        </div>
      </Sheet>
    </header>
  );
};
