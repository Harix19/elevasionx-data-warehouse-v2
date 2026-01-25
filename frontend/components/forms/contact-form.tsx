'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import { useCreateContact, useCompaniesForDropdown } from '@/hooks/use-contacts';
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
import type { Contact } from '@/types/contact';

interface ContactFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  existingContact?: Contact;
  prefillCompanyId?: string;
}

const STATUS_OPTIONS = [
  { value: 'new', label: 'New' },
  { value: 'contacted', label: 'Contacted' },
  { value: 'qualified', label: 'Qualified' },
  { value: 'customer', label: 'Customer' },
  { value: 'churned', label: 'Churned' },
];

const SENIORITY_OPTIONS = [
  { value: 'c_level', label: 'C-Level' },
  { value: 'director', label: 'Director' },
  { value: 'manager', label: 'Manager' },
  { value: 'individual_contributor', label: 'Individual Contributor' },
  { value: 'other', label: 'Other' },
];

export function ContactForm({ open, onOpenChange, existingContact, prefillCompanyId }: ContactFormProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const createContact = useCreateContact();
  const { data: companiesData } = useCompaniesForDropdown();

  const [formData, setFormData] = useState({
    first_name: existingContact?.first_name || '',
    last_name: existingContact?.last_name || '',
    email: existingContact?.email || '',
    phone: existingContact?.phone || '',
    location: existingContact?.location || '',
    linkedin_url: existingContact?.linkedin_url || '',
    job_title: existingContact?.job_title || '',
    seniority_level: existingContact?.seniority_level || '',
    department: existingContact?.department || '',
    company_id: existingContact?.company_id || prefillCompanyId || '',
    custom_tags_a: existingContact?.custom_tags_a || [],
    custom_tags_b: existingContact?.custom_tags_b || [],
    custom_tags_c: existingContact?.custom_tags_c || [],
    lead_source: existingContact?.lead_source || '',
    lead_score: existingContact?.lead_score || '',
    status: existingContact?.status || 'new',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    const newErrors: Record<string, string> = {};
    if (!formData.first_name.trim()) {
      newErrors.first_name = 'First name is required';
    }
    if (!formData.last_name.trim()) {
      newErrors.last_name = 'Last name is required';
    }
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }
    if (formData.lead_score && (Number(formData.lead_score) < 0 || Number(formData.lead_score) > 100)) {
      newErrors.lead_score = 'Lead score must be 0-100';
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
        company_id: formData.company_id || undefined,
        lead_score: formData.lead_score ? Number(formData.lead_score) : undefined,
      };

      await createContact.mutateAsync(submitData as any);

      // Close and reset
      onOpenChange(false);
      setFormData({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        location: '',
        linkedin_url: '',
        job_title: '',
        seniority_level: '',
        department: '',
        company_id: '',
        custom_tags_a: [],
        custom_tags_b: [],
        custom_tags_c: [],
        lead_source: '',
        lead_score: '',
        status: 'new',
      });
      setErrors({});
    } catch (error: any) {
      if (error?.response?.status === 404) {
        setErrors({ company_id: 'Company not found' });
      } else {
        setErrors({ form: error?.response?.data?.detail || 'Failed to create contact' });
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
          <DialogTitle>{existingContact ? 'Edit Contact' : 'Add Contact'}</DialogTitle>
          <DialogDescription>
            {existingContact ? 'Update contact information below.' : 'Fill in the details to add a new contact.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-6 py-4">
            {errors.form && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {errors.form}
              </div>
            )}

            {/* Name */}
            <Card>
              <CardHeader>
                <CardTitle>Name *</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <FormField
                  label="First Name *"
                  required
                  error={errors.first_name}
                  value={formData.first_name}
                  onChange={(v) => handleChange('first_name', v)}
                />
                <FormField
                  label="Last Name *"
                  required
                  error={errors.last_name}
                  value={formData.last_name}
                  onChange={(v) => handleChange('last_name', v)}
                />
              </CardContent>
            </Card>

            {/* Contact Information */}
            <Card>
              <CardHeader>
                <CardTitle>Contact Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <FormField
                  label="Email"
                  type="email"
                  error={errors.email}
                  value={formData.email}
                  onChange={(v) => handleChange('email', v)}
                  placeholder="john@example.com"
                />
                <FormField
                  label="Phone"
                  value={formData.phone}
                  onChange={(v) => handleChange('phone', v)}
                  placeholder="+1 (555) 123-4567"
                />
                <FormField
                  label="Location"
                  value={formData.location}
                  onChange={(v) => handleChange('location', v)}
                  placeholder="San Francisco, CA"
                />
                <FormField
                  label="LinkedIn URL"
                  value={formData.linkedin_url}
                  onChange={(v) => handleChange('linkedin_url', v)}
                  placeholder="https://linkedin.com/in/..."
                />
              </CardContent>
            </Card>

            {/* Work Information */}
            <Card>
              <CardHeader>
                <CardTitle>Work Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-1 block">Company</label>
                  <select
                    value={formData.company_id}
                    onChange={(e) => handleChange('company_id', e.target.value)}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="">No Company</option>
                    {companiesData?.items.map((company) => (
                      <option key={company.id} value={company.id}>
                        {company.name}
                      </option>
                    ))}
                  </select>
                  {errors.company_id && <p className="text-red-500 text-sm mt-1">{errors.company_id}</p>}
                </div>
                <FormField
                  label="Job Title"
                  value={formData.job_title}
                  onChange={(v) => handleChange('job_title', v)}
                  placeholder="Software Engineer"
                />
                <div>
                  <label className="text-sm font-medium mb-1 block">Seniority Level</label>
                  <select
                    value={formData.seniority_level}
                    onChange={(e) => handleChange('seniority_level', e.target.value)}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="">Select...</option>
                    {SENIORITY_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
                <FormField
                  label="Department"
                  value={formData.department}
                  onChange={(v) => handleChange('department', v)}
                  placeholder="Engineering"
                />
              </CardContent>
            </Card>

            {/* Tags & Metrics */}
            <Card>
              <CardHeader>
                <CardTitle>Tags & Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
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
                <FormField
                  label="Lead Source"
                  value={formData.lead_source}
                  onChange={(v) => handleChange('lead_source', v)}
                  placeholder="LinkedIn, Referral, etc."
                />
                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    label="Lead Score"
                    type="number"
                    min={0}
                    max={100}
                    error={errors.lead_score}
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
              {isSubmitting ? 'Saving...' : existingContact ? 'Update' : 'Create'}
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
  type?: 'text' | 'email' | 'number';
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
