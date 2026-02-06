import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { ApiService } from './api.service';
import { User, UserRole } from '../models/user.model';
import { PaginatedResponse, QueryParams } from '../models';

export interface CreateUserDto {
  email: string;
  password: string;
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
  private readonly endpoint = '/users';

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

    return this.api.post<User>(this.endpoint, data).pipe(
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
