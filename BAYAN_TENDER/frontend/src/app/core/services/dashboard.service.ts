import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError, of, delay, map } from 'rxjs';
import { ApiService } from './api.service';
import {
  TenderManagerDashboard,
  TenderManagerDashboardParams,
  ApproverDashboard,
  ApproverDashboardParams,
  DashboardKpi,
  ActiveTender,
  DeadlineItem,
  ActivityFeedItem,
  PendingApprovalItem,
  RecentDecision,
  ApprovalStats
} from '../models/dashboard.model';

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  private readonly api = inject(ApiService);
  private readonly endpoint = '/dashboard';

  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  /**
   * Get Tender Manager dashboard data
   * GET /api/dashboard/tender-manager
   */
  getTenderManagerDashboard(params?: TenderManagerDashboardParams): Observable<TenderManagerDashboard> {
    this._isLoading.set(true);
    this._error.set(null);

    // In production: return this.api.get<TenderManagerDashboard>(`${this.endpoint}/tender-manager`, params);

    // Mock implementation for development
    return of(null).pipe(
      delay(500),
      map(() => this.getMockTenderManagerDashboard()),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load dashboard data');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get Approver dashboard data
   * GET /api/dashboard/approver
   */
  getApproverDashboard(params?: ApproverDashboardParams): Observable<ApproverDashboard> {
    this._isLoading.set(true);
    this._error.set(null);

    // In production: return this.api.get<ApproverDashboard>(`${this.endpoint}/approver`, params);

    // Mock implementation for development
    return of(null).pipe(
      delay(500),
      map(() => this.getMockApproverDashboard()),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load approver dashboard data');
        return throwError(() => error);
      })
    );
  }

  clearError(): void {
    this._error.set(null);
  }

  // ==================== Mock Data ====================

  private getMockTenderManagerDashboard(): TenderManagerDashboard {
    const now = new Date();

    const kpis: DashboardKpi[] = [
      {
        name: 'Active Tenders',
        value: 12,
        icon: 'pi-file',
        color: 'blue',
        change: 8,
        changeIsPositive: true
      },
      {
        name: 'In Evaluation',
        value: 5,
        icon: 'pi-chart-bar',
        color: 'orange',
        change: 2,
        changeIsPositive: true
      },
      {
        name: 'Awarded This Month',
        value: 3,
        icon: 'pi-trophy',
        color: 'green',
        change: 15,
        changeIsPositive: true
      },
      {
        name: 'Overdue Tasks',
        value: 2,
        icon: 'pi-exclamation-triangle',
        color: 'red',
        change: -25,
        changeIsPositive: true
      }
    ];

    const activeTenders: ActiveTender[] = [
      {
        id: '1',
        reference: 'TND-2026-0001',
        title: 'IT Infrastructure Upgrade Project',
        clientName: 'Ministry of Finance',
        status: 'Active',
        statusText: 'Active',
        submissionDeadline: this.addDays(now, 5).toISOString(),
        bidsReceived: 4,
        invitedBidders: 8,
        daysRemaining: 5,
        createdAt: this.addDays(now, -10).toISOString()
      },
      {
        id: '2',
        reference: 'TND-2026-0002',
        title: 'Annual Office Supplies Contract',
        clientName: 'Health Authority',
        status: 'Active',
        statusText: 'Active',
        submissionDeadline: this.addDays(now, 12).toISOString(),
        bidsReceived: 2,
        invitedBidders: 6,
        daysRemaining: 12,
        createdAt: this.addDays(now, -5).toISOString()
      },
      {
        id: '3',
        reference: 'TND-2026-0003',
        title: 'Building Security Services',
        clientName: 'Education Ministry',
        status: 'Evaluation',
        statusText: 'Evaluation',
        submissionDeadline: this.addDays(now, -2).toISOString(),
        bidsReceived: 6,
        invitedBidders: 10,
        daysRemaining: -2,
        createdAt: this.addDays(now, -20).toISOString()
      },
      {
        id: '4',
        reference: 'TND-2026-0004',
        title: 'Strategic Consulting Services',
        clientName: 'Economic Development Agency',
        status: 'Active',
        statusText: 'Active',
        submissionDeadline: this.addDays(now, 8).toISOString(),
        bidsReceived: 1,
        invitedBidders: 5,
        daysRemaining: 8,
        createdAt: this.addDays(now, -3).toISOString()
      },
      {
        id: '5',
        reference: 'TND-2026-0005',
        title: 'Data Center Maintenance',
        clientName: 'Ministry of Finance',
        status: 'Evaluation',
        statusText: 'Evaluation',
        submissionDeadline: this.addDays(now, -5).toISOString(),
        bidsReceived: 4,
        invitedBidders: 6,
        daysRemaining: -5,
        createdAt: this.addDays(now, -30).toISOString()
      }
    ];

    const upcomingDeadlines: DeadlineItem[] = [
      {
        tenderId: '1',
        tenderReference: 'TND-2026-0001',
        tenderTitle: 'IT Infrastructure Upgrade Project',
        deadlineType: 'Submission',
        deadline: this.addDays(now, 2).toISOString(),
        daysRemaining: 2,
        hoursRemaining: 48,
        isOverdue: false,
        isUrgent: true
      },
      {
        tenderId: '6',
        tenderReference: 'TND-2026-0006',
        tenderTitle: 'Network Equipment Procurement',
        deadlineType: 'Clarification',
        deadline: this.addDays(now, 1).toISOString(),
        daysRemaining: 1,
        hoursRemaining: 24,
        isOverdue: false,
        isUrgent: true
      },
      {
        tenderId: '2',
        tenderReference: 'TND-2026-0002',
        tenderTitle: 'Annual Office Supplies Contract',
        deadlineType: 'Submission',
        deadline: this.addDays(now, 5).toISOString(),
        daysRemaining: 5,
        hoursRemaining: 120,
        isOverdue: false,
        isUrgent: false
      },
      {
        tenderId: '4',
        tenderReference: 'TND-2026-0004',
        tenderTitle: 'Strategic Consulting Services',
        deadlineType: 'Clarification',
        deadline: this.addDays(now, 3).toISOString(),
        daysRemaining: 3,
        hoursRemaining: 72,
        isOverdue: false,
        isUrgent: false
      }
    ];

    const recentActivity: ActivityFeedItem[] = [
      {
        id: '1',
        activityType: 'created',
        description: 'New tender created: Network Equipment Procurement',
        entityType: 'Tender',
        entityId: '6',
        performedBy: 'Ahmed Al-Rashid',
        occurredAt: this.addHours(now, -2).toISOString(),
        icon: 'pi-plus-circle',
        color: 'blue'
      },
      {
        id: '2',
        activityType: 'submitted',
        description: 'Bid received from ABC Technologies for TND-2026-0001',
        entityType: 'BidSubmission',
        entityId: '10',
        performedBy: 'System',
        occurredAt: this.addHours(now, -5).toISOString(),
        icon: 'pi-upload',
        color: 'purple'
      },
      {
        id: '3',
        activityType: 'approved',
        description: 'Approval completed for TND-2026-0005',
        entityType: 'ApprovalWorkflow',
        entityId: '3',
        performedBy: 'Mohammed Al-Hassan',
        occurredAt: this.addHours(now, -8).toISOString(),
        icon: 'pi-check-circle',
        color: 'green'
      },
      {
        id: '4',
        activityType: 'published',
        description: 'Tender published: Annual Office Supplies Contract',
        entityType: 'Tender',
        entityId: '2',
        performedBy: 'Sarah Al-Mahmoud',
        occurredAt: this.addHours(now, -24).toISOString(),
        icon: 'pi-send',
        color: 'green'
      },
      {
        id: '5',
        activityType: 'updated',
        description: 'Submission deadline extended for TND-2026-0004',
        entityType: 'Tender',
        entityId: '4',
        performedBy: 'Admin User',
        occurredAt: this.addHours(now, -48).toISOString(),
        icon: 'pi-pencil',
        color: 'orange'
      }
    ];

    return {
      kpis,
      activeTenders,
      upcomingDeadlines,
      recentActivity
    };
  }

  private getMockApproverDashboard(): ApproverDashboard {
    const now = new Date();

    const pendingApprovals: PendingApprovalItem[] = [
      {
        workflowId: '1',
        tenderId: '1',
        tenderReference: 'TND-2026-0001',
        tenderTitle: 'IT Infrastructure Upgrade Project',
        clientName: 'Ministry of Finance',
        tenderValue: 2500000,
        currency: 'AED',
        currentLevel: 2,
        totalLevels: 3,
        initiatedByName: 'Ahmed Al-Rashid',
        submittedAt: this.addDays(now, -3).toISOString(),
        deadline: this.addDays(now, -1).toISOString(),
        daysUntilDeadline: -1,
        isOverdue: true,
        isUrgent: false
      },
      {
        workflowId: '2',
        tenderId: '3',
        tenderReference: 'TND-2026-0003',
        tenderTitle: 'Building Security Services',
        clientName: 'Education Ministry',
        tenderValue: 1200000,
        currency: 'AED',
        currentLevel: 1,
        totalLevels: 3,
        initiatedByName: 'Sarah Al-Mahmoud',
        submittedAt: this.addDays(now, -1).toISOString(),
        deadline: this.addHours(now, 12).toISOString(),
        daysUntilDeadline: 0,
        isOverdue: false,
        isUrgent: true
      },
      {
        workflowId: '3',
        tenderId: '5',
        tenderReference: 'TND-2026-0005',
        tenderTitle: 'Data Center Maintenance',
        clientName: 'Ministry of Finance',
        tenderValue: 350000,
        currency: 'AED',
        currentLevel: 1,
        totalLevels: 3,
        initiatedByName: 'Admin User',
        submittedAt: this.addDays(now, -2).toISOString(),
        deadline: this.addDays(now, 3).toISOString(),
        daysUntilDeadline: 3,
        isOverdue: false,
        isUrgent: false
      }
    ];

    const recentDecisions: RecentDecision[] = [
      {
        id: '1',
        tenderId: '10',
        tenderReference: 'TND-2025-0020',
        tenderTitle: 'Software Licensing Contract',
        decision: 'Approve',
        decisionText: 'Approved',
        comment: 'All requirements met. Proceed with award.',
        decidedAt: this.addDays(now, -2).toISOString()
      },
      {
        id: '2',
        tenderId: '11',
        tenderReference: 'TND-2025-0021',
        tenderTitle: 'Fleet Management Services',
        decision: 'Approve',
        decisionText: 'Approved',
        decidedAt: this.addDays(now, -5).toISOString()
      },
      {
        id: '3',
        tenderId: '12',
        tenderReference: 'TND-2025-0022',
        tenderTitle: 'Catering Services',
        decision: 'ReturnForRevision',
        decisionText: 'Returned',
        comment: 'Please clarify the evaluation scoring methodology.',
        decidedAt: this.addDays(now, -7).toISOString()
      },
      {
        id: '4',
        tenderId: '13',
        tenderReference: 'TND-2025-0023',
        tenderTitle: 'Marketing Campaign',
        decision: 'Reject',
        decisionText: 'Rejected',
        comment: 'Budget exceeds approved limits. Requires re-tender.',
        decidedAt: this.addDays(now, -10).toISOString()
      }
    ];

    const stats: ApprovalStats = {
      pendingCount: 3,
      approvedCount: 24,
      rejectedCount: 3,
      returnedCount: 5,
      totalThisMonth: 8,
      averageResponseTimeHours: 18.5
    };

    return {
      pendingApprovals,
      recentDecisions,
      stats
    };
  }

  // Helper methods for mock data
  private addDays(date: Date, days: number): Date {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
  }

  private addHours(date: Date, hours: number): Date {
    const result = new Date(date);
    result.setHours(result.getHours() + hours);
    return result;
  }
}
