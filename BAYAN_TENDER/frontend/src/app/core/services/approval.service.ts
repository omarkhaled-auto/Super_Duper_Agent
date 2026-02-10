import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError, of, map } from 'rxjs';
import { ApiService } from './api.service';
import {
  ApprovalWorkflow,
  ApprovalWorkflowStatus,
  ApprovalLevelStatus,
  ApprovalDecision,
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

  // Maps for converting backend numeric enums to frontend string types
  private readonly workflowStatusMap: Record<number, ApprovalWorkflowStatus> = {
    0: 'not_initiated',  // Pending
    1: 'in_progress',    // InProgress
    2: 'approved',       // Approved
    3: 'rejected',       // Rejected
    4: 'returned'        // RevisionNeeded
  };

  private readonly levelStatusMap: Record<number, ApprovalLevelStatus> = {
    0: 'waiting',   // Waiting
    1: 'active',    // Active
    2: 'approved',  // Approved
    3: 'rejected',  // Rejected
    4: 'returned'   // Returned
  };

  private readonly decisionToBackendMap: Record<ApprovalDecision, number> = {
    'approve': 0,            // Approve
    'reject': 1,             // Reject
    'return': 2              // ReturnForRevision
  };

  private readonly decisionFromBackendMap: Record<number, ApprovalDecision> = {
    0: 'approve',
    1: 'reject',
    2: 'return'
  };

  /**
   * Get approval workflow for a tender
   * GET /api/tenders/{id}/approval
   */
  getApprovalWorkflow(tenderId: number): Observable<ApprovalWorkflow | null> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<any>(`/tenders/${tenderId}/approval`).pipe(
      map(dto => this.mapWorkflowDtoToModel(dto)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        // 404 means no workflow exists yet — return null
        if (error.status === 404) {
          return of(null);
        }
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

    // Transform frontend DTO shape to backend request shape
    const requestBody = {
      approverUserIds: [
        data.level1ApproverId,
        data.level2ApproverId,
        data.level3ApproverId
      ],
      levelDeadlines: [
        data.level1Deadline || null,
        data.level2Deadline || null,
        data.level3Deadline || null
      ]
    };

    return this.api.post<any>(`/tenders/${tenderId}/approval/initiate`, requestBody).pipe(
      map(result => this.mapWorkflowDtoToModel(result.workflow)),
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

    // Transform frontend decision string to backend numeric enum
    const requestBody = {
      decision: this.decisionToBackendMap[data.decision],
      comment: data.comment
    };

    return this.api.post<any>(`/tenders/${tenderId}/approval/decide`, requestBody).pipe(
      map(result => this.mapWorkflowDtoToModel(result.workflow)),
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

    return this.api.get<any>('/approvals/pending').pipe(
      map(paginated => this.mapPendingApprovalsResponse(paginated)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load pending approvals');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get users with Approver role for dropdown.
   * GET /api/approvers
   * Dedicated endpoint accessible to Admin and TenderManager roles.
   */
  getApprovers(): Observable<ApproverOption[]> {
    return this.api.get<any>('/approvers').pipe(
      map(paginated => {
        const users: any[] = paginated.items || [];
        return users.map((u: any) => ({
          id: u.id,
          firstName: u.firstName,
          lastName: u.lastName,
          email: u.email,
          fullName: u.fullName || `${u.firstName} ${u.lastName}`
        }));
      })
    );
  }

  /**
   * Download award pack PDF
   */
  downloadAwardPack(tenderId: number): Observable<Blob> {
    return this.api.download(`/tenders/${tenderId}/award-pack.pdf`);
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

  // ── Private mapping helpers ──────────────────────────────────────

  /**
   * Maps a backend ApprovalWorkflowDto to the frontend ApprovalWorkflow model.
   * Handles numeric enum conversion, shape differences, and nested level mapping.
   */
  private mapWorkflowDtoToModel(dto: any): ApprovalWorkflow {
    const levels = (dto.levels || []).map((l: any) => ({
      level: l.levelNumber,
      approver: {
        id: l.approverUserId,
        firstName: this.extractFirstName(l.approverName),
        lastName: this.extractLastName(l.approverName),
        email: l.approverEmail
      },
      status: this.mapLevelStatus(l.status),
      deadline: l.deadline,
      decidedAt: l.decidedAt,
      decision: l.decision != null ? this.mapDecisionFromBackend(l.decision) : undefined,
      comment: l.decisionComment
    }));

    // Build timeline from levels that have decisions
    const timeline: ApprovalTimelineEntry[] = levels
      .filter((l: any) => l.decision != null && l.decidedAt != null)
      .map((l: any) => ({
        id: l.level,
        level: l.level,
        approverName: `${l.approver.firstName} ${l.approver.lastName}`,
        decision: l.decision,
        comment: l.comment,
        timestamp: l.decidedAt
      }));

    return {
      id: dto.id,
      tenderId: dto.tenderId,
      status: this.mapWorkflowStatus(dto.status),
      currentLevel: dto.currentLevel,
      levels,
      initiatedBy: {
        id: dto.initiatedBy,
        firstName: this.extractFirstName(dto.initiatedByName),
        lastName: this.extractLastName(dto.initiatedByName),
        email: ''
      },
      initiatedAt: dto.initiatedAt,
      completedAt: dto.completedAt,
      awardPackUrl: dto.awardPackPdfPath,
      timeline
    };
  }

  /**
   * Maps backend PaginatedList<PendingApprovalDto> to frontend PendingApprovalsResponse.
   */
  private mapPendingApprovalsResponse(paginated: any): PendingApprovalsResponse {
    const items: PendingApprovalItem[] = (paginated.items || []).map((p: any) => {
      const deadline = p.deadline ? new Date(p.deadline) : null;
      const now = new Date();
      const isOverdue = deadline ? deadline < now : false;
      const oneDayMs = 24 * 60 * 60 * 1000;
      const isApproaching = deadline && !isOverdue
        ? (deadline.getTime() - now.getTime()) < oneDayMs
        : false;

      return {
        id: p.workflowId,
        tenderId: p.tenderId,
        tenderTitle: p.tenderTitle,
        tenderReference: p.tenderReference,
        tenderValue: 0,
        currency: 'SAR',
        level: p.levelNumber,
        submittedAt: p.initiatedAt,
        deadline: p.deadline,
        isOverdue,
        isApproaching,
        initiatorName: p.initiatedByName
      };
    });

    return {
      items,
      total: paginated.totalCount ?? items.length
    };
  }

  private mapWorkflowStatus(status: number | string): ApprovalWorkflowStatus {
    if (typeof status === 'string') {
      // Already a string (in case backend ever adds JsonStringEnumConverter)
      const lower = status.toLowerCase();
      if (lower === 'pending') return 'not_initiated';
      if (lower === 'inprogress') return 'in_progress';
      if (lower === 'revisionneeded') return 'returned';
      return lower as ApprovalWorkflowStatus;
    }
    return this.workflowStatusMap[status] ?? 'not_initiated';
  }

  private mapLevelStatus(status: number | string): ApprovalLevelStatus {
    if (typeof status === 'string') {
      return status.toLowerCase() as ApprovalLevelStatus;
    }
    return this.levelStatusMap[status] ?? 'waiting';
  }

  private mapDecisionFromBackend(decision: number | string): ApprovalDecision {
    if (typeof decision === 'string') {
      const lower = decision.toLowerCase();
      if (lower === 'returnforrevision') return 'return';
      return lower as ApprovalDecision;
    }
    return this.decisionFromBackendMap[decision] ?? 'approve';
  }

  private extractFirstName(fullName: string): string {
    if (!fullName) return '';
    const parts = fullName.trim().split(/\s+/);
    return parts[0] || '';
  }

  private extractLastName(fullName: string): string {
    if (!fullName) return '';
    const parts = fullName.trim().split(/\s+/);
    return parts.slice(1).join(' ') || '';
  }
}
