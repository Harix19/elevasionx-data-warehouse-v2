import Papa from 'papaparse';

export interface CSVPreview {
  headers: string[];
  rows: any[];
}

export interface FieldDefinition {
  key: string;
  label: string;
  required?: boolean;
  aliases?: string[];
}

// Chunk size for async processing to prevent UI blocking
const TRANSFORM_CHUNK_SIZE = 500;

export const COMPANY_FIELDS: FieldDefinition[] = [
  { key: 'name', label: 'Company Name', required: true, aliases: ['company', 'company name', 'name', 'organization'] },
  { key: 'domain', label: 'Domain/Website', aliases: ['website', 'url', 'company domain', 'domain'] },
  { key: 'linkedin_url', label: 'LinkedIn URL', aliases: ['linkedin', 'company linkedin', 'linkedin url'] },
  { key: 'location', label: 'Location', aliases: ['address', 'city', 'state', 'country', 'headquarters'] },
  { key: 'employee_count', label: 'Employee Count', aliases: ['employees', 'size', 'headcount'] },
  { key: 'industry', label: 'Industry', aliases: ['sector', 'vertical', 'category'] },
  { key: 'description', label: 'Description', aliases: ['about', 'summary', 'bio'] },
  { key: 'revenue', label: 'Revenue', aliases: ['annual revenue', 'sales'] },
  { key: 'lead_source', label: 'Lead Source', aliases: ['source'] },
  { key: 'lead_score', label: 'Lead Score', aliases: ['score', 'priority'] },
  { key: 'status', label: 'Status', aliases: ['state', 'stage'] },
  { key: 'custom_tags_a', label: 'Tags A', aliases: ['tags', 'labels'] },
  { key: 'custom_tags_b', label: 'Tags B' },
  { key: 'custom_tags_c', label: 'Tags C' },
];

export const CONTACT_FIELDS: FieldDefinition[] = [
  { key: 'first_name', label: 'First Name', required: true, aliases: ['firstname', 'first', 'given name'] },
  { key: 'last_name', label: 'Last Name', required: true, aliases: ['lastname', 'last', 'surname', 'family name'] },
  { key: 'full_name', label: 'Full Name', aliases: ['name', 'fullname', 'complete name'] },
  { key: 'email', label: 'Email', aliases: ['email address', 'e-mail', 'mail', 'work email'] },
  { key: 'phone', label: 'Phone', aliases: ['phone number', 'telephone', 'mobile', 'cell'] },
  { key: 'job_title', label: 'Job Title', aliases: ['title', 'position', 'role', 'occupation', 'job title'] },
  { key: 'company_domain', label: 'Company Domain', aliases: ['company domain', 'domain', 'website', 'organization_website_url', 'organization website url'] },
  { key: 'working_company_name', label: 'Company Name', aliases: ['company', 'employer', 'organization_name', 'organization name', 'organization'] },
  { key: 'linkedin_url', label: 'LinkedIn URL', aliases: ['linkedin', 'profile', 'social', 'person linkedin', 'linkedin profile', 'person linkedin url', 'linkedin url'] },
  { key: 'company_linkedin_url', label: 'Company LinkedIn URL', aliases: ['company linkedin', 'organization_linkedin_url', 'organization linkedin url'] },
  { key: 'location', label: 'Location', aliases: ['address', 'city', 'country'] },
  { key: 'department', label: 'Department', aliases: ['team', 'division', 'job department'] },
  { key: 'seniority_level', label: 'Seniority', aliases: ['level', 'rank', 'seniority', 'job seniority'] },
  { key: 'industry', label: 'Industry', aliases: ['sector', 'vertical'] },
  { key: 'country', label: 'Country', aliases: ['person country'] },
  { key: 'city', label: 'City', aliases: ['person city'] },
  { key: 'state', label: 'State', aliases: ['person state'] },
  { key: 'lead_source', label: 'Lead Source', aliases: ['source'] },
  { key: 'lead_score', label: 'Lead Score', aliases: ['score'] },
  { key: 'status', label: 'Status', aliases: ['state', 'stage'] },
  { key: 'custom_tags_a', label: 'Tags A', aliases: ['tags', 'labels'] },
  { key: 'custom_tags_b', label: 'Tags B' },
  { key: 'custom_tags_c', label: 'Tags C' },
];

export async function parseCSV(file: File): Promise<CSVPreview> {
  return new Promise((resolve, reject) => {
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      preview: 5,
      complete: (results) => {
        resolve({
          headers: results.meta.fields || [],
          rows: results.data,
        });
      },
      error: (error) => {
        reject(error);
      },
    });
  });
}

export async function parseFullCSV(file: File): Promise<any[]> {
  // Try to use Web Worker for non-blocking parsing
  if (typeof Worker !== 'undefined') {
    try {
      return await parseCSVWithWorker(file);
    } catch (error) {
      console.warn('Web Worker parsing failed, falling back to main thread:', error);
    }
  }
  
  // Fallback to main thread parsing with chunked reading
  return new Promise((resolve, reject) => {
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        resolve(results.data);
      },
      error: (error) => {
        reject(error);
      },
    });
  });
}

/**
 * Parse CSV using a Web Worker to avoid blocking the main thread.
 * This is essential for large files (1000+ rows).
 */
