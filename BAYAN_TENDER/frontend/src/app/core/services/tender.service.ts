import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError, map } from 'rxjs';
import { ApiService } from './api.service';
import {
  Tender,
  TenderListItem,
  CreateTenderDto,
  UpdateTenderDto,
  TenderFilterParams,
  TenderInvitedBidder,
  TenderActivity,
  TenderStatus,
  TenderType
} from '../models/tender.model';
import { PaginatedResponse, PaginationParams } from '../models';

// Backend enum mappings (API returns numeric enums by default)
const TENDER_STATUS_MAP: Record<number, TenderStatus> = {
  0: 'draft',
  1: 'active',
  2: 'evaluation',
  3: 'awarded',
  4: 'cancelled'
};

const TENDER_TYPE_MAP: Record<number, TenderType> = {
  0: 'open',
  1: 'selective',
  2: 'negotiated'
};

const TENDER_TYPE_TO_API: Record<string, number> = {
  'open': 0,
  'selective': 1,
  'negotiated': 2
};

function mapTenderStatus(status: number | string): TenderStatus {
  if (typeof status === 'number') return TENDER_STATUS_MAP[status] ?? 'draft';
  const lower = String(status).toLowerCase();
  const valid: TenderStatus[] = ['draft', 'active', 'evaluation', 'awarded', 'closed', 'cancelled'];
  return valid.includes(lower as TenderStatus) ? lower as TenderStatus : 'draft';
}

function mapTenderType(type: number | string): TenderType {
  if (typeof type === 'number') return TENDER_TYPE_MAP[type] ?? 'open';
  const lower = String(type).toLowerCase();
  const valid: TenderType[] = ['open', 'selective', 'negotiated'];
  return valid.includes(lower as TenderType) ? lower as TenderType : 'open';
}

export interface TenderQueryParams extends PaginationParams, TenderFilterParams {}

@Injectable({
  providedIn: 'root'
})
export class TenderService {
  private readonly api = inject(ApiService);
  private readonly endpoint = '/tenders';

  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  getTenders(params?: TenderQueryParams): Observable<PaginatedResponse<TenderListItem>> {
    this._isLoading.set(true);
    this._error.set(null);

    // Map frontend params to backend query params
    const queryParams: Record<string, string | number | boolean> = {};
    if (params?.page) queryParams['page'] = params.page;
    if (params?.pageSize) queryParams['pageSize'] = params.pageSize;
    if (params?.search) queryParams['search'] = params.search;
    if (params?.status) {
      const statuses = Array.isArray(params.status) ? params.status : [params.status];
      queryParams['status'] = statuses[0];
    }
    if (params?.clientId) queryParams['clientId'] = params.clientId;
    if (params?.dateFrom) queryParams['dateFrom'] = params.dateFrom;
    if (params?.dateTo) queryParams['dateTo'] = params.dateTo;
    if (params?.type) queryParams['tenderType'] = TENDER_TYPE_TO_API[params.type] ?? params.type;
    if (params?.sortBy) queryParams['sortBy'] = params.sortBy;
    if (params?.sortOrder) queryParams['sortDescending'] = params.sortOrder === 'desc';

    return this.api.get<any>(this.endpoint, queryParams).pipe(
      map((data: any) => {
        // Backend returns PaginatedList flat structure → map to frontend nested pagination
        const items: TenderListItem[] = (data.items || []).map((item: any) => ({
          id: item.id,
          title: item.title || '',
          reference: item.reference || '',
          clientId: item.clientId || '',
          clientName: item.clientName || '',
          status: mapTenderStatus(item.status),
          submissionDeadline: item.submissionDeadline,
          estimatedValue: item.estimatedValue,
          currency: item.baseCurrency || item.currency || 'AED',
          invitedBiddersCount: item.bidderCount ?? 0,
          submittedBidsCount: item.bidCount ?? 0
        }));

        return {
          items,
          pagination: {
            currentPage: data.pageNumber ?? 1,
            pageSize: data.pageSize ?? 10,
            totalItems: data.totalCount ?? items.length,
            totalPages: data.totalPages ?? 1,
            hasNextPage: data.hasNextPage ?? false,
            hasPreviousPage: data.hasPreviousPage ?? false
          }
        } as PaginatedResponse<TenderListItem>;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load tenders');
        return throwError(() => error);
      })
    );
  }

