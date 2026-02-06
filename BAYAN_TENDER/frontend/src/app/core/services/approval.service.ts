import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError, of, delay, map } from 'rxjs';
import { ApiService } from './api.service';
import {
  ApprovalWorkflow,
  ApprovalWorkflowStatus,
  ApprovalLevelStatus,
  InitiateApprovalDto,
  SubmitDecisionDto,
  PendingApprovalItem,
  PendingApprovalsResponse,
  ApproverOption,
  ApprovalTimelineEntry
} from '../models/approval.model';

@Injectable({
  providedIn: 'root'
})
export class ApprovalService {
  private readonly api = inject(ApiService);

  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  // Mock data for development
  private mockWorkflows: Map<number, ApprovalWorkflow> = new Map();

  /**
   * Get approval workflow for a tender
   * GET /api/tenders/{id}/approval
   */
  getApprovalWorkflow(tenderId: number): Observable<ApprovalWorkflow | null> {
    this._isLoading.set(true);
    this._error.set(null);

    // In production: return this.api.get<ApprovalWorkflow>(`/tenders/${tenderId}/approval`);

    // Mock implementation
    return of(null).pipe(
      delay(300),
      map(() => {
        const workflow = this.mockWorkflows.get(tenderId);
        return workflow || null;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load approval workflow');
        return throwError(() => error);
      })
    );
  }

  /**
   * Initiate approval workflow
   * POST /api/tenders/{id}/approval/initiate
   */
  initiateApproval(tenderId: number, data: InitiateApprovalDto): Observable<ApprovalWorkflow> {
    this._isLoading.set(true);
    this._error.set(null);

    // In production: return this.api.post<ApprovalWorkflow>(`/tenders/${tenderId}/approval/initiate`, data);

    // Mock implementation
    return of(null).pipe(
      delay(500),
      map(() => {
        const newWorkflow: ApprovalWorkflow = {
          id: Date.now(),
          tenderId,
          status: 'in_progress',
          currentLevel: 1,
          levels: [
            {
              level: 1,
              approver: {
                id: data.level1ApproverId,
                firstName: 'Ahmed',
                lastName: 'Al-Rashid',
                email: 'ahmed.rashid@company.com'
              },
              status: 'active',
              deadline: data.level1Deadline
            },
            {
              level: 2,
              approver: {
                id: data.level2ApproverId,
                firstName: 'Sarah',
                lastName: 'Al-Mahmoud',
                email: 'sarah.mahmoud@company.com'
              },
              status: 'waiting',
              deadline: data.level2Deadline
            },
            {
              level: 3,
              approver: {
                id: data.level3ApproverId,
                firstName: 'Mohammed',
                lastName: 'Al-Hassan',
                email: 'mohammed.hassan@company.com'
              },
              status: 'waiting',
              deadline: data.level3Deadline
            }
          ],
          initiatedBy: {
            id: 1,
            firstName: 'Admin',
            lastName: 'User',
            email: 'admin@company.com'
          },
          initiatedAt: new Date().toISOString(),
          awardPackUrl: `/api/tenders/${tenderId}/award-pack.pdf`,
          timeline: []
        };

        this.mockWorkflows.set(tenderId, newWorkflow);
        return newWorkflow;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to initiate approval workflow');
        return throwError(() => error);
      })
    );
  }

