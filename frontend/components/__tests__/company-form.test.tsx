import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { CompanyForm } from '../forms/company-form';
import { useRouter } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import { useCreateCompany } from '@/hooks/use-companies';

// Mock dependencies
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({
    replace: vi.fn(),
  })),
}));

vi.mock('@tanstack/react-query', () => ({
  useQueryClient: vi.fn(() => ({
    invalidateQueries: vi.fn(),
  })),
}));

vi.mock('@/hooks/use-companies', () => ({
  useCreateCompany: vi.fn(() => ({
    mutateAsync: vi.fn(),
  })),
}));

// Mock TagInput as it might be complex
vi.mock('../forms/tag-input', () => ({
  TagInput: ({ value, onChange, placeholder }: any) => (
    <input
      data-testid="tag-input"
      placeholder={placeholder}
      value={value.join(', ')}
      onChange={(e) => onChange(e.target.value.split(',').map((s: string) => s.trim()))}
    />
  ),
}));

describe('CompanyForm', () => {
  const onOpenChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly when open', () => {
    render(<CompanyForm open={true} onOpenChange={onOpenChange} />);
    
    expect(screen.getByText('Add Company')).toBeDefined();
    expect(screen.getByLabelText(/Name/)).toBeDefined();
    expect(screen.getByLabelText(/Domain/)).toBeDefined();
  });

  it('shows error message when name is missing', async () => {
    render(<CompanyForm open={true} onOpenChange={onOpenChange} />);
    
    const submitButton = screen.getByText('Create');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Name is required')).toBeDefined();
    });
  });

  it('calls mutateAsync and onOpenChange on successful submission', async () => {
    const mutateAsync = vi.fn().mockResolvedValue({});
    (useCreateCompany as any).mockReturnValue({ mutateAsync });
    const invalidateQueries = vi.fn();
    (useQueryClient as any).mockReturnValue({ invalidateQueries });

    render(<CompanyForm open={true} onOpenChange={onOpenChange} />);
    
    fireEvent.change(screen.getByLabelText(/Name/), { target: { value: 'Test Company' } });
    fireEvent.change(screen.getByLabelText(/Domain/), { target: { value: 'test.com' } });
    
    const submitButton = screen.getByText('Create');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith(expect.objectContaining({
        name: 'Test Company',
        domain: 'test.com',
      }));
      expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ['companies'] });
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });
});
