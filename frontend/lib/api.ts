import axios from 'axios';
import { tokenStorage } from './auth';
import type { CompaniesListParams, CompaniesListResponse, CompanyFilterOptions } from '@/types/company';
import type { ContactsListParams, ContactsListResponse, ContactFilterOptions } from '@/types/contact';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_URL,
});

// Add auth interceptor to include token in requests
api.interceptors.request.use((config) => {
  const token = tokenStorage.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    console.log('[API] Adding auth header for:', config.url, 'Token:', token.substring(0, 20) + '...');
  } else {
    console.log('[API] No token found for:', config.url);
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[API] Response error:', error.response?.status, error.config?.url);
    if (error.response?.status === 401) {
      console.log('[API] 401 Unauthorized - redirecting to login');
      tokenStorage.removeToken();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Companies API
export const companiesApi = {
  list: async (params?: CompaniesListParams): Promise<CompaniesListResponse> => {
    const response = await api.get<CompaniesListResponse>('/companies', { params });
    return response.data;
  },

  getFilterOptions: async (): Promise<CompanyFilterOptions> => {
    const response = await api.get<CompanyFilterOptions>('/companies/filter-options');
    return response.data;
  },

  getById: async (id: string) => {
    const response = await api.get(`/companies/${id}`);
    return response.data;
  },

  listContacts: async (companyId: string) => {
    const response = await api.get(`/companies/${companyId}/contacts`, {
      params: { include_deleted: false }
    });
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/companies', data);
    return response.data;
  },

  update: async (id: string, data: any) => {
    const response = await api.patch(`/companies/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    const response = await api.delete(`/companies/${id}`);
    return response.data;
  },

  export: async (params?: CompaniesListParams): Promise<void> => {
    const response = await api.get('/export/companies', {
      params,
      responseType: 'blob',
    });

    // Get filename from Content-Disposition header or use default
    const contentDisposition = response.headers['content-disposition'];
    const filenameMatch = contentDisposition?.match(/filename="?(.+)"?/);
    const filename = filenameMatch?.[1] || `companies-${new Date().toISOString().split('T')[0]}.csv`;

    // Create download link and trigger download
    const blob = new Blob([response.data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
  },
};

// Contacts API
export const contactsApi = {
  list: async (params?: ContactsListParams): Promise<ContactsListResponse> => {
    const response = await api.get<ContactsListResponse>('/contacts', { params });
    return response.data;
  },

  getFilterOptions: async (): Promise<ContactFilterOptions> => {
    const response = await api.get<ContactFilterOptions>('/contacts/filter-options');
    return response.data;
  },

  getById: async (id: string) => {
    const response = await api.get(`/contacts/${id}`);
    return response.data;
  },

  create: async (data: any) => {
    const response = await api.post('/contacts', data);
    return response.data;
  },

  update: async (id: string, data: any) => {
    const response = await api.patch(`/contacts/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    const response = await api.delete(`/contacts/${id}`);
    return response.data;
  },

  export: async (params?: ContactsListParams): Promise<void> => {
    const response = await api.get('/export/contacts', {
      params,
      responseType: 'blob',
    });

    // Get filename from Content-Disposition header or use default
    const contentDisposition = response.headers['content-disposition'];
    const filenameMatch = contentDisposition?.match(/filename="?(.+)"?/);
    const filename = filenameMatch?.[1] || `contacts-${new Date().toISOString().split('T')[0]}.csv`;

    // Create download link and trigger download
    const blob = new Blob([response.data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
  },
};

// Import API
export const importApi = {
  companies: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/bulk/import', formData, {
      params: { type: 'companies' },
    });
    return response.data;
  },

  contacts: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/bulk/import', formData, {
      params: { type: 'contacts' },
    });
    return response.data;
  },

  bulkCompanies: async (records: any[]) => {
    const response = await api.post('/bulk/companies', { records });
    return response.data;
  },

  bulkContacts: async (records: any[]) => {
    const response = await api.post('/bulk/contacts', { records });
    return response.data;
  },
};

// Stats API
export interface StatsResponse {
  total_companies: number;
  total_contacts: number;
  total_sources: number;
  recent_activity: Array<{
    type: 'company' | 'contact';
    id: string;
    name: string;
    created_at: string | null;
  }>;
}

export const statsApi = {
  get: async (): Promise<StatsResponse> => {
    const response = await api.get<StatsResponse>('/stats');
    return response.data;
  },
};

export default api;
