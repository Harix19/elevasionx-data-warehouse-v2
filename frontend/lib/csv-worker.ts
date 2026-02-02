/**
 * Web Worker for parsing CSV files off the main thread.
 * This prevents UI freezing when processing large files.
 */

import Papa from 'papaparse';

export interface CSVWorkerMessage {
  type: 'parse';
  fileContent: string;
}

export interface CSVWorkerResponse {
  type: 'success' | 'error';
  data?: any[];
  error?: string;
}

// Worker context
const ctx: Worker = self as any;

ctx.onmessage = (event: MessageEvent<CSVWorkerMessage>) => {
  const { type, fileContent } = event.data;

  if (type === 'parse') {
    try {
      const result = Papa.parse(fileContent, {
        header: true,
        skipEmptyLines: true,
        transformHeader: (header: string) => header.trim(),
      });

      if (result.errors.length > 0) {
        ctx.postMessage({
          type: 'error',
          error: `CSV parsing errors: ${result.errors.map(e => e.message).join(', ')}`,
        } as CSVWorkerResponse);
        return;
      }

      ctx.postMessage({
        type: 'success',
        data: result.data,
      } as CSVWorkerResponse);
    } catch (error: any) {
      ctx.postMessage({
        type: 'error',
        error: error.message || 'Unknown parsing error',
      } as CSVWorkerResponse);
    }
  }
};
