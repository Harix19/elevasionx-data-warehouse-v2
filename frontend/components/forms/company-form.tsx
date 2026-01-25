'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import { useCreateCompany } from '@/hooks/use-companies';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TagInput } from './tag-input';
import type { Company } from '@/types/company';

interface CompanyFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  existingCompany?: Company;
}

const STATUS_OPTIONS = [
  { value: 'new', label: 'New' },
  { value: 'contacted', label: 'Contacted' },
  { value: 'qualified', label: 'Qualified' },
  { value: 'customer', label: 'Customer' },
  { value: 'churned', label: 'Churned' },
];

export function CompanyForm({ open, onOpenChange, existingCompany }: CompanyFormProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const createCompany = useCreateCompany();

  const [formData, setFormData] = useState({
    name: existingCompany?.name || '',
    domain: existingCompany?.domain || '',
    linkedin_url: existingCompany?.linkedin_url || '',
    location: existingCompany?.location || '',
    employee_count: existingCompany?.employee_count || '',
    industry: existingCompany?.industry || '',
    description: existingCompany?.description || '',
    country: existingCompany?.country || '',
    twitter_url: existingCompany?.twitter_url || '',
    facebook_url: existingCompany?.facebook_url || '',
    revenue: existingCompany?.revenue || '',
    funding_date: existingCompany?.funding_date || '',
    lead_source: existingCompany?.lead_source || '',
    lead_score: existingCompany?.lead_score || '',
    status: existingCompany?.status || 'new',
    keywords: existingCompany?.keywords || [],
    technologies: existingCompany?.technologies || [],
    custom_tags_a: existingCompany?.custom_tags_a || [],
    custom_tags_b: existingCompany?.custom_tags_b || [],
    custom_tags_c: existingCompany?.custom_tags_c || [],
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    setIsSubmitting(true);

    try {
      const submitData = {
        ...formData,
        employee_count: formData.employee_count ? Number(formData.employee_count) : undefined,
        revenue: formData.revenue ? Number(formData.revenue) : undefined,
        lead_score: formData.lead_score ? Number(formData.lead_score) : undefined,
      };

      await createCompany.mutateAsync(submitData as any);

      // Invalidate and refresh
      queryClient.invalidateQueries({ queryKey: ['companies'] });

      // Close and reset
      onOpenChange(false);
      setFormData({
        name: '',
        domain: '',
        linkedin_url: '',
        location: '',
        employee_count: '',
        industry: '',
        description: '',
        country: '',
        twitter_url: '',
        facebook_url: '',
        revenue: '',
        funding_date: '',
        lead_source: '',
        lead_score: '',
        status: 'new',
        keywords: [],
        technologies: [],
        custom_tags_a: [],
        custom_tags_b: [],
        custom_tags_c: [],
      });
      setErrors({});
    } catch (error: any) {
      if (error?.response?.status === 409) {
        setErrors({ domain: 'Company with this domain already exists' });
      } else {
        setErrors({ form: error?.response?.data?.detail || 'Failed to create company' });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: string, value: any) => {
    setFormData({ ...formData, [field]: value });
    // Clear error for this field when user changes it
    if (errors[field]) {
      setErrors({ ...errors, [field]: '' });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{existingCompany ? 'Edit Company' : 'Add Company'}</DialogTitle>
          <DialogDescription>
            {existingCompany ? 'Update company information below.' : 'Fill in the details to add a new company.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-6 py-4">
            {errors.form && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {errors.form}
              </div>
            )}

            {/* Basic Information */}
            <Card>
              <CardHeader>
                <CardTitle>Basic Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <FormField
                  label="Name *"
                  required
                  error={errors.name}
                  value={formData.name}
                  onChange={(v) => handleChange('name', v)}
                />
                <FormField
                  label="Domain"
                  error={errors.domain}
                  value={formData.domain}
                  onChange={(v) => handleChange('domain', v)}
                  placeholder="example.com"
                />
                <FormField
                  label="Industry"
                  value={formData.industry}
                  onChange={(v) => handleChange('industry', v)}
                  placeholder="SaaS, E-commerce, etc."
                />
                <FormField
                  label="Location"
                  value={formData.location}
                  onChange={(v) => handleChange('location', v)}
                  placeholder="San Francisco, CA"
                />
                <div>
                  <label className="text-sm font-medium mb-1 block">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => handleChange('description', e.target.value)}
                    placeholder="Company description..."
                    className="flex w-full px-3 py-2 border rounded-md min-h-[80px]"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Metrics */}
            <Card>
              <CardHeader>
                <CardTitle>Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <FormField
                  label="Employee Count"
                  type="number"
                  value={formData.employee_count}
                  onChange={(v) => handleChange('employee_count', v)}
                />
                <FormField
                  label="Revenue"
                  type="number"
                  value={formData.revenue}
                  onChange={(v) => handleChange('revenue', v)}
                />
                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    label="Lead Score"
                    type="number"
                    min={0}
                    max={100}
                    value={formData.lead_score}
                    onChange={(v) => handleChange('lead_score', v)}
                  />
                  <div>
                    <label className="text-sm font-medium mb-1 block">Status</label>
                    <select
                      value={formData.status}
                      onChange={(e) => handleChange('status', e.target.value)}
                      className="w-full px-3 py-2 border rounded-md"
                    >
                      {STATUS_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <FormField
                  label="Lead Source"
                  value={formData.lead_source}
                  onChange={(v) => handleChange('lead_source', v)}
                />
              </CardContent>
            </Card>

            {/* Tags & Keywords */}
            <Card>
              <CardHeader>
                <CardTitle>Tags & Keywords</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <TagInput
                  value={formData.keywords}
                  onChange={(v) => handleChange('keywords', v)}
                  placeholder="Enter keywords separated by commas"
                />
                <TagInput
                  value={formData.technologies}
                  onChange={(v) => handleChange('technologies', v)}
                  placeholder="Enter technologies separated by commas"
                />
                <TagInput
                  value={formData.custom_tags_a}
                  onChange={(v) => handleChange('custom_tags_a', v)}
                  placeholder="Custom Tags A (comma-separated)"
                />
                <TagInput
                  value={formData.custom_tags_b}
                  onChange={(v) => handleChange('custom_tags_b', v)}
                  placeholder="Custom Tags B (comma-separated)"
                />
                <TagInput
                  value={formData.custom_tags_c}
                  onChange={(v) => handleChange('custom_tags_c', v)}
                  placeholder="Custom Tags C (comma-separated)"
                />
              </CardContent>
            </Card>

            {/* URLs */}
            <Card>
              <CardHeader>
                <CardTitle>Social & URLs</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <FormField
                  label="LinkedIn URL"
                  value={formData.linkedin_url}
                  onChange={(v) => handleChange('linkedin_url', v)}
                  placeholder="https://linkedin.com/company/..."
                />
                <FormField
                  label="Twitter URL"
                  value={formData.twitter_url}
                  onChange={(v) => handleChange('twitter_url', v)}
                  placeholder="https://twitter.com/..."
                />
                <FormField
                  label="Facebook URL"
                  value={formData.facebook_url}
                  onChange={(v) => handleChange('facebook_url', v)}
                  placeholder="https://facebook.com/..."
                />
              </CardContent>
            </Card>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : existingCompany ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function FormField({
  label,
  required = false,
  error,
  type = 'text',
  value,
  onChange,
  placeholder,
  min,
  max,
}: {
  label: string;
  required?: boolean;
  error?: string;
  type?: 'text' | 'number';
  value: string | number;
  onChange: (value: string) => void;
  placeholder?: string;
  min?: number;
  max?: number;
}) {
  return (
    <div>
      <label className="text-sm font-medium mb-1 block">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      <Input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        min={min}
        max={max}
        className={error ? 'border-red-500' : ''}
      />
      {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
    </div>
  );
}

