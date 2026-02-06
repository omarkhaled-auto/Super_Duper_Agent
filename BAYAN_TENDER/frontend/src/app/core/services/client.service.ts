import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { ApiService } from './api.service';
import { Client, CreateClientDto, UpdateClientDto } from '../models/client.model';
import { PaginatedResponse, QueryParams } from '../models';

export interface ClientQueryParams extends QueryParams {
  isActive?: boolean;
  search?: string;
  city?: string;
  country?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ClientService {
  private readonly api = inject(ApiService);
  private readonly endpoint = '/clients';

  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  getClients(params?: ClientQueryParams): Observable<PaginatedResponse<Client>> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.getList<Client>(this.endpoint, params).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load clients');
        return throwError(() => error);
      })
    );
  }

  getClientById(id: number): Observable<Client> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<Client>(`${this.endpoint}/${id}`).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load client');
        return throwError(() => error);
      })
    );
  }

  createClient(data: CreateClientDto): Observable<Client> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<Client>(this.endpoint, data).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to create client');
        return throwError(() => error);
      })
    );
  }

  updateClient(id: number, data: UpdateClientDto): Observable<Client> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.put<Client>(`${this.endpoint}/${id}`, data).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update client');
        return throwError(() => error);
      })
    );
  }

  deleteClient(id: number): Observable<void> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.delete<void>(`${this.endpoint}/${id}`).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to delete client');
        return throwError(() => error);
      })
    );
  }

  toggleClientStatus(id: number, isActive: boolean): Observable<Client> {
    return this.updateClient(id, { isActive });
  }

  clearError(): void {
    this._error.set(null);
  }
}
