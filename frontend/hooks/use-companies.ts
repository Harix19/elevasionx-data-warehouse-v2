import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { companiesApi } from '@/lib/api';
import type { CompaniesListParams, Company } from '@/types/company';

export function useCompanies(params?: CompaniesListParams) {
  return useQuery({
    queryKey: ['companies', params],
    queryFn: () => companiesApi.list(params),
    staleTime: 30 * 1000, // 30 seconds for lists
  });
}

export function useCompany(id: string) {
  return useQuery({
    queryKey: ['company', id],
    queryFn: () => companiesApi.getById(id),
    enabled: !!id,
    staleTime: 2 * 60 * 1000, // 2 minutes for detail views
  });
}

export function useCompanyContacts(companyId: string) {
  return useQuery({
    queryKey: ['company', companyId, 'contacts'],
    queryFn: () => companiesApi.listContacts(companyId),
    enabled: !!companyId,
    staleTime: 60 * 1000, // 1 minute for contact lists
  });
}

export function useCreateCompany() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: companiesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
    },
  });
}

export function useUpdateCompany() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Company> }) =>
      companiesApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['company', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['companies'] });
    },
  });
}

export function useDeleteCompany() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => companiesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
    },
  });
}

export function useCompaniesForDropdown() {
  return useQuery({
    queryKey: ['companies', { limit: 100 }],
    queryFn: () => companiesApi.list({ limit: 100 }),
  });
}
