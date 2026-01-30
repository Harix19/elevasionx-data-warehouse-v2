'use client';

import { useState } from 'react';
import { Filter, X, ChevronLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FilterAccordion, FilterGroup } from './filter-accordion';
import { cn } from '@/lib/utils';

interface FilterSidebarProps {
  filterGroups: FilterGroup[];
  activeFilters: Record<string, any>;
  onFilterChange: (key: string, value: any) => void;
  resultCount?: number;
  isLoading?: boolean;
  className?: string;
}

export function FilterSidebar({
  filterGroups,
  activeFilters,
  onFilterChange,
  resultCount,
  isLoading,
  className,
}: FilterSidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const activeFilterCount = Object.entries(activeFilters).filter(([key, value]) => {
    // Skip pagination and search params
    if (key === 'cursor' || key === 'q') return false;
    if (value === undefined || value === null || value === '') return false;
    if (Array.isArray(value) && value.length === 0) return false;
    return true;
  }).length;

  const clearAllFilters = () => {
    filterGroups.forEach((group) => {
      onFilterChange(group.key, undefined);
    });
  };

  if (isCollapsed) {
    return (
      <div className={cn("w-14 flex flex-col items-center py-4 border-r border-border bg-background", className)}>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsCollapsed(false)}
          className="relative"
        >
          <Filter className="w-5 h-5" />
          {activeFilterCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 text-xs font-medium bg-primary text-primary-foreground rounded-full flex items-center justify-center">
              {activeFilterCount}
            </span>
          )}
        </Button>
      </div>
    );
  }

  return (
    <div className={cn("w-[280px] flex flex-col border-r border-border bg-background", className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <span className="font-semibold text-sm">Filters</span>
          {activeFilterCount > 0 && (
            <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-medium bg-primary text-primary-foreground rounded-full">
              {activeFilterCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {activeFilterCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAllFilters}
              className="h-8 text-xs text-muted-foreground hover:text-foreground"
            >
              Clear all
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsCollapsed(true)}
            className="h-8 w-8"
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Result count */}
      {(resultCount !== undefined || isLoading) && (
        <div className="px-4 py-2 bg-accent/30 border-b border-border">
          <p className="text-sm text-muted-foreground">
            {isLoading ? (
              <span className="animate-pulse">Counting results...</span>
            ) : (
              <>
                <span className="font-semibold text-foreground">{resultCount?.toLocaleString()}</span>
                {' '}results
              </>
            )}
          </p>
        </div>
      )}

      {/* Filter groups */}
      <div className="flex-1 overflow-y-auto">
        {filterGroups.map((group) => (
          <FilterAccordion
            key={group.key}
            group={group}
            value={activeFilters[group.key]}
            onChange={(value) => onFilterChange(group.key, value)}
          />
        ))}
      </div>
    </div>
  );
}