  /**
   * Submit approval decision
   * POST /api/tenders/{id}/approval/decide
   */
  submitDecision(tenderId: number, data: SubmitDecisionDto): Observable<ApprovalWorkflow> {
    this._isLoading.set(true);
    this._error.set(null);

    // In production: return this.api.post<ApprovalWorkflow>(`/tenders/${tenderId}/approval/decide`, data);

    // Mock implementation
    return of(null).pipe(
      delay(500),
      map(() => {
        const workflow = this.mockWorkflows.get(tenderId);
        if (!workflow) {
          throw new Error('Workflow not found');
        }

        const currentLevel = workflow.levels.find(l => l.status === 'active');
        if (!currentLevel) {
          throw new Error('No active approval level');
        }

        // Update current level
        currentLevel.status = data.decision === 'approve' ? 'approved' :
                              data.decision === 'reject' ? 'rejected' : 'returned';
        currentLevel.decision = data.decision;
        currentLevel.comment = data.comment;
        currentLevel.decidedAt = new Date().toISOString();

        // Add timeline entry
        const timelineEntry: ApprovalTimelineEntry = {
          id: Date.now(),
          level: currentLevel.level,
          approverName: `${currentLevel.approver.firstName} ${currentLevel.approver.lastName}`,
          decision: data.decision,
          comment: data.comment,
          timestamp: new Date().toISOString()
        };
        workflow.timeline.push(timelineEntry);

        // Update workflow status
        if (data.decision === 'reject') {
          workflow.status = 'rejected';
        } else if (data.decision === 'return') {
          workflow.status = 'returned';
        } else if (data.decision === 'approve') {
          // Move to next level or complete
          const nextLevel = workflow.levels.find(l => l.level === currentLevel.level + 1);
          if (nextLevel) {
            nextLevel.status = 'active';
            workflow.currentLevel = nextLevel.level;
          } else {
            // All levels approved
            workflow.status = 'approved';
            workflow.completedAt = new Date().toISOString();
          }
        }

        return workflow;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to submit decision');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get pending approvals for current user
   * GET /api/approvals/pending
   */
  getPendingApprovals(): Observable<PendingApprovalsResponse> {
    this._isLoading.set(true);
    this._error.set(null);

    // In production: return this.api.get<PendingApprovalsResponse>('/approvals/pending');

    // Mock implementation
    return of(null).pipe(
      delay(300),
      map(() => {
        const now = new Date();
        const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
        const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        const nextWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

        const mockPending: PendingApprovalItem[] = [
          {
            id: 1,
            tenderId: 1,
            tenderTitle: 'IT Infrastructure Upgrade Project',
            tenderReference: 'TND-2026-0001',
            tenderValue: 2500000,
            currency: 'AED',
            level: 1,
            submittedAt: new Date('2026-02-01').toISOString(),
            deadline: yesterday.toISOString(),
            isOverdue: true,
            isApproaching: false,
            initiatorName: 'Admin User'
          },
          {
            id: 2,
            tenderId: 3,
            tenderTitle: 'Building Security Services - 2026',
            tenderReference: 'TND-2026-0003',
            tenderValue: 1200000,
            currency: 'AED',
            level: 2,
            submittedAt: new Date('2026-02-03').toISOString(),
            deadline: tomorrow.toISOString(),
            isOverdue: false,
            isApproaching: true,
            initiatorName: 'Manager User'
          },
          {
            id: 3,
            tenderId: 5,
            tenderTitle: 'Data Center Equipment Maintenance',
            tenderReference: 'TND-2026-0005',
            tenderValue: 350000,
            currency: 'AED',
            level: 1,
            submittedAt: new Date('2026-02-04').toISOString(),
            deadline: nextWeek.toISOString(),
            isOverdue: false,
            isApproaching: false,
            initiatorName: 'Admin User'
          }
        ];

        return {
          items: mockPending,
          total: mockPending.length
        };
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load pending approvals');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get users with Approver role for dropdown
   */
  getApprovers(): Observable<ApproverOption[]> {
    // In production: return this.api.get<ApproverOption[]>('/users?role=approver');

    // Mock implementation
    return of([
      { id: 10, firstName: 'Ahmed', lastName: 'Al-Rashid', email: 'ahmed.rashid@company.com', fullName: 'Ahmed Al-Rashid' },
      { id: 11, firstName: 'Sarah', lastName: 'Al-Mahmoud', email: 'sarah.mahmoud@company.com', fullName: 'Sarah Al-Mahmoud' },
      { id: 12, firstName: 'Mohammed', lastName: 'Al-Hassan', email: 'mohammed.hassan@company.com', fullName: 'Mohammed Al-Hassan' },
      { id: 13, firstName: 'Fatima', lastName: 'Al-Farsi', email: 'fatima.farsi@company.com', fullName: 'Fatima Al-Farsi' },
      { id: 14, firstName: 'Omar', lastName: 'Al-Qasim', email: 'omar.qasim@company.com', fullName: 'Omar Al-Qasim' },
      { id: 15, firstName: 'Layla', lastName: 'Al-Nouri', email: 'layla.nouri@company.com', fullName: 'Layla Al-Nouri' }
    ]).pipe(delay(200));
  }

  /**
   * Download award pack PDF
   */
  downloadAwardPack(tenderId: number): Observable<Blob> {
    // In production: return this.api.download(`/tenders/${tenderId}/award-pack.pdf`);

    // Mock implementation - return empty PDF blob
    return of(new Blob(['Mock PDF content'], { type: 'application/pdf' })).pipe(delay(300));
  }

  /**
   * Check if current user is the active approver for a workflow
   */
  isCurrentUserActiveApprover(workflow: ApprovalWorkflow, currentUserId: number): boolean {
    const activeLevel = workflow.levels.find(l => l.status === 'active');
    return activeLevel?.approver.id === currentUserId;
  }

  clearError(): void {
    this._error.set(null);
  }
}
