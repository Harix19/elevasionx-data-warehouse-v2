'use client';

import Link from 'next/link';
import { Building2, User, Clock, History } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export interface RecentActivityItem {
  type: 'company' | 'contact';
  id: string;
  name: string;
  action: 'created' | 'updated' | 'added';
  timestamp: string;
}

interface RecentActivityProps {
  activities: RecentActivityItem[];
  isLoading?: boolean;
}

export function RecentActivity({ activities, isLoading = false }: RecentActivityProps) {
  const timeAgo = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  if (isLoading) {
    return (
      <Card className="glass rounded-2xl border-glass-border overflow-hidden">
        <CardHeader className="border-b border-glass-border pb-4">
          <CardTitle className="text-xl font-bold flex items-center gap-2" style={{ color: 'var(--foreground)' }}>
            <History className="w-5 h-5 text-primary" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-glass-border">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex items-center gap-4 p-5 animate-pulse">
                <div className="h-10 w-10 bg-white/5 rounded-xl"></div>
                <div className="flex-1">
                  <div className="h-4 bg-white/5 rounded w-1/3 mb-2"></div>
                  <div className="h-3 bg-white/5 rounded w-1/4"></div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass rounded-2xl border-glass-border overflow-hidden shadow-xl">
      <CardHeader className="border-b border-glass-border pb-4 bg-white/5">
        <CardTitle className="text-xl font-bold flex items-center gap-2" style={{ color: 'var(--foreground)' }}>
          <History className="w-5 h-5 text-primary" />
          Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {activities.length === 0 ? (
          <div className="py-12 text-center">
            <Clock className="w-10 h-10 mx-auto mb-3 opacity-20" style={{ color: 'var(--foreground-muted)' }} />
            <p style={{ color: 'var(--foreground-muted)' }}>No recent activity to report</p>
          </div>
        ) : (
          <div className="divide-y divide-glass-border">
            {activities.map((activity, index) => (
              <div 
                key={`${activity.type}-${activity.id}`} 
                className="flex items-center gap-4 p-5 hover:bg-white/5 transition-all group cursor-pointer"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-transform group-hover:scale-110 ${
                  activity.type === 'company' ? 'bg-blue-500/10 text-blue-400' : 'bg-green-500/10 text-green-400'
                }`}>
                  {activity.type === 'company' ? (
                    <Building2 className="w-5 h-5" />
                  ) : (
                    <User className="w-5 h-5" />
                  )}
                </div>
                <div className="flex-1">
                  <Link
                    href={`/${activity.type}s/${activity.id}`}
                    className="font-bold text-base hover:text-primary transition-colors block"
                    style={{ color: 'var(--foreground)' }}
                  >
                    {activity.name}
                  </Link>
                  <p className="text-xs uppercase tracking-widest font-black opacity-40 mt-0.5">
                    {activity.action === 'created' ? 'NEW RECORD' : activity.action}
                  </p>
                </div>
                <Badge variant="outline" className="glass border-glass-border text-[10px] font-bold px-2 py-0.5 rounded-lg opacity-60">
                  <Clock className="w-3 h-3 mr-1" />
                  {timeAgo(activity.timestamp)}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
