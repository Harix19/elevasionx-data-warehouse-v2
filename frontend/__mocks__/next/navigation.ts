import { vi } from 'vitest';

export const useRouter = () => ({
  push: vi.fn(),
  replace: vi.fn(),
  prefetch: vi.fn(),
  back: vi.fn(),
  pathname: '/',
  query: {},
  asPath: '/',
});

export const useSearchParams = () => new URLSearchParams();

export const useParams = () => ({});

export const usePathname = () => '/';
