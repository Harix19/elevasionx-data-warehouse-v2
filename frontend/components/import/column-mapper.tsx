'use client';

import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { FieldDefinition } from '@/lib/import-utils';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

interface ColumnMapperProps {
  headers: string[];
  fields: FieldDefinition[];
  previewRows: any[];
  mappings: Record<string, string>;
  onMappingChange: (header: string, fieldKey: string) => void;
}

export function ColumnMapper({
  headers,
  fields,
  previewRows,
  mappings,
  onMappingChange,
}: ColumnMapperProps) {
  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[30%]">CSV Column</TableHead>
              <TableHead className="w-[40%]">Database Field</TableHead>
              <TableHead className="w-[30%]">Preview (First Row)</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {headers.map((header) => {
              const selectedFieldKey = mappings[header] || '';
              const selectedField = fields.find(f => f.key === selectedFieldKey);
              const previewValue = previewRows[0]?.[header];

              return (
                <TableRow key={header}>
                  <TableCell className="font-medium">
                    {header}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <select
                        value={selectedFieldKey}
                        onChange={(e) => onMappingChange(header, e.target.value)}
                        className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <option value="">-- Skip Column --</option>
                        {fields.map((field) => (
                          <option key={field.key} value={field.key}>
                            {field.label} {field.required ? '*' : ''}
                          </option>
                        ))}
                      </select>
                      {selectedFieldKey ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-muted-foreground shrink-0" />
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-muted-foreground truncate max-w-[200px]">
                    {previewValue !== undefined && previewValue !== null ? String(previewValue) : <span className="italic text-xs">Empty</span>}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
      
      <div className="text-xs text-muted-foreground">
        * Fields marked with asterisk are recommended for a good data quality.
      </div>
    </div>
  );
}
