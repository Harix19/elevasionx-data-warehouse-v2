'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface CSVUploadProps {
  onUpload: (file: File) => void;
  isUploading?: boolean;
}

export function CSVUpload({ onUpload, isUploading }: CSVUploadProps) {
  const [file, setFile] = useState<File | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
    },
    multiple: false,
  });

  const handleUpload = () => {
    if (file) {
      onUpload(file);
    }
  };

  const removeFile = () => {
    setFile(null);
  };

  return (
    <div className="space-y-6">
      {!file ? (
        <div 
          {...getRootProps()} 
          className={`
            border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer
            ${isDragActive ? 'border-primary bg-primary/5' : 'border-zinc-800 hover:border-zinc-700 bg-zinc-950/30'}
          `}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center">
              <Upload className={`w-6 h-6 ${isDragActive ? 'text-primary' : 'text-muted-foreground'}`} />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">
                {isDragActive ? 'Drop the file here' : 'Click or drag CSV to upload'}
              </p>
              <p className="text-xs text-muted-foreground">Only CSV files are supported (max 10MB)</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="surface-card p-6 border-zinc-800 bg-zinc-950/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center">
                <FileText className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">{file.name}</p>
                <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
            {!isUploading && (
              <Button variant="ghost" size="icon" onClick={removeFile} className="text-muted-foreground hover:text-destructive">
                <X className="w-4 h-4" />
              </Button>
            )}
          </div>
          
          <div className="mt-8">
            <Button 
              onClick={handleUpload} 
              disabled={isUploading}
              className="w-full h-11 bg-primary hover:bg-primary/90 text-white font-medium"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                'Confirm and Upload'
              )}
            </Button>
          </div>
        </div>
      )}

      {/* Info Tips */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800 flex items-start gap-3">
          <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5" />
          <div className="space-y-1">
            <p className="text-xs font-semibold text-foreground uppercase tracking-wider">Format Requirements</p>
            <p className="text-xs text-muted-foreground leading-relaxed">Ensure your CSV contains headers for Name, Email, and Company.</p>
          </div>
        </div>
        <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800 flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-primary mt-0.5" />
          <div className="space-y-1">
            <p className="text-xs font-semibold text-foreground uppercase tracking-wider">Validation</p>
            <p className="text-xs text-muted-foreground leading-relaxed">Our system will automatically validate data before final ingestion.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
