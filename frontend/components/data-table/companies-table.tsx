'use client';

import { useRouter } from 'next/navigation';
import type { Company } from '@/types/company';
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
import { Building2, Globe, MapPin, BarChart3, ExternalLink, ChevronLeft, ChevronRight } from 'lucide-react';

interface CompaniesTableProps {
  companies: Company[];
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

export function CompaniesTable({ 
  companies, 
  isLoading,
  isFetching,
  hasMore,
  hasPrevious,
  onNextPage,
  onPreviousPage,
  pageIndex = 0,
}: CompaniesTableProps) {
  const router = useRouter();

  const handleRowClick = (companyId: string) => {
    router.push(`/companies/${companyId}`);
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

  if (companies.length === 0 && pageIndex === 0) {
    return (
      <div className="surface-card rounded-xl py-20 text-center border-dashed border-zinc-800">
        <Building2 className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-20" />
        <p className="text-muted-foreground">No companies found in your warehouse</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className={`surface-card overflow-hidden ${isFetching ? 'opacity-60' : ''}`}>
        <Table>
          <TableHeader className="bg-background-alt">
            <TableRow className="hover:bg-transparent border-border">
              <TableHead className="table-header">Company</TableHead>
              <TableHead className="table-header">Domain</TableHead>
              <TableHead className="table-header">Industry</TableHead>
              <TableHead className="table-header">Location</TableHead>
              <TableHead className="table-header">Status</TableHead>
              <TableHead className="table-header text-right">Score</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {companies.map((company) => (
              <TableRow
                key={company.id}
                onClick={() => handleRowClick(company.id)}
                className="table-row group cursor-pointer"
              >
                <TableCell className="table-cell">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-zinc-900 border border-border flex items-center justify-center font-bold text-primary transition-transform group-hover:scale-110">
                      {company.name[0]}
                    </div>
                    <span className="font-medium text-foreground group-hover:text-primary transition-colors">{company.name}</span>
                  </div>
                </TableCell>
                <TableCell className="table-cell">
                  <div className="flex flex-col">
                    <span className="text-sm">{company.domain || '-'}</span>
                    {company.domain && (
                      <a 
                        href={`https://${company.domain}`} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="text-xs flex items-center gap-1 text-muted-foreground hover:text-primary transition-colors"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Globe className="w-3 h-3" /> Visit site <ExternalLink className="w-2 h-2" />
                      </a>
                    )}
                  </div>
                </TableCell>
                <TableCell className="table-cell text-muted-foreground">
                  {company.industry || '—'}
                </TableCell>
                <TableCell className="table-cell">
                  <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                    <MapPin className="w-3.5 h-3.5" />
                    {company.location || company.country || 'Global'}
                  </div>
                </TableCell>
                <TableCell className="table-cell">
                  {company.status && (
                    <Badge variant="outline" className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${statusColors[company.status]}`}>
                      {company.status}
                    </Badge>
                  )}
                </TableCell>
                <TableCell className="table-cell text-right">
                  <div className="inline-flex items-center gap-2 font-bold text-sm">
                    <BarChart3 className="w-3.5 h-3.5 opacity-40" />
                    {company.lead_score ?? '0'}
                  </div>
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
