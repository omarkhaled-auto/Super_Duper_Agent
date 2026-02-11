import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError, map, switchMap } from 'rxjs';
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
    contactPhone: raw.contactPhone ?? raw.ContactPhone ?? undefined,
    isActive: raw.isActive ?? raw.IsActive ?? true,
    createdAt: raw.createdAt ?? raw.CreatedAt,
    updatedAt: raw.updatedAt ?? raw.UpdatedAt,
    tendersCount: raw.tenderCount ?? raw.TenderCount ?? raw.tendersCount ?? 0,
    totalContractValue: raw.totalContractValue ?? raw.TotalContractValue ?? 0
  };
}

/** Converts frontend create/update DTO to backend payload shape */
function mapClientToBackend(data: CreateClientDto | UpdateClientDto): any {
  const payload: any = {};
  if ('name' in data && data.name !== undefined) payload.name = data.name;
  if ('email' in data && data.email !== undefined) payload.email = data.email;
  if ('phone' in data && data.phone !== undefined) payload.phone = data.phone || null;
  if ('address' in data && data.address !== undefined) payload.address = data.address || null;
  if ('city' in data && data.city !== undefined) payload.city = data.city || null;
  if ('country' in data && data.country !== undefined) payload.country = data.country || null;
  if ('crNumber' in data && data.crNumber !== undefined) payload.crNumber = data.crNumber || null;
  if ('vatNumber' in data && data.vatNumber !== undefined) payload.vatNumber = data.vatNumber || null;
  if ('contactPerson' in data && data.contactPerson !== undefined) payload.contactPerson = data.contactPerson || null;
  if ('contactEmail' in data && data.contactEmail !== undefined) payload.contactEmail = data.contactEmail || null;
  if ('contactPhone' in data && data.contactPhone !== undefined) payload.contactPhone = data.contactPhone || null;
  if ('isActive' in data && (data as UpdateClientDto).isActive !== undefined) {
    payload.isActive = (data as UpdateClientDto).isActive;
  }
  return payload;
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

    const backendPayload = mapClientToBackend(data);

    return this.api.post<any>(this.endpoint, backendPayload).pipe(
      switchMap(raw => {
        const id = raw?.id ?? raw?.Id;
        if (id) {
          return this.api.get<any>(`${this.endpoint}/${id}`).pipe(
            map(fresh => mapApiClient(fresh))
          );
        }
        return [mapApiClient({ ...backendPayload, ...raw })];
      }),
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

    const backendPayload = mapClientToBackend(data);

    return this.api.put<any>(`${this.endpoint}/${id}`, backendPayload).pipe(
      switchMap(() => this.api.get<any>(`${this.endpoint}/${id}`)),
      map(raw => mapApiClient(raw)),
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
