'use client';

import { useCallback, useMemo } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';

export function useFilterUrlState<T extends Record<string, any>>(
  defaultFilters: T
): [T, (filters: T) => void, () => void] {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  // Parse filters from URL
  const filters = useMemo(() => {
    const parsed: Record<string, any> = {};

    searchParams.forEach((value, key) => {
      // Skip pagination params
      if (key === 'cursor' || key === 'page') return;

      // Parse arrays (comma-separated)
      if (value.includes(',')) {
        parsed[key] = value.split(',').filter(Boolean);
      }
      // Parse numbers
      else if (!isNaN(Number(value)) && value !== '') {
        parsed[key] = Number(value);
      }
      // Keep as string
      else {
        parsed[key] = value;
      }
    });

    return { ...defaultFilters, ...parsed } as T;
  }, [searchParams, defaultFilters]);

  // Update URL when filters change
  const setFilters = useCallback((newFilters: T) => {
    const params = new URLSearchParams();

    Object.entries(newFilters).forEach(([key, value]) => {
      // Skip undefined, null, empty strings, and default values
      if (value === undefined || value === null || value === '') return;
      if (Array.isArray(value) && value.length === 0) return;

      // Handle arrays (join with comma)
      if (Array.isArray(value)) {
        params.set(key, value.join(','));
      }
      // Handle numbers
      else if (typeof value === 'number') {
        params.set(key, value.toString());
      }
      // Handle strings
      else if (typeof value === 'string') {
        params.set(key, value);
      }
    });

    const queryString = params.toString();
    router.push(queryString ? `${pathname}?${queryString}` : pathname);
  }, [router, pathname]);

  // Clear all filters
  const clearFilters = useCallback(() => {
    router.push(pathname);
  }, [router, pathname]);

  return [filters, setFilters, clearFilters];
}
