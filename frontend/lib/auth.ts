const TOKEN_KEY = 'access_token';

const getCookie = (name: string): string | null => {
  if (typeof document === 'undefined') return null;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
  return null;
};

export const tokenStorage = {
  getToken(): string | null {
    return getCookie(TOKEN_KEY);
  },

  setToken(token: string): void {
    if (typeof window === 'undefined') return;
    // Set cookie (Secure and SameSite=Strict recommended)
    // Note: HttpOnly can only be set by the server, but we can set the cookie from JS
    // if the server doesn't do it. If the server sets it as HttpOnly, this JS set 
    // will be ignored/overwritten by the server's header if configured correctly.
    document.cookie = `${TOKEN_KEY}=${token}; path=/; max-age=86400; SameSite=Strict; Secure`;
  },

  removeToken(): void {
    if (typeof window === 'undefined') return;
    // Remove cookie by setting max-age to 0
    document.cookie = `${TOKEN_KEY}=; path=/; max-age=0; SameSite=Strict; Secure`;
  },

  isAuthenticated(): boolean {
    return !!this.getToken();
  },
};
