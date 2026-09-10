import React from 'react';
import type { FilterState } from '@/types/forensics';
import { SlidersHorizontal, RotateCcw, Search, Filter } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

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

  const handleScoreChange = (val: number) => {
    onFilterChange({
      ...filters,
      minRiskScore: val,
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
    <aside className="w-full lg:w-72 shrink-0">
      <Card className="sticky top-20 shadow-card border-border/80">
        <CardHeader className="p-4 pb-3 border-b border-border/60">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-serif font-bold text-accent flex items-center gap-2">
              <SlidersHorizontal className="h-4 w-4" />
              Queue Filters
            </CardTitle>
            <Badge variant="outline" className="text-[10px] font-mono">
              <Filter className="h-2.5 w-2.5 mr-1 text-accent" />
              {filteredRecords} / {totalRecords}
            </Badge>
          </div>
          <div className="text-[11px] text-muted-foreground pt-1">
            Showing <strong className="text-accent font-semibold">{filteredRecords}</strong> of{' '}
            <strong className="text-foreground">{totalRecords}</strong> entities
          </div>
        </CardHeader>

        <CardContent className="p-4 space-y-4">
          {/* Search Target Input */}
          <div className="space-y-1.5">
            <label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
              Search Target Entity
            </label>
            <div className="relative">
              <Input
                placeholder="Search address or pattern..."
                value={filters.searchQuery}
                onChange={handleSearchChange}
                className="pr-8 text-xs h-8"
              />
              <Search className="absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
            </div>
          </div>

          {/* Min Risk Score Slider */}
          <div className="space-y-2 pt-1">
            <div className="flex items-center justify-between text-xs">
              <label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                Min Risk Score
              </label>
              <span className="font-mono font-bold text-accent text-xs">
                {filters.minRiskScore.toFixed(0)} / 100
              </span>
            </div>
            <Slider
              value={filters.minRiskScore}
              min={0}
              max={100}
              step={1}
              onValueChange={handleScoreChange}
            />
          </div>

          {/* Severity Confidence Checkboxes */}
          <div className="space-y-2 pt-1">
            <label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground block">
              Severity Confidence
            </label>
            <div className="grid grid-cols-2 gap-2">
              {severities.map((sev) => {
                const isChecked = filters.selectedSeverities.includes(sev);
                const colors = {
                  Critical: 'hover:border-risk-critical/40',
                  High: 'hover:border-risk-high/40',
                  Medium: 'hover:border-risk-medium/40',
                  Low: 'hover:border-risk-low/40',
                };
                return (
                  <label
                    key={sev}
                    className={`flex items-center gap-2 p-1.5 rounded-md border text-xs cursor-pointer transition-colors ${
                      isChecked
                        ? 'bg-card-raised border-border text-foreground font-medium'
                        : 'border-transparent text-muted-foreground hover:bg-card-raised/50'
                    } ${colors[sev as keyof typeof colors]}`}
                  >
                    <Checkbox
                      checked={isChecked}
                      onCheckedChange={() => handleSeverityToggle(sev)}
                    />
                    <span className="text-xs">{sev}</span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Behavioral Patterns */}
          {availablePatterns.length > 0 && (
            <div className="space-y-2 pt-1">
              <label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground block">
                Behavioral Pattern
              </label>
              <div className="max-h-40 overflow-y-auto space-y-1.5 pr-1 text-xs">
                {availablePatterns.map((pat) => {
                  const isChecked = filters.selectedPatterns.includes(pat);
                  return (
                    <label
                      key={pat}
                      className={`flex items-center gap-2 p-1.5 rounded-md border text-xs cursor-pointer transition-colors ${
                        isChecked
                          ? 'bg-card-raised border-border text-foreground'
                          : 'border-transparent text-muted-foreground hover:bg-card-raised/50'
                      }`}
                    >
                      <Checkbox
                        checked={isChecked}
                        onCheckedChange={() => handlePatternToggle(pat)}
                      />
                      <span className="font-mono text-[11px] truncate">{pat}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          )}

          {/* Reset Filters Button */}
          <div className="pt-2 border-t border-border">
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              className="w-full text-xs"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              Reset All Filters
            </Button>
          </div>
        </CardContent>
      </Card>
    </aside>
  );
};
