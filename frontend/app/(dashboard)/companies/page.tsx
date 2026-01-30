'use client';

import { useMemo, useCallback, Suspense } from 'react';
import { useCompanies } from '@/hooks/use-companies';
import { useCompanyFilterOptions } from '@/hooks/use-company-filter-options';
import { useFilterUrlState } from '@/hooks/use-filter-url-state';
import { FilterSidebar, FilterGroup, ActiveFiltersBar } from '@/components/filters';
import { CompaniesTable } from '@/components/data-table/companies-table';
import { Input } from '@/components/ui/input';
import { Search } from 'lucide-react';
import { formatCompactCurrency } from '@/lib/format';
import type { CompaniesListParams, CompanyFilterState } from '@/types/company';

const PAGE_SIZE = 20;

const leadStatusOptions = [
  { value: 'new', label: 'New' },
  { value: 'contacted', label: 'Contacted' },
  { value: 'qualified', label: 'Qualified' },
  { value: 'customer', label: 'Customer' },
  { value: 'churned', label: 'Churned' },
];

function CompaniesPageContent() {
  // URL-synced filters (UI state with nested structures)
  const [filters, setFilters] = useFilterUrlState<CompanyFilterState>({});

  // Dynamic filter options from API
  const { data: filterOptions, isLoading: optionsLoading } = useCompanyFilterOptions();

  // Build filter groups based on available data (Apollo pattern)
  const filterGroups: FilterGroup[] = useMemo(() => {
    const groups: FilterGroup[] = [
      // Status filter (always shown)
      {
        key: 'lead_status',
        label: 'Status',
        type: 'select',
        defaultOpen: true,
        options: leadStatusOptions,
      },
    ];

    // Industry filter (only if data exists)
    if (filterOptions?.industries?.length) {
      groups.push({
        key: 'industry',
        label: 'Industry',
        type: 'multiselect',
        searchable: true,
        options: filterOptions.industries.map((industry) => ({
          value: industry,
          label: industry,
        })),
      });
    }

    // Country filter (only if data exists)
    if (filterOptions?.countries?.length) {
      groups.push({
        key: 'country',
        label: 'Country',
        type: 'multiselect',
        searchable: true,
        options: filterOptions.countries.map((country) => ({
          value: country,
          label: country,
        })),
      });
    }

    // Revenue range filter (only if data exists)
    if (filterOptions?.revenue_range) {
      groups.push({
        key: 'revenue',
        label: 'Revenue',
        type: 'range',
        rangeConfig: {
          min: Math.floor(filterOptions.revenue_range.min),
          max: Math.ceil(filterOptions.revenue_range.max),
          format: 'currency',
        },
      });
    }

    // Employee count filter (only if data exists)
    if (filterOptions?.employee_count_range) {
      groups.push({
        key: 'employee_count',
        label: 'Employees',
        type: 'range',
        rangeConfig: {
          min: filterOptions.employee_count_range.min,
          max: filterOptions.employee_count_range.max,
          format: 'compact',
        },
      });
    }

    // Lead score filter (only if data exists)
    if (filterOptions?.lead_score_range) {
      groups.push({
        key: 'lead_score',
        label: 'Lead Score',
        type: 'range',
        rangeConfig: {
          min: filterOptions.lead_score_range.min,
          max: filterOptions.lead_score_range.max,
        },
      });
    }

    // Tags A filter (Categories)
    if (filterOptions?.tags_a?.length) {
      groups.push({
        key: 'tags_a',
        label: 'Categories',
        type: 'tags',
        searchable: true,
        options: filterOptions.tags_a.map((tag) => ({
          value: tag,
          label: tag,
        })),
      });
    }

    // Tags B filter (Labels)
    if (filterOptions?.tags_b?.length) {
      groups.push({
        key: 'tags_b',
        label: 'Labels',
        type: 'tags',
        searchable: true,
        options: filterOptions.tags_b.map((tag) => ({
          value: tag,
          label: tag,
        })),
      });
    }

    // Tags C filter (Sources)
    if (filterOptions?.tags_c?.length) {
      groups.push({
        key: 'tags_c',
        label: 'Sources',
        type: 'tags',
        searchable: true,
        options: filterOptions.tags_c.map((tag) => ({
          value: tag,
          label: tag,
        })),
      });
    }

    return groups;
  }, [filterOptions]);

  // Handle filter changes
  const handleFilterChange = useCallback((key: string, value: any) => {
    setFilters({ ...filters, [key]: value });
  }, [filters, setFilters]);

  // Handle search query
  const handleSearchChange = useCallback((q: string) => {
    setFilters({ ...filters, q: q || undefined });
  }, [filters, setFilters]);

  // Prepare API params from filters (flatten nested structures)
  const params: CompaniesListParams = useMemo(() => {
    const apiParams: CompaniesListParams = {
      limit: PAGE_SIZE,
      q: filters.q,
      lead_status: filters.lead_status,
      industry: filters.industry,
      country: filters.country,
    };

    // Handle range filters
    if (filters.revenue) {
      apiParams.revenue_min = filters.revenue.min;
      apiParams.revenue_max = filters.revenue.max;
    }
    if (filters.employee_count) {
      apiParams.employee_count_min = filters.employee_count.min;
      apiParams.employee_count_max = filters.employee_count.max;
    }
    if (filters.lead_score) {
      apiParams.lead_score_min = filters.lead_score.min;
      apiParams.lead_score_max = filters.lead_score.max;
    }

    // Handle tags filters with logic
    if (filters.tags_a) {
      const tags = filters.tags_a.tags || [];
      const logic = filters.tags_a.logic || 'or';
      if (tags.length) {
        if (logic === 'and') {
          apiParams.tags_a_all = tags;
        } else {
          apiParams.tags_a = tags;
        }
      }
    }
    if (filters.tags_b) {
      const tags = filters.tags_b.tags || [];
      const logic = filters.tags_b.logic || 'or';
      if (tags.length) {
        if (logic === 'and') {
          apiParams.tags_b_all = tags;
        } else {
          apiParams.tags_b = tags;
        }
      }
    }
    if (filters.tags_c) {
      const tags = filters.tags_c.tags || [];
      const logic = filters.tags_c.logic || 'or';
      if (tags.length) {
        if (logic === 'and') {
          apiParams.tags_c_all = tags;
        } else {
          apiParams.tags_c = tags;
        }
      }
    }

    return apiParams;
  }, [filters]);

  // Fetch companies
  const { data: companies, isLoading, isFetching } = useCompanies(params);

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Left Sidebar - Apollo style */}
      <FilterSidebar
        filterGroups={filterGroups}
        activeFilters={filters}
        onFilterChange={handleFilterChange}
        resultCount={companies?.items?.length}
        isLoading={optionsLoading}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Search Bar */}
        <div className="p-4 border-b border-border">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search companies by name or domain..."
              value={filters.q || ''}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Active Filters Bar */}
        <div className="px-4 border-b border-border">
          <ActiveFiltersBar
            filterGroups={filterGroups}
            activeFilters={filters}
            onFilterChange={handleFilterChange}
            resultCount={companies?.items?.length}
            isLoading={isLoading || isFetching}
          />
        </div>

        {/* Table */}
        <div className="flex-1 overflow-auto p-4">
          <CompaniesTable
            companies={companies?.items || []}
            isLoading={isLoading}
            isFetching={isFetching}
            hasMore={companies?.has_more || false}
            hasPrevious={false}
            onNextPage={() => {}}
            onPreviousPage={() => {}}
          />
        </div>
      </div>
    </div>
  );
}

export default function CompaniesPage() {
  return (
    <Suspense fallback={<div className="flex h-[calc(100vh-4rem)] items-center justify-center">Loading filters...</div>}>
      <CompaniesPageContent />
    </Suspense>
  );
}
