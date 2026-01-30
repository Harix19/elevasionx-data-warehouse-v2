export interface Company {
  id: string;
  name: string;
  domain?: string;
  linkedin_url?: string;
  location?: string;
  employee_count?: number;
  industry?: string;
  keywords?: string[];
  technologies?: string[];
  description?: string;
  country?: string;
  twitter_url?: string;
  facebook_url?: string;
  revenue?: number;
  funding_date?: string;
  custom_tags_a?: string[];
  custom_tags_b?: string[];
  custom_tags_c?: string[];
  lead_source?: string;
  lead_score?: number;
  status?: LeadStatus;
  created_at: string;
  updated_at: string;
}

export type LeadStatus = 'new' | 'contacted' | 'qualified' | 'customer' | 'churned';

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
export interface CompanyFilterState {
  limit?: number;
  cursor?: string;
  q?: string;
  industry?: string;
  country?: string;
  lead_status?: LeadStatus;
  revenue?: RangeValue;
  lead_score?: RangeValue;
  employee_count?: RangeValue;
  tags_a?: TagsValue;
  tags_b?: TagsValue;
  tags_c?: TagsValue;
}

// API filter params (flattened for backend)
export interface CompaniesListParams {
  limit?: number;
  cursor?: string;
  q?: string;
  tags_a?: string[];
  tags_b?: string[];
  tags_c?: string[];
  tags_a_all?: string[];
  tags_b_all?: string[];
  tags_c_all?: string[];
  industry?: string;
  country?: string;
  lead_status?: LeadStatus;
  revenue_min?: number;
  revenue_max?: number;
  lead_score_min?: number;
  lead_score_max?: number;
  employee_count_min?: number;
  employee_count_max?: number;
}

export interface CompaniesListResponse {
  items: Company[];
  next_cursor: string | null;
  has_more: boolean;
  total_count: number | null;
}

// Apollo-style filter options
export interface RangeConfig {
  min: number;
  max: number;
}

export interface CompanyFilterOptions {
  industries?: string[];
  countries?: string[];
  revenue_range?: RangeConfig;
  lead_score_range?: RangeConfig;
  employee_count_range?: RangeConfig;
  tags_a?: string[];
  tags_b?: string[];
  tags_c?: string[];
}