  getTenderById(id: string | number): Observable<Tender> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<any>(`${this.endpoint}/${id}`).pipe(
      map((data: any) => this.mapDetailToTender(data)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load tender');
        return throwError(() => error);
      })
    );
  }

  createTender(data: CreateTenderDto): Observable<Tender> {
    this._isLoading.set(true);
    this._error.set(null);

    const payload = this.mapCreateDtoToCommand(data);

    return this.api.post<any>(this.endpoint, payload).pipe(
      map((result: any) => this.mapTenderDtoToTender(result)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to create tender');
        return throwError(() => error);
      })
    );
  }

  updateTender(id: string | number, data: UpdateTenderDto): Observable<Tender> {
    this._isLoading.set(true);
    this._error.set(null);

    const payload = this.mapUpdateDtoToCommand(data);

    return this.api.put<any>(`${this.endpoint}/${id}`, payload).pipe(
      map((result: any) => this.mapTenderDtoToTender(result)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update tender');
        return throwError(() => error);
      })
    );
  }

  deleteTender(id: string | number): Observable<void> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.delete<void>(`${this.endpoint}/${id}`).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to delete tender');
        return throwError(() => error);
      })
    );
  }

  updateTenderStatus(id: string | number, status: TenderStatus): Observable<Tender> {
    if (status === 'active') {
      return this.api.post<any>(`${this.endpoint}/${id}/publish`, {}).pipe(
        map((result: any) => this.mapTenderDtoToTender(result)),
        catchError(error => throwError(() => error))
      );
    }
    if (status === 'cancelled') {
      return this.api.post<any>(`${this.endpoint}/${id}/cancel`, {}).pipe(
        map((result: any) => this.mapTenderDtoToTender(result)),
        catchError(error => throwError(() => error))
      );
    }
    return this.updateTender(id, { status });
  }

  generateReference(): Observable<string> {
    return this.api.get<string>(`${this.endpoint}/next-reference`);
  }

  getInvitedBidders(tenderId: string | number): Observable<TenderInvitedBidder[]> {
    return this.api.get<any>(`${this.endpoint}/${tenderId}/bidders`).pipe(
      map((data: any) => {
        const items = data.items || data || [];
        return items.map((b: any) => ({
          id: b.id,
          tenderId: tenderId,
          bidderId: b.bidderId,
          bidderName: b.companyName || '',
          bidderEmail: b.email || '',
          invitedAt: b.invitationSentAt,
          status: this.mapBidderStatus(b),
          viewedAt: b.registeredAt
        } as TenderInvitedBidder));
      }),
      catchError(error => throwError(() => error))
    );
  }

  getActivityLog(tenderId: string | number): Observable<TenderActivity[]> {
    return this.api.get<any>(`${this.endpoint}/${tenderId}/activity`).pipe(
      map((data: any) => {
        const items = Array.isArray(data) ? data : data.items || [];
        return items.map((a: any) => ({
          id: a.id,
          tenderId: tenderId,
          action: a.action || a.activityType || '',
          description: a.description || '',
          userId: a.userId || a.performedBy,
          userName: a.userName || a.performedByName || '',
          timestamp: a.timestamp || a.createdAt
        } as TenderActivity));
      }),
      catchError(error => throwError(() => error))
    );
  }

  exportToExcel(params?: TenderFilterParams): Observable<Blob> {
    return this.api.download(`${this.endpoint}/export`);
  }

  clearError(): void {
    this._error.set(null);
  }

  // --- Private mapping methods ---

  private mapDetailToTender(data: any): Tender {
    return {
      id: data.id,
      title: data.title || '',
      reference: data.reference || '',
      description: data.description,
      clientId: data.clientId,
      clientName: data.clientName || '',
      type: mapTenderType(data.tenderType),
      status: mapTenderStatus(data.status),
      currency: data.baseCurrency || 'AED',
      estimatedValue: data.estimatedValue,
      bidValidityPeriod: data.bidValidityDays,
      dates: {
        issueDate: data.issueDate,
        clarificationDeadline: data.clarificationDeadline,
        submissionDeadline: data.submissionDeadline,
        openingDate: data.openingDate
      },
      technicalWeight: data.technicalWeight ?? 0,
      commercialWeight: data.commercialWeight ?? 0,
      evaluationCriteria: (data.evaluationCriteria || []).map((c: any) => ({
        id: c.id,
        name: c.name || '',
        weight: c.weightPercentage ?? c.weight ?? 0,
        description: c.guidanceNotes
      })),
      invitedBiddersCount: data.bidders?.length ?? data.bidderCount ?? 0,
      submittedBidsCount: data.bidCount ?? 0,
      createdAt: data.createdAt,
      updatedAt: data.updatedAt || data.createdAt,
      createdBy: data.createdBy,
      createdByName: data.createdByName
    };
  }

  private mapTenderDtoToTender(data: any): Tender {
    return {
      id: data.id,
      title: data.title || '',
      reference: data.reference || '',
      description: data.description,
      clientId: data.clientId,
      clientName: data.clientName || '',
      type: mapTenderType(data.tenderType),
      status: mapTenderStatus(data.status),
      currency: data.baseCurrency || 'AED',
      estimatedValue: data.estimatedValue,
      bidValidityPeriod: data.bidValidityDays,
      dates: {
        issueDate: data.issueDate || data.submissionDeadline,
        submissionDeadline: data.submissionDeadline
      },
      technicalWeight: data.technicalWeight ?? 0,
      commercialWeight: data.commercialWeight ?? 0,
      evaluationCriteria: (data.evaluationCriteria || []).map((c: any) => ({
        id: c.id,
        name: c.name || '',
        weight: c.weightPercentage ?? c.weight ?? 0,
        description: c.guidanceNotes
      })),
      invitedBiddersCount: data.bidderCount ?? 0,
      submittedBidsCount: data.bidCount ?? 0,
      createdAt: data.createdAt,
      updatedAt: data.updatedAt || data.createdAt,
      createdBy: data.createdBy,
      createdByName: data.createdByName
    };
  }

  private mapCreateDtoToCommand(data: CreateTenderDto): any {
    return {
      title: data.title,
      description: data.description,
      clientId: data.clientId,
      tenderType: TENDER_TYPE_TO_API[data.type] ?? 0,
      baseCurrency: data.currency || 'AED',
      bidValidityDays: data.bidValidityPeriod ?? 90,
      issueDate: data.dates.issueDate,
      clarificationDeadline: data.dates.clarificationDeadline,
      submissionDeadline: data.dates.submissionDeadline,
      openingDate: data.dates.openingDate,
      technicalWeight: data.technicalWeight,
      commercialWeight: data.commercialWeight,
      evaluationCriteria: (data.evaluationCriteria || []).map((c, i) => ({
        name: c.name,
        weightPercentage: c.weight,
        guidanceNotes: c.description,
        sortOrder: i + 1
      }))
    };
  }

  private mapUpdateDtoToCommand(data: UpdateTenderDto): any {
    const command: any = {};
    if (data.title !== undefined) command.title = data.title;
    if (data.description !== undefined) command.description = data.description;
    if (data.clientId !== undefined) command.clientId = data.clientId;
    if (data.type !== undefined) command.tenderType = TENDER_TYPE_TO_API[data.type] ?? 0;
    if (data.currency !== undefined) command.baseCurrency = data.currency;
    if (data.bidValidityPeriod !== undefined) command.bidValidityDays = data.bidValidityPeriod;
    if (data.dates) {
      if (data.dates.issueDate !== undefined) command.issueDate = data.dates.issueDate;
      if (data.dates.clarificationDeadline !== undefined) command.clarificationDeadline = data.dates.clarificationDeadline;
      if (data.dates.submissionDeadline !== undefined) command.submissionDeadline = data.dates.submissionDeadline;
      if (data.dates.openingDate !== undefined) command.openingDate = data.dates.openingDate;
    }
    if (data.technicalWeight !== undefined) command.technicalWeight = data.technicalWeight;
    if (data.commercialWeight !== undefined) command.commercialWeight = data.commercialWeight;
    if (data.evaluationCriteria) {
      command.evaluationCriteria = data.evaluationCriteria.map((c, i) => ({
        name: c.name,
        weightPercentage: c.weight,
        guidanceNotes: c.description,
        sortOrder: i + 1
      }));
    }
    return command;
  }

  private mapBidderStatus(bidder: any): 'pending' | 'viewed' | 'declined' | 'submitted' {
    const qs = bidder.qualificationStatus;
    if (qs === 1 || qs === 'Qualified') return 'submitted';
    if (qs === 2 || qs === 'Rejected') return 'declined';
    if (bidder.registeredAt) return 'viewed';
    return 'pending';
  }
}
