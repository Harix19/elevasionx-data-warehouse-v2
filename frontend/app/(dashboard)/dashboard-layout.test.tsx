import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import DashboardLayout from '../layout';
import { useRouter, usePathname } from 'next/navigation';
import { tokenStorage } from '@/lib/auth';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({
    replace: vi.fn(),
  })),
  usePathname: vi.fn(() => '/'),
}));

// Mock token storage
vi.mock('@/lib/auth', () => ({
  tokenStorage: {
    isAuthenticated: vi.fn(() => true),
    removeToken: vi.fn(),
  },
}));

// Mock Lucide icons to avoid issues with rendering
vi.mock('lucide-react', () => ({
  Home: () => <div data-testid="icon-home" />,
  Building2: () => <div data-testid="icon-building" />,
  Users: () => <div data-testid="icon-users" />,
  Upload: () => <div data-testid="icon-upload" />,
  LogOut: () => <div data-testid="icon-logout" />,
  Zap: () => <div data-testid="icon-zap" />,
  AlertCircle: () => <div data-testid="icon-alert" />,
  RefreshCcw: () => <div data-testid="icon-refresh" />,
}));

describe('DashboardLayout', () => {
  it('renders the sidebar with navigation items', () => {
    render(
      <DashboardLayout>
        <div data-testid="child-content">Child Content</div>
      </DashboardLayout>
    );

    expect(screen.getByText('ElevationX')).toBeDefined();
    expect(screen.getByText('Overview')).toBeDefined();
    expect(screen.getByText('Companies')).toBeDefined();
    expect(screen.getByText('Contacts')).toBeDefined();
    expect(screen.getByText('Ingestion')).toBeDefined();
    expect(screen.getByTestId('child-content')).toBeDefined();
  });

  it('redirects to login if not authenticated', () => {
    const replaceMock = vi.fn();
    (useRouter as any).mockReturnValue({ replace: replaceMock });
    (tokenStorage.isAuthenticated as any).mockReturnValue(false);

    render(
      <DashboardLayout>
        <div>Content</div>
      </DashboardLayout>
    );

    expect(replaceMock).toHaveBeenCalledWith('/login');
  });
});
