import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '../test-utils';
import { ContactsTable } from '@/components/data-table/contacts-table';

// Mock push function
const mockPush = vi.fn();

describe('ContactsTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state', () => {
    const { container } = render(<ContactsTable contacts={[]} isLoading={true} />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBe(5);
  });

  it('renders empty state', () => {
    render(<ContactsTable contacts={[]} isLoading={false} />);
    expect(screen.getByText('No contacts found')).toBeDefined();
  });

  it('renders contacts list', () => {
    const mockContacts: any[] = [
      {
        id: '1',
        first_name: 'John',
        last_name: 'Doe',
        full_name: 'John Doe',
        email: 'john@example.com',
        job_title: 'Developer',
        status: 'new',
        created_at: '2023-01-01',
        updated_at: '2023-01-01'
      }
    ];

    render(<ContactsTable contacts={mockContacts} isLoading={false} />);
    expect(screen.getByText('John Doe')).toBeDefined();
    expect(screen.getByText('john@example.com')).toBeDefined();
    expect(screen.getByText('Developer')).toBeDefined();
    // expect(screen.getByText('new')).toBeDefined(); 
  });

  it('navigates on row click', () => {
    const mockContacts: any[] = [
      {
        id: '100',
        full_name: 'Jane Doe',
        created_at: '2023-01-01',
        updated_at: '2023-01-01'
      }
    ];

    render(<ContactsTable contacts={mockContacts} isLoading={false} />);
    fireEvent.click(screen.getByText('Jane Doe'));
    expect(mockPush).toHaveBeenCalledWith('/contacts/100');
  });
});
