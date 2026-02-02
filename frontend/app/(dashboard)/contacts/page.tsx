'use client';

import { useMemo, useCallback, useState, Suspense } from 'react';
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

  // Pagination state
  const [cursorHistory, setCursorHistory] = useState<string[]>([]);
  const [currentCursor, setCurrentCursor] = useState<string | undefined>(undefined);
  const [pageIndex, setPageIndex] = useState(0);

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
    // Reset pagination when filters change
    setCursorHistory([]);
    setCurrentCursor(undefined);
    setPageIndex(0);
    setFilters({ ...filters, [key]: value });
  }, [filters, setFilters]);

  // Handle search query
  const handleSearchChange = useCallback((q: string) => {
    // Reset pagination when search changes
    setCursorHistory([]);
    setCurrentCursor(undefined);
    setPageIndex(0);
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
      cursor: currentCursor,
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
  }, [filters, currentCursor]);

  // Fetch contacts
  const { data: contacts, isLoading, isFetching } = useContacts(params);

  // Pagination handlers
  const handleNextPage = useCallback(() => {
    if (contacts?.next_cursor) {
      // Save current cursor to history before moving forward
      if (currentCursor) {
        setCursorHistory((prev) => [...prev, currentCursor]);
      } else {
        // First page has no cursor (undefined), store a marker
        setCursorHistory((prev) => [...prev, '']);
      }
      setCurrentCursor(contacts.next_cursor);
      setPageIndex((prev) => prev + 1);
    }
  }, [contacts?.next_cursor, currentCursor]);

  const handlePreviousPage = useCallback(() => {
    if (cursorHistory.length > 0) {
      const previousCursor = cursorHistory[cursorHistory.length - 1];
      // Remove the last cursor from history
      setCursorHistory((prev) => prev.slice(0, -1));
      // Restore previous cursor (empty string means first page)
      setCurrentCursor(previousCursor || undefined);
      setPageIndex((prev) => Math.max(0, prev - 1));
    }
  }, [cursorHistory]);

  const hasPrevious = pageIndex > 0;

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
            hasPrevious={hasPrevious}
            onNextPage={handleNextPage}
            onPreviousPage={handlePreviousPage}
            pageIndex={pageIndex}
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
