import { useCompanies } from './use-companies';
import { useContacts } from './use-contacts';
import type { Company } from '@/types/company';
import type { Contact } from '@/types/contact';

export interface DashboardMetrics {
  totalCompanies: number;
  totalContacts: number;
  totalQualified: number;
  recentActivity: RecentActivityItem[];
  isLoading: boolean;
  error: any;
}

export interface RecentActivityItem {
  type: 'company' | 'contact';
  id: string;
  name: string;
  action: 'created' | 'updated' | 'added';
  timestamp: string;
}

export function useDashboardMetrics(): DashboardMetrics {
  const companies = useCompanies({ limit: 1 });
  const contacts = useContacts({ limit: 1 });
  const qualifiedCompanies = useCompanies({ limit: 1, lead_status: 'qualified' });
  const qualifiedContacts = useContacts({ limit: 1, lead_status: 'qualified' });
  const recentCompanies = useCompanies({ limit: 5 });
  const recentContacts = useContacts({ limit: 5 });

  const totalCompanies = companies.data?.total_count ?? 0;
  const totalContacts = contacts.data?.total_count ?? 0;
  const totalQualified =
    (qualifiedCompanies.data?.total_count ?? 0) +
    (qualifiedContacts.data?.total_count ?? 0);

  const recentActivity = mergeRecentActivity(
    recentCompanies.data?.items ?? [],
    recentContacts.data?.items ?? []
  );

  const isLoading =
    companies.isLoading ||
    contacts.isLoading ||
    qualifiedCompanies.isLoading ||
    qualifiedContacts.isLoading ||
    recentCompanies.isLoading ||
    recentContacts.isLoading;

  const error =
    companies.error ||
    contacts.error ||
    qualifiedCompanies.error ||
    qualifiedContacts.error ||
    recentCompanies.error ||
    recentContacts.error;

  return {
    totalCompanies,
    totalContacts,
    totalQualified,
    recentActivity,
    isLoading,
    error,
  };
}

function mergeRecentActivity(
  companies: Company[],
  contacts: Contact[]
): RecentActivityItem[] {
  const activities: RecentActivityItem[] = [
    ...companies.map((c) => ({
      type: 'company' as const,
      id: c.id,
      name: c.name,
      action: 'created' as const,
      timestamp: c.created_at,
    })),
    ...contacts.map((c) => ({
      type: 'contact' as const,
      id: c.id,
      name: `${c.first_name} ${c.last_name}`,
      action: 'added' as const,
      timestamp: c.created_at,
    })),
  ];

  return activities
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 5);
}
