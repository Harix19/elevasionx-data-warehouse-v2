'use client';

import { useState } from 'react';
import { ReactNode } from 'react';
import { Search, X, Filter, ChevronDown, ListFilter } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useDebouncedCallback } from 'use-debounce';

interface ToolbarProps {
  searchPlaceholder?: string;
  filters?: FilterConfig[];
  activeFilters?: Record<string, any>;
  onSearchChange?: (search: string) => void;
  onFilterChange?: (filters: Record<string, any>) => void;
  exportAction?: ReactNode;
}

export interface FilterConfig {
  key: string;
  label: string;
  type: 'select' | 'multiselect';
  options?: Array<{ value: string; label: string }>;
}

export function DataTableToolbar({
  searchPlaceholder = 'Search...',
  filters = [],
  activeFilters = {},
  onSearchChange,
  onFilterChange,
  exportAction,
}: ToolbarProps) {
  const [searchValue, setSearchValue] = useState('');

  // Debounced search handler
  const debouncedSearch = useDebouncedCallback(
    (value: string) => {
      onSearchChange?.(value);
    },
    500
  );

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchValue(value);
    debouncedSearch(value);
  };

  const handleClearSearch = () => {
    setSearchValue('');
    onSearchChange?.('');
  };

  const handleRemoveFilter = (key: string) => {
    const newFilters = { ...activeFilters };
    delete newFilters[key];
    onFilterChange?.(newFilters);
  };

  const handleClearAllFilters = () => {
    onFilterChange?.({});
  };

  // Get active filter display labels with proper option labels
  const activeFilterPills = Object.entries(activeFilters)
    .filter(([_, value]) => value !== undefined && value !== '' && value !== null)
    .map(([key, value]) => {
      const filterConfig = filters.find(f => f.key === key);
      const label = filterConfig?.label || key;
      // Look up the display label for the value from options
      let displayValue: string;
      if (Array.isArray(value)) {
        const valueLabels = value.map(v => {
          const option = filterConfig?.options?.find(opt => opt.value === v);
          return option?.label || v;
        });
        displayValue = valueLabels.join(', ');
      } else {
        const option = filterConfig?.options?.find(opt => opt.value === value);
        displayValue = option?.label || value;
      }
      return { key, label, value: displayValue };
    });

  return (
    <div className="space-y-4 mb-6">
      {/* Search and Filter Bar */}
      <div className="flex items-center gap-4 flex-wrap">
        {/* Search Input */}
        <div className="relative flex-1 min-w-[300px] max-w-md group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted group-focus-within:text-primary transition-colors" />
          <Input
            placeholder={searchPlaceholder}
            value={searchValue}
            onChange={handleSearchChange}
            className="pl-11 h-12 glass border-glass-border focus:ring-primary/20 focus:border-primary rounded-2xl transition-all shadow-sm"
          />
          {searchValue && (
            <button
              onClick={handleClearSearch}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-foreground-muted hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Filter Buttons */}
          {filters.map((filter) => (
            <FilterDropdown
              key={filter.key}
              config={filter}
              value={activeFilters[filter.key]}
              onChange={(value) => onFilterChange?.({ ...activeFilters, [filter.key]: value })}
            />
          ))}

          {/* Clear All Filters */}
          {activeFilterPills.length > 0 && (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={handleClearAllFilters}
              className="text-foreground-muted hover:text-red-400 hover:bg-red-400/10 rounded-xl"
            >
              <ListFilter className="w-4 h-4 mr-2" />
              Reset Filters
            </Button>
          )}
        </div>

        <div className="ml-auto">
          {/* Export Action */}
          {exportAction}
        </div>
      </div>

      {/* Active Filter Pills */}
      {activeFilterPills.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap animate-fade-in-up">
          <span className="text-xs font-bold uppercase tracking-wider text-foreground-muted mr-1">Active Filters:</span>
          {activeFilterPills.map((pill) => (
            <Badge 
              key={pill.key} 
              variant="secondary" 
              className="gap-2 px-3 py-1.5 glass border-primary/30 text-primary-light rounded-xl font-medium shadow-sm hover:border-primary transition-all"
            >
              <span className="opacity-60">{pill.label}:</span> {pill.value}
              <button
                onClick={() => handleRemoveFilter(pill.key)}
                className="hover:bg-primary/20 rounded-full p-0.5 transition-colors"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

function FilterDropdown({
  config,
  value,
  onChange,
}: {
  config: FilterConfig;
  value: any;
  onChange: (value: any) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);

  if (config.type === 'select') {
    return (
      <div className="relative">
        <Button
          variant="outline"
          size="default"
          onClick={() => setIsOpen(!isOpen)}
          className={`
            h-12 glass border-glass-border hover:bg-white/5 rounded-2xl px-5 gap-2 transition-all
            ${value ? 'border-primary bg-primary/5 text-primary-light' : 'text-foreground-muted'}
          `}
        >
          <Filter className="w-4 h-4" />
          <span className="font-semibold">{config.label}</span>
          {value && (
            <span className="ml-1 text-primary">: {config.options?.find(opt => opt.value === value)?.label || value}</span>
          )}
          <ChevronDown className={`w-4 h-4 ml-1 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </Button>
        {isOpen && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
            <div className="absolute top-full left-0 mt-2 glass border-glass-border rounded-2xl shadow-2xl z-20 p-2 min-w-[200px] animate-fade-in-up overflow-hidden">
              <button
                className={`
                  block w-full text-left px-4 py-3 rounded-xl transition-all font-medium text-sm mb-1
                  ${!value ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'hover:bg-white/5 text-foreground-muted'}
                `}
                onClick={() => {
                  onChange(undefined);
                  setIsOpen(false);
                }}
              >
                Show All
              </button>
              <div className="h-px bg-glass-border my-1" />
              {config.options?.map((option) => (
                <button
                  key={option.value}
                  className={`
                    block w-full text-left px-4 py-3 rounded-xl transition-all font-medium text-sm mb-1
                    ${value === option.value ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'hover:bg-white/5 text-foreground-muted'}
                  `}
                  onClick={() => {
                    onChange(option.value);
                    setIsOpen(false);
                  }}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    );
  }

  return null;
}
