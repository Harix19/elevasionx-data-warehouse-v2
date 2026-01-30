'use client';

import { useMemo, useCallback, Suspense } from 'react';
import { useContacts } from '@/hooks/use-contacts';
import { useContactFilterOptions } from '@/hooks/use-contact-filter-options';
import { useFilterUrlState } from '@/hooks/use-filter-url-state';
import { FilterSidebar, FilterGroup, ActiveFiltersBar } from '@/components/filters';
import { ContactsTable } from '@/components/data-table/contacts-table';
import { Input } from '@/components/ui/input';
import { Search } from 'lucide-react';
import type { ContactsListParams, ContactFilterState } from '@/types/contact';

const PAGE_SIZE = 20;

const leadStatusOptions = [
  { value: 'new', label: 'New' },
  { value: 'contacted', label: 'Contacted' },
  { value: 'qualified', label: 'Qualified' },
  { value: 'customer', label: 'Customer' },
  { value: 'churned', label: 'Churned' },
];

const seniorityOptions = [
  { value: 'c_level', label: 'C-Level' },
  { value: 'director', label: 'Director' },
  { value: 'manager', label: 'Manager' },
  { value: 'individual_contributor', label: 'Individual Contributor' },
  { value: 'other', label: 'Other' },
];

function ContactsPageContent() {
  // URL-synced filters (UI state with nested structures)
  const [filters, setFilters] = useFilterUrlState<ContactFilterState>({});

  // Dynamic filter options from API
  const { data: filterOptions, isLoading: optionsLoading } = useContactFilterOptions();

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

    // Seniority level filter (static options)
    groups.push({
      key: 'seniority_level',
      label: 'Seniority',
      type: 'multiselect',
      options: seniorityOptions,
    });

    // Department filter (only if data exists)
    if (filterOptions?.departments?.length) {
      groups.push({
        key: 'department',
        label: 'Department',
        type: 'multiselect',
        searchable: true,
        options: filterOptions.departments.map((dept) => ({
          value: dept,
          label: dept,
        })),
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
  const params: ContactsListParams = useMemo(() => {
    const apiParams: ContactsListParams = {
      limit: PAGE_SIZE,
      q: filters.q,
      lead_status: filters.lead_status,
      seniority_level: filters.seniority_level,
      department: filters.department,
    };

    // Handle range filters
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

  // Fetch contacts
  const { data: contacts, isLoading, isFetching } = useContacts(params);

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Left Sidebar - Apollo style */}
      <FilterSidebar
        filterGroups={filterGroups}
        activeFilters={filters}
        onFilterChange={handleFilterChange}
        resultCount={contacts?.items?.length}
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
              placeholder="Search contacts by name, email, or role..."
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
            resultCount={contacts?.items?.length}
            isLoading={isLoading || isFetching}
          />
        </div>

        {/* Table */}
        <div className="flex-1 overflow-auto p-4">
          <ContactsTable
            contacts={contacts?.items || []}
            isLoading={isLoading}
            isFetching={isFetching}
            hasMore={contacts?.has_more || false}
            hasPrevious={false}
            onNextPage={() => {}}
            onPreviousPage={() => {}}
          />
        </div>
      </div>
    </div>
  );
}

export default function ContactsPage() {
  return (
    <Suspense fallback={<div className="flex h-[calc(100vh-4rem)] items-center justify-center">Loading filters...</div>}>
      <ContactsPageContent />
    </Suspense>
  );
}
