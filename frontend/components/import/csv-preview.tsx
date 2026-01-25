'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, XCircle } from 'lucide-react';

interface CsvPreviewProps {
  fileName: string;
  fileSize: number;
  headers: string[];
  rows: string[][];
  requiredColumns: string[];
  allColumns: string[];
}

export function CsvPreview({
  fileName,
  fileSize,
  headers,
  rows,
  requiredColumns,
  allColumns,
}: CsvPreviewProps) {
  const missingColumns = requiredColumns.filter(col => !headers.includes(col));
  const extraColumns = headers.filter(col => !allColumns.includes(col));
  const hasAllRequired = missingColumns.length === 0;

  return (
    <div className="space-y-4">
      {/* File Info */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">{fileName}</p>
              <p className="text-sm text-gray-500">{(fileSize / 1024).toFixed(2)} KB</p>
            </div>
            {hasAllRequired ? (
              <Badge variant="default" className="gap-1">
                <CheckCircle2 className="h-3 w-3" />
                All required columns detected
              </Badge>
            ) : (
              <Badge variant="destructive" className="gap-1">
                <XCircle className="h-3 w-3" />
                Missing required columns
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Column Validation */}
      {(missingColumns.length > 0 || extraColumns.length > 0) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Column Validation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {missingColumns.length > 0 && (
              <div>
                <p className="text-sm font-medium text-red-600 mb-1">Missing required columns:</p>
                <div className="flex flex-wrap gap-1">
                  {missingColumns.map(col => (
                    <Badge key={col} variant="destructive">{col}</Badge>
                  ))}
                </div>
              </div>
            )}
            {extraColumns.length > 0 && (
              <div>
                <p className="text-sm font-medium text-yellow-600 mb-1">Extra columns (will be ignored):</p>
                <div className="flex flex-wrap gap-1">
                  {extraColumns.map(col => (
                    <Badge key={col} variant="secondary">{col}</Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Expected Columns */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Expected Columns</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {requiredColumns.map(col => (
              <Badge key={col} variant="default">
                {col} *
              </Badge>
            ))}
            {allColumns.filter(col => !requiredColumns.includes(col)).map(col => (
              <Badge key={col} variant="outline">
                {col}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Preview Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Preview (first 5 rows)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  {headers.map((header, i) => (
                    <th key={i} className="p-2 text-left font-medium">
                      {header}
                      {requiredColumns.includes(header) && (
                        <span className="text-red-500 ml-1">*</span>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, rowIndex) => (
                  <tr key={rowIndex} className="border-b">
                    {row.map((cell, cellIndex) => (
                      <td key={cellIndex} className="p-2 text-gray-600 max-w-xs truncate">
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function parseCsvPreview(file: File): Promise<{ headers: string[]; rows: string[][] }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const lines = text.split('\n').filter(line => line.trim());

        if (lines.length === 0) {
          reject(new Error('CSV file is empty'));
          return;
        }

        // Parse headers (first line)
        const headers = parseCsvLine(lines[0]);

        // Parse up to 5 data rows
        const rows = lines.slice(1, 6).map(line => parseCsvLine(line));

        resolve({ headers, rows });
      } catch (err) {
        reject(err);
      }
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
}

function parseCsvLine(line: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  result.push(current.trim());

  return result;
}
