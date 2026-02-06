import { Injectable, inject, signal } from '@angular/core';
import { Observable, of, delay, map, tap, catchError, throwError } from 'rxjs';
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
  BidSummary
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

  // Mock data for development
  private mockBids: BidSubmission[] = [
    {
      id: 1,
      tenderId: 1,
      bidderId: 1,
      bidderName: 'Tech Solutions Ltd',
      bidderNameAr: 'حلول تقنية المحدودة',
      bidderEmail: 'info@techsolutions.sa',
      submissionTime: new Date('2026-02-25T14:30:00'),
      status: 'submitted',
      bidAmount: 485000,
      currency: 'SAR',
      isLate: false,
      filesCount: 8,
      documents: this.generateMockDocuments(1),
      createdAt: new Date('2026-02-25T14:30:00'),
      updatedAt: new Date('2026-02-25T14:30:00')
    },
    {
      id: 2,
      tenderId: 1,
      bidderId: 2,
      bidderName: 'SecureTech Solutions',
      bidderEmail: 'bids@securetech.sa',
      submissionTime: new Date('2026-02-26T09:15:00'),
      status: 'submitted',
      bidAmount: 512000,
      currency: 'SAR',
      isLate: false,
      filesCount: 7,
      documents: this.generateMockDocuments(2),
      createdAt: new Date('2026-02-26T09:15:00'),
      updatedAt: new Date('2026-02-26T09:15:00')
    },
    {
      id: 3,
      tenderId: 1,
      bidderId: 3,
      bidderName: 'Global IT Partners',
      bidderEmail: 'tender@globalit.com',
      submissionTime: new Date('2026-02-27T16:45:00'),
      status: 'submitted',
      bidAmount: 498500,
      currency: 'SAR',
      isLate: false,
      filesCount: 9,
      documents: this.generateMockDocuments(3),
      createdAt: new Date('2026-02-27T16:45:00'),
      updatedAt: new Date('2026-02-27T16:45:00')
    },
    {
      id: 4,
      tenderId: 1,
      bidderId: 4,
      bidderName: 'Network Systems LLC',
      bidderEmail: 'procurement@networksys.sa',
      submissionTime: new Date('2026-03-01T10:20:00'),
      status: 'late',
      bidAmount: 475000,
      currency: 'SAR',
      isLate: true,
      lateReason: 'Technical issues with portal submission',
      filesCount: 6,
      documents: this.generateMockDocuments(4),
      createdAt: new Date('2026-03-01T10:20:00'),
      updatedAt: new Date('2026-03-01T10:20:00')
    },
    {
      id: 5,
      tenderId: 1,
      bidderId: 5,
      bidderName: 'Digital Infrastructure Co',
      bidderEmail: 'bids@digitalinfra.sa',
      submissionTime: new Date('2026-03-02T08:00:00'),
      status: 'late',
      bidAmount: 520000,
      currency: 'SAR',
      isLate: true,
      lateReason: 'Delayed internal approvals',
      filesCount: 8,
      documents: this.generateMockDocuments(5),
      createdAt: new Date('2026-03-02T08:00:00'),
      updatedAt: new Date('2026-03-02T08:00:00')
    }
  ];

  private bidsOpened = false;

  private generateMockDocuments(bidId: number): BidDocument[] {
    return [
      {
        id: bidId * 10 + 1,
        bidId,
        filename: `bid_${bidId}_priced_boq.xlsx`,
        originalFilename: 'Priced_BOQ.xlsx',
        fileSize: 125000,
        mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        documentType: 'priced_boq',
        category: 'commercial',
        uploadedAt: new Date(),
        isPreviewable: false
      },
      {
        id: bidId * 10 + 2,
        bidId,
        filename: `bid_${bidId}_methodology.pdf`,
        originalFilename: 'Technical_Methodology.pdf',
        fileSize: 2500000,
        mimeType: 'application/pdf',
        documentType: 'methodology',
        category: 'technical',
        uploadedAt: new Date(),
        isPreviewable: true
      },
      {
        id: bidId * 10 + 3,
        bidId,
        filename: `bid_${bidId}_team_cvs.pdf`,
        originalFilename: 'Team_CVs.pdf',
        fileSize: 3200000,
        mimeType: 'application/pdf',
        documentType: 'team_cvs',
        category: 'technical',
        uploadedAt: new Date(),
        isPreviewable: true
      },
      {
        id: bidId * 10 + 4,
        bidId,
        filename: `bid_${bidId}_work_program.pdf`,
        originalFilename: 'Work_Program.pdf',
        fileSize: 1800000,
        mimeType: 'application/pdf',
        documentType: 'work_program',
        category: 'technical',
        uploadedAt: new Date(),
        isPreviewable: true
      },
      {
        id: bidId * 10 + 5,
        bidId,
        filename: `bid_${bidId}_hse_plan.pdf`,
        originalFilename: 'HSE_Plan.pdf',
        fileSize: 1200000,
        mimeType: 'application/pdf',
        documentType: 'hse_plan',
        category: 'technical',
        uploadedAt: new Date(),
        isPreviewable: true
      },
      {
        id: bidId * 10 + 6,
        bidId,
        filename: `bid_${bidId}_bid_bond.pdf`,
        originalFilename: 'Bid_Bond.pdf',
        fileSize: 500000,
        mimeType: 'application/pdf',
        documentType: 'bid_bond',
        category: 'supporting',
        uploadedAt: new Date(),
        isPreviewable: true
      }
    ];
  }

  /**
   * Get all bids for a tender with optional filters
   */
  getBids(tenderId: number, params?: BidQueryParams): Observable<PaginatedResponse<BidListItem>> {
    this._isLoading.set(true);
    this._error.set(null);

    // Mock implementation
    return of(null).pipe(
      delay(500),
      map(() => {
        let filtered = this.mockBids.filter(b => b.tenderId === tenderId);

        // Apply filters
        if (params?.status) {
          const statuses = Array.isArray(params.status) ? params.status : [params.status];
          filtered = filtered.filter(b => statuses.includes(b.status));
        }

        if (params?.isLate !== undefined) {
          filtered = filtered.filter(b => b.isLate === params.isLate);
        }

        if (params?.search) {
          const term = params.search.toLowerCase();
          filtered = filtered.filter(b =>
            b.bidderName.toLowerCase().includes(term) ||
            b.bidderEmail.toLowerCase().includes(term)
          );
        }

        // Apply pagination
        const page = params?.page || 1;
        const pageSize = params?.pageSize || 10;
        const startIndex = (page - 1) * pageSize;
        const paginatedItems = filtered.slice(startIndex, startIndex + pageSize);

        const items: BidListItem[] = paginatedItems.map(b => ({
          id: b.id,
          tenderId: b.tenderId,
          bidderId: b.bidderId,
          bidderName: b.bidderName,
          submissionTime: b.submissionTime,
          status: b.status,
          bidAmount: this.bidsOpened ? b.bidAmount : undefined,
          currency: b.currency,
          filesCount: b.filesCount,
          isLate: b.isLate
        }));

        return {
          items,
          pagination: {
            currentPage: page,
            pageSize,
            totalItems: filtered.length,
            totalPages: Math.ceil(filtered.length / pageSize),
            hasNextPage: page < Math.ceil(filtered.length / pageSize),
            hasPreviousPage: page > 1
          }
        };
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

    return of(null).pipe(
      delay(300),
      map(() => {
        const bid = this.mockBids.find(b => b.id === bidId && b.tenderId === tenderId);
        if (!bid) {
          throw new Error('Bid not found');
        }

        // Hide amount if bids not opened
        const result = { ...bid };
        if (!this.bidsOpened && !bid.isLate) {
          result.bidAmount = undefined;
        }

        return result;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load bid details');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get bid statistics for a tender
   */
  getStatistics(tenderId: number): Observable<BidStatistics> {
    return of(null).pipe(
      delay(200),
      map(() => {
        const bids = this.mockBids.filter(b => b.tenderId === tenderId);
        return {
          totalBids: bids.length,
          lateBids: bids.filter(b => b.isLate).length,
          openedBids: bids.filter(b => b.status === 'opened').length,
          importedBids: bids.filter(b => b.status === 'imported').length,
          disqualifiedBids: bids.filter(b => b.status === 'disqualified').length,
          pendingLateBids: bids.filter(b => b.status === 'late').length,
          bidsOpened: this.bidsOpened
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

    return of(null).pipe(
      delay(1000),
      map(() => {
        // Mark all non-late bids as opened
        this.mockBids = this.mockBids.map(b => {
          if (b.tenderId === tenderId && !b.isLate) {
            return {
              ...b,
              status: 'opened' as const,
              openedAt: new Date(),
              openedBy: 1,
              openedByName: 'Admin User'
            };
          }
          return b;
        });

        this.bidsOpened = true;

        return {
          success: true,
          openedCount: this.mockBids.filter(b => b.tenderId === tenderId && !b.isLate).length,
          openedAt: new Date(),
          openedBy: 'Admin User'
        };
      }),
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
  acceptLateBid(bidId: number): Observable<BidSubmission> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(500),
      map(() => {
        const bidIndex = this.mockBids.findIndex(b => b.id === bidId);
        if (bidIndex === -1) {
          throw new Error('Bid not found');
        }

        const updatedBid: BidSubmission = {
          ...this.mockBids[bidIndex],
          status: this.bidsOpened ? 'opened' : 'accepted',
          lateAcceptedAt: new Date(),
          lateAcceptedBy: 1,
          lateAcceptedByName: 'Admin User'
        };

        this.mockBids[bidIndex] = updatedBid;
        return updatedBid;
      }),
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
  rejectLateBid(bidId: number, data: RejectLateBidDto): Observable<BidSubmission> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(500),
      map(() => {
        const bidIndex = this.mockBids.findIndex(b => b.id === bidId);
        if (bidIndex === -1) {
          throw new Error('Bid not found');
        }

        const updatedBid: BidSubmission = {
          ...this.mockBids[bidIndex],
          status: 'rejected',
          lateRejectedAt: new Date(),
          lateRejectedBy: 1,
          lateRejectedByName: 'Admin User',
          lateRejectionReason: data.reason
        };

        this.mockBids[bidIndex] = updatedBid;
        return updatedBid;
      }),
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
  disqualifyBid(bidId: number, data: DisqualifyBidDto): Observable<BidSubmission> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(500),
      map(() => {
        const bidIndex = this.mockBids.findIndex(b => b.id === bidId);
        if (bidIndex === -1) {
          throw new Error('Bid not found');
        }

        const updatedBid: BidSubmission = {
          ...this.mockBids[bidIndex],
          status: 'disqualified',
          disqualifiedAt: new Date(),
          disqualifiedBy: 1,
          disqualifiedByName: 'Admin User',
          disqualificationReason: data.reason
        };

        this.mockBids[bidIndex] = updatedBid;
        return updatedBid;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to disqualify bid');
        return throwError(() => error);
      })
    );
  }

  /**
   * Import BOQ from a bid
   */
  importBoq(bidId: number): Observable<BidSubmission> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(1000),
      map(() => {
        const bidIndex = this.mockBids.findIndex(b => b.id === bidId);
        if (bidIndex === -1) {
          throw new Error('Bid not found');
        }

        const bid = this.mockBids[bidIndex];

        const bidSummary: BidSummary = {
          totalAmount: bid.bidAmount || 0,
          currency: bid.currency || 'SAR',
          validityDays: 90,
          validUntil: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000),
          exceptions: ['Subject to confirmation of delivery schedule'],
          paymentTerms: 'Net 30 days from invoice date'
        };

        const updatedBid: BidSubmission = {
          ...bid,
          status: 'imported',
          importedAt: new Date(),
          importedBy: 1,
          importedByName: 'Admin User',
          bidSummary
        };

        this.mockBids[bidIndex] = updatedBid;
        return updatedBid;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to import BOQ');
        return throwError(() => error);
      })
    );
  }

  /**
   * Download all bids as a ZIP file
   */
  downloadAllBids(tenderId: number): Observable<Blob> {
    return of(null).pipe(
      delay(1500),
      map(() => {
        // In production, this would return the actual ZIP file
        return new Blob([''], { type: 'application/zip' });
      })
    );
  }

  /**
   * Download files for a specific bid
   */
  downloadBidFiles(bidId: number): Observable<Blob> {
    return of(null).pipe(
      delay(1000),
      map(() => {
        // In production, this would return the actual ZIP file
        return new Blob([''], { type: 'application/zip' });
      })
    );
  }

  /**
   * Download a single document
   */
  downloadDocument(documentId: number): Observable<Blob> {
    return of(null).pipe(
      delay(500),
      map(() => {
        // In production, this would return the actual file
        return new Blob([''], { type: 'application/octet-stream' });
      })
    );
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
