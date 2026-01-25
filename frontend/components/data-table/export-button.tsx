'use client';

import { useState } from 'react';
import { Download, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { companiesApi } from '@/lib/api';
import type { CompaniesListParams } from '@/types/company';
import type { ContactsListParams } from '@/types/contact';

interface ExportButtonProps {
  entityType: 'companies' | 'contacts';
  filters?: CompaniesListParams | ContactsListParams;
  totalCount?: number;
}

export function ExportButton({ entityType, filters = {}, totalCount }: ExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    // Warn if exporting large dataset
    if (totalCount && totalCount > 10000) {
      const confirmed = confirm(
        `You are about to export ${totalCount.toLocaleString()} records. This may take a while. Continue?`
      );
      if (!confirmed) return;
    }

    setIsExporting(true);
    setError(null);

    try {
      if (entityType === 'companies') {
        await companiesApi.export(filters as CompaniesListParams);
      } else {
        // Import contactsApi dynamically to avoid circular dependency
        const { contactsApi } = await import('@/lib/api');
        await contactsApi.export(filters as ContactsListParams);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Export failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="flex flex-col items-end gap-1">
      <Button
        onClick={handleExport}
        disabled={isExporting}
        variant="outline"
        size="sm"
      >
        {isExporting ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Exporting...
          </>
        ) : (
          <>
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </>
        )}
      </Button>
      {error && (
        <span className="text-xs text-red-600">{error}</span>
      )}
    </div>
  );
}
