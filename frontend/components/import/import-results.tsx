'use client';

import { CheckCircle2, AlertCircle, Building2, Users, ArrowRight, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

interface ImportResultsProps {
  results: {
    type: 'companies' | 'contacts';
    total: number;
    success: number;
    failed: number;
    duplicates?: number;
    errors: Array<{ row: number; message: string }>;
    partialSuccess?: boolean;
    completedBatches?: number;
    totalBatches?: number;
  };
}

export function ImportResults({ results }: ImportResultsProps) {
  const Icon = results.type === 'companies' ? Building2 : Users;

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Summary Card */}
      <div className="surface-card p-8 bg-zinc-950/50 border-zinc-800">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${
              results.partialSuccess 
                ? 'bg-yellow-500/10 border-yellow-500/20' 
                : results.failed === 0 
                  ? 'bg-green-500/10 border-green-500/20' 
                  : 'bg-primary/10 border-primary/20'
            } border`}>
              {results.partialSuccess ? (
                <AlertTriangle className="w-8 h-8 text-yellow-500" />
              ) : results.failed === 0 ? (
                <CheckCircle2 className="w-8 h-8 text-green-500" />
              ) : (
                <Icon className="w-8 h-8 text-primary" />
              )}
            </div>
            <div className="space-y-1">
              <h2 className="text-xl font-bold text-foreground">
                {results.partialSuccess ? 'Import Partially Complete' : 'Import Complete'}
              </h2>
              <p className="text-sm text-muted-foreground">
                {results.partialSuccess 
                  ? `Completed ${results.completedBatches}/${results.totalBatches} batches. Some records may not have been saved.`
                  : `Processed ${results.total} ${results.type} records.`
                }
              </p>
            </div>
          </div>
          <div className="flex gap-4">
            <Link href={results.type === 'companies' ? '/companies' : '/contacts'}>
              <Button variant="outline" className="h-10 gap-2 border-zinc-800">
                View {results.type.charAt(0).toUpperCase() + results.type.slice(1)}
              </Button>
            </Link>
            <Button onClick={() => window.location.reload()} className="h-10 bg-primary text-white">
              Import More
            </Button>
          </div>
        </div>

        <div className={`grid grid-cols-1 ${results.duplicates && results.duplicates > 0 ? 'md:grid-cols-4' : 'md:grid-cols-3'} gap-6 mt-10`}>
          <div className="p-4 rounded-lg bg-zinc-900/30 border border-zinc-800/50">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-1">Total Records</p>
            <p className="text-2xl font-bold text-foreground">{results.total}</p>
          </div>
          <div className="p-4 rounded-lg bg-green-500/5 border border-green-500/10">
            <p className="text-xs font-semibold text-green-500/70 uppercase tracking-widest mb-1">Successful</p>
            <p className="text-2xl font-bold text-green-500">{results.success}</p>
          </div>
          <div className="p-4 rounded-lg bg-destructive/5 border border-destructive/10">
            <p className="text-xs font-semibold text-destructive/70 uppercase tracking-widest mb-1">Failed</p>
            <p className="text-2xl font-bold text-destructive">{results.failed}</p>
          </div>
          {results.duplicates && results.duplicates > 0 && (
            <div className="p-4 rounded-lg bg-amber-500/5 border border-amber-500/10">
              <p className="text-xs font-semibold text-amber-500/70 uppercase tracking-widest mb-1">Duplicates Found</p>
              <p className="text-2xl font-bold text-amber-500">{results.duplicates}</p>
            </div>
          )}
        </div>
      </div>

      {/* Errors Section */}
      {results.errors.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-destructive" />
            <h3 className="font-semibold text-sm">Validation Issues</h3>
          </div>
          <div className="surface-card overflow-hidden border-destructive/20">
            <table className="w-full text-left">
              <thead className="bg-destructive/5">
                <tr>
                  <th className="px-6 py-3 text-xs font-semibold text-destructive/70 uppercase">Row</th>
                  <th className="px-6 py-3 text-xs font-semibold text-destructive/70 uppercase">Issue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/50">
                {results.errors.map((error, i) => (
                  <tr key={i} className="hover:bg-destructive/[0.02] transition-colors">
                    <td className="px-6 py-4 text-sm font-medium text-foreground">{error.row}</td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">{error.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
