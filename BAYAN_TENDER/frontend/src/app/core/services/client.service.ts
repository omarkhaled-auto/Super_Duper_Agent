import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError, map } from 'rxjs';
import { ApiService } from './api.service';
import { Client, CreateClientDto, UpdateClientDto } from '../models/client.model';
import { PaginatedResponse, QueryParams } from '../models';

export interface ClientQueryParams extends QueryParams {
  isActive?: boolean;
  search?: string;
  city?: string;
  country?: string;
}

/** Maps a raw backend client object to the frontend Client model */
function mapApiClient(raw: any): Client {
  return {
    id: raw.id ?? raw.Id,
    name: raw.name ?? raw.Name ?? '',
    nameAr: raw.nameAr ?? raw.NameAr ?? undefined,
    email: raw.email ?? raw.Email ?? '',
    phone: raw.phone ?? raw.Phone ?? undefined,
    address: raw.address ?? raw.Address ?? undefined,
    city: raw.city ?? raw.City ?? undefined,
    country: raw.country ?? raw.Country ?? undefined,
    crNumber: raw.crNumber ?? raw.CRNumber ?? raw.cRNumber ?? undefined,
    vatNumber: raw.vatNumber ?? raw.VatNumber ?? undefined,
    contactPerson: raw.contactPerson ?? raw.ContactPerson ?? undefined,
    contactEmail: raw.contactEmail ?? raw.ContactEmail ?? undefined,
    contactPhone: raw.contactPhone ?? raw.ContactPhone ?? raw.phone ?? raw.Phone ?? undefined,
    isActive: raw.isActive ?? raw.IsActive ?? true,
    createdAt: raw.createdAt ?? raw.CreatedAt,
    updatedAt: raw.updatedAt ?? raw.UpdatedAt,
    tendersCount: raw.tendersCount ?? raw.tenderCount ?? raw.TenderCount ?? 0,
    totalContractValue: raw.totalContractValue ?? raw.TotalContractValue ?? 0
  };
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

    return this.api.getList<any>(this.endpoint, params).pipe(
      map(response => ({
        ...response,
        items: (response.items || []).map(mapApiClient)
      })),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load clients');
        return throwError(() => error);
      })
    );
  }

  getClientById(id: number | string): Observable<Client> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<any>(`${this.endpoint}/${id}`).pipe(
      map(raw => mapApiClient(raw)),
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

    return this.api.post<any>(this.endpoint, data).pipe(
      map(raw => mapApiClient({ ...data, ...raw })),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to create client');
        return throwError(() => error);
      })
    );
  }

  updateClient(id: number | string, data: UpdateClientDto): Observable<Client> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.put<any>(`${this.endpoint}/${id}`, data).pipe(
      map(raw => mapApiClient({ id, ...data, ...raw })),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update client');
        return throwError(() => error);
      })
    );
  }

  deleteClient(id: number | string): Observable<void> {
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

  toggleClientStatus(id: number | string, isActive: boolean): Observable<Client> {
    return this.updateClient(id, { isActive });
  }

  clearError(): void {
    this._error.set(null);
  }
}
