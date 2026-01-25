import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '../test-utils';
import { CompaniesTable } from '@/components/data-table/companies-table';

// Mock push function
const mockPush = vi.fn();

describe('CompaniesTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state', () => {
    const { container } = render(<CompaniesTable companies={[]} isLoading={true} />);
    // The component renders 5 divs with animate-pulse class
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBe(5);
  });

  it('renders empty state', () => {
    render(<CompaniesTable companies={[]} isLoading={false} />);
    expect(screen.getByText('No companies found')).toBeDefined();
  });

  it('renders companies list', () => {
    const mockCompanies: any[] = [
      {
        id: '1',
        name: 'Test Company',
        domain: 'test.com',
        industry: 'Tech',
        country: 'US',
        status: 'new',
        lead_score: 85,
        created_at: '2023-01-01',
        updated_at: '2023-01-01'
      }
    ];

    render(<CompaniesTable companies={mockCompanies} isLoading={false} />);
    expect(screen.getByText('Test Company')).toBeDefined();
    expect(screen.getByText('test.com')).toBeDefined();
    expect(screen.getByText('Tech')).toBeDefined();
    expect(screen.getByText('US')).toBeDefined();
    // expect(screen.getByText('new')).toBeDefined(); // Badge
    expect(screen.getByText('85')).toBeDefined();
  });

  it('navigates on row click', () => {
    const mockCompanies: any[] = [
      {
        id: '123',
        name: 'Clickable Company',
        status: 'new',
        created_at: '2023-01-01',
        updated_at: '2023-01-01'
      }
    ];

    render(<CompaniesTable companies={mockCompanies} isLoading={false} />);
    fireEvent.click(screen.getByText('Clickable Company'));
    expect(mockPush).toHaveBeenCalledWith('/companies/123');
  });
});
