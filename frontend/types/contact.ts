export interface Contact {
  id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  email?: string;
  phone?: string;
  location?: string;
  linkedin_url?: string;
  working_company_name?: string;
  job_title?: string;
  seniority_level?: 'c_level' | 'director' | 'manager' | 'individual_contributor' | 'other' | null;
  department?: string;
  company_id?: string;
  company_domain?: string;
  company_linkedin_url?: string;
  custom_tags_a?: string[];
  custom_tags_b?: string[];
  custom_tags_c?: string[];
  lead_source?: string;
  lead_score?: number;
  status?: 'new' | 'contacted' | 'qualified' | 'customer' | 'churned';
  created_at: string;
  updated_at: string;
}

export type SeniorityLevel = 'c_level' | 'director' | 'manager' | 'individual_contributor' | 'other' | null;

export interface ContactsListParams {
  limit?: number;
  cursor?: string;
  tags_a?: string[];
  tags_b?: string[];
  tags_c?: string[];
  seniority_level?: SeniorityLevel;
  department?: string;
  lead_status?: Contact['status'];
  lead_score_min?: number;
  lead_score_max?: number;
}

export interface ContactsListResponse {
  items: Contact[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}
