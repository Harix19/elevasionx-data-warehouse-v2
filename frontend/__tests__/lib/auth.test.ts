import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { tokenStorage } from '@/lib/auth';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value.toString(); },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

// Mock window and document
Object.defineProperty(global, 'window', {
  value: {
    localStorage: localStorageMock,
  },
  writable: true,
});

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
});

let mockCookie = '';
Object.defineProperty(global, 'document', {
  value: {
    cookie: mockCookie,
  },
  writable: true,
});

describe('tokenStorage', () => {
  beforeEach(() => {
    localStorage.clear();
    mockCookie = '';
  });

  afterEach(() => {
    localStorage.clear();
    mockCookie = '';
  });

  describe('getToken', () => {
    it('should return null when no token is stored', () => {
      expect(tokenStorage.getToken()).toBeNull();
    });

    it('should return the token when stored', () => {
      localStorage.setItem('access_token', 'test-token');
      expect(tokenStorage.getToken()).toBe('test-token');
    });
  });

  describe('setToken', () => {
    it('should store token in localStorage', () => {
      tokenStorage.setToken('test-token');
      expect(localStorage.getItem('access_token')).toBe('test-token');
    });

    it('should set cookie for middleware', () => {
      tokenStorage.setToken('test-token');
      expect(document.cookie).toContain('access_token=test-token');
    });
  });

  describe('removeToken', () => {
    it('should remove token from localStorage', () => {
      localStorage.setItem('access_token', 'test-token');
      tokenStorage.removeToken();
      expect(localStorage.getItem('access_token')).toBeNull();
    });

    it('should clear cookie', () => {
      tokenStorage.setToken('test-token');
      tokenStorage.removeToken();
      expect(document.cookie).toContain('access_token=');
      expect(document.cookie).toContain('max-age=0');
    });
  });

  describe('isAuthenticated', () => {
    it('should return false when no token', () => {
      expect(tokenStorage.isAuthenticated()).toBe(false);
    });

    it('should return true when token exists', () => {
      tokenStorage.setToken('test-token');
      expect(tokenStorage.isAuthenticated()).toBe(true);
    });

    it('should return false when token is removed', () => {
      tokenStorage.setToken('test-token');
      tokenStorage.removeToken();
      expect(tokenStorage.isAuthenticated()).toBe(false);
    });
  });
});
