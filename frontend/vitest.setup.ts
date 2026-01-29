import { JSDOM } from 'jsdom';
import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

// Setup JSDOM BEFORE importing @testing-library/react
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

// Clean up after each test
afterEach(() => {
  cleanup();
});

// Mock next/navigation BEFORE any imports
const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  prefetch: vi.fn(),
  back: vi.fn(),
  pathname: '/',
  query: {},
  asPath: '/',
};

vi.mock('next/navigation', () => ({
  useRouter: () => mockRouter,
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({}),
  usePathname: () => '/',
}));

// Mock @tanstack/react-query
vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...(actual as any),
    useQueryClient: () => ({
      invalidateQueries: vi.fn(),
    }),
  };
});

// Mock next/font/google
vi.mock('next/font/google', () => ({
  Inter: () => ({
    variable: '--font-inter',
    className: 'inter-font',
  }),
  JetBrains_Mono: () => ({
    variable: '--font-jetbrains-mono',
    className: 'jetbrains-mono-font',
  }),
}));
