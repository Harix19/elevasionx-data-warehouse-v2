'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { tokenStorage } from '@/lib/auth';
import { statsApi } from '@/lib/api';
import { Building2, Users, Upload, ArrowRight, Activity, Database, Globe, Clock } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    if (!tokenStorage.isAuthenticated()) {
      router.replace('/login');
    }
  }, [router]);

  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: statsApi.get,
    refetchInterval: 60000, // Refetch every minute
  });

  const statCards = [
    { 
      label: 'Total Companies', 
      value: isLoading ? '...' : stats?.total_companies.toLocaleString() || '0', 
      icon: Building2,
    },
    { 
      label: 'Total Contacts', 
      value: isLoading ? '...' : stats?.total_contacts.toLocaleString() || '0', 
      icon: Users,
    },
    { 
      label: 'Data Sources', 
      value: isLoading ? '...' : stats?.total_sources.toString() || '0', 
      icon: Globe,
    },
    { 
      label: 'Recent Activity', 
      value: isLoading ? '...' : stats?.recent_activity?.length.toString() || '0', 
      icon: Activity,
    },
  ];

  const quickActions = [
    { 
      title: 'Company Directory', 
      description: 'Manage and enrich your company data.', 
      icon: Building2, 
      href: '/companies',
      color: 'blue'
    },
    { 
      title: 'Contact List', 
      description: 'Unified view of all stakeholders.', 
      icon: Users, 
      href: '/contacts',
      color: 'blue'
    },
    { 
      title: 'Data Import', 
      description: 'Bulk upload CSV or JSON data files.', 
      icon: Upload, 
      href: '/import',
      color: 'blue'
    },
  ];

  const formatTimeAgo = (dateString: string | null) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Overview</h1>
        <p className="text-muted-foreground text-sm">Welcome back. Here's what's happening across your data warehouse.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => (
          <div key={stat.label} className={`surface-card p-6 space-y-4 ${isLoading ? 'animate-pulse' : ''}`}>
            <div className="flex items-center justify-between">
              <div className="p-2 rounded-md bg-zinc-900 border border-border">
                <stat.icon className="w-4 h-4 text-primary" />
              </div>
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{stat.label}</p>
              <h3 className="text-2xl font-bold text-foreground">{stat.value}</h3>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-foreground">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickActions.map((action) => (
            <Link key={action.title} href={action.href} className="group">
              <div className="surface-card p-6 h-full flex flex-col justify-between hover:border-primary/50 transition-all">
                <div className="space-y-4">
                  <div className="w-10 h-10 rounded-lg bg-zinc-900 border border-border flex items-center justify-center group-hover:border-primary/50 transition-colors">
                    <action.icon className="w-5 h-5 text-primary" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="font-semibold text-foreground">{action.title}</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">{action.description}</p>
                  </div>
                </div>
                <div className="mt-6 flex items-center text-xs font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                  Explore <ArrowRight className="ml-1 w-3 h-3" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="surface-card overflow-hidden">
        <div className="p-6 border-b border-border bg-background-alt">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-primary" />
            <h3 className="font-semibold text-sm">Recent Activity</h3>
          </div>
        </div>
        <div className="divide-y divide-border">
          {isLoading ? (
            <div className="p-6 flex items-center justify-center h-48 text-muted-foreground text-sm">
              Loading activity...
            </div>
          ) : stats?.recent_activity && stats.recent_activity.length > 0 ? (
            stats.recent_activity.map((item) => (
              <Link 
                key={`${item.type}-${item.id}`} 
                href={`/${item.type === 'company' ? 'companies' : 'contacts'}/${item.id}`}
                className="flex items-center justify-between p-4 hover:bg-zinc-900/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    item.type === 'company' 
                      ? 'bg-blue-500/10 text-blue-400' 
                      : 'bg-purple-500/10 text-purple-400'
                  }`}>
                    {item.type === 'company' ? (
                      <Building2 className="w-4 h-4" />
                    ) : (
                      <Users className="w-4 h-4" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">{item.name}</p>
                    <p className="text-xs text-muted-foreground capitalize">{item.type} added</p>
                  </div>
                </div>
                <span className="text-xs text-muted-foreground">{formatTimeAgo(item.created_at)}</span>
              </Link>
            ))
          ) : (
            <div className="p-6 flex items-center justify-center h-48 text-muted-foreground text-sm italic">
              No recent activity. Import some data to get started.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
