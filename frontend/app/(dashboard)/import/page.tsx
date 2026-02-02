'use client';

import { useState, useRef } from 'react';
import { importApi } from '@/lib/api';
import { CSVUpload } from '@/components/import/csv-upload';
import { ImportResults } from '@/components/import/import-results';
import { ColumnMapper } from '@/components/import/column-mapper';
import { TagInput } from '@/components/import/tag-input';
import { ImportStepper } from '@/components/import/import-stepper';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { 
  parseCSV, 
  parseFullCSV, 
  suggestMappings, 
  transformData, 
  COMPANY_FIELDS, 
  CONTACT_FIELDS,
  CSVPreview
} from '@/lib/import-utils';
import { ArrowRight, ArrowLeft, Upload, Loader2, Info, Check } from 'lucide-react';

type Step = 'upload' | 'mapping' | 'tags' | 'results';
type ImportType = 'companies' | 'contacts';

const STEPS = [
  { id: 'upload', name: 'Upload' },
  { id: 'mapping', name: 'Map Columns' },
  { id: 'tags', name: 'Add Tags' },
  { id: 'results', name: 'Results' },
];

export default function ImportPage() {
  // Step management
  const [step, setStep] = useState<Step>('upload');
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  
  // Data state
  const [importType, setImportType] = useState<ImportType>('companies');
  const [file, setFile] = useState<File | null>(null);
  const [csvPreview, setCsvPreview] = useState<CSVPreview | null>(null);
  
  // Mapping state
  const [mappings, setMappings] = useState<Record<string, string>>({});
  
  // Tags state
  const [manualTags, setManualTags] = useState({
    a: [] as string[],
    b: [] as string[],
    c: [] as string[],
  });

  // UI state
  const [isProcessing, setIsProcessing] = useState(false);
  const [importProgress, setImportProgress] = useState({ processed: 0, total: 0 });
  const [importResults, setImportResults] = useState<any>(null);
  
  // AbortController for cancellation
  const abortControllerRef = useRef<AbortController | null>(null);

  const handleFileSelect = async (selectedFile: File) => {
    setFile(selectedFile);
    setIsProcessing(true);
    try {
      const preview = await parseCSV(selectedFile);
      setCsvPreview(preview);
      
      // Auto-suggest mappings
      const fields = importType === 'companies' ? COMPANY_FIELDS : CONTACT_FIELDS;
      const suggested = suggestMappings(preview.headers, fields);
      setMappings(suggested);
      
      setStep('mapping');
      setCurrentStepIndex(1);
    } catch (error) {
      console.error('Failed to parse CSV:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const goToTags = () => {
    // Basic validation
    const fields = importType === 'companies' ? COMPANY_FIELDS : CONTACT_FIELDS;
    const requiredFields = fields.filter(f => f.required);
    const missingRequired = requiredFields.filter(f => !Object.values(mappings).includes(f.key));
    
    if (missingRequired.length > 0) {
      alert(`Please map the following required fields: ${missingRequired.map(f => f.label).join(', ')}`);
      return;
    }
    
    setStep('tags');
    setCurrentStepIndex(2);
  };

  const handleImport = async () => {
    if (!file) return;
    
    // Create new AbortController for this import
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;
    
    setIsProcessing(true);
    setImportProgress({ processed: 0, total: 0 });
    
    try {
      const fullData = await parseFullCSV(file);
      
      // Check for cancellation after CSV parsing
      if (signal.aborted) {
        throw new Error('Import cancelled');
      }
      
      const transformedData = await transformData(fullData, mappings, manualTags, importType);
      
      // Check for cancellation after transformation
      if (signal.aborted) {
        throw new Error('Import cancelled');
      }
      
      setImportProgress({ processed: 0, total: transformedData.length });
      
      const handleProgress = (processed: number, total: number) => {
        setImportProgress({ processed, total });
      };
      
      let results;
      if (importType === 'companies') {
        results = await importApi.bulkCompanies(transformedData, handleProgress, signal);
      } else {
        results = await importApi.bulkContacts(transformedData, handleProgress, signal);
      }
      
      setImportResults({
        type: importType,
        total: results.total,
        success: results.created + results.updated,
        failed: results.errors.length,
        duplicates: results.duplicates || 0,
        errors: results.errors.map((e: any) => ({ 
          row: e.index + 2,
          message: e.error 
        })),
        partialSuccess: results.partialSuccess,
        completedBatches: results.completedBatches,
        totalBatches: results.totalBatches
      });
      
      setStep('results');
      setCurrentStepIndex(3);
    } catch (error: any) {
      // Handle cancellation gracefully
      if (error.message === 'Import cancelled' || error.name === 'CanceledError') {
        console.log('Import was cancelled by user');
        return;
      }
      
      console.error('Import failed:', error);
      // Extract validation error details from 422 response
      const errorDetail = error.response?.data?.detail;
      let errorMessage = 'Import failed.';
      if (Array.isArray(errorDetail)) {
        // Pydantic validation errors
        const issues = errorDetail.map((e: any) => {
          const field = e.loc?.join('.') || 'unknown';
          return `${field}: ${e.msg}`;
        }).join('\n');
        errorMessage = `Validation errors:\n${issues}`;
      } else if (typeof errorDetail === 'string') {
        errorMessage = errorDetail;
      } else if (error.response?.status === 422) {
        errorMessage = 'Validation failed. Please ensure all required fields are mapped correctly.';
      } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMessage = 'Request timed out. The server may be processing a large batch. Please try again.';
      }
      alert(errorMessage);
    } finally {
      setIsProcessing(false);
      setImportProgress({ processed: 0, total: 0 });
      abortControllerRef.current = null;
    }
  };

  const handleCancelImport = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  };

  const reset = () => {
    handleCancelImport();
    setStep('upload');
    setCurrentStepIndex(0);
    setFile(null);
    setCsvPreview(null);
    setMappings({});
    setManualTags({ a: [], b: [], c: [] });
    setImportResults(null);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-20">
      {/* Page Header */}
      <div className="flex justify-between items-end">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Data Import</h1>
          <p className="text-muted-foreground">Import your GTM data from CSV with intelligent mapping.</p>
        </div>
        {step !== 'upload' && step !== 'results' && (
          <Button variant="outline" size="sm" onClick={reset}>
            Cancel & Reset
          </Button>
        )}
      </div>

      {/* Progress Stepper */}
      <div className="px-4 py-6 bg-zinc-950/30 rounded-xl border border-zinc-800/50">
        <ImportStepper steps={STEPS} currentStepIndex={currentStepIndex} />
      </div>

      {/* Main Content Area */}
      <div className="min-h-[400px]">
        {step === 'upload' && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <Card className="p-8 border-dashed border-2 bg-zinc-950/50">
              <div className="flex flex-col items-center gap-6">
                <div className="flex bg-zinc-900 p-1 rounded-lg border border-zinc-800">
                  <button
                    onClick={() => setImportType('companies')}
                    className={`px-6 py-2 rounded-md text-sm font-medium transition-all ${
                      importType === 'companies' 
                        ? 'bg-blue-600 text-white shadow-lg' 
                        : 'text-zinc-400 hover:text-white'
                    }`}
                  >
                    Companies
                  </button>
                  <button
                    onClick={() => setImportType('contacts')}
                    className={`px-6 py-2 rounded-md text-sm font-medium transition-all ${
                      importType === 'contacts' 
                        ? 'bg-blue-600 text-white shadow-lg' 
                        : 'text-zinc-400 hover:text-white'
                    }`}
                  >
                    Contacts
                  </button>
                </div>
                
                <div className="w-full">
                  <CSVUpload 
                    onUpload={handleFileSelect} 
                    isUploading={isProcessing} 
                  />
                </div>
              </div>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-950/30 space-y-2">
                <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                  <Upload className="w-4 h-4 text-blue-500" />
                </div>
                <h3 className="font-semibold text-sm">Flexible Import</h3>
                <p className="text-xs text-muted-foreground">Support for any CSV format from Apollo, LinkedIn, or custom sheets.</p>
              </div>
              <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-950/30 space-y-2">
                <div className="w-8 h-8 rounded-lg bg-green-500/10 flex items-center justify-center">
                  <Info className="w-4 h-4 text-green-500" />
                </div>
                <h3 className="font-semibold text-sm">Smart Mapping</h3>
                <p className="text-xs text-muted-foreground">Automatically detects fields and allows manual mapping for precision.</p>
              </div>
              <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-950/30 space-y-2">
                <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center">
                  <Loader2 className="w-4 h-4 text-purple-500" />
                </div>
                <h3 className="font-semibold text-sm">Async Processing</h3>
                <p className="text-xs text-muted-foreground">Handles large files efficiently with real-time progress indicators.</p>
              </div>
            </div>
          </div>
        )}

        {step === 'mapping' && csvPreview && (
          <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
            <Card className="p-6 bg-zinc-950/50 border-zinc-800">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-xl font-semibold">Column Mapping</h2>
                  <p className="text-sm text-muted-foreground">Map your CSV columns to database fields.</p>
                </div>
                <div className="flex gap-3">
                  <Button variant="outline" onClick={() => setStep('upload')}>Back</Button>
                  <Button onClick={goToTags} className="bg-blue-600 hover:bg-blue-700">
                    Next: Add Tags <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              </div>
              
              <ColumnMapper
                headers={csvPreview.headers}
                fields={importType === 'companies' ? COMPANY_FIELDS : CONTACT_FIELDS}
                previewRows={csvPreview.rows}
                mappings={mappings}
                onMappingChange={(header, fieldKey) => {
                  setMappings(prev => ({ ...prev, [header]: fieldKey }));
                }}
              />
            </Card>
          </div>
        )}

        {step === 'tags' && (
          <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
            <Card className="p-8 max-w-2xl mx-auto bg-zinc-950/50 border-zinc-800">
              <div className="mb-8">
                <h2 className="text-xl font-semibold">Apply Global Tags</h2>
                <p className="text-sm text-muted-foreground">These tags will be added to every record in this import batch.</p>
              </div>
              
              <div className="space-y-8">
                <TagInput
                  label="Campaign / Source (Tag A)"
                  description="General category for this import (e.g., 'Jan 2026 Batch', 'Apollo Export')"
                  value={manualTags.a}
                  onChange={(tags) => setManualTags(prev => ({ ...prev, a: tags }))}
                />
                <TagInput
                  label="Industry / Segment (Tag B)"
                  description="Specific segment or industry vertical (e.g., 'SaaS', 'Healthcare')"
                  value={manualTags.b}
                  onChange={(tags) => setManualTags(prev => ({ ...prev, b: tags }))}
                />
                <TagInput
                  label="Custom Category (Tag C)"
                  description="Any additional categorization needed"
                  value={manualTags.c}
                  onChange={(tags) => setManualTags(prev => ({ ...prev, c: tags }))}
                />
              </div>

              <div className="flex justify-between mt-12 pt-6 border-t border-zinc-800">
                <Button variant="outline" onClick={() => setStep('mapping')} disabled={isProcessing}>
                  <ArrowLeft className="mr-2 h-4 w-4" /> Back to Mapping
                </Button>
                <div className="flex gap-3">
                  {isProcessing && (
                    <Button 
                      variant="destructive" 
                      onClick={handleCancelImport}
                      className="min-w-[100px]"
                    >
                      Cancel
                    </Button>
                  )}
                  <Button 
                    onClick={handleImport} 
                    disabled={isProcessing}
                    className="bg-green-600 hover:bg-green-700 min-w-[180px]"
                  >
                    {isProcessing ? (
                      <> 
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> 
                        {importProgress.total > 0 
                          ? `${importProgress.processed} / ${importProgress.total}` 
                          : 'Preparing...'
                        }
                      </>
                    ) : (
                      <> Finalize & Import <Check className="ml-2 h-4 w-4" /> </>
                    )}
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        )}

        {step === 'results' && importResults && (
          <div className="animate-in zoom-in-95 duration-500">
            <ImportResults results={importResults} />
            <div className="mt-8 flex justify-center">
              <Button onClick={reset} variant="outline">
                Start New Import
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
