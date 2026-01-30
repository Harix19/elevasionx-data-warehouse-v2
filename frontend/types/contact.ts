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

// Range filter value type
export interface RangeValue {
  min?: number;
  max?: number;
}

// Tags filter value type
export interface TagsValue {
  tags: string[];
  logic?: 'or' | 'and';
}

// Frontend filter state (includes nested structures for UI)
export interface ContactFilterState {
  limit?: number;
  cursor?: string;
  q?: string;
  seniority_level?: SeniorityLevel;
  department?: string;
  lead_status?: Contact['status'];
  lead_score?: RangeValue;
  tags_a?: TagsValue;
  tags_b?: TagsValue;
  tags_c?: TagsValue;
}

// API filter params (flattened for backend)
export interface ContactsListParams {
  limit?: number;
  cursor?: string;
  q?: string;
  tags_a?: string[];
  tags_b?: string[];
  tags_c?: string[];
  tags_a_all?: string[];
  tags_b_all?: string[];
  tags_c_all?: string[];
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

// Apollo-style filter options
export interface RangeConfig {
  min: number;
  max: number;
}

export interface ContactFilterOptions {
  seniority_levels?: string[];
  departments?: string[];
  lead_score_range?: RangeConfig;
  tags_a?: string[];
  tags_b?: string[];
  tags_c?: string[];
}
