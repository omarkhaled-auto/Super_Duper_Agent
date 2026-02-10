import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, throwError, BehaviorSubject, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { StorageService } from '../services/storage.service';
import {
  User,
  LoginCredentials,
  LoginResponse,
  RegisterData,
  PasswordResetRequest,
  PasswordResetConfirm,
  mapApiRole
} from '../models/user.model';
import { ApiResponse } from '../models/api-response.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly storage = inject(StorageService);
  private readonly apiUrl = `${environment.apiUrl}/auth`;

  // Signals for reactive state
  private readonly _currentUser = signal<User | null>(null);
  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  // Public readonly signals
  readonly currentUser = this._currentUser.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();
  readonly isAuthenticated = computed(() => this._currentUser() !== null);
  readonly userRole = computed(() => this._currentUser()?.role);

  // Token refresh subject for handling concurrent requests
  private refreshTokenSubject = new BehaviorSubject<string | null>(null);
  private isRefreshing = false;

  constructor() {
    this.loadUserFromStorage();
  }

  private loadUserFromStorage(): void {
    const user = this.storage.getUser<User>();
    if (user && this.storage.getAccessToken()) {
      // Ensure role is mapped correctly (handles stale storage with numeric roles)
      const mappedUser = { ...user, role: mapApiRole(user.role as any) };
      this._currentUser.set(mappedUser);
    }
  }

  login(credentials: LoginCredentials): Observable<LoginResponse> {
    this._isLoading.set(true);
    this._error.set(null);

    if (credentials.rememberMe !== undefined) {
      this.storage.setRememberMe(credentials.rememberMe);
    }

    return this.http.post<ApiResponse<LoginResponse>>(`${this.apiUrl}/login`, credentials).pipe(
      tap(response => {
        const data = response.data;
        this.handleAuthSuccess(data);
        this._isLoading.set(false);
      }),
      map(response => response.data),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.error?.message || 'Login failed');
        return throwError(() => error);
      })
    );
  }

  register(data: RegisterData): Observable<LoginResponse> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.http.post<ApiResponse<LoginResponse>>(`${this.apiUrl}/register`, data).pipe(
      tap(response => {
        const authData = response.data;
        this.handleAuthSuccess(authData);
        this._isLoading.set(false);
      }),
      map(response => response.data),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.error?.message || 'Registration failed');
        return throwError(() => error);
      })
    );
  }

  logout(): void {
    this.http.post(`${this.apiUrl}/logout`, {}).pipe(
      catchError(() => {
        // Even if logout fails on server, clear local data
        return throwError(() => new Error('Logout failed'));
      })
    ).subscribe({
      complete: () => this.handleLogout(),
      error: () => this.handleLogout()
    });
  }

  private handleLogout(): void {
    this.storage.clearAuthData();
    this._currentUser.set(null);
    this._error.set(null);
    this.router.navigate(['/auth/login']);
  }

  private handleAuthSuccess(data: LoginResponse): void {
    this.storage.setAccessToken(data.accessToken);
    this.storage.setRefreshToken(data.refreshToken);
    // Map numeric role from API to string enum
    const user = { ...data.user, role: mapApiRole(data.user.role as any) };
    this.storage.setUser(user);
    this._currentUser.set(user);
  }

  refreshToken(): Observable<{ accessToken: string; refreshToken: string }> {
    const refreshToken = this.storage.getRefreshToken();
    if (!refreshToken) {
      return throwError(() => new Error('No refresh token available'));
    }

    return this.http.post<ApiResponse<{ accessToken: string; refreshToken: string }>>(
      `${this.apiUrl}/refresh`,
      { refreshToken }
    ).pipe(
      tap(response => {
        this.storage.setAccessToken(response.data.accessToken);
        this.storage.setRefreshToken(response.data.refreshToken);
        this.refreshTokenSubject.next(response.data.accessToken);
      }),
      map(response => response.data),
      catchError(error => {
        this.handleLogout();
        return throwError(() => error);
      })
    );
  }

  forgotPassword(data: PasswordResetRequest): Observable<{ message: string }> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.http.post<ApiResponse<{ message: string }>>(`${this.apiUrl}/forgot-password`, data).pipe(
      tap(() => this._isLoading.set(false)),
      map(response => response.data),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.error?.message || 'Failed to send reset email');
        return throwError(() => error);
      })
    );
  }

  resetPassword(data: PasswordResetConfirm): Observable<{ message: string }> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.http.post<ApiResponse<{ message: string }>>(`${this.apiUrl}/reset-password`, data).pipe(
      tap(() => this._isLoading.set(false)),
      map(response => response.data),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.error?.message || 'Password reset failed');
        return throwError(() => error);
      })
    );
  }

  getAccessToken(): string | null {
    return this.storage.getAccessToken();
  }

  hasRole(role: string | string[]): boolean {
    const user = this._currentUser();
    if (!user) return false;

    const roles = Array.isArray(role) ? role : [role];
    return roles.includes(user.role);
  }

  clearError(): void {
    this._error.set(null);
  }
}
