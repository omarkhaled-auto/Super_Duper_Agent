import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError, map } from 'rxjs';
import { ApiService } from './api.service';
import {
  Bidder,
  CreateBidderDto,
  UpdateBidderDto,
  TenderBidder,
  BidderQueryParams,
  InviteBiddersDto,
  PrequalificationStatus,
  NdaStatus,
  TradeSpecialization
} from '../models/bidder.model';
import { PaginatedResponse } from '../models';

/** Maps backend integer prequalification status to frontend string enum */
const PREQUAL_FROM_BACKEND: Record<number, PrequalificationStatus> = {
  0: PrequalificationStatus.PENDING,
  1: PrequalificationStatus.APPROVED,   // Backend: "Qualified"
  2: PrequalificationStatus.REJECTED
};

/** Maps frontend string enum to backend integer */
const PREQUAL_TO_BACKEND: Record<string, number> = {
  [PrequalificationStatus.PENDING]: 0,
  [PrequalificationStatus.APPROVED]: 1,
  [PrequalificationStatus.REJECTED]: 2
};

/** Converts a backend bidder API object to the frontend Bidder model */
function mapApiBidder(raw: any): Bidder {
  const tradeSpec = raw.tradeSpecialization || raw.TradeSpecialization || '';
  const specs: TradeSpecialization[] = tradeSpec
    ? tradeSpec.split(',').map((s: string) => s.trim().toLowerCase()).filter(Boolean) as TradeSpecialization[]
    : [];

  const prequalRaw = raw.prequalificationStatus ?? raw.PrequalificationStatus ?? 0;
  const prequal = typeof prequalRaw === 'number'
    ? (PREQUAL_FROM_BACKEND[prequalRaw] || PrequalificationStatus.PENDING)
    : prequalRaw;

  return {
    id: raw.id || raw.Id,
    companyNameEn: raw.companyName || raw.CompanyName || '',
    companyNameAr: raw.companyNameAr || raw.CompanyNameAr || undefined,
    email: raw.email || raw.Email || '',
    phone: raw.phone || raw.Phone || undefined,
    crNumber: raw.crNumber || raw.CRNumber || raw.cRNumber || undefined,
    address: raw.address || raw.Address || undefined,
    tradeSpecializations: specs,
    prequalificationStatus: prequal,
    ndaStatus: raw.ndaStatus || NdaStatus.NOT_SENT,
    contactPersonName: raw.contactPerson || raw.ContactPerson || undefined,
    contactPersonEmail: raw.contactPersonEmail || undefined,
    contactPersonPhone: raw.contactPersonPhone || raw.phone || undefined,
    isActive: raw.isActive ?? raw.IsActive ?? true,
    createdAt: raw.createdAt || raw.CreatedAt,
    updatedAt: raw.updatedAt || raw.UpdatedAt,
    tendersCount: raw.tenderCount ?? raw.tendersCount ?? 0,
    activeTendersCount: raw.activeTendersCount ?? 0
  };
}

/** Converts frontend create/update DTO to backend payload shape */
function mapBidderToBackend(data: CreateBidderDto | UpdateBidderDto): any {
  const payload: any = {};
  if ('companyNameEn' in data && data.companyNameEn !== undefined) payload.companyName = data.companyNameEn;
  if ('email' in data && data.email !== undefined) payload.email = data.email;
  if ('phone' in data && data.phone !== undefined) payload.phone = data.phone;
  if ('crNumber' in data && data.crNumber !== undefined) payload.crNumber = data.crNumber;
  if ('contactPersonName' in data && data.contactPersonName !== undefined) payload.contactPerson = data.contactPersonName;
  if ('tradeSpecializations' in data && data.tradeSpecializations !== undefined) {
    payload.tradeSpecialization = data.tradeSpecializations.join(',');
  }
  if ('prequalificationStatus' in data && data.prequalificationStatus !== undefined) {
    payload.prequalificationStatus = PREQUAL_TO_BACKEND[data.prequalificationStatus] ?? 0;
  }
  if ('isActive' in data && (data as UpdateBidderDto).isActive !== undefined) {
    payload.isActive = (data as UpdateBidderDto).isActive;
  }
  return payload;
}

