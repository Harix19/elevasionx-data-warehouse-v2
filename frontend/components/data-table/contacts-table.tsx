'use client';

import { useRouter } from 'next/navigation';
import type { Contact } from '@/types/contact';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { User, Mail, Briefcase, Building2, Linkedin, ChevronLeft, ChevronRight } from 'lucide-react';

interface ContactsTableProps {
  contacts: Contact[];
  isLoading?: boolean;
  isFetching?: boolean;
  hasMore?: boolean;
  hasPrevious?: boolean;
  onNextPage?: () => void;
  onPreviousPage?: () => void;
  pageIndex?: number;
}

const statusColors: Record<string, string> = {
  new: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  contacted: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  qualified: 'bg-green-500/10 text-green-400 border-green-500/20',
  customer: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  churned: 'bg-red-500/10 text-red-400 border-red-500/20',
};

export function ContactsTable({ 
  contacts, 
  isLoading,
  isFetching,
  hasMore,
  hasPrevious,
  onNextPage,
  onPreviousPage,
  pageIndex = 0,
}: ContactsTableProps) {
  const router = useRouter();

  const handleRowClick = (contactId: string) => {
    router.push(`/contacts/${contactId}`);
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-16 surface-card animate-pulse rounded-lg" />
        ))}
      </div>
    );
  }

  if (contacts.length === 0 && pageIndex === 0) {
    return (
      <div className="surface-card rounded-xl py-20 text-center border-dashed border-zinc-800">
        <User className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-20" />
        <p className="text-muted-foreground">No contacts found in your warehouse</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className={`surface-card overflow-hidden ${isFetching ? 'opacity-60' : ''}`}>
        <Table>
          <TableHeader className="bg-background-alt">
            <TableRow className="hover:bg-transparent border-border">
              <TableHead className="table-header">Full Name</TableHead>
              <TableHead className="table-header">Contact Info</TableHead>
              <TableHead className="table-header">Company</TableHead>
              <TableHead className="table-header">Role</TableHead>
              <TableHead className="table-header">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {contacts.map((contact) => (
              <TableRow
                key={contact.id}
                onClick={() => handleRowClick(contact.id)}
                className="table-row group cursor-pointer"
              >
                <TableCell className="table-cell">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-zinc-900 border border-border flex items-center justify-center font-bold text-zinc-400 transition-transform group-hover:scale-110">
                      {contact.first_name?.[0]}{contact.last_name?.[0]}
                    </div>
                    <div className="flex flex-col">
                      <span className="font-medium text-foreground group-hover:text-primary transition-colors">{contact.full_name}</span>
                      <span className="text-[10px] text-muted-foreground uppercase tracking-widest">ID: {contact.id.slice(0, 8)}</span>
                    </div>
                  </div>
                </TableCell>
                <TableCell className="table-cell">
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-1.5 text-sm">
                      <Mail className="w-3.5 h-3.5 text-primary/70" />
                      {contact.email || '-'}
                    </div>
                    {contact.linkedin_url && (
                      <a 
                        href={contact.linkedin_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-[10px] flex items-center gap-1 text-muted-foreground hover:text-primary transition-colors"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Linkedin className="w-2.5 h-2.5" /> LinkedIn Profile
                      </a>
                    )}
                  </div>
                </TableCell>
                <TableCell className="table-cell">
                  <div className="flex items-center gap-2 text-sm text-foreground">
                    <Building2 className="w-3.5 h-3.5 text-muted-foreground" />
                    {contact.working_company_name || 'Individual'}
                  </div>
                </TableCell>
                <TableCell className="table-cell">
                  <div className="flex items-center gap-2">
                    <Briefcase className="w-3.5 h-3.5 text-muted-foreground" />
                    <span className="text-sm">{contact.job_title || 'Lead'}</span>
                  </div>
                </TableCell>
                <TableCell className="table-cell">
                  {contact.status && (
                    <Badge variant="outline" className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${statusColors[contact.status]}`}>
                      {contact.status}
                    </Badge>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between px-2">
        <p className="text-sm text-muted-foreground">
          Page {pageIndex + 1}
        </p>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onPreviousPage}
            disabled={!hasPrevious || isFetching}
            className="gap-1"
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onNextPage}
            disabled={!hasMore || isFetching}
            className="gap-1"
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
