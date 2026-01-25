'use client';

import { useQuery } from '@tanstack/react-query';
import { companiesApi } from '@/lib/api';
import { Plus, Search, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { CompaniesTable } from '@/components/data-table/companies-table';

export default function CompaniesPage() {
  const { data: companies, isLoading } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companiesApi.list(),
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Companies</h1>
          <p className="text-sm text-muted-foreground">Manage and track your target organizations.</p>
        </div>
        <Button className="bg-primary hover:bg-primary/90 text-white h-10 px-4 gap-2">
          <Plus className="w-4 h-4" />
          Add Company
        </Button>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input 
            placeholder="Search companies by name or domain..." 
            className="pl-10 bg-background border-border focus:border-primary/50"
          />
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="h-10 gap-2 text-sm">
            <Filter className="w-4 h-4" />
            Filters
          </Button>
          <Button variant="outline" className="h-10 text-sm">
            Export
          </Button>
        </div>
      </div>

      {/* Table Component */}
      <CompaniesTable 
        companies={companies?.items || []} 
        isLoading={isLoading} 
      />
    </div>
  );
}
