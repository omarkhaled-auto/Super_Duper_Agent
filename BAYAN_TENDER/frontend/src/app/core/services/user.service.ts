import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError, map } from 'rxjs';
import { ApiService } from './api.service';
import { User, UserRole } from '../models/user.model';
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

    return this.api.getList<User>(this.endpoint, params).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load users');
        return throwError(() => error);
      })
    );
  }

  getUserById(id: number): Observable<User> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<User>(`${this.endpoint}/${id}`).pipe(
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
      map(result => ({
        id: 0,
        email: data.email,
        firstName: data.firstName,
        lastName: data.lastName,
        role: data.role,
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date(),
        ...result
      } as User)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to create user');
        return throwError(() => error);
      })
    );
  }

  updateUser(id: number, data: UpdateUserDto): Observable<User> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.put<User>(`${this.endpoint}/${id}`, data).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update user');
        return throwError(() => error);
      })
    );
  }

  deleteUser(id: number): Observable<void> {
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

  toggleUserStatus(id: number, isActive: boolean): Observable<User> {
    return this.updateUser(id, { isActive });
  }

  clearError(): void {
    this._error.set(null);
  }
}
