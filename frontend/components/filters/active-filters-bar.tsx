'use client';

import { X } from 'lucide-react';
import { FilterGroup } from './filter-accordion';
import { cn } from '@/lib/utils';

interface ActiveFiltersBarProps {
  filterGroups: FilterGroup[];
  activeFilters: Record<string, any>;
  onFilterChange: (key: string, value: any) => void;
  resultCount?: number;
  isLoading?: boolean;
}

export function ActiveFiltersBar({
  filterGroups,
  activeFilters,
  onFilterChange,
  resultCount,
  isLoading,
}: ActiveFiltersBarProps) {
  // Build list of active filter pills
  const activePills = Object.entries(activeFilters)
    .filter(([key, value]) => {
      // Skip pagination and search params
      if (key === 'cursor' || key === 'q') return false;
      if (value === undefined || value === null || value === '') return false;
      if (Array.isArray(value) && value.length === 0) return false;
      return true;
    })
    .map(([key, value]) => {
      const group = filterGroups.find((g) => g.key === key);
      if (!group) return null;

      let displayLabel: string;
      let displayValue: string;

      // Format based on filter type
      if (group.type === 'range') {
        const min = value?.min;
        const max = value?.max;
        if (min !== undefined && max !== undefined) {
          displayValue = `${min} - ${max}`;
        } else if (min !== undefined) {
          displayValue = `≥ ${min}`;
        } else if (max !== undefined) {
          displayValue = `≤ ${max}`;
        } else {
          return null;
        }
        displayLabel = group.label;
      } else if (group.type === 'tags') {
        const tags = value?.tags || [];
        const logic = value?.logic || 'or';
        if (tags.length === 0) return null;
        displayLabel = group.label;
        const tagLabels = tags.map((t: string) => {
          const opt = group.options?.find((o) => o.value === t);
          return opt?.label || t;
        });
        displayValue = `${tagLabels.join(logic === 'and' ? ' + ' : ' or ')}`;
      } else if (Array.isArray(value)) {
        displayLabel = group.label;
        const labels = value.map((v) => {
          const opt = group.options?.find((o) => o.value === v);
          return opt?.label || v;
        });
        displayValue = labels.join(', ');
      } else {
        displayLabel = group.label;
        const opt = group.options?.find((o) => o.value === value);
        displayValue = opt?.label || value;
      }

      return {
        key,
        label: displayLabel,
        value: displayValue,
        rawValue: value,
      };
    })
    .filter(Boolean);

  const clearAll = () => {
    activePills.forEach((pill) => {
      if (pill) onFilterChange(pill.key, undefined);
    });
  };

  if (activePills.length === 0) {
    return (
      <div className="flex items-center justify-between py-2">
        <p className="text-sm text-muted-foreground">
          {isLoading ? (
            <span className="animate-pulse">Loading...</span>
          ) : resultCount !== undefined ? (
            <>
              <span className="font-semibold text-foreground">{resultCount.toLocaleString()}</span>
              {' '}results
            </>
          ) : null}
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-2 py-2">
      {/* Result count */}
      {(resultCount !== undefined || isLoading) && (
        <span className="text-sm text-muted-foreground mr-2">
          {isLoading ? (
            <span className="animate-pulse">Loading...</span>
          ) : (
            <>
              <span className="font-semibold text-foreground">{resultCount?.toLocaleString()}</span>
              {' '}results
            </>
          )}
        </span>
      )}

      {/* Active filter pills */}
      {activePills.map((pill) =>
        pill ? (
          <div
            key={pill.key}
            className={cn(
              'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm',
              'bg-primary/10 text-primary-foreground border border-primary/20',
              'hover:bg-primary/20 transition-colors'
            )}
          >
            <span className="font-medium">{pill.label}:</span>
            <span>{pill.value}</span>
            <button
              onClick={() => onFilterChange(pill.key, undefined)}
              className="ml-1 p-0.5 rounded-full hover:bg-primary/20 transition-colors"
              aria-label={`Remove ${pill.label} filter`}
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : null
      )}

      {/* Clear all button */}
      <button
        onClick={clearAll}
        className="text-sm text-muted-foreground hover:text-foreground underline underline-offset-2 transition-colors"
      >
        Clear all
      </button>
    </div>
  );
}
