// Setup JSDOM BEFORE importing @testing-library/react
import { JSDOM } from 'jsdom';

const jsdom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
  url: 'http://localhost:3000',
});

Object.defineProperty(global, 'window', {
  value: jsdom.window as any,
  writable: true,
});

Object.defineProperty(global, 'document', {
  value: jsdom.window.document as any,
  writable: true,
});

Object.defineProperty(global, 'navigator', {
  value: jsdom.window.navigator as any,
  writable: true,
});

Object.defineProperty(global, 'HTMLElement', {
  value: jsdom.window.HTMLElement as any,
  writable: true,
});

Object.defineProperty(global, 'HTMLAnchorElement', {
  value: jsdom.window.HTMLAnchorElement as any,
  writable: true,
});

import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
