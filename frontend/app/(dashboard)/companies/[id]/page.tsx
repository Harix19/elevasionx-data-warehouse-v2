'use client';

import { useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { useCompany, useCompanyContacts, useUpdateCompany, useDeleteCompany } from '@/hooks/use-companies';
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

export default function CompanyDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;

  const { data: company, isLoading, error } = useCompany(id);
  const { data: contacts } = useCompanyContacts(id);
  const updateCompany = useUpdateCompany();
  const deleteCompany = useDeleteCompany();

  const [isEditing, setIsEditing] = useState(false);
  const [editedData, setEditedData] = useState<Record<string, any>>({});
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleEdit = () => {
    if (company) {
      setEditedData({ ...company });
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
      await updateCompany.mutateAsync({ id, data: editedData });
      setIsEditing(false);
      setErrorMessage('');
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to update company');
    }
  };

  const handleDelete = async () => {
    try {
      await deleteCompany.mutateAsync(id);
      router.push('/companies');
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to delete company');
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

  if (error || !company) {
    return (
      <div className="space-y-6">
        <Link href="/companies" className="text-primary hover:underline">
          ← Back to Companies
        </Link>
        <Card className="surface-card">
          <CardContent className="p-6">
            <p className="text-red-400">
              {(error as Error)?.message || 'Company not found'}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const displayData = isEditing ? editedData : company;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/companies">
            <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <h2 className="text-2xl font-bold text-foreground">{company.name}</h2>
            <p className="text-muted-foreground">{company.domain || 'No domain'}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {company.status && (
            <Badge variant="outline" className={statusColors[company.status]}>
              {company.status}
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
              <Button onClick={handleSave} size="sm" disabled={updateCompany.isPending}>
                {updateCompany.isPending ? 'Saving...' : 'Save'}
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
            label="Industry"
            value={displayData.industry}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, industry: value })}
          />
          <DetailRow
            label="Location"
            value={displayData.location}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, location: value })}
          />
          <DetailRow
            label="Country"
            value={displayData.country}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, country: value })}
          />
          <DetailRow
            label="Description"
            value={displayData.description}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, description: value })}
            textarea
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
            label="Employee Count"
            value={displayData.employee_count?.toString()}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, employee_count: value ? parseInt(value) : undefined })}
            type="number"
          />
          <DetailRow
            label="Revenue"
            value={displayData.revenue?.toString()}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, revenue: value ? parseInt(value) : undefined })}
            type="number"
          />
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
        </CardContent>
      </Card>

      {/* URLs */}
      <Card className="surface-card">
        <CardHeader>
          <CardTitle className="text-foreground">Links</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <DetailRow
            label="Domain"
            value={displayData.domain}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, domain: value })}
          />
          <DetailRow
            label="LinkedIn URL"
            value={displayData.linkedin_url}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, linkedin_url: value })}
          />
          <DetailRow
            label="Twitter URL"
            value={displayData.twitter_url}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, twitter_url: value })}
          />
          <DetailRow
            label="Facebook URL"
            value={displayData.facebook_url}
            isEditing={isEditing}
            onChange={(value) => setEditedData({ ...editedData, facebook_url: value })}
          />
        </CardContent>
      </Card>

      {/* Contacts */}
      <Card className="surface-card">
        <CardHeader>
          <CardTitle className="text-foreground">Contacts at this company</CardTitle>
          <CardDescription className="text-muted-foreground">
            {contacts?.items?.length || 0} contact{((contacts?.items?.length || 0) !== 1) ? 's' : ''} linked
          </CardDescription>
        </CardHeader>
        <CardContent>
          {contacts?.items && contacts.items.length > 0 ? (
            <div className="space-y-2">
              {contacts.items.map((contact: any) => (
                <div key={contact.id} className="flex items-center justify-between p-3 border border-border rounded hover:bg-zinc-800/50 transition-colors">
                  <div>
                    <p className="font-medium text-foreground">{contact.first_name} {contact.last_name}</p>
                    <p className="text-sm text-muted-foreground">{contact.email}</p>
                  </div>
                  <p className="text-sm text-muted-foreground">{contact.job_title || 'No title'}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No contacts linked to this company</p>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Company</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{company.name}"? This action will soft-delete the company and it can be restored later.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteCompany.isPending}
            >
              {deleteCompany.isPending ? 'Deleting...' : 'Delete'}
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
  textarea = false,
  options,
}: {
  label: string;
  value: any;
  isEditing: boolean;
  onChange: (value: string) => void;
  type?: 'text' | 'number' | 'select';
  textarea?: boolean;
  options?: string[];
}) {
  return (
    <div className="flex items-start justify-between py-2 border-b border-border last:border-0">
      <span className="font-medium text-muted-foreground w-48">{label}:</span>
      {isEditing ? (
        textarea ? (
          <textarea
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className="flex-1 px-3 py-2 border border-border rounded-md bg-zinc-900 text-foreground focus:border-primary/50 focus:outline-none"
            rows={3}
          />
        ) : type === 'select' ? (
          <select
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className="flex-1 px-3 py-2 border border-border rounded-md bg-zinc-900 text-foreground focus:border-primary/50 focus:outline-none"
          >
            <option value="">None</option>
            {options?.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        ) : (
          <input
            type={type}
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className="flex-1 px-3 py-2 border border-border rounded-md bg-zinc-900 text-foreground focus:border-primary/50 focus:outline-none"
          />
        )
      ) : (
        <span className="flex-1 text-foreground">{value || '-'}</span>
      )}
    </div>
  );
}
