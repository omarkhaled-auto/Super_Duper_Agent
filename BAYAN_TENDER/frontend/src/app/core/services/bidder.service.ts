import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { ApiService } from './api.service';
import {
  Bidder,
  CreateBidderDto,
  UpdateBidderDto,
  TenderBidder,
  BidderQueryParams,
  InviteBiddersDto
} from '../models/bidder.model';
import { PaginatedResponse } from '../models';

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

    return this.api.getList<Bidder>(this.endpoint, params).pipe(
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
  getBidder(id: number): Observable<Bidder> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<Bidder>(`${this.endpoint}/${id}`).pipe(
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

    return this.api.post<Bidder>(this.endpoint, data).pipe(
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
  updateBidder(id: number, data: UpdateBidderDto): Observable<Bidder> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.put<Bidder>(`${this.endpoint}/${id}`, data).pipe(
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
  deleteBidder(id: number): Observable<void> {
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
  toggleBidderStatus(id: number, isActive: boolean): Observable<Bidder> {
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
