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
  { key: 'email', label: 'Email', aliases: ['email address', 'e-mail', 'mail'] },
  { key: 'phone', label: 'Phone', aliases: ['phone number', 'telephone', 'mobile', 'cell'] },
  { key: 'job_title', label: 'Job Title', aliases: ['title', 'position', 'role', 'occupation'] },
  { key: 'company_domain', label: 'Company Domain', aliases: ['company domain', 'domain', 'website'] },
  { key: 'working_company_name', label: 'Company Name', aliases: ['company', 'employer'] },
  { key: 'linkedin_url', label: 'LinkedIn URL', aliases: ['linkedin', 'profile', 'social'] },
  { key: 'location', label: 'Location', aliases: ['address', 'city', 'country'] },
  { key: 'department', label: 'Department', aliases: ['team', 'division'] },
  { key: 'seniority_level', label: 'Seniority', aliases: ['level', 'rank'] },
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

export function transformData(
  data: any[],
  mappings: Record<string, string>,
  manualTags: { a: string[]; b: string[]; c: string[] }
): any[] {
  return data.map((row) => {
    const transformed: any = {};
    
    // Initialize array fields
    transformed.custom_tags_a = [...manualTags.a];
    transformed.custom_tags_b = [...manualTags.b];
    transformed.custom_tags_c = [...manualTags.c];
    transformed.keywords = [];
    transformed.technologies = [];

    Object.entries(mappings).forEach(([csvHeader, targetKey]) => {
      const value = row[csvHeader];
      if (value === undefined || value === null || value === '') return;

      if (targetKey.startsWith('custom_tags_') || targetKey === 'keywords' || targetKey === 'technologies') {
        const items = value.split(',').map((s: string) => s.trim()).filter(Boolean);
        transformed[targetKey] = [...(transformed[targetKey] || []), ...items];
      } else {
        transformed[targetKey] = value;
      }
    });

    return transformed;
  });
}
