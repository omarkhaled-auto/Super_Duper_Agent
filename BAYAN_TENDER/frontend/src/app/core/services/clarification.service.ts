import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError, of, delay, map } from 'rxjs';
import { ApiService } from './api.service';
import { PaginatedResponse, PaginationParams } from '../models';
import {
  Clarification,
  ClarificationStatus,
  ClarificationPriority,
  ClarificationSource,
  ClarificationBulletin,
  ClarificationAttachment,
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
  private readonly endpoint = '/clarifications';

  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  // Mock data for development
  private mockClarifications: Clarification[] = [
    {
      id: 1,
      tenderId: 1,
      referenceNumber: 'RFI-001',
      subject: 'Clarification on concrete specifications',
      question: 'Please confirm the required concrete grade for foundation works. The technical specifications mention Grade 40, but the drawings indicate Grade 35.',
      answer: 'The correct concrete grade for foundation works is Grade 40 as specified in the technical specifications. The drawings will be updated in an addendum.',
      status: 'answered',
      priority: 'high',
      source: 'bidder',
      bidderId: 1,
      bidderName: 'Tech Solutions Ltd',
      relatedBoqSectionId: 6,
      relatedBoqSectionTitle: '2.2 - Concrete Works',
      submittedAt: new Date('2026-01-20'),
      answeredAt: new Date('2026-01-22'),
      createdAt: new Date('2026-01-20'),
      updatedAt: new Date('2026-01-22'),
      submittedById: 10,
      submittedByName: 'John Doe',
      answeredById: 1,
      answeredByName: 'Admin User'
    },
    {
      id: 2,
      tenderId: 1,
      referenceNumber: 'RFI-002',
      subject: 'Site access during construction',
      question: 'What are the working hours allowed for construction activities on site? Are there any restrictions during weekends or holidays?',
      status: 'submitted',
      priority: 'medium',
      source: 'bidder',
      bidderId: 2,
      bidderName: 'SecureTech Solutions',
      submittedAt: new Date('2026-01-25'),
      createdAt: new Date('2026-01-25'),
      updatedAt: new Date('2026-01-25'),
      submittedById: 11,
      submittedByName: 'Jane Smith'
    },
    {
      id: 3,
      tenderId: 1,
      referenceNumber: 'RFI-003',
      subject: 'Payment terms clarification',
      question: 'The tender documents mention 30-day payment terms, but the contract draft shows 45 days. Which one applies?',
      answer: 'The payment terms are 30 days as stated in the tender documents. The contract will be amended accordingly.',
      status: 'published',
      priority: 'high',
      source: 'bidder',
      bidderId: 1,
      bidderName: 'Tech Solutions Ltd',
      bulletinId: 1,
      bulletinNumber: 'QB-001',
      submittedAt: new Date('2026-01-18'),
      answeredAt: new Date('2026-01-19'),
      publishedAt: new Date('2026-01-21'),
      createdAt: new Date('2026-01-18'),
      updatedAt: new Date('2026-01-21'),
      submittedById: 10,
      submittedByName: 'John Doe',
      answeredById: 1,
      answeredByName: 'Admin User'
    },
    {
      id: 4,
      tenderId: 1,
      referenceNumber: 'INT-001',
      subject: 'Internal review - Equipment specifications',
      question: 'Need to verify if the HVAC equipment specifications are complete. The consultant mentioned possible updates.',
      status: 'under_review',
      priority: 'medium',
      source: 'internal',
      dueDate: new Date('2026-02-05'),
      createdAt: new Date('2026-01-28'),
      updatedAt: new Date('2026-01-28'),
      submittedById: 2,
      submittedByName: 'Manager User'
    },
    {
      id: 5,
      tenderId: 1,
      referenceNumber: 'RFI-004',
      subject: 'Insurance requirements',
      question: 'What are the minimum insurance coverage requirements for the contractor?',
      status: 'draft',
      priority: 'low',
      source: 'internal',
      createdAt: new Date('2026-01-30'),
      updatedAt: new Date('2026-01-30'),
      submittedById: 2,
      submittedByName: 'Manager User'
    },
    {
      id: 6,
      tenderId: 1,
      referenceNumber: 'RFI-005',
      subject: 'Alternative materials acceptance',
      question: 'Will alternative materials be considered if they meet the same performance specifications?',
      answer: 'Alternative materials may be proposed as alternates. Bidders must submit technical data sheets and certifications for evaluation.',
      status: 'answered',
      priority: 'medium',
      source: 'bidder',
      bidderId: 3,
      bidderName: 'Global Contractors Inc',
      submittedAt: new Date('2026-01-26'),
      answeredAt: new Date('2026-01-28'),
      createdAt: new Date('2026-01-26'),
      updatedAt: new Date('2026-01-28'),
      submittedById: 12,
      submittedByName: 'Mike Johnson',
      answeredById: 1,
      answeredByName: 'Admin User'
    }
  ];

  private mockBulletins: ClarificationBulletin[] = [
    {
      id: 1,
      tenderId: 1,
      bulletinNumber: 'QB-001',
      issueDate: new Date('2026-01-21'),
      title: 'Q&A Bulletin #1',
      introduction: 'This bulletin addresses questions received from bidders regarding the IT Infrastructure Upgrade Project.',
      closingNotes: 'All bidders are requested to acknowledge receipt of this bulletin.',
      clarificationIds: [3],
      status: 'published',
      publishedAt: new Date('2026-01-21'),
      publishedById: 1,
      publishedByName: 'Admin User',
      pdfUrl: '/api/bulletins/1/pdf',
      createdAt: new Date('2026-01-21'),
      updatedAt: new Date('2026-01-21')
    }
  ];

  private lastClarificationId = 6;
  private lastBulletinId = 1;

  /**
   * Get clarifications for a tender with filtering and pagination
   */
  getClarifications(
    tenderId: number,
    params?: ClarificationQueryParams
  ): Observable<PaginatedResponse<Clarification>> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(400),
      map(() => {
        let filtered = this.mockClarifications.filter(c => c.tenderId === tenderId);

        // Apply filters
        if (params?.search) {
          const term = params.search.toLowerCase();
          filtered = filtered.filter(c =>
            c.subject.toLowerCase().includes(term) ||
            c.question.toLowerCase().includes(term) ||
            c.referenceNumber.toLowerCase().includes(term)
          );
        }

        if (params?.status) {
          const statuses = Array.isArray(params.status) ? params.status : [params.status];
          filtered = filtered.filter(c => statuses.includes(c.status));
        }

        if (params?.source) {
          const sources = Array.isArray(params.source) ? params.source : [params.source];
          filtered = filtered.filter(c => sources.includes(c.source));
        }

        if (params?.priority) {
          const priorities = Array.isArray(params.priority) ? params.priority : [params.priority];
          filtered = filtered.filter(c => priorities.includes(c.priority));
        }

        if (params?.boqSectionId) {
          filtered = filtered.filter(c => c.relatedBoqSectionId === params.boqSectionId);
        }

        if (params?.bidderId) {
          filtered = filtered.filter(c => c.bidderId === params.bidderId);
        }

        // Sort by date descending
        filtered.sort((a, b) =>
          new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
        );

        // Apply pagination
        const page = params?.page || 1;
        const pageSize = params?.pageSize || 10;
        const startIndex = (page - 1) * pageSize;
        const paginatedItems = filtered.slice(startIndex, startIndex + pageSize);

        return {
          items: paginatedItems,
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
        this._error.set(error.message || 'Failed to load clarifications');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get a single clarification by ID
   */
  getClarificationById(id: number): Observable<Clarification> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(200),
      map(() => {
        const clarification = this.mockClarifications.find(c => c.id === id);
        if (!clarification) {
          throw new Error('Clarification not found');
        }
        return clarification;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load clarification');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get clarification summary statistics for a tender
   */
  getSummary(tenderId: number): Observable<ClarificationSummary> {
    return of(null).pipe(
      delay(200),
      map(() => {
        const clarifications = this.mockClarifications.filter(c => c.tenderId === tenderId);

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
          byStatus[c.status]++;
          byPriority[c.priority]++;
          bySource[c.source]++;
        });

        return {
          total: clarifications.length,
          byStatus,
          byPriority,
          bySource,
          pendingAnswers: byStatus.submitted + byStatus.under_review,
          averageResponseTime: 24 // Mock: 24 hours average
        };
      })
    );
  }

  /**
   * Create a new clarification (internal RFI)
   */
  createClarification(data: CreateClarificationDto): Observable<Clarification> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(400),
      map(() => {
        const refPrefix = data.source === 'internal' ? 'INT' : 'RFI';
        const count = this.mockClarifications.filter(c =>
          c.tenderId === data.tenderId && c.source === data.source
        ).length + 1;

        const newClarification: Clarification = {
          id: ++this.lastClarificationId,
          tenderId: data.tenderId,
          referenceNumber: `${refPrefix}-${String(count).padStart(3, '0')}`,
          subject: data.subject,
          question: data.question,
          status: data.source === 'internal' ? 'draft' : 'submitted',
          priority: data.priority || 'medium',
          source: data.source,
          relatedBoqSectionId: data.relatedBoqSectionId,
          dueDate: data.dueDate,
          createdAt: new Date(),
          updatedAt: new Date(),
          submittedById: 1, // Current user
          submittedByName: 'Current User'
        };

        this.mockClarifications.push(newClarification);
        return newClarification;
      }),
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
  updateClarification(id: number, data: UpdateClarificationDto): Observable<Clarification> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(300),
      map(() => {
        const index = this.mockClarifications.findIndex(c => c.id === id);
        if (index === -1) {
          throw new Error('Clarification not found');
        }
        const updated: Clarification = {
          ...this.mockClarifications[index],
          ...data,
          updatedAt: new Date()
        };
        this.mockClarifications[index] = updated;
        return updated;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update clarification');
        return throwError(() => error);
      })
    );
  }

  /**
   * Answer a clarification
   */
  answerClarification(id: number, data: AnswerClarificationDto): Observable<Clarification> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(400),
      map(() => {
        const index = this.mockClarifications.findIndex(c => c.id === id);
        if (index === -1) {
          throw new Error('Clarification not found');
        }
        const updated: Clarification = {
          ...this.mockClarifications[index],
          answer: data.answer,
          status: 'answered',
          answeredAt: new Date(),
          answeredById: 1,
          answeredByName: 'Admin User',
          updatedAt: new Date()
        };
        this.mockClarifications[index] = updated;
        return updated;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to answer clarification');
        return throwError(() => error);
      })
    );
  }

  /**
   * Submit a draft clarification for review
   */
  submitClarification(id: number): Observable<Clarification> {
    return this.updateStatus(id, 'submitted');
  }

  /**
   * Mark clarification as under review
   */
  startReview(id: number): Observable<Clarification> {
    return this.updateStatus(id, 'under_review');
  }

  /**
   * Reject a clarification
   */
  rejectClarification(id: number, reason?: string): Observable<Clarification> {
    return this.updateStatus(id, 'rejected');
  }

  private updateStatus(id: number, status: ClarificationStatus): Observable<Clarification> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(300),
      map(() => {
        const index = this.mockClarifications.findIndex(c => c.id === id);
        if (index === -1) {
          throw new Error('Clarification not found');
        }
        const updated: Clarification = {
          ...this.mockClarifications[index],
          status,
          updatedAt: new Date()
        };
        if (status === 'submitted') {
          updated.submittedAt = new Date();
        }
        this.mockClarifications[index] = updated;
        return updated;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update status');
        return throwError(() => error);
      })
    );
  }

  /**
   * Delete a clarification (only drafts)
   */
  deleteClarification(id: number): Observable<void> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(300),
      map(() => {
        const index = this.mockClarifications.findIndex(c => c.id === id);
        if (index === -1) {
          throw new Error('Clarification not found');
        }
        if (this.mockClarifications[index].status !== 'draft') {
          throw new Error('Only draft clarifications can be deleted');
        }
        this.mockClarifications.splice(index, 1);
      }),
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
   * Get all bulletins for a tender
   */
  getBulletins(tenderId: number): Observable<ClarificationBulletin[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(300),
      map(() => this.mockBulletins.filter(b => b.tenderId === tenderId)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load bulletins');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get a single bulletin by ID
   */
  getBulletinById(id: number): Observable<ClarificationBulletin> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(200),
      map(() => {
        const bulletin = this.mockBulletins.find(b => b.id === id);
        if (!bulletin) {
          throw new Error('Bulletin not found');
        }
        // Include clarifications
        bulletin.clarifications = this.mockClarifications.filter(
          c => bulletin.clarificationIds.includes(c.id)
        );
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
   * Get answered clarifications available for bulletin
   */
  getAnsweredClarifications(tenderId: number): Observable<Clarification[]> {
    return of(null).pipe(
      delay(200),
      map(() =>
        this.mockClarifications.filter(
          c => c.tenderId === tenderId && c.status === 'answered'
        )
      )
    );
  }

  /**
   * Create a new bulletin (draft)
   */
  createBulletin(data: CreateBulletinDto): Observable<ClarificationBulletin> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(400),
      map(() => {
        const newBulletin: ClarificationBulletin = {
          id: ++this.lastBulletinId,
          tenderId: data.tenderId,
          bulletinNumber: data.bulletinNumber,
          issueDate: data.issueDate,
          title: data.title,
          introduction: data.introduction,
          closingNotes: data.closingNotes,
          clarificationIds: data.clarificationIds,
          status: 'draft',
          createdAt: new Date(),
          updatedAt: new Date()
        };
        this.mockBulletins.push(newBulletin);
        return newBulletin;
      }),
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
  updateBulletin(id: number, data: UpdateBulletinDto): Observable<ClarificationBulletin> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(300),
      map(() => {
        const index = this.mockBulletins.findIndex(b => b.id === id);
        if (index === -1) {
          throw new Error('Bulletin not found');
        }
        const updated: ClarificationBulletin = {
          ...this.mockBulletins[index],
          ...data,
          updatedAt: new Date()
        };
        this.mockBulletins[index] = updated;
        return updated;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update bulletin');
        return throwError(() => error);
      })
    );
  }

  /**
   * Publish a bulletin and send to bidders
   */
  publishBulletin(id: number): Observable<ClarificationBulletin> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(500),
      map(() => {
        const index = this.mockBulletins.findIndex(b => b.id === id);
        if (index === -1) {
          throw new Error('Bulletin not found');
        }

        const bulletin = this.mockBulletins[index];
        const updated: ClarificationBulletin = {
          ...bulletin,
          status: 'published',
          publishedAt: new Date(),
          publishedById: 1,
          publishedByName: 'Admin User',
          pdfUrl: `/api/bulletins/${id}/pdf`,
          updatedAt: new Date()
        };
        this.mockBulletins[index] = updated;

        // Update included clarifications to published status
        bulletin.clarificationIds.forEach(cId => {
          const cIndex = this.mockClarifications.findIndex(c => c.id === cId);
          if (cIndex !== -1) {
            this.mockClarifications[cIndex] = {
              ...this.mockClarifications[cIndex],
              status: 'published',
              publishedAt: new Date(),
              bulletinId: id,
              bulletinNumber: bulletin.bulletinNumber,
              updatedAt: new Date()
            };
          }
        });

        return updated;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to publish bulletin');
        return throwError(() => error);
      })
    );
  }

  /**
   * Generate next bulletin number
   */
  generateBulletinNumber(tenderId: number): Observable<string> {
    return of(null).pipe(
      delay(100),
      map(() => {
        const count = this.mockBulletins.filter(b => b.tenderId === tenderId).length + 1;
        return `QB-${String(count).padStart(3, '0')}`;
      })
    );
  }

  /**
   * Get bulletin PDF preview
   */
  getBulletinPdfPreview(id: number): Observable<Blob> {
    return of(null).pipe(
      delay(500),
      map(() => new Blob([''], { type: 'application/pdf' }))
    );
  }

  /**
   * Download bulletin PDF
   */
  downloadBulletinPdf(id: number): Observable<Blob> {
    return of(null).pipe(
      delay(500),
      map(() => new Blob([''], { type: 'application/pdf' }))
    );
  }

  clearError(): void {
    this._error.set(null);
  }
}
