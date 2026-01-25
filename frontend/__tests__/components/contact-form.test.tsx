import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../test-utils';
import { ContactForm } from '@/components/forms/contact-form';

describe('ContactForm', () => {
  const defaultProps = {
    open: true,
    onOpenChange: vi.fn(),
  };

  it('renders form fields', () => {
    render(<ContactForm {...defaultProps} />);
    expect(screen.getByText('Add Contact')).toBeDefined();
    // First Name and Last Name inputs
    const inputs = document.querySelectorAll('input[type="text"]');
    expect(inputs.length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText('Acme Corp')).toBeDefined(); // Dropdown option
  });

  it('validates required fields', async () => {
    render(<ContactForm {...defaultProps} />);
    fireEvent.click(screen.getByText('Create'));
    expect(await screen.findByText('First name is required')).toBeDefined();
  });

  it('submits form with valid data', async () => {
    render(<ContactForm {...defaultProps} />);
    
    // First Name is 1st input, Last Name is 2nd (both type="text")
    const textInputs = document.querySelectorAll('input[type="text"]');
    fireEvent.change(textInputs[0], { target: { value: 'Alice' } });
    fireEvent.change(textInputs[1], { target: { value: 'Smith' } });
    
    // Email input
    fireEvent.change(screen.getByPlaceholderText('john@example.com'), { target: { value: 'alice@example.com' } });
    
    fireEvent.click(screen.getByText('Create'));
    
    await waitFor(() => {
      expect(defaultProps.onOpenChange).toHaveBeenCalledWith(false);
    });
  });
});
