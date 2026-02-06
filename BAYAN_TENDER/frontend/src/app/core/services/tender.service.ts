import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError, of, delay, map } from 'rxjs';
import { ApiService } from './api.service';
import {
  Tender,
  TenderListItem,
  CreateTenderDto,
  UpdateTenderDto,
  TenderFilterParams,
  TenderInvitedBidder,
  TenderActivity,
  TenderStatus
} from '../models/tender.model';
import { PaginatedResponse, PaginationParams } from '../models';

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

  // Mock data for development
  private mockTenders: Tender[] = [
    {
      id: 1,
      title: 'IT Infrastructure Upgrade and Modernization Project',
      reference: 'TND-2026-0001',
      description: 'Complete upgrade of IT infrastructure including servers, networking equipment, and cloud migration.',
      clientId: 1,
      clientName: 'Ministry of Finance',
      type: 'open',
      status: 'active',
      currency: 'AED',
      estimatedValue: 2500000,
      bidValidityPeriod: 90,
      dates: {
        issueDate: new Date('2026-01-15'),
        clarificationDeadline: new Date('2026-02-10'),
        submissionDeadline: new Date('2026-02-28'),
        openingDate: new Date('2026-03-01')
      },
      technicalWeight: 70,
      commercialWeight: 30,
      evaluationCriteria: [
        { id: 1, name: 'Compliance', weight: 20 },
        { id: 2, name: 'Methodology', weight: 25 },
        { id: 3, name: 'Team CVs', weight: 15 },
        { id: 4, name: 'Program', weight: 15 },
        { id: 5, name: 'QA/QC', weight: 15 },
        { id: 6, name: 'HSE', weight: 10 }
      ],
      invitedBiddersCount: 12,
      submittedBidsCount: 5,
      createdAt: new Date('2026-01-10'),
      updatedAt: new Date('2026-01-15'),
      createdBy: 1,
      createdByName: 'Admin User'
    },
    {
      id: 2,
      title: 'Annual Office Supplies Procurement Contract',
      reference: 'TND-2026-0002',
      description: 'Framework agreement for supply of office consumables and stationery.',
      clientId: 2,
      clientName: 'Health Authority',
      type: 'selective',
      status: 'draft',
      currency: 'AED',
      estimatedValue: 500000,
      bidValidityPeriod: 60,
      dates: {
        issueDate: new Date('2026-02-01'),
        clarificationDeadline: new Date('2026-02-15'),
        submissionDeadline: new Date('2026-02-28'),
        openingDate: new Date('2026-03-01')
      },
      technicalWeight: 40,
      commercialWeight: 60,
      evaluationCriteria: [
        { id: 1, name: 'Compliance', weight: 30 },
        { id: 2, name: 'Product Quality', weight: 40 },
        { id: 3, name: 'Delivery Capability', weight: 30 }
      ],
      invitedBiddersCount: 8,
      submittedBidsCount: 0,
      createdAt: new Date('2026-01-25'),
      updatedAt: new Date('2026-01-25'),
      createdBy: 1,
      createdByName: 'Admin User'
    },
    {
      id: 3,
      title: 'Building Security Services - 2026',
      reference: 'TND-2026-0003',
      description: 'Annual contract for security services including manned guarding and CCTV monitoring.',
      clientId: 3,
      clientName: 'Education Ministry',
      type: 'open',
      status: 'evaluation',
      currency: 'AED',
      estimatedValue: 1200000,
      bidValidityPeriod: 90,
      dates: {
        issueDate: new Date('2025-12-01'),
        clarificationDeadline: new Date('2025-12-20'),
        submissionDeadline: new Date('2026-01-15'),
        openingDate: new Date('2026-01-16')
      },
      technicalWeight: 60,
      commercialWeight: 40,
      evaluationCriteria: [
        { id: 1, name: 'Compliance', weight: 15 },
        { id: 2, name: 'Experience', weight: 25 },
        { id: 3, name: 'Methodology', weight: 20 },
        { id: 4, name: 'Team Qualifications', weight: 20 },
        { id: 5, name: 'HSE', weight: 20 }
      ],
      invitedBiddersCount: 15,
      submittedBidsCount: 8,
      createdAt: new Date('2025-11-20'),
      updatedAt: new Date('2026-01-16'),
      createdBy: 2,
      createdByName: 'Manager User'
    },
    {
      id: 4,
      title: 'Strategic Consulting Services for Digital Transformation',
      reference: 'TND-2026-0004',
      description: 'Expert consulting services to support organization-wide digital transformation initiative.',
      clientId: 4,
      clientName: 'Economic Development Agency',
      type: 'negotiated',
      status: 'awarded',
      currency: 'USD',
      estimatedValue: 800000,
      bidValidityPeriod: 120,
      dates: {
        issueDate: new Date('2025-10-01'),
        clarificationDeadline: new Date('2025-10-20'),
        submissionDeadline: new Date('2025-11-15'),
        openingDate: new Date('2025-11-16')
      },
      technicalWeight: 80,
      commercialWeight: 20,
      evaluationCriteria: [
        { id: 1, name: 'Methodology', weight: 30 },
        { id: 2, name: 'Team Expertise', weight: 35 },
        { id: 3, name: 'Similar Experience', weight: 25 },
        { id: 4, name: 'Innovation', weight: 10 }
      ],
      invitedBiddersCount: 5,
      submittedBidsCount: 3,
      createdAt: new Date('2025-09-15'),
      updatedAt: new Date('2025-12-20'),
      createdBy: 1,
      createdByName: 'Admin User'
    },
    {
      id: 5,
      title: 'Data Center Equipment Maintenance',
      reference: 'TND-2026-0005',
      description: 'Preventive and corrective maintenance for data center infrastructure.',
      clientId: 1,
      clientName: 'Ministry of Finance',
      type: 'selective',
      status: 'closed',
      currency: 'AED',
      estimatedValue: 350000,
      bidValidityPeriod: 60,
      dates: {
        issueDate: new Date('2025-08-01'),
        clarificationDeadline: new Date('2025-08-15'),
        submissionDeadline: new Date('2025-08-31'),
        openingDate: new Date('2025-09-01')
      },
      technicalWeight: 65,
      commercialWeight: 35,
      evaluationCriteria: [
        { id: 1, name: 'Compliance', weight: 20 },
        { id: 2, name: 'Technical Capability', weight: 30 },
        { id: 3, name: 'Response Time SLA', weight: 25 },
        { id: 4, name: 'Experience', weight: 25 }
      ],
      invitedBiddersCount: 6,
      submittedBidsCount: 4,
      createdAt: new Date('2025-07-20'),
      updatedAt: new Date('2025-10-15'),
      createdBy: 2,
      createdByName: 'Manager User'
    }
  ];

  private lastGeneratedRef = 5;

  getTenders(params?: TenderQueryParams): Observable<PaginatedResponse<TenderListItem>> {
    this._isLoading.set(true);
    this._error.set(null);

    // In production, use API
    // return this.api.getList<TenderListItem>(this.endpoint, params).pipe(...)

    // Mock implementation for development
    return of(null).pipe(
      delay(500),
      map(() => {
        let filtered = [...this.mockTenders];

        // Apply filters
        if (params?.search) {
          const term = params.search.toLowerCase();
          filtered = filtered.filter(t =>
            t.title.toLowerCase().includes(term) ||
            t.reference.toLowerCase().includes(term) ||
            t.clientName?.toLowerCase().includes(term)
          );
        }

        if (params?.status) {
          const statuses = Array.isArray(params.status) ? params.status : [params.status];
          filtered = filtered.filter(t => statuses.includes(t.status));
        }

        if (params?.clientId) {
          filtered = filtered.filter(t => t.clientId === params.clientId);
        }

        if (params?.currency) {
          filtered = filtered.filter(t => t.currency === params.currency);
        }

        if (params?.dateFrom) {
          const from = new Date(params.dateFrom);
          filtered = filtered.filter(t => new Date(t.dates.submissionDeadline) >= from);
        }

        if (params?.dateTo) {
          const to = new Date(params.dateTo);
          filtered = filtered.filter(t => new Date(t.dates.submissionDeadline) <= to);
        }

        // Apply sorting
        if (params?.sortBy) {
          const sortOrder = params.sortOrder === 'asc' ? 1 : -1;
          filtered.sort((a, b) => {
            const aVal = (a as any)[params.sortBy!];
            const bVal = (b as any)[params.sortBy!];
            if (aVal < bVal) return -1 * sortOrder;
            if (aVal > bVal) return 1 * sortOrder;
            return 0;
          });
        }

        // Apply pagination
        const page = params?.page || 1;
        const pageSize = params?.pageSize || 10;
        const startIndex = (page - 1) * pageSize;
        const paginatedItems = filtered.slice(startIndex, startIndex + pageSize);

        const items: TenderListItem[] = paginatedItems.map(t => ({
          id: t.id,
          title: t.title,
          reference: t.reference,
          clientId: t.clientId,
          clientName: t.clientName || '',
          status: t.status,
          submissionDeadline: t.dates.submissionDeadline,
          estimatedValue: t.estimatedValue,
          currency: t.currency,
          invitedBiddersCount: t.invitedBiddersCount || 0,
          submittedBidsCount: t.submittedBidsCount || 0
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
        this._error.set(error.message || 'Failed to load tenders');
        return throwError(() => error);
      })
    );
  }

  getTenderById(id: number): Observable<Tender> {
    this._isLoading.set(true);
    this._error.set(null);

    // Mock implementation
    return of(null).pipe(
      delay(300),
      map(() => {
        const tender = this.mockTenders.find(t => t.id === id);
        if (!tender) {
          throw new Error('Tender not found');
        }
        return tender;
      }),
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

    // Mock implementation
    return of(null).pipe(
      delay(500),
      map(() => {
        const newId = Math.max(...this.mockTenders.map(t => t.id)) + 1;
        const newTender: Tender = {
          ...data,
          id: newId,
          clientName: 'New Client', // Would be fetched from client service
          status: data.status || 'draft',
          invitedBiddersCount: 0,
          submittedBidsCount: 0,
          createdAt: new Date(),
          updatedAt: new Date(),
          createdBy: 1,
          createdByName: 'Current User',
          evaluationCriteria: data.evaluationCriteria.map((c, i) => ({ ...c, id: i + 1 }))
        };
        this.mockTenders.push(newTender);
        return newTender;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to create tender');
        return throwError(() => error);
      })
    );
  }

  updateTender(id: number, data: UpdateTenderDto): Observable<Tender> {
    this._isLoading.set(true);
    this._error.set(null);

    // Mock implementation
    return of(null).pipe(
      delay(500),
      map(() => {
        const index = this.mockTenders.findIndex(t => t.id === id);
        if (index === -1) {
          throw new Error('Tender not found');
        }
        const updated: Tender = {
          ...this.mockTenders[index],
          ...data,
          updatedAt: new Date(),
          evaluationCriteria: data.evaluationCriteria
            ? data.evaluationCriteria.map((c, i) => ({ ...c, id: (c as any).id || i + 1 }))
            : this.mockTenders[index].evaluationCriteria
        };
        this.mockTenders[index] = updated;
        return updated;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update tender');
        return throwError(() => error);
      })
    );
  }

  deleteTender(id: number): Observable<void> {
    this._isLoading.set(true);
    this._error.set(null);

    // Mock implementation
    return of(null).pipe(
      delay(300),
      map(() => {
        const index = this.mockTenders.findIndex(t => t.id === id);
        if (index === -1) {
          throw new Error('Tender not found');
        }
        this.mockTenders.splice(index, 1);
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to delete tender');
        return throwError(() => error);
      })
    );
  }

  updateTenderStatus(id: number, status: TenderStatus): Observable<Tender> {
    return this.updateTender(id, { status });
  }

  generateReference(): Observable<string> {
    return of(null).pipe(
      delay(200),
      map(() => {
        this.lastGeneratedRef++;
        const year = new Date().getFullYear();
        const num = String(this.lastGeneratedRef).padStart(4, '0');
        return `TND-${year}-${num}`;
      })
    );
  }

  getInvitedBidders(tenderId: number): Observable<TenderInvitedBidder[]> {
    // Mock implementation
    return of([
      {
        id: 1,
        tenderId,
        bidderId: 1,
        bidderName: 'ABC Technologies LLC',
        bidderEmail: 'bids@abctech.com',
        invitedAt: new Date('2026-01-16'),
        status: 'submitted' as const,
        viewedAt: new Date('2026-01-17'),
        submittedAt: new Date('2026-02-15')
      },
      {
        id: 2,
        tenderId,
        bidderId: 2,
        bidderName: 'Global Solutions Inc',
        bidderEmail: 'tenders@globalsol.com',
        invitedAt: new Date('2026-01-16'),
        status: 'viewed' as const,
        viewedAt: new Date('2026-01-18')
      },
      {
        id: 3,
        tenderId,
        bidderId: 3,
        bidderName: 'Tech Partners FZE',
        bidderEmail: 'procurement@techpartners.ae',
        invitedAt: new Date('2026-01-16'),
        status: 'pending' as const
      },
      {
        id: 4,
        tenderId,
        bidderId: 4,
        bidderName: 'Innovation Works',
        bidderEmail: 'bids@innovationworks.com',
        invitedAt: new Date('2026-01-16'),
        status: 'declined' as const,
        viewedAt: new Date('2026-01-17')
      }
    ]).pipe(delay(300));
  }

  getActivityLog(tenderId: number): Observable<TenderActivity[]> {
    // Mock implementation
    return of([
      {
        id: 1,
        tenderId,
        action: 'created',
        description: 'Tender created',
        userId: 1,
        userName: 'Admin User',
        timestamp: new Date('2026-01-10T09:00:00')
      },
      {
        id: 2,
        tenderId,
        action: 'updated',
        description: 'Submission deadline extended',
        userId: 1,
        userName: 'Admin User',
        timestamp: new Date('2026-01-12T14:30:00')
      },
      {
        id: 3,
        tenderId,
        action: 'published',
        description: 'Tender published and invitations sent',
        userId: 1,
        userName: 'Admin User',
        timestamp: new Date('2026-01-15T10:00:00')
      },
      {
        id: 4,
        tenderId,
        action: 'bid_received',
        description: 'Bid received from ABC Technologies LLC',
        userId: 0,
        userName: 'System',
        timestamp: new Date('2026-02-15T16:45:00')
      }
    ]).pipe(delay(300));
  }

  exportToExcel(params?: TenderFilterParams): Observable<Blob> {
    // In production, this would call the API to generate an Excel file
    // For mock, we'll return an empty blob
    return of(new Blob([''], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })).pipe(
      delay(1000)
    );
  }

  clearError(): void {
    this._error.set(null);
  }
}
