import { Injectable, inject, signal } from '@angular/core';
import { Observable, map, tap, catchError, throwError } from 'rxjs';
import { ApiService } from './api.service';
import {
  BidSubmission,
  BidListItem,
  BidFilterParams,
  BidStatistics,
  OpenBidsResponse,
  RejectLateBidDto,
  DisqualifyBidDto,
  BidDocument,
  BidSummary,
  BidStatus
} from '../models/bid.model';
import { PaginatedResponse, PaginationParams } from '../models';

export interface BidQueryParams extends PaginationParams, BidFilterParams {}

@Injectable({
  providedIn: 'root'
})
export class BidService {
  private readonly api = inject(ApiService);

  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  /** Map backend numeric BidSubmissionStatus to frontend string BidStatus */
  private readonly statusMap: Record<number, BidStatus> = {
    0: 'submitted',
    1: 'opened',
    2: 'imported',
    3: 'disqualified'
  };

  private mapStatus(status: number | string): BidStatus {
    if (typeof status === 'number') {
      return this.statusMap[status] ?? 'submitted';
    }
    return (status as BidStatus) || 'submitted';
  }

  /**
   * Get all bids for a tender with optional filters
   */
  getBids(tenderId: number, params?: BidQueryParams): Observable<PaginatedResponse<BidListItem>> {
    this._isLoading.set(true);
    this._error.set(null);

    const queryParams: Record<string, string | number | boolean | undefined> = {
      page: params?.page ?? 1,
      pageSize: params?.pageSize ?? 10,
      search: params?.search,
      sortBy: params?.sortBy ?? 'SubmissionTime',
      sortDescending: params?.sortOrder === 'asc' ? false : true
    };

    if (params?.isLate !== undefined) {
      queryParams['isLate'] = params.isLate;
    }

    // Backend uses enum-based status filter, pass first status if array
    if (params?.status) {
      const statusVal = Array.isArray(params.status) ? params.status[0] : params.status;
      if (statusVal) {
        queryParams['status'] = statusVal;
      }
    }

    return this.api.get<any>(`/tenders/${tenderId}/bids`, queryParams as any).pipe(
      map((result: any) => {
        // Backend returns PaginatedList<BidListDto> with fields:
        // items, pageNumber, totalPages, totalCount, pageSize, hasPreviousPage, hasNextPage
        const items: BidListItem[] = (result.items || []).map((b: any) => ({
          id: b.id,
          tenderId: b.tenderId,
          bidderId: b.bidderId,
          bidderName: b.bidderName,
          submissionTime: b.submissionTime,
          status: this.mapStatus(b.status),
          bidAmount: b.nativeTotalAmount ?? undefined,
          currency: b.nativeCurrency ?? undefined,
          filesCount: b.totalFileCount ?? 0,
          isLate: b.isLate
        }));

        return {
          items,
          pagination: {
            currentPage: result.pageNumber,
            pageSize: result.pageSize,
            totalItems: result.totalCount,
            totalPages: result.totalPages,
            hasNextPage: result.hasNextPage,
            hasPreviousPage: result.hasPreviousPage
          }
        } as PaginatedResponse<BidListItem>;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load bids');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get detailed bid information
   */
  getBidDetails(tenderId: number, bidId: number): Observable<BidSubmission> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<any>(`/tenders/${tenderId}/bids/${bidId}`).pipe(
      map((b: any) => this.mapBidDetailToSubmission(b)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load bid details');
        return throwError(() => error);
      })
    );
  }

  /** Maps backend BidDetailDto to frontend BidSubmission */
  private mapBidDetailToSubmission(b: any): BidSubmission {
    const status = this.mapStatus(b.status);
    const documents: BidDocument[] = (b.documents || []).map((d: any) => ({
      id: d.id,
      bidId: b.id,
      filename: d.fileName,
      originalFilename: d.fileName,
      fileSize: d.fileSizeBytes,
      mimeType: d.contentType,
      documentType: (d.documentTypeName || 'other').toLowerCase().replace(/\s+/g, '_'),
      category: (d.category || 'supporting').toLowerCase(),
      uploadedAt: d.uploadedAt,
      isPreviewable: (d.contentType || '').includes('pdf')
    }));

    return {
      id: b.id,
      tenderId: b.tenderId,
      bidderId: b.bidderId,
      bidderName: b.bidderName,
      bidderEmail: b.bidderEmail,
      submissionTime: b.submissionTime,
      status,
      bidAmount: b.nativeTotalAmount ?? undefined,
      currency: b.nativeCurrency ?? undefined,
      isLate: b.isLate,
      lateAcceptedBy: b.lateAcceptedBy ?? undefined,
      lateAcceptedByName: b.lateAcceptedByName ?? undefined,
      disqualificationReason: b.disqualificationReason ?? undefined,
      lateRejectionReason: b.lateBidRejectionReason ?? undefined,
      importedAt: b.importCompletedAt ?? undefined,
      importedBy: b.importedBy ?? undefined,
      importedByName: b.importedByName ?? undefined,
      documents,
      filesCount: documents.length,
      createdAt: b.createdAt,
      updatedAt: b.createdAt
    };
  }

  /**
   * Get bid statistics for a tender.
   * Derived from the bids list since the backend has no dedicated statistics endpoint.
   */
  getStatistics(tenderId: number): Observable<BidStatistics> {
    return this.getBids(tenderId, { page: 1, pageSize: 100 }).pipe(
      map(result => {
        const bids = result.items;
        const openedCount = bids.filter(b => b.status === 'opened').length;
        return {
          totalBids: result.pagination.totalItems,
          lateBids: bids.filter(b => b.isLate).length,
          openedBids: openedCount,
          importedBids: bids.filter(b => b.status === 'imported').length,
          disqualifiedBids: bids.filter(b => b.status === 'disqualified').length,
          pendingLateBids: bids.filter(b => b.isLate && b.status === 'submitted').length,
          bidsOpened: openedCount > 0 || bids.some(b => b.status === 'imported')
        };
      })
    );
  }

  /**
   * Open all bids (irreversible action)
   */
  openBids(tenderId: number): Observable<OpenBidsResponse> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<any>(`/tenders/${tenderId}/bids/open`, {}).pipe(
      map((result: any) => ({
        success: true,
        openedCount: result.bidsOpenedCount,
        openedAt: result.openedAt,
        openedBy: result.openedByName
      } as OpenBidsResponse)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to open bids');
        return throwError(() => error);
      })
    );
  }

