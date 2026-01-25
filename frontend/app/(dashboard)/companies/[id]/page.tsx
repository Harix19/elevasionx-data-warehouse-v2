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
  new: 'bg-blue-100 text-blue-800',
  contacted: 'bg-yellow-100 text-yellow-800',
  qualified: 'bg-green-100 text-green-800',
  customer: 'bg-purple-100 text-purple-800',
  churned: 'bg-red-100 text-red-800',
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
        <div className="h-8 bg-gray-100 animate-pulse rounded w-48" />
        <Card>
          <CardContent className="p-6 space-y-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-6 bg-gray-100 animate-pulse rounded" />
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !company) {
    return (
      <div className="space-y-6">
        <Link href="/companies" className="text-blue-600 hover:underline">
          ← Back to Companies
        </Link>
        <Card>
          <CardContent className="p-6">
            <p className="text-red-600">
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
          <Link href="/companies" className="text-blue-600 hover:underline">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <h2 className="text-2xl font-bold">{company.name}</h2>
            <p className="text-gray-600">{company.domain || 'No domain'}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {company.status && (
            <Badge className={statusColors[company.status]}>
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
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {errorMessage}
        </div>
      )}

      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
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
      <Card>
        <CardHeader>
          <CardTitle>Metrics</CardTitle>
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
      <Card>
        <CardHeader>
          <CardTitle>Links</CardTitle>
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
      <Card>
        <CardHeader>
          <CardTitle>Contacts at this company</CardTitle>
          <CardDescription>
            {contacts?.items?.length || 0} contact{((contacts?.items?.length || 0) !== 1) ? 's' : ''} linked
          </CardDescription>
        </CardHeader>
        <CardContent>
          {contacts?.items && contacts.items.length > 0 ? (
            <div className="space-y-2">
              {contacts.items.map((contact: any) => (
                <div key={contact.id} className="flex items-center justify-between p-3 border rounded hover:bg-gray-50">
                  <div>
                    <p className="font-medium">{contact.first_name} {contact.last_name}</p>
                    <p className="text-sm text-gray-600">{contact.email}</p>
                  </div>
                  <p className="text-sm text-gray-500">{contact.job_title || 'No title'}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No contacts linked to this company</p>
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
    <div className="flex items-start justify-between py-2 border-b last:border-0">
      <span className="font-medium text-gray-700 w-48">{label}:</span>
      {isEditing ? (
        textarea ? (
          <textarea
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className="flex-1 px-3 py-2 border rounded-md"
            rows={3}
          />
        ) : type === 'select' ? (
          <select
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className="flex-1 px-3 py-2 border rounded-md"
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
            className="flex-1 px-3 py-2 border rounded-md"
          />
        )
      ) : (
        <span className="flex-1 text-gray-900">{value || '-'}</span>
      )}
    </div>
  );
}
