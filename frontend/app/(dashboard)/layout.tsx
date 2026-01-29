'use client';

import { useRouter, usePathname } from 'next/navigation';
import { useEffect } from 'react';
import { tokenStorage } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { Home, Building2, Users, Upload, LogOut, Zap } from 'lucide-react';
import ErrorBoundary from '@/components/error-boundary';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!tokenStorage.isAuthenticated()) {
      router.replace('/login');
    }
  }, [router]);

  const handleLogout = () => {
    tokenStorage.removeToken();
    router.replace('/login');
  };

  const navItems = [
    { href: '/', label: 'Overview', icon: Home },
    { href: '/companies', label: 'Companies', icon: Building2 },
    { href: '/contacts', label: 'Contacts', icon: Users },
    { href: '/import', label: 'Ingestion', icon: Upload },
  ];

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname?.startsWith(href);
  };

  const currentLabel = navItems.find(item => isActive(item.href))?.label || 'Dashboard';

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-background-alt flex flex-col flex-shrink-0">
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Zap className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-bold tracking-tight text-foreground">ElevationX</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-item ${active ? 'nav-item-active' : ''}`}
              >
                <Icon className="w-4 h-4" />
                <span className="text-sm font-medium">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Bottom Actions */}
        <div className="p-4 border-t border-border">
          <Button 
            onClick={handleLogout} 
            className="w-full justify-start gap-3 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
            variant="ghost"
          >
            <LogOut className="w-4 h-4" />
            <span className="text-sm font-medium">Logout</span>
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 bg-background">
        {/* Top Bar */}
        <header className="h-16 border-b border-border px-8 flex items-center justify-between bg-background sticky top-0 z-20">
          <div className="flex items-center gap-4">
            <h2 className="text-sm font-semibold text-foreground">{currentLabel}</h2>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 pr-4 border-r border-border">
              <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">System Status</span>
              <div className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></div>
            </div>
            <div className="w-8 h-8 rounded-full bg-zinc-900 border border-border flex items-center justify-center text-[10px] font-bold text-zinc-400">
              HK
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-6xl mx-auto p-8 md:p-12">
            <ErrorBoundary>
              {children}
            </ErrorBoundary>
          </div>
        </main>
      </div>
    </div>
  );
}
