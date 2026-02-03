import axios from 'axios';
import { tokenStorage } from './auth';
import type { CompaniesListParams, CompaniesListResponse, CompanyFilterOptions } from '@/types/company';
import type { ContactsListParams, ContactsListResponse, ContactFilterOptions } from '@/types/contact';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Default timeout for regular requests
const DEFAULT_TIMEOUT = 30000; // 30 seconds

// Extended timeout for bulk operations
const BULK_TIMEOUT = 120000; // 2 minutes per batch

export const api = axios.create({
  baseURL: API_URL,
  timeout: DEFAULT_TIMEOUT,
});

// Add auth interceptor to include token in requests
api.interceptors.request.use((config) => {
  const token = tokenStorage.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    if (process.env.NODE_ENV === 'development') {
      console.log('[API] Request:', config.url);
    }
  } else if (process.env.NODE_ENV === 'development') {
    console.log('[API] No token found for:', config.url);
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (process.env.NODE_ENV === 'development') {
      console.error('[API] Response error:', error.response?.status, error.config?.url);
    }
    if (error.response?.status === 401) {
      if (process.env.NODE_ENV === 'development') {
        console.log('[API] 401 Unauthorized - redirecting to login');
      }
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

  bulkCompanies: async (
    records: any[], 
    onProgress?: (processed: number, total: number) => void,
    signal?: AbortSignal
  ) => {
    const BATCH_SIZE = 250;
    const BATCH_DELAY_MS = 150;
    const MAX_RETRIES = 3;
    const RETRY_DELAY_BASE_MS = 1000;
    const totalBatches = Math.ceil(records.length / BATCH_SIZE);
    const results = { total: 0, created: 0, updated: 0, duplicates: 0, errors: [] as any[] };
    let completedBatches = 0;
    
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Import] Starting companies import: ${records.length} records in ${totalBatches} batches`);
    }
    
    for (let i = 0; i < records.length; i += BATCH_SIZE) {
      const batchNum = Math.floor(i / BATCH_SIZE) + 1;
      
      // Check for cancellation before each batch
      if (signal?.aborted) {
        throw new Error('Import cancelled');
      }
      
      const batch = records.slice(i, i + BATCH_SIZE);
      if (process.env.NODE_ENV === 'development') {
        console.log(`[Import] Batch ${batchNum}/${totalBatches}: ${batch.length} records (${i}-${Math.min(i + BATCH_SIZE, records.length)})`);
      }
      
      // Try sending batch with retry logic
      let response = null;
      let lastError: any = null;
      const isLastBatch = i + BATCH_SIZE >= records.length;
      const batchTimeout = isLastBatch ? BULK_TIMEOUT * 2 : BULK_TIMEOUT;
      
      for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
        try {
          if (attempt > 1) {
            const retryDelay = RETRY_DELAY_BASE_MS * (attempt - 1);
            if (process.env.NODE_ENV === 'development') {
              console.log(`[Import] Batch ${batchNum} retry ${attempt - 1}/${MAX_RETRIES - 1} after ${retryDelay}ms delay...`);
            }
            await new Promise(resolve => setTimeout(resolve, retryDelay));
          }
          
          response = await api.post('/bulk/companies', { records: batch }, {
            timeout: batchTimeout,
            signal,
          });
          
          if (process.env.NODE_ENV === 'development') {
            console.log(`[Import] Batch ${batchNum}/${totalBatches} completed successfully:`, {
              total: response.data.total,
              created: response.data.created,
              updated: response.data.updated,
              errors: response.data.errors?.length || 0
            });
          }
          
          break; // Success, exit retry loop
        } catch (error: any) {
          lastError = error;
          if (process.env.NODE_ENV === 'development') {
            console.error(`[Import] Batch ${batchNum}/${totalBatches} attempt ${attempt} failed:`, error.message);
          }
          
          if (signal?.aborted) {
            throw new Error('Import cancelled');
          }
          
          // Don't retry if we've exhausted retries
          if (attempt === MAX_RETRIES) {
            if (process.env.NODE_ENV === 'development') {
              console.error(`[Import] Batch ${batchNum}/${totalBatches} failed after ${MAX_RETRIES} attempts`);
            }
            throw error;
          }
        }
      }
      
      if (!response) {
        throw new Error(`Batch ${batchNum} failed to complete after ${MAX_RETRIES} attempts`);
      }
      
      // Aggregate results with error handling
      try {
        results.total += response.data.total || 0;
        results.created += response.data.created || 0;
        results.updated += response.data.updated || 0;
        results.duplicates += response.data.duplicates || 0;
        
        if (response.data.errors && Array.isArray(response.data.errors)) {
          results.errors.push(...response.data.errors.map((e: any) => ({
            ...e,
            index: (e.index || 0) + i // Adjust index to global position
          })));
        }
      } catch (err: any) {
        if (process.env.NODE_ENV === 'development') {
          console.error(`[Import] Failed to process batch ${batchNum} response:`, err);
        }
        throw new Error(`Failed to process batch ${batchNum} results: ${err.message}`);
      }
      
      completedBatches++;
      const processed = Math.min(i + BATCH_SIZE, records.length);
      if (process.env.NODE_ENV === 'development') {
        console.log(`[Import] Progress: ${processed}/${records.length} records, ${completedBatches}/${totalBatches} batches`);
      }
      onProgress?.(processed, records.length);
      
      // Delay between batches to allow Neon connections to close
      if (i + BATCH_SIZE < records.length) {
        if (process.env.NODE_ENV === 'development') {
          console.log(`[Import] Waiting ${BATCH_DELAY_MS}ms before next batch...`);
        }
        await new Promise(resolve => setTimeout(resolve, BATCH_DELAY_MS));
      }
    }
    
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Import] Import complete: ${results.created + results.updated}/${results.total} successful, ${results.errors.length} errors`);
    }
    
    return {
      ...results,
      completedBatches,
      totalBatches,
      partialSuccess: completedBatches < totalBatches
    };
  },

  bulkContacts: async (
    records: any[], 
    onProgress?: (processed: number, total: number) => void,
    signal?: AbortSignal
  ) => {
    const BATCH_SIZE = 250;
    const BATCH_DELAY_MS = 150;
    const MAX_RETRIES = 3;
    const RETRY_DELAY_BASE_MS = 1000;
    const totalBatches = Math.ceil(records.length / BATCH_SIZE);
    const results = { total: 0, created: 0, updated: 0, duplicates: 0, errors: [] as any[] };
    let completedBatches = 0;
    
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Import] Starting contacts import: ${records.length} records in ${totalBatches} batches`);
    }
    
    for (let i = 0; i < records.length; i += BATCH_SIZE) {
      const batchNum = Math.floor(i / BATCH_SIZE) + 1;
      
      // Check for cancellation before each batch
      if (signal?.aborted) {
        throw new Error('Import cancelled');
      }
      
      const batch = records.slice(i, i + BATCH_SIZE);
      if (process.env.NODE_ENV === 'development') {
        console.log(`[Import] Batch ${batchNum}/${totalBatches}: ${batch.length} records (${i}-${Math.min(i + BATCH_SIZE, records.length)})`);
      }
      
      // Try sending batch with retry logic
      let response = null;
      let lastError: any = null;
      const isLastBatch = i + BATCH_SIZE >= records.length;
      const batchTimeout = isLastBatch ? BULK_TIMEOUT * 2 : BULK_TIMEOUT;
      
      for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
        try {
          if (attempt > 1) {
            const retryDelay = RETRY_DELAY_BASE_MS * (attempt - 1);
            if (process.env.NODE_ENV === 'development') {
              console.log(`[Import] Batch ${batchNum} retry ${attempt - 1}/${MAX_RETRIES - 1} after ${retryDelay}ms delay...`);
            }
            await new Promise(resolve => setTimeout(resolve, retryDelay));
          }
          
          response = await api.post('/bulk/contacts', { records: batch }, {
            timeout: batchTimeout,
            signal,
          });
          
          if (process.env.NODE_ENV === 'development') {
            console.log(`[Import] Batch ${batchNum}/${totalBatches} completed successfully:`, {
              total: response.data.total,
              created: response.data.created,
              updated: response.data.updated,
              errors: response.data.errors?.length || 0
            });
          }
          
          break; // Success, exit retry loop
        } catch (error: any) {
          lastError = error;
          if (process.env.NODE_ENV === 'development') {
            console.error(`[Import] Batch ${batchNum}/${totalBatches} attempt ${attempt} failed:`, error.message);
          }
          
          if (signal?.aborted) {
            throw new Error('Import cancelled');
          }
          
          // Don't retry if we've exhausted retries
          if (attempt === MAX_RETRIES) {
            if (process.env.NODE_ENV === 'development') {
              console.error(`[Import] Batch ${batchNum}/${totalBatches} failed after ${MAX_RETRIES} attempts`);
            }
            throw error;
          }
        }
      }
      
      if (!response) {
        throw new Error(`Batch ${batchNum} failed to complete after ${MAX_RETRIES} attempts`);
      }
      
      // Aggregate results with error handling
      try {
        results.total += response.data.total || 0;
        results.created += response.data.created || 0;
        results.updated += response.data.updated || 0;
        results.duplicates += response.data.duplicates || 0;
        
        if (response.data.errors && Array.isArray(response.data.errors)) {
          results.errors.push(...response.data.errors.map((e: any) => ({
            ...e,
            index: (e.index || 0) + i // Adjust index to global position
          })));
        }
      } catch (err: any) {
        if (process.env.NODE_ENV === 'development') {
          console.error(`[Import] Failed to process batch ${batchNum} response:`, err);
        }
        throw new Error(`Failed to process batch ${batchNum} results: ${err.message}`);
      }
      
      completedBatches++;
      const processed = Math.min(i + BATCH_SIZE, records.length);
      if (process.env.NODE_ENV === 'development') {
        console.log(`[Import] Progress: ${processed}/${records.length} records, ${completedBatches}/${totalBatches} batches`);
      }
      onProgress?.(processed, records.length);
      
      // Delay between batches to allow Neon connections to close
      if (i + BATCH_SIZE < records.length) {
        if (process.env.NODE_ENV === 'development') {
          console.log(`[Import] Waiting ${BATCH_DELAY_MS}ms before next batch...`);
        }
        await new Promise(resolve => setTimeout(resolve, BATCH_DELAY_MS));
      }
    }
    
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Import] Import complete: ${results.created + results.updated}/${results.total} successful, ${results.errors.length} errors`);
    }
    
    return {
      ...results,
      completedBatches,
      totalBatches,
      partialSuccess: completedBatches < totalBatches
    };
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
