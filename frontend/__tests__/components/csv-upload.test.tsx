import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '../test-utils';
import { CsvUpload } from '@/components/import/csv-upload';

describe('CsvUpload', () => {
  it('renders upload area', () => {
    render(<CsvUpload onFileSelect={vi.fn()} />);
    expect(screen.getByText('Drop CSV file here')).toBeDefined();
    expect(screen.getByText('Select File')).toBeDefined();
  });

  it('handles file selection via input', () => {
    const onFileSelect = vi.fn();
    render(<CsvUpload onFileSelect={onFileSelect} />);
    
    const file = new File(['dummy content'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByLabelText('', { selector: 'input[type="file"]' });
    
    fireEvent.change(input, { target: { files: [file] } });
    
    expect(onFileSelect).toHaveBeenCalledWith(file);
  });

  it('ignores non-csv files via input', () => {
    const onFileSelect = vi.fn();
    render(<CsvUpload onFileSelect={onFileSelect} />);
    
    const file = new File(['dummy content'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByLabelText('', { selector: 'input[type="file"]' });
    
    fireEvent.change(input, { target: { files: [file] } });
    
    expect(onFileSelect).not.toHaveBeenCalled();
  });

  it('is disabled when prop is passed', () => {
    render(<CsvUpload onFileSelect={vi.fn()} disabled={true} />);
    const button = screen.getByText('Select File').closest('button');
    expect(button).toBeDisabled();
    
    const input = screen.getByLabelText('', { selector: 'input[type="file"]' });
    expect(input).toBeDisabled();
  });
});
