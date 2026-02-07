import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError, map } from 'rxjs';
import { ApiService } from './api.service';
import { PaginatedResponse, PaginationParams } from '../models';
import {
  Clarification,
  ClarificationStatus,
  ClarificationPriority,
  ClarificationSource,
  ClarificationBulletin,
  CreateClarificationDto,
  UpdateClarificationDto,
  AnswerClarificationDto,
  CreateBulletinDto,
  UpdateBulletinDto,
  ClarificationFilterParams,
  ClarificationSummary
} from '../models/clarification.model';

export interface ClarificationQueryParams extends PaginationParams, ClarificationFilterParams {}

@Injectable({
  providedIn: 'root'
})
export class ClarificationService {
  private readonly api = inject(ApiService);

  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  /** Build the base endpoint for a tender's clarifications */
  private basePath(tenderId: number): string {
    return `/tenders/${tenderId}/clarifications`;
  }

  /**
   * Get clarifications for a tender with filtering and pagination
   */
  getClarifications(
    tenderId: number,
    params?: ClarificationQueryParams
  ): Observable<PaginatedResponse<Clarification>> {
    this._isLoading.set(true);
    this._error.set(null);

    const queryParams: Record<string, string | number | boolean | undefined> = {
      page: params?.page ?? 1,
      pageSize: params?.pageSize ?? 10,
      search: params?.search || undefined,
      sortBy: params?.sortBy || 'SubmittedAt',
      sortDescending: params?.sortOrder === 'asc' ? false : true,
    };

    // Map frontend filter values to backend query params
    if (params?.status) {
      const statuses = Array.isArray(params.status) ? params.status : [params.status];
      queryParams['status'] = statuses[0]; // Backend accepts single status
    }
    if (params?.priority) {
      const priorities = Array.isArray(params.priority) ? params.priority : [params.priority];
      queryParams['priority'] = priorities[0];
    }
    if (params?.bidderId) {
      queryParams['bidderId'] = params.bidderId;
    }
    if (params?.boqSectionId) {
      queryParams['section'] = params.boqSectionId;
    }

    return this.api.getList<Clarification>(this.basePath(tenderId), queryParams as any).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load clarifications');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get a single clarification by ID
   */
  getClarificationById(tenderId: number, id: number): Observable<Clarification> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<Clarification>(`${this.basePath(tenderId)}/${id}`).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load clarification');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get clarification summary statistics for a tender.
   * Computed client-side from a full fetch (backend has no dedicated summary endpoint).
   */
  getSummary(tenderId: number): Observable<ClarificationSummary> {
    return this.api.getList<Clarification>(this.basePath(tenderId), { page: 1, pageSize: 1000 } as any).pipe(
      map(result => {
        const clarifications = result.items;

        const byStatus: Record<ClarificationStatus, number> = {
          draft: 0,
          submitted: 0,
          under_review: 0,
          answered: 0,
          published: 0,
          rejected: 0
        };

        const byPriority: Record<ClarificationPriority, number> = {
          low: 0,
          medium: 0,
          high: 0,
          urgent: 0
        };

        const bySource: Record<ClarificationSource, number> = {
          bidder: 0,
          internal: 0,
          addendum: 0
        };

        clarifications.forEach(c => {
          if (byStatus[c.status] !== undefined) byStatus[c.status]++;
          if (byPriority[c.priority] !== undefined) byPriority[c.priority]++;
          if (bySource[c.source] !== undefined) bySource[c.source]++;
        });

        return {
          total: clarifications.length,
          byStatus,
          byPriority,
          bySource,
          pendingAnswers: byStatus.submitted + byStatus.under_review
        };
      })
    );
  }

  /**
   * Create a new clarification.
   * Routes to internal-rfi endpoint for internal source, otherwise to the standard submit endpoint.
   */
  createClarification(data: CreateClarificationDto): Observable<Clarification> {
    this._isLoading.set(true);
    this._error.set(null);

    const base = this.basePath(data.tenderId);
    const endpoint = data.source === 'internal'
      ? `${base}/internal-rfi`
      : base;

    return this.api.post<Clarification>(endpoint, {
      subject: data.subject,
      question: data.question,
      relatedBoqSection: data.relatedBoqSectionId ? String(data.relatedBoqSectionId) : undefined,
      priority: data.priority,
      attachmentIds: data.attachmentIds || []
    }).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to create clarification');
        return throwError(() => error);
      })
    );
  }

  /**
   * Update a clarification
   */
  updateClarification(tenderId: number, id: number, data: UpdateClarificationDto): Observable<Clarification> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.put<Clarification>(`${this.basePath(tenderId)}/${id}`, data).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update clarification');
        return throwError(() => error);
      })
    );
  }

  /**
   * Answer a clarification (draft answer).
   * Backend endpoint: POST /api/tenders/{tenderId}/clarifications/{id}/answer
   */
  answerClarification(tenderId: number, id: number, data: AnswerClarificationDto): Observable<Clarification> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<Clarification>(`${this.basePath(tenderId)}/${id}/answer`, {
      answer: data.answer
    }).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to answer clarification');
        return throwError(() => error);
      })
    );
  }

  /**
   * Submit a draft clarification for review.
   * Uses PUT to update the clarification status.
   */
  submitClarification(tenderId: number, id: number): Observable<Clarification> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.put<Clarification>(`${this.basePath(tenderId)}/${id}`, {
      status: 'submitted'
    }).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to submit clarification');
        return throwError(() => error);
      })
    );
  }

  /**
   * Mark clarification as under review.
   * Uses PUT to update the clarification status.
   */
  startReview(tenderId: number, id: number): Observable<Clarification> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.put<Clarification>(`${this.basePath(tenderId)}/${id}`, {
      status: 'under_review'
    }).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to start review');
        return throwError(() => error);
      })
    );
  }

  /**
   * Approve a drafted answer, changing status to Answered.
   * Backend endpoint: POST /api/tenders/{tenderId}/clarifications/{id}/approve
   */
  approveClarification(tenderId: number, id: number): Observable<Clarification> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<Clarification>(`${this.basePath(tenderId)}/${id}/approve`, {}).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to approve clarification');
        return throwError(() => error);
      })
    );
  }

  /**
   * Assign a clarification to a team member.
   * Backend endpoint: POST /api/tenders/{tenderId}/clarifications/{id}/assign
   */
  assignClarification(tenderId: number, id: number, assignToUserId: string): Observable<Clarification> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<Clarification>(`${this.basePath(tenderId)}/${id}/assign`, {
      assignToUserId
    }).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to assign clarification');
        return throwError(() => error);
      })
    );
  }

  /**
   * Mark a clarification as duplicate.
   * Backend endpoint: POST /api/tenders/{tenderId}/clarifications/{id}/duplicate
   */
  markDuplicate(tenderId: number, id: number, originalClarificationId: string): Observable<Clarification> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<Clarification>(`${this.basePath(tenderId)}/${id}/duplicate`, {
      originalClarificationId
    }).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to mark as duplicate');
        return throwError(() => error);
      })
    );
  }

  /**
   * Reject a clarification with a reason.
   * Backend endpoint: POST /api/tenders/{tenderId}/clarifications/{id}/reject
   */
  rejectClarification(tenderId: number, id: number, reason?: string): Observable<Clarification> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<Clarification>(`${this.basePath(tenderId)}/${id}/reject`, {
      reason: reason || ''
    }).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to reject clarification');
        return throwError(() => error);
      })
    );
  }

  /**
   * Delete a clarification (only drafts)
   */
  deleteClarification(tenderId: number, id: number): Observable<void> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.delete<void>(`${this.basePath(tenderId)}/${id}`).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to delete clarification');
        return throwError(() => error);
      })
    );
  }

  // ========== Bulletin Methods ==========

  /**
   * Get all bulletins for a tender.
   * Backend endpoint: GET /api/tenders/{tenderId}/clarifications/bulletins
   */
  getBulletins(tenderId: number): Observable<ClarificationBulletin[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<ClarificationBulletin[]>(`${this.basePath(tenderId)}/bulletins`).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load bulletins');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get a single bulletin by ID.
   * Fetches all bulletins for the tender and filters client-side (no dedicated backend endpoint).
   */
  getBulletinById(tenderId: number, id: number): Observable<ClarificationBulletin> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<ClarificationBulletin[]>(`${this.basePath(tenderId)}/bulletins`).pipe(
      map(bulletins => {
        const bulletin = bulletins.find((b: any) => b.id === id);
        if (!bulletin) {
          throw new Error('Bulletin not found');
        }
        return bulletin;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load bulletin');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get answered clarifications available for bulletin.
   * Fetches clarifications with status filter = 'answered'.
   */
  getAnsweredClarifications(tenderId: number): Observable<Clarification[]> {
    return this.api.getList<Clarification>(this.basePath(tenderId), {
      page: 1,
      pageSize: 1000,
      status: 'answered'
    } as any).pipe(
      map(result => result.items)
    );
  }

  /**
   * Create and publish a new bulletin.
   * Backend endpoint: POST /api/tenders/{tenderId}/clarifications/bulletins
   * Note: The backend creates and publishes in a single step.
   */
  createBulletin(data: CreateBulletinDto): Observable<ClarificationBulletin> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<ClarificationBulletin>(`${this.basePath(data.tenderId)}/bulletins`, {
      clarificationIds: data.clarificationIds,
      introduction: data.introduction,
      closingNotes: data.closingNotes
    }).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to create bulletin');
        return throwError(() => error);
      })
    );
  }

  /**
   * Update a bulletin
   */
  updateBulletin(tenderId: number, id: number, data: UpdateBulletinDto): Observable<ClarificationBulletin> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.put<ClarificationBulletin>(`${this.basePath(tenderId)}/bulletins/${id}`, data).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update bulletin');
        return throwError(() => error);
      })
    );
  }

  /**
   * Publish a bulletin and send to bidders.
   * Note: The backend POST /bulletins endpoint creates and publishes in a single step.
   * This method is kept for compatibility with the component's create-then-publish flow.
   * It re-fetches the bulletin to confirm published state.
   */
  publishBulletin(tenderId: number, id: number): Observable<ClarificationBulletin> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.getBulletinById(tenderId, id).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to publish bulletin');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get the next available clarification reference number.
   * Backend endpoint: GET /api/tenders/{tenderId}/clarifications/next-reference
   */
  generateBulletinNumber(tenderId: number): Observable<string> {
    return this.api.get<string>(`${this.basePath(tenderId)}/next-reference`);
  }

  /**
   * Get bulletin PDF preview.
   * Backend endpoint: GET /api/tenders/{tenderId}/clarifications/bulletins/{bulletinId}/download
   */
  getBulletinPdfPreview(tenderId: number, id: number): Observable<Blob> {
    return this.api.download(`${this.basePath(tenderId)}/bulletins/${id}/download`);
  }

  /**
   * Download bulletin PDF.
   * Backend endpoint: GET /api/tenders/{tenderId}/clarifications/bulletins/{bulletinId}/download
   */
  downloadBulletinPdf(tenderId: number, id: number): Observable<Blob> {
    return this.api.download(`${this.basePath(tenderId)}/bulletins/${id}/download`);
  }

  clearError(): void {
    this._error.set(null);
  }
}
