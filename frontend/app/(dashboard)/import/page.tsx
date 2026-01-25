'use client';

import { useState } from 'react';
import { importApi } from '@/lib/api';
import { CSVUpload } from '@/components/import/csv-upload';
import { ImportResults } from '@/components/import/import-results';
import { Upload, Database, LayoutGrid, Check } from 'lucide-react';

type Step = 'upload' | 'results';

export default function ImportPage() {
  const [step, setStep] = useState<Step>('upload');
  const [isUploading, setIsUploading] = useState(false);
  const [importResults, setImportResults] = useState<any>(null);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    try {
      // For now, default to companies import
      const results = await importApi.companies(file);
      setImportResults({
        type: 'companies',
        ...results
      });
      setStep('results');
    } catch (error) {
      console.error('Import failed:', error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-10">
      {/* Page Header */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Data Ingestion</h1>
        <p className="text-sm text-muted-foreground">Upload and validate your GTM datasets.</p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center gap-8 relative">
        <div className="flex items-center gap-3 relative z-10">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border transition-all ${step === 'upload' ? 'bg-primary border-primary text-white shadow-[0_0_15px_rgba(0,112,243,0.3)]' : 'bg-green-500 border-green-500 text-white'}`}>
            {step === 'results' ? <Check className="w-4 h-4" /> : '1'}
          </div>
          <span className={`text-sm font-medium ${step === 'upload' ? 'text-foreground' : 'text-muted-foreground'}`}>Upload Source</span>
        </div>
        <div className="h-[1px] w-12 bg-zinc-800"></div>
        <div className="flex items-center gap-3 relative z-10">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border transition-all ${step === 'results' ? 'bg-primary border-primary text-white shadow-[0_0_15px_rgba(0,112,243,0.3)]' : 'bg-zinc-900 border-zinc-800 text-muted-foreground'}`}>
            2
          </div>
          <span className={`text-sm font-medium ${step === 'results' ? 'text-foreground' : 'text-muted-foreground'}`}>Validation & Sync</span>
        </div>
      </div>

      {/* Main Container */}
      <div className="space-y-8">
        {step === 'upload' && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div className="surface-card p-8 bg-zinc-950/50 border-zinc-800">
              <CSVUpload onUpload={handleUpload} isUploading={isUploading} />
            </div>

            {/* Features */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                { title: 'Automatic Mapping', description: 'Intelligent field detection for major GTM tools.', icon: LayoutGrid },
                { title: 'Data Cleaning', description: 'Automated deduplication and normalization.', icon: Database },
                { title: 'Bulk Actions', description: 'Process up to 10,000 records per upload.', icon: Upload },
              ].map((feature) => (
                <div key={feature.title} className="space-y-3">
                  <div className="w-8 h-8 rounded-md bg-zinc-900 border border-zinc-800 flex items-center justify-center">
                    <feature.icon className="w-4 h-4 text-primary" />
                  </div>
                  <h3 className="text-sm font-semibold text-foreground">{feature.title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {step === 'results' && importResults && (
          <ImportResults results={importResults} />
        )}
      </div>
    </div>
  );
}
