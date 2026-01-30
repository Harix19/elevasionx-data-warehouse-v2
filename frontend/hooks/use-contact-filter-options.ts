import { useQuery } from '@tanstack/react-query';
import { contactsApi } from '@/lib/api';

export function useContactFilterOptions() {
  return useQuery({
    queryKey: ['contact-filter-options'],
    queryFn: () => contactsApi.getFilterOptions(),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}
