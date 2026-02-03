import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contactsApi } from '@/lib/api';
import { companiesApi } from '@/lib/api';
import type { ContactsListParams, Contact } from '@/types/contact';

export function useContacts(params?: ContactsListParams) {
  return useQuery({
    queryKey: ['contacts', params],
    queryFn: () => contactsApi.list(params),
    staleTime: 30 * 1000, // 30 seconds for lists
    gcTime: 2 * 60 * 1000, // 2 minutes garbage collection time
  });
}

export function useContact(id: string) {
  return useQuery({
    queryKey: ['contact', id],
    queryFn: () => contactsApi.getById(id),
    enabled: !!id,
    staleTime: 2 * 60 * 1000, // 2 minutes for detail views
    gcTime: 5 * 60 * 1000, // 5 minutes garbage collection time
  });
}

export function useCreateContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: contactsApi.create,
    onSuccess: (contact) => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      if (contact?.company_id) {
        queryClient.invalidateQueries({ queryKey: ['company', contact.company_id, 'contacts'] });
      }
    },
  });
}

export function useUpdateContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Contact> }) =>
      contactsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['contact', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
    },
  });
}

export function useDeleteContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => contactsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
    },
  });
}

// Fetch all companies for dropdown
export function useCompaniesForDropdown() {
  return useQuery({
    queryKey: ['companies', { limit: 100 }],
    queryFn: () => companiesApi.list({ limit: 100 }),
  });
}
