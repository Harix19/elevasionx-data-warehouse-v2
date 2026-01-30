'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface FilterOption {
  value: string;
  label: string;
  count?: number;
}

export interface FilterGroup {
  key: string;
  label: string;
  type: 'select' | 'multiselect' | 'range' | 'tags';
  defaultOpen?: boolean;
  searchable?: boolean;
  options?: FilterOption[];
  rangeConfig?: {
    min: number;
    max: number;
    step?: number;
    format?: 'currency' | 'number' | 'compact';
    prefix?: string;
    suffix?: string;
  };
}

interface FilterAccordionProps {
  group: FilterGroup;
  value: any;
  onChange: (value: any) => void;
}

export function FilterAccordion({ group, value, onChange }: FilterAccordionProps) {
  const [isOpen, setIsOpen] = useState(group.defaultOpen ?? false);
  const [searchQuery, setSearchQuery] = useState('');

  const hasValue = value !== undefined && value !== null && value !== '' &&
    !(Array.isArray(value) && value.length === 0);

  const activeCount = Array.isArray(value) ? value.length : (hasValue ? 1 : 0);

  // Filter options by search query
  const filteredOptions = group.searchable && searchQuery
    ? group.options?.filter(opt =>
        opt.label.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : group.options;

  return (
    <div className="border-b border-border/50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between py-3 px-4 text-left hover:bg-accent/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{group.label}</span>
          {activeCount > 0 && (
            <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-medium bg-primary text-primary-foreground rounded-full">
              {activeCount}
            </span>
          )}
        </div>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        )}
      </button>

      {isOpen && (
        <div className="px-4 pb-4 animate-in fade-in slide-in-from-top-2 duration-200">
          {/* Search within filter */}
          {group.searchable && (
            <div className="mb-3">
              <input
                type="text"
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-[var(--input)] rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
              />
            </div>
          )}

          {/* Render filter content based on type */}
          {group.type === 'select' && (
            <div className="space-y-1">
              {filteredOptions?.map((option) => (
                <label
                  key={option.value}
                  className="flex items-center gap-3 py-2 px-2 rounded-md hover:bg-accent/50 cursor-pointer transition-colors"
                >
                  <input
                    type="radio"
                    name={group.key}
                    value={option.value}
                    checked={value === option.value}
                    onChange={() => onChange(option.value)}
                    className="w-4 h-4 text-primary border-border focus:ring-primary"
                  />
                  <span className="flex-1 text-sm">{option.label}</span>
                  {option.count !== undefined && (
                    <span className="text-xs text-muted-foreground">{option.count}</span>
                  )}
                </label>
              ))}
            </div>
          )}

          {group.type === 'multiselect' && (
            <div className="space-y-1 max-h-64 overflow-y-auto">
              {filteredOptions?.map((option) => {
                const isSelected = (value || []).includes(option.value);
                return (
                  <label
                    key={option.value}
                    className={cn(
                      "flex items-center gap-3 py-2 px-2 rounded-md cursor-pointer transition-colors",
                      isSelected ? "bg-primary/10" : "hover:bg-accent/50"
                    )}
                  >
                    <input
                      type="checkbox"
                      value={option.value}
                      checked={isSelected}
                      onChange={(e) => {
                        const current = Array.isArray(value) ? value : [];
                        if (e.target.checked) {
                          onChange([...current, option.value]);
                        } else {
                          onChange(current.filter((v: string) => v !== option.value));
                        }
                      }}
                      className="w-4 h-4 text-primary border-border rounded focus:ring-primary"
                    />
                    <span className="flex-1 text-sm">{option.label}</span>
                    {option.count !== undefined && (
                      <span className="text-xs text-muted-foreground">{option.count}</span>
                    )}
                  </label>
                );
              })}
            </div>
          )}

          {group.type === 'range' && group.rangeConfig && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <div className="flex-1">
                  <label className="block text-xs text-muted-foreground mb-1">Min</label>
                  <input
                    type="number"
                    value={value?.min ?? ''}
                    onChange={(e) => {
                      const min = e.target.value ? Number(e.target.value) : undefined;
                      onChange({ ...value, min });
                    }}
                    placeholder={group.rangeConfig.min.toString()}
                    className="w-full px-3 py-2 text-sm border border-[var(--input)] rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                  />
                </div>
                <span className="text-muted-foreground pt-6">-</span>
                <div className="flex-1">
                  <label className="block text-xs text-muted-foreground mb-1">Max</label>
                  <input
                    type="number"
                    value={value?.max ?? ''}
                    onChange={(e) => {
                      const max = e.target.value ? Number(e.target.value) : undefined;
                      onChange({ ...value, max });
                    }}
                    placeholder={group.rangeConfig.max.toString()}
                    className="w-full px-3 py-2 text-sm border border-[var(--input)] rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                  />
                </div>
              </div>
            </div>
          )}

          {group.type === 'tags' && (
            <div className="space-y-3">
              {/* Logic toggle */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Match:</span>
                <div className="flex rounded-md border border-[var(--input)] overflow-hidden">
                  <button
                    onClick={() => onChange({ ...value, logic: 'or' })}
                    className={cn(
                      "px-3 py-1 text-xs font-medium transition-colors",
                      (value?.logic || 'or') === 'or'
                        ? "bg-primary text-primary-foreground"
                        : "bg-background hover:bg-accent"
                    )}
                  >
                    Any
                  </button>
                  <button
                    onClick={() => onChange({ ...value, logic: 'and' })}
                    className={cn(
                      "px-3 py-1 text-xs font-medium transition-colors",
                      value?.logic === 'and'
                        ? "bg-primary text-primary-foreground"
                        : "bg-background hover:bg-accent"
                    )}
                  >
                    All
                  </button>
                </div>
              </div>

              {/* Tag options */}
              <div className="space-y-1 max-h-64 overflow-y-auto">
                {filteredOptions?.map((option) => {
                  const tags = value?.tags || [];
                  const isSelected = tags.includes(option.value);
                  return (
                    <label
                      key={option.value}
                      className={cn(
                        "flex items-center gap-3 py-2 px-2 rounded-md cursor-pointer transition-colors",
                        isSelected ? "bg-primary/10" : "hover:bg-accent/50"
                      )}
                    >
                      <input
                        type="checkbox"
                        value={option.value}
                        checked={isSelected}
                        onChange={(e) => {
                          if (e.target.checked) {
                            onChange({ ...value, tags: [...tags, option.value] });
                          } else {
                            onChange({ ...value, tags: tags.filter((v: string) => v !== option.value) });
                          }
                        }}
                        className="w-4 h-4 text-primary border-border rounded focus:ring-primary"
                      />
                      <span className="flex-1 text-sm">{option.label}</span>
                      {option.count !== undefined && (
                        <span className="text-xs text-muted-foreground">{option.count}</span>
                      )}
                    </label>
                  );
                })}
              </div>
            </div>
          )}

          {/* Clear button */}
          {hasValue && (
            <button
              onClick={() => onChange(undefined)}
              className="mt-3 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Clear selection
            </button>
          )}
        </div>
      )}
    </div>
  );
}
