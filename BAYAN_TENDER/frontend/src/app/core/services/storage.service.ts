import { Injectable, PLATFORM_ID, inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

@Injectable({
  providedIn: 'root'
})
export class StorageService {
  private readonly platformId = inject(PLATFORM_ID);
  private readonly isBrowser = isPlatformBrowser(this.platformId);

  private readonly ACCESS_TOKEN_KEY = 'bayan_access_token';
  private readonly REFRESH_TOKEN_KEY = 'bayan_refresh_token';
  private readonly USER_KEY = 'bayan_user';
  private readonly REMEMBER_ME_KEY = 'bayan_remember_me';

  // Generic storage methods
  setItem(key: string, value: string, useSession = false): void {
    if (!this.isBrowser) return;
    const storage = useSession ? sessionStorage : localStorage;
    storage.setItem(key, value);
  }

  getItem(key: string, useSession = false): string | null {
    if (!this.isBrowser) return null;
    const storage = useSession ? sessionStorage : localStorage;
    return storage.getItem(key);
  }

  removeItem(key: string, useSession = false): void {
    if (!this.isBrowser) return;
    const storage = useSession ? sessionStorage : localStorage;
    storage.removeItem(key);
  }

  setObject<T>(key: string, value: T, useSession = false): void {
    this.setItem(key, JSON.stringify(value), useSession);
  }

  getObject<T>(key: string, useSession = false): T | null {
    const item = this.getItem(key, useSession);
    if (!item) return null;
    try {
      return JSON.parse(item) as T;
    } catch {
      return null;
    }
  }

  clear(useSession = false): void {
    if (!this.isBrowser) return;
    const storage = useSession ? sessionStorage : localStorage;
    storage.clear();
  }

  // Auth-specific methods
  setAccessToken(token: string): void {
    const useSession = !this.getRememberMe();
    this.setItem(this.ACCESS_TOKEN_KEY, token, useSession);
  }

  getAccessToken(): string | null {
    return this.getItem(this.ACCESS_TOKEN_KEY, false) ||
           this.getItem(this.ACCESS_TOKEN_KEY, true);
  }

  removeAccessToken(): void {
    this.removeItem(this.ACCESS_TOKEN_KEY, false);
    this.removeItem(this.ACCESS_TOKEN_KEY, true);
  }

  setRefreshToken(token: string): void {
    const useSession = !this.getRememberMe();
    this.setItem(this.REFRESH_TOKEN_KEY, token, useSession);
  }

  getRefreshToken(): string | null {
    return this.getItem(this.REFRESH_TOKEN_KEY, false) ||
           this.getItem(this.REFRESH_TOKEN_KEY, true);
  }

  removeRefreshToken(): void {
    this.removeItem(this.REFRESH_TOKEN_KEY, false);
    this.removeItem(this.REFRESH_TOKEN_KEY, true);
  }

  setUser<T>(user: T): void {
    const useSession = !this.getRememberMe();
    this.setObject(this.USER_KEY, user, useSession);
  }

  getUser<T>(): T | null {
    return this.getObject<T>(this.USER_KEY, false) ||
           this.getObject<T>(this.USER_KEY, true);
  }

  removeUser(): void {
    this.removeItem(this.USER_KEY, false);
    this.removeItem(this.USER_KEY, true);
  }

  setRememberMe(value: boolean): void {
    this.setItem(this.REMEMBER_ME_KEY, String(value), false);
  }

  getRememberMe(): boolean {
    return this.getItem(this.REMEMBER_ME_KEY, false) === 'true';
  }

  clearAuthData(): void {
    this.removeAccessToken();
    this.removeRefreshToken();
    this.removeUser();
  }
}