  /**
   * Accept a late bid
   */
  acceptLateBid(tenderId: number, bidId: number): Observable<BidSubmission> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<any>(`/tenders/${tenderId}/bids/${bidId}/accept-late`, {}).pipe(
      map((result: any) => ({
        id: result.bidId,
        tenderId,
        bidderId: 0,
        bidderName: result.bidderName,
        bidderEmail: result.bidderEmail,
        submissionTime: result.decisionAt,
        status: 'accepted' as BidStatus,
        isLate: true,
        lateAcceptedAt: result.decisionAt,
        lateAcceptedByName: result.decisionByName,
        documents: [],
        filesCount: 0,
        createdAt: result.decisionAt,
        updatedAt: result.decisionAt
      } as BidSubmission)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to accept late bid');
        return throwError(() => error);
      })
    );
  }

  /**
   * Reject a late bid
   */
  rejectLateBid(tenderId: number, bidId: number, data: RejectLateBidDto): Observable<BidSubmission> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<any>(`/tenders/${tenderId}/bids/${bidId}/reject-late`, { reason: data.reason }).pipe(
      map((result: any) => ({
        id: result.bidId,
        tenderId,
        bidderId: 0,
        bidderName: result.bidderName,
        bidderEmail: result.bidderEmail,
        submissionTime: result.decisionAt,
        status: 'rejected' as BidStatus,
        isLate: true,
        lateRejectedAt: result.decisionAt,
        lateRejectedByName: result.decisionByName,
        lateRejectionReason: result.reason,
        documents: [],
        filesCount: 0,
        createdAt: result.decisionAt,
        updatedAt: result.decisionAt
      } as BidSubmission)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to reject late bid');
        return throwError(() => error);
      })
    );
  }

  /**
   * Disqualify a bid
   */
  disqualifyBid(tenderId: number, bidId: number, data: DisqualifyBidDto): Observable<BidSubmission> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<any>(`/tenders/${tenderId}/bids/${bidId}/disqualify`, { reason: data.reason }).pipe(
      map((result: any) => ({
        id: result.bidId,
        tenderId,
        bidderId: 0,
        bidderName: result.bidderName,
        bidderEmail: '',
        submissionTime: result.disqualifiedAt,
        status: 'disqualified' as BidStatus,
        isLate: false,
        disqualifiedAt: result.disqualifiedAt,
        disqualifiedByName: result.disqualifiedByName,
        disqualificationReason: result.reason,
        documents: [],
        filesCount: 0,
        createdAt: result.disqualifiedAt,
        updatedAt: result.disqualifiedAt
      } as BidSubmission)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to disqualify bid');
        return throwError(() => error);
      })
    );
  }

  /**
   * Import BOQ from a bid.
   * Calls the BidAnalysis execute-import endpoint.
   */
  importBoq(tenderId: number, bidId: number): Observable<BidSubmission> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<any>(`/tenders/${tenderId}/bids/${bidId}/import/execute`, {}).pipe(
      map((result: any) => ({
        id: bidId,
        tenderId,
        bidderId: 0,
        bidderName: '',
        bidderEmail: '',
        submissionTime: '',
        status: (result.status === 'Imported' || result.status === 8) ? 'imported' as BidStatus : 'submitted' as BidStatus,
        isLate: false,
        importedAt: result.completedAt ?? new Date().toISOString(),
        bidSummary: result.totalAmount ? {
          totalAmount: result.totalAmount,
          currency: result.currency || 'SAR',
          validityDays: 0,
          validUntil: ''
        } as BidSummary : undefined,
        documents: [],
        filesCount: 0,
        createdAt: '',
        updatedAt: ''
      } as BidSubmission)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to import BOQ');
        return throwError(() => error);
      })
    );
  }

  /**
   * Download all bids as a ZIP file.
   * Backend returns a presigned URL; we fetch the actual blob from that URL.
   */
  downloadAllBids(tenderId: number): Observable<Blob> {
    return this.api.get<any>(`/tenders/${tenderId}/bids/download-all`).pipe(
      map((result: any) => {
        // Open the presigned download URL in a new tab / trigger download
        if (result.downloadUrl) {
          window.open(result.downloadUrl, '_blank');
        }
        // Return an empty blob to satisfy the Observable<Blob> contract
        return new Blob([], { type: 'application/zip' });
      })
    );
  }

  /**
   * Download files for a specific bid.
   * TODO: Backend endpoint for per-bid file download not yet available.
   * Uses api.download to the expected endpoint path.
   */
  downloadBidFiles(tenderId: number, bidId: number): Observable<Blob> {
    return this.api.download(`/tenders/${tenderId}/bids/${bidId}/download`);
  }

  /**
   * Download a single document
   */
  downloadDocument(documentId: number): Observable<Blob> {
    return this.api.download(`/documents/${documentId}/download`);
  }

  /**
   * Get preview URL for a document (if previewable)
   */
  getDocumentPreviewUrl(documentId: number): string {
    // In production, this would return the actual preview URL
    return `/api/documents/${documentId}/preview`;
  }

  clearError(): void {
    this._error.set(null);
  }
}