async function parseCSVWithWorker(file: File): Promise<any[]> {
  return new Promise(async (resolve, reject) => {
    try {
      // Read file content first
      const fileContent = await file.text();
      
      // Create an inline worker using a blob
      const workerCode = `
        importScripts('https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.4.1/papaparse.min.js');
        
        self.onmessage = function(event) {
          const { fileContent } = event.data;
          
          try {
            const result = Papa.parse(fileContent, {
              header: true,
              skipEmptyLines: true,
              transformHeader: function(header) { return header.trim(); }
            });
            
            if (result.errors.length > 0) {
              self.postMessage({
                type: 'error',
                error: 'CSV parsing errors: ' + result.errors.map(function(e) { return e.message; }).join(', ')
              });
              return;
            }
            
            self.postMessage({
              type: 'success',
              data: result.data
            });
          } catch (error) {
            self.postMessage({
              type: 'error',
              error: error.message || 'Unknown parsing error'
            });
          }
        };
      `;
      
      const blob = new Blob([workerCode], { type: 'application/javascript' });
      const workerUrl = URL.createObjectURL(blob);
      const worker = new Worker(workerUrl);
      
      worker.onmessage = (event) => {
        URL.revokeObjectURL(workerUrl);
        worker.terminate();
        
        if (event.data.type === 'success') {
          resolve(event.data.data);
        } else {
          reject(new Error(event.data.error));
        }
      };
      
      worker.onerror = (error) => {
        URL.revokeObjectURL(workerUrl);
        worker.terminate();
        reject(error);
      };
      
      // Send file content to worker
      worker.postMessage({ fileContent });
      
    } catch (error) {
      reject(error);
    }
  });
}

export function suggestMappings(headers: string[], fields: FieldDefinition[]): Record<string, string> {
  const mappings: Record<string, string> = {};

  headers.forEach((header) => {
    const lowerHeader = header.toLowerCase().trim();
    
    const matchedField = fields.find((field) => {
      if (field.key === lowerHeader || field.label.toLowerCase() === lowerHeader) return true;
      return field.aliases?.some((alias) => alias.toLowerCase() === lowerHeader);
    });

    if (matchedField) {
      mappings[header] = matchedField.key;
    }
  });

  return mappings;
}

/**
 * Transform data asynchronously with chunked processing to prevent UI blocking.
 * For large datasets, this yields to the main thread every TRANSFORM_CHUNK_SIZE records.
 */
export async function transformData(
  data: any[],
  mappings: Record<string, string>,
  manualTags: { a: string[]; b: string[]; c: string[] },
  importType: 'companies' | 'contacts'
): Promise<any[]> {
  const results: any[] = [];
  
  for (let i = 0; i < data.length; i += TRANSFORM_CHUNK_SIZE) {
    const chunk = data.slice(i, i + TRANSFORM_CHUNK_SIZE);
    
    // Process chunk
    for (const row of chunk) {
      const transformed = transformSingleRecord(row, mappings, manualTags, importType);
      if (transformed) {
        results.push(transformed);
      }
    }
    
    // Yield to main thread to prevent UI blocking
    if (i + TRANSFORM_CHUNK_SIZE < data.length) {
      await new Promise(resolve => setTimeout(resolve, 0));
    }
  }
  
  return results;
}

/**
 * Transform a single record. Returns null if record should be filtered out.
 */
function transformSingleRecord(
  row: any,
  mappings: Record<string, string>,
  manualTags: { a: string[]; b: string[]; c: string[] },
  importType: 'companies' | 'contacts'
): any | null {
  const transformed: any = {};
  
  // Initialize array fields
  transformed.custom_tags_a = [...manualTags.a];
  transformed.custom_tags_b = [...manualTags.b];
  transformed.custom_tags_c = [...manualTags.c];
  
  // Only companies have keywords and technologies
  if (importType === 'companies') {
    transformed.keywords = [];
    transformed.technologies = [];
  }

  Object.entries(mappings).forEach(([csvHeader, targetKey]) => {
    const value = row[csvHeader];
    if (value === undefined || value === null || value === '') return;

    // Only process keywords/technologies for companies
    const isCompanyField = targetKey === 'keywords' || targetKey === 'technologies';
    if (isCompanyField && importType !== 'companies') {
      return; // Skip company-only fields for contacts
    }
    
    if (targetKey.startsWith('custom_tags_') || isCompanyField) {
      const items = value.split(',').map((s: string) => s.trim()).filter(Boolean);
      transformed[targetKey] = [...(transformed[targetKey] || []), ...items];
    } else {
      transformed[targetKey] = value;
    }
  });

  // For contacts: try to derive first_name/last_name from full_name if missing
  if (importType === 'contacts') {
    if (!transformed.first_name || !transformed.last_name) {
      if (transformed.full_name) {
        const nameParts = transformed.full_name.trim().split(/\s+/);
        if (!transformed.first_name && nameParts[0]) {
          transformed.first_name = nameParts[0];
        }
        if (!transformed.last_name && nameParts.length > 1) {
          transformed.last_name = nameParts.slice(1).join(' ');
        }
      }
    }
  }

  // Filter out records missing required fields
  if (importType === 'contacts') {
    // Contacts require: first_name, last_name, AND email (for upsert to work)
    if (!transformed.first_name || !transformed.last_name || !transformed.email) {
      return null;
    }
  } else if (importType === 'companies') {
    if (!transformed.name) {
      return null;
    }
  }

  return transformed;
}
