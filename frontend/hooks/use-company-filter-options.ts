import { useQuery } from '@tanstack/react-query';
import { companiesApi } from '@/lib/api';

export function useCompanyFilterOptions() {
  return useQuery({
    queryKey: ['company-filter-options'],
    queryFn: () => companiesApi.getFilterOptions(),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}