@Injectable({
  providedIn: 'root'
})
export class BidderService {
  private readonly api = inject(ApiService);
  private readonly endpoint = '/bidders';

  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  /**
   * Get paginated list of bidders with optional filters
   */
  getBidders(params?: BidderQueryParams): Observable<PaginatedResponse<Bidder>> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.getList<any>(this.endpoint, params).pipe(
      map(response => ({
        ...response,
        items: (response.items || []).map(mapApiBidder)
      })),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load bidders');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get a single bidder by ID
   */
  getBidder(id: number | string): Observable<Bidder> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<any>(`${this.endpoint}/${id}`).pipe(
      map(raw => mapApiBidder(raw)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load bidder');
        return throwError(() => error);
      })
    );
  }

  /**
   * Create a new bidder
   */
  createBidder(data: CreateBidderDto): Observable<Bidder> {
    this._isLoading.set(true);
    this._error.set(null);

    const backendPayload = mapBidderToBackend(data);

    return this.api.post<any>(this.endpoint, backendPayload).pipe(
      map(raw => mapApiBidder({ ...backendPayload, ...raw })),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to create bidder');
        return throwError(() => error);
      })
    );
  }

  /**
   * Update an existing bidder
   */
  updateBidder(id: number | string, data: UpdateBidderDto): Observable<Bidder> {
    this._isLoading.set(true);
    this._error.set(null);

    const backendPayload = mapBidderToBackend(data);

    return this.api.put<any>(`${this.endpoint}/${id}`, backendPayload).pipe(
      map(raw => mapApiBidder({ id, ...backendPayload, ...raw })),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update bidder');
        return throwError(() => error);
      })
    );
  }

  /**
   * Delete a bidder
   */
  deleteBidder(id: number | string): Observable<void> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.delete<void>(`${this.endpoint}/${id}`).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to delete bidder');
        return throwError(() => error);
      })
    );
  }

  /**
   * Toggle bidder active status
   */
  toggleBidderStatus(id: number | string, isActive: boolean): Observable<Bidder> {
    return this.updateBidder(id, { isActive });
  }

  /**
   * Invite bidders to a specific tender
   */
  inviteBiddersToTender(tenderId: number | string, bidderIds: (number | string)[]): Observable<any> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<any>(`/tenders/${tenderId}/invite`, bidderIds).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to invite bidders');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get all bidders invited to a specific tender
   */
  getTenderBidders(tenderId: number): Observable<TenderBidder[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<TenderBidder[]>(`/tenders/${tenderId}/bidders`).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load tender bidders');
        return throwError(() => error);
      })
    );
  }

  /**
   * Remove a bidder from a tender
   */
  removeTenderBidder(tenderId: number, bidderId: number): Observable<void> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.delete<void>(`/tenders/${tenderId}/bidders/${bidderId}`).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to remove bidder from tender');
        return throwError(() => error);
      })
    );
  }

  /**
   * Resend invitation to a bidder for a tender
   */
  resendInvitation(tenderId: number, bidderId: number): Observable<TenderBidder> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<TenderBidder>(`/tenders/${tenderId}/bidders/${bidderId}/resend-invitation`, {}).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to resend invitation');
        return throwError(() => error);
      })
    );
  }

  /**
   * Check if CR Number already exists (for validation)
   */
  checkCrNumberExists(crNumber: string, excludeId?: number): Observable<boolean> {
    const params: Record<string, string | number> = { crNumber };
    if (excludeId) {
      params['excludeId'] = excludeId;
    }
    return this.api.get<boolean>(`${this.endpoint}/check-cr-number`, params);
  }

  /**
   * Clear current error state
   */
  clearError(): void {
    this._error.set(null);
  }
}
