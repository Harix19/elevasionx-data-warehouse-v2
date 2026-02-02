'use client';

import { useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { useContact, useUpdateContact, useDeleteContact, useCompaniesForDropdown } from '@/hooks/use-contacts';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ArrowLeft, Pencil, Trash2 } from 'lucide-react';

const statusColors: Record<string, string> = {
  new: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  contacted: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  qualified: 'bg-green-500/10 text-green-400 border-green-500/20',
  customer: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  churned: 'bg-red-500/10 text-red-400 border-red-500/20',
};

export default function ContactDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;

  const { data: contact, isLoading, error } = useContact(id);
  const { data: companiesData } = useCompaniesForDropdown();
  const updateContact = useUpdateContact();
  const deleteContact = useDeleteContact();

  const [isEditing, setIsEditing] = useState(false);
  const [editedData, setEditedData] = useState<Record<string, any>>({});
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleEdit = () => {
    if (contact) {
      setEditedData({ ...contact });
      setIsEditing(true);
      setErrorMessage('');
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditedData({});
    setErrorMessage('');
  };

  const handleSave = async () => {
    try {
      await updateContact.mutateAsync({ id, data: editedData });
      setIsEditing(false);
      setErrorMessage('');
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to update contact');
    }
  };

  const handleDelete = async () => {
    try {
      await deleteContact.mutateAsync(id);
      router.push('/contacts');
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to delete contact');
      setShowDeleteDialog(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-zinc-800 animate-pulse rounded w-48" />
        <Card className="surface-card">
          <CardContent className="p-6 space-y-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-6 bg-zinc-800 animate-pulse rounded" />
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !contact) {
    return (
      <div className="space-y-6">
        <Link href="/contacts">
          <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Contacts
          </Button>
        </Link>
        <Card className="surface-card">
          <CardContent className="p-6">
            <p className="text-red-400">
              {(error as Error)?.message || 'Contact not found'}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const displayData = isEditing ? editedData : contact;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground" onClick={() => router.push('/contacts')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <h2 className="text-2xl font-bold text-foreground">{contact.full_name}</h2>
            <p className="text-muted-foreground">{contact.email || 'No email'}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {contact.status && (
            <Badge className={statusColors[contact.status]}>
              {contact.status}
            </Badge>
          )}
          {!isEditing ? (
            <>
              <Button onClick={handleEdit} variant="outline" size="sm">
                <Pencil className="h-4 w-4 mr-2" />
                Edit
              </Button>
              <Button
                onClick={() => setShowDeleteDialog(true)}
                variant="destructive"
                size="sm"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </Button>
            </>
          ) : (
            <>
              <Button onClick={handleSave} size="sm" disabled={updateContact.isPending}>
                {updateContact.isPending ? 'Saving...' : 'Save'}
              </Button>
              <Button onClick={handleCancel} variant="outline" size="sm">
                Cancel
              </Button>
            </>
          )}
        </div>
      </div>

      {errorMessage && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded">
          {errorMessage}
        </div>
      )}

      {/* Basic Information */}
      <Card className="surface-card">
        <CardHeader>
          <CardTitle className="text-foreground">Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <DetailRow
            label="First Name"
            value={displayData.first_name}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, first_name: value })}
          />
          <DetailRow
            label="Last Name"
            value={displayData.last_name}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, last_name: value })}
          />
          <DetailRow
            label="Email"
            value={displayData.email}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, email: value })}
            type="email"
          />
          <DetailRow
            label="Phone"
            value={displayData.phone}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, phone: value })}
          />
          <DetailRow
            label="Location"
            value={displayData.location}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, location: value })}
          />
        </CardContent>
      </Card>

      {/* Work Information */}
      <Card className="surface-card">
        <CardHeader>
          <CardTitle className="text-foreground">Work Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <DetailRow
            label="Company"
            value={displayData.company_id}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, company_id: value || null })}
            type="select"
            options={companiesData?.items.map(c => ({ label: c.name, value: c.id }))}
          />
          <DetailRow
            label="Job Title"
            value={displayData.job_title}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, job_title: value })}
          />
          <DetailRow
            label="Seniority Level"
            value={displayData.seniority_level}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, seniority_level: value as any || null })}
            type="select"
            options={['c_level', 'director', 'manager', 'individual_contributor', 'other']}
          />
          <DetailRow
            label="Department"
            value={displayData.department}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, department: value })}
          />
          <DetailRow
            label="LinkedIn URL"
            value={displayData.linkedin_url}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, linkedin_url: value })}
          />
        </CardContent>
      </Card>

      {/* Metrics */}
      <Card className="surface-card">
        <CardHeader>
          <CardTitle className="text-foreground">Metrics</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <DetailRow
            label="Lead Score"
            value={displayData.lead_score?.toString()}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, lead_score: value ? parseInt(value) : undefined })}
            type="number"
          />
          <DetailRow
            label="Status"
            value={displayData.status}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, status: value as any })}
            type="select"
            options={['new', 'contacted', 'qualified', 'customer', 'churned']}
          />
          <DetailRow
            label="Lead Source"
            value={displayData.lead_source}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, lead_source: value })}
          />
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent className="bg-zinc-900 border-zinc-800">
          <DialogHeader>
            <DialogTitle className="text-foreground">Delete Contact</DialogTitle>
            <DialogDescription className="text-muted-foreground">
              Are you sure you want to delete "{contact.full_name}"? This action will soft-delete the contact and it can be restored later.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteContact.isPending}
            >
              {deleteContact.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function DetailRow({
  label,
  value,
  isEditing,
  onChange,
  type = 'text',
  options,
}: {
  label: string;
  value: any;
  isEditing: boolean;
  onChange: (value: string) => void;
  type?: 'text' | 'email' | 'number' | 'select';
  options?: Array<{ label: string; value: string }> | string[];
}) {
  const isOptionsArray = options && Array.isArray(options) && options.length > 0;
  const isObjectOptions = isOptionsArray && typeof options[0] === 'object' && 'label' in options[0];
  const displayValue = isObjectOptions
    ? (options as Array<{ label: string; value: string }>)?.find((o) => o.value === value)?.label || value
    : value;

  return (
    <div className="flex items-start justify-between py-2 border-b last:border-0 border-border">
      <span className="font-medium text-muted-foreground w-48">{label}:</span>
      {isEditing ? (
        type === 'select' ? (
          <select
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className="flex-1 px-3 py-2 bg-zinc-900 text-foreground border border-border rounded-md focus:border-primary/50 focus:outline-none"
          >
            <option value="">None</option>
            {(options as any)?.map((opt: any) => (
              <option key={typeof opt === 'string' ? opt : opt.value} value={typeof opt === 'string' ? opt : opt.value}>
                {typeof opt === 'string' ? opt : opt.label}
              </option>
            ))}
          </select>
        ) : (
          <input
            type={type}
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className="flex-1 px-3 py-2 bg-zinc-900 text-foreground border border-border rounded-md focus:border-primary/50 focus:outline-none"
          />
        )
      ) : (
        <span className="flex-1 text-foreground">{displayValue || '-'}</span>
      )}
    </div>
  );
}
