import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../test-utils';
import { CompanyForm } from '@/components/forms/company-form';

describe('CompanyForm', () => {
  const defaultProps = {
    open: true,
    onOpenChange: vi.fn(),
  };

  it('renders form fields', () => {
    render(<CompanyForm {...defaultProps} />);
    expect(screen.getByText('Add Company')).toBeDefined();
    // Verify inputs exist in document (Dialog uses Portal)
    const inputs = document.querySelectorAll('input');
    expect(inputs.length).toBeGreaterThan(0);
    expect(screen.getByPlaceholderText('example.com')).toBeDefined();
  });

  it('validates required fields', async () => {
    render(<CompanyForm {...defaultProps} />);
    
    // Submit without filling name
    fireEvent.click(screen.getByText('Create'));
    
    expect(await screen.findByText('Name is required')).toBeDefined();
  });

  it('submits form with valid data', async () => {
    render(<CompanyForm {...defaultProps} />);
    
    // Name is first text input in form
    const inputs = document.querySelectorAll('input[type="text"]');
    fireEvent.change(inputs[0], { target: { value: 'New Corp' } });
    
    // Domain
    fireEvent.change(screen.getByPlaceholderText('example.com'), { target: { value: 'newcorp.com' } });
    
    fireEvent.click(screen.getByText('Create'));
    
    await waitFor(() => {
      expect(defaultProps.onOpenChange).toHaveBeenCalledWith(false);
    });
  });
});
