import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError, map } from 'rxjs';
import { ApiService } from './api.service';
import { User, UserRole, mapApiRole } from '../models/user.model';
import { PaginatedResponse, QueryParams } from '../models';

export interface CreateUserDto {
  email: string;
  password?: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  phone?: string;
  company?: string;
  isActive?: boolean;
}

export interface UpdateUserDto {
  email?: string;
  firstName?: string;
  lastName?: string;
  role?: UserRole;
  phone?: string;
  company?: string;
  isActive?: boolean;
}

/** Maps frontend UserRole enum values to backend integer role IDs */
const ROLE_TO_BACKEND: Record<string, number> = {
  [UserRole.ADMIN]: 0,
  [UserRole.TENDER_MANAGER]: 1,
  [UserRole.COMMERCIAL_ANALYST]: 2,
  [UserRole.TECHNICAL_PANELIST]: 3,
  [UserRole.APPROVER]: 4,
  [UserRole.AUDITOR]: 5,
  [UserRole.BIDDER]: 6,
  [UserRole.VIEWER]: 5, // Viewer doesn't exist in backend, map to Auditor (5)
};

export interface UserQueryParams extends QueryParams {
  role?: UserRole;
  isActive?: boolean;
  search?: string;
}

/** Maps a raw backend user object to the frontend User model */
function mapApiUser(raw: any): User {
  return {
    id: raw.id ?? raw.Id,
    email: raw.email ?? raw.Email ?? '',
    firstName: raw.firstName ?? raw.FirstName ?? '',
    lastName: raw.lastName ?? raw.LastName ?? '',
    role: mapApiRole(raw.role ?? raw.Role ?? 6),
    isActive: raw.isActive ?? raw.IsActive ?? true,
    createdAt: raw.createdAt ?? raw.CreatedAt,
    updatedAt: raw.updatedAt ?? raw.UpdatedAt,
    lastLogin: raw.lastLoginAt ?? raw.LastLoginAt ?? raw.lastLogin ?? undefined,
    phone: raw.phoneNumber ?? raw.PhoneNumber ?? raw.phone ?? undefined,
    company: raw.companyName ?? raw.CompanyName ?? raw.company ?? undefined,
    avatar: raw.profilePictureUrl ?? raw.ProfilePictureUrl ?? undefined
  };
}

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private readonly api = inject(ApiService);
  private readonly endpoint = '/admin/users';

  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  getUsers(params?: UserQueryParams): Observable<PaginatedResponse<User>> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.getList<any>(this.endpoint, params).pipe(
      map(response => ({
        ...response,
        items: (response.items || []).map(mapApiUser)
      })),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load users');
        return throwError(() => error);
      })
    );
  }

  getUserById(id: number | string): Observable<User> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<any>(`${this.endpoint}/${id}`).pipe(
      map(raw => mapApiUser(raw)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load user');
        return throwError(() => error);
      })
    );
  }

  createUser(data: CreateUserDto): Observable<User> {
    this._isLoading.set(true);
    this._error.set(null);

    // Transform frontend DTO to match backend CreateUserRequest
    const backendPayload = {
      firstName: data.firstName,
      lastName: data.lastName,
      email: data.email,
      role: ROLE_TO_BACKEND[data.role] ?? 5,
      phone: data.phone || null,
      companyName: data.company || null,
      sendInvitationEmail: false
    };

    return this.api.post<any>(this.endpoint, backendPayload).pipe(
      map(result => mapApiUser({
        email: data.email,
        firstName: data.firstName,
        lastName: data.lastName,
        role: data.role,
        isActive: true,
        phone: data.phone,
        companyName: data.company,
        ...result
      })),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to create user');
        return throwError(() => error);
      })
    );
  }

  updateUser(id: number | string, data: UpdateUserDto): Observable<User> {
    this._isLoading.set(true);
    this._error.set(null);

    // Transform frontend DTO to match backend UpdateUserRequest
    const backendPayload = {
      firstName: data.firstName,
      lastName: data.lastName,
      email: data.email,
      role: data.role ? (ROLE_TO_BACKEND[data.role] ?? undefined) : undefined,
      phone: data.phone || null,
      companyName: data.company || null
    };

    return this.api.put<any>(`${this.endpoint}/${id}`, backendPayload).pipe(
      map(() => ({
        id: typeof id === 'string' ? id : id,
        ...data,
        updatedAt: new Date()
      } as unknown as User)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update user');
        return throwError(() => error);
      })
    );
  }

  deleteUser(id: number | string): Observable<void> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.delete<void>(`${this.endpoint}/${id}`).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to delete user');
        return throwError(() => error);
      })
    );
  }

  toggleUserStatus(id: number | string): Observable<any> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<any>(`${this.endpoint}/${id}/toggle-active`, {}).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to toggle user status');
        return throwError(() => error);
      })
    );
  }

  clearError(): void {
    this._error.set(null);
  }
}
