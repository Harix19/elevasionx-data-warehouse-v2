'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { tokenStorage } from '@/lib/auth';
import { Building2, Users, Upload, ArrowRight, Activity, Database, Globe } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    if (!tokenStorage.isAuthenticated()) {
      router.replace('/login');
    }
  }, [router]);

  const stats = [
    { label: 'Total Companies', value: '1,284', icon: Building2, change: '+12%', trend: 'up' },
    { label: 'Active Contacts', value: '4,592', icon: Users, change: '+8%', trend: 'up' },
    { label: 'Data Sources', value: '12', icon: Globe, change: '0%', trend: 'neutral' },
    { label: 'API Requests', value: '85k', icon: Activity, change: '+24%', trend: 'up' },
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

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Overview</h1>
        <p className="text-muted-foreground text-sm">Welcome back. Here's what's happening across your data warehouse.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="surface-card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="p-2 rounded-md bg-zinc-900 border border-border">
                <stat.icon className="w-4 h-4 text-primary" />
              </div>
              <span className={`text-xs font-medium ${stat.trend === 'up' ? 'text-green-500' : 'text-muted-foreground'}`}>
                {stat.change}
              </span>
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

      {/* Recent Activity Placeholder */}
      <div className="surface-card overflow-hidden">
        <div className="p-6 border-b border-border bg-background-alt">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-primary" />
            <h3 className="font-semibold text-sm">System Performance</h3>
          </div>
        </div>
        <div className="p-6 flex items-center justify-center h-48 text-muted-foreground text-sm italic">
          Ingestion pipelines active. All systems operational.
        </div>
      </div>
    </div>
  );
}
