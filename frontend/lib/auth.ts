const TOKEN_KEY = 'access_token';

export const tokenStorage = {
  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(TOKEN_KEY);
  },

  setToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(TOKEN_KEY, token);
    // Also set cookie for middleware (httpOnly for security)
    document.cookie = `access_token=${token}; path=/; max-age=86400; SameSite=Strict`;
  },

  removeToken(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(TOKEN_KEY);
    // Also remove cookie
    document.cookie = 'access_token=; path=/; max-age=0; SameSite=Strict';
  },

  isAuthenticated(): boolean {
    return !!this.getToken();
  },
};
