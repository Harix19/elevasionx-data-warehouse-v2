'use client';

import { useRouter } from 'next/navigation';
import { Plus, Upload, Building2, UserPlus, FileSpreadsheet } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export function QuickActions() {
  const router = useRouter();

  const actions = [
    {
      label: 'Add Company',
      icon: Building2,
      onClick: () => router.push('/companies'),
      color: 'var(--primary)',
      bg: 'var(--primary-dark)',
    },
    {
      label: 'Add Contact',
      icon: UserPlus,
      onClick: () => router.push('/contacts'),
      color: 'var(--accent-green)',
      bg: 'rgba(16, 185, 129, 0.2)',
    },
    {
      label: 'Import CSV',
      icon: FileSpreadsheet,
      onClick: () => router.push('/import'),
      color: 'var(--accent)',
      bg: 'rgba(245, 158, 11, 0.2)',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {actions.map((action, index) => {
        const Icon = action.icon;
        return (
          <button
            key={action.label}
            onClick={action.onClick}
            className="glass group relative overflow-hidden p-4 rounded-2xl flex items-center gap-4 transition-all hover:translate-y-[-2px] hover:shadow-lg active:translate-y-0"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <div 
              className="w-12 h-12 rounded-xl flex items-center justify-center transition-transform group-hover:scale-110"
              style={{ background: action.bg }}
            >
              <Icon className="w-6 h-6" style={{ color: action.color }} />
            </div>
            <div className="text-left">
              <p className="font-bold text-base" style={{ color: 'var(--foreground)' }}>{action.label}</p>
              <p className="text-xs" style={{ color: 'var(--foreground-muted)' }}>Quick data entry</p>
            </div>
            <div className="absolute top-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <Plus className="w-4 h-4" style={{ color: action.color }} />
            </div>
          </button>
        );
      })}
    </div>
  );
}
