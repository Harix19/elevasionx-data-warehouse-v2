const TOKEN_KEY = 'access_token';

export const tokenStorage = {
  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    
    // First try localStorage as fallback
    const localToken = localStorage.getItem(TOKEN_KEY);
    if (localToken) return localToken;
    
    // Then try cookies
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${TOKEN_KEY}=`);
    if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
    return null;
  },

  setToken(token: string): void {
    if (typeof window === 'undefined') return;
    
    // Set both localStorage and cookie for redundancy
    localStorage.setItem(TOKEN_KEY, token);
    
    // Set cookie (Secure only on HTTPS to allow localhost development)
    const isHttps = typeof window !== 'undefined' && window.location.protocol === 'https:';
    const secureFlag = isHttps ? 'Secure;' : '';
    document.cookie = `${TOKEN_KEY}=${token}; path=/; max-age=86400; SameSite=Lax; ${secureFlag}`;
    
    if (process.env.NODE_ENV === 'development') {
      console.log('[Auth] Token stored');
    }
  },

  removeToken(): void {
    if (typeof window === 'undefined') return;
    
    // Remove from both
    localStorage.removeItem(TOKEN_KEY);
    
    const isHttps = typeof window !== 'undefined' && window.location.protocol === 'https:';
    const secureFlag = isHttps ? 'Secure;' : '';
    document.cookie = `${TOKEN_KEY}=; path=/; max-age=0; SameSite=Lax; ${secureFlag}`;
    
    if (process.env.NODE_ENV === 'development') {
      console.log('[Auth] Token removed');
    }
  },

  isAuthenticated(): boolean {
    const token = this.getToken();
    if (process.env.NODE_ENV === 'development') {
      console.log('[Auth] Auth check, token exists:', !!token);
    }
    return !!token;
  },
};
