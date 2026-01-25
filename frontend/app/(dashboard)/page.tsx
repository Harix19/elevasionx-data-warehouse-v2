'use client';

import { Building2, Users, Award, TrendingUp, ArrowUpRight, Sparkles } from 'lucide-react';
import { MetricCard } from '@/components/dashboard/metric-card';
import { QuickActions } from '@/components/dashboard/quick-actions';
import { RecentActivity } from '@/components/dashboard/recent-activity';
import { useDashboardMetrics } from '@/hooks/use-dashboard-metrics';
import Link from 'next/link';

export default function DashboardPage() {
  const { totalCompanies, totalContacts, totalQualified, recentActivity, isLoading, error } =
    useDashboardMetrics();

  if (error) {
    return (
      <div className="space-y-6 animate-fade-in-up">
        <div>
          <h2 className="text-3xl font-bold" style={{ color: 'var(--foreground)' }}>Dashboard</h2>
          <p style={{ color: 'var(--foreground-muted)' }}>Overview of your lead pipeline</p>
        </div>
        <div className="glass rounded-2xl p-6 border border-red-500/20 bg-red-500/5">
          <p className="text-red-400">Failed to load dashboard data. Please try again later.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="animate-fade-in-up">
        <h2 className="text-4xl font-bold mb-2" style={{ color: 'var(--foreground)' }}>
          Welcome back! <Sparkles className="inline w-8 h-8 ml-2" style={{ color: 'var(--accent)' }} />
        </h2>
        <p className="text-lg" style={{ color: 'var(--foreground-muted)' }}>
          Here's what's happening with your sales pipeline today
        </p>
      </div>

      {/* Quick Actions */}
      <div className="animate-fade-in-up" style={{ animationDelay: '100ms' }}>
        <QuickActions />
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link 
          href="/companies" 
          className="glass rounded-2xl p-6 hover-glow group cursor-pointer animate-fade-in-up relative overflow-hidden"
          style={{ animationDelay: '200ms' }}
        >
          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500" 
            style={{ background: 'radial-gradient(circle at top right, rgba(99, 102, 241, 0.1), transparent)' }}
          ></div>
          <div className="relative z-10">
            <div className="flex items-start justify-between mb-4">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center" 
                style={{ background: 'var(--gradient-primary)' }}>
                <Building2 className="w-6 h-6 text-white" />
              </div>
              <ArrowUpRight className="w-5 h-5 opacity-0 group-hover:opacity-100 transition-opacity" 
                style={{ color: 'var(--primary)' }} />
            </div>
            <p className="text-sm mb-2" style={{ color: 'var(--foreground-muted)' }}>Total Companies</p>
            <p className="text-4xl font-bold" style={{ color: 'var(--foreground)' }}>
              {isLoading ? '...' : totalCompanies.toLocaleString()}
            </p>
            <div className="flex items-center gap-2 mt-3">
              <TrendingUp className="w-4 h-4" style={{ color: 'var(--accent-green)' }} />
              <span className="text-sm font-medium" style={{ color: 'var(--accent-green)' }}>+5.2%</span>
              <span className="text-sm" style={{ color: 'var(--foreground-muted)' }}>vs last month</span>
            </div>
          </div>
        </Link>

        <Link 
          href="/contacts" 
          className="glass rounded-2xl p-6 hover-glow group cursor-pointer animate-fade-in-up relative overflow-hidden"
          style={{ animationDelay: '300ms' }}
        >
          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500" 
            style={{ background: 'radial-gradient(circle at top right, rgba(139, 92, 246, 0.1), transparent)' }}
          ></div>
          <div className="relative z-10">
            <div className="flex items-start justify-between mb-4">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center" 
                style={{ background: 'var(--gradient-success)' }}>
                <Users className="w-6 h-6 text-white" />
              </div>
              <ArrowUpRight className="w-5 h-5 opacity-0 group-hover:opacity-100 transition-opacity" 
                style={{ color: 'var(--accent-green)' }} />
            </div>
            <p className="text-sm mb-2" style={{ color: 'var(--foreground-muted)' }}>Total Contacts</p>
            <p className="text-4xl font-bold" style={{ color: 'var(--foreground)' }}>
              {isLoading ? '...' : totalContacts.toLocaleString()}
            </p>
            <div className="flex items-center gap-2 mt-3">
              <TrendingUp className="w-4 h-4" style={{ color: 'var(--accent-green)' }} />
              <span className="text-sm font-medium" style={{ color: 'var(--accent-green)' }}>+8.1%</span>
              <span className="text-sm" style={{ color: 'var(--foreground-muted)' }}>vs last month</span>
            </div>
          </div>
        </Link>

        <Link 
          href="/companies?status=qualified" 
          className="glass rounded-2xl p-6 hover-glow group cursor-pointer animate-fade-in-up relative overflow-hidden"
          style={{ animationDelay: '400ms' }}
        >
          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500" 
            style={{ background: 'radial-gradient(circle at top right, rgba(245, 158, 11, 0.1), transparent)' }}
          ></div>
          <div className="relative z-10">
            <div className="flex items-start justify-between mb-4">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center" 
                style={{ background: 'var(--gradient-accent)' }}>
                <Award className="w-6 h-6 text-white" />
              </div>
              <ArrowUpRight className="w-5 h-5 opacity-0 group-hover:opacity-100 transition-opacity" 
                style={{ color: 'var(--accent)' }} />
            </div>
            <p className="text-sm mb-2" style={{ color: 'var(--foreground-muted)' }}>Qualified Leads</p>
            <p className="text-4xl font-bold" style={{ color: 'var(--foreground)' }}>
              {isLoading ? '...' : totalQualified.toLocaleString()}
            </p>
            <div className="flex items-center gap-2 mt-3">
              <TrendingUp className="w-4 h-4" style={{ color: 'var(--accent-green)' }} />
              <span className="text-sm font-medium" style={{ color: 'var(--accent-green)' }}>+12.4%</span>
              <span className="text-sm" style={{ color: 'var(--foreground-muted)' }}>vs last month</span>
            </div>
          </div>
        </Link>
      </div>

      {/* Recent Activity */}
      <div className="animate-fade-in-up" style={{ animationDelay: '500ms' }}>
        <RecentActivity activities={recentActivity} isLoading={isLoading} />
      </div>
    </div>
  );
}
