import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { map } from 'rxjs/operators';
import { ApiService } from './api.service';
import {
  TenderManagerDashboard,
  TenderManagerDashboardParams,
  OverviewDashboard,
  OverviewDashboardParams,
  ApproverDashboard,
  ApproverDashboardParams,
  TenderDashboardStatus,
  ApprovalDecisionType
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

  // Backend numeric enum -> frontend string mappings
  private static readonly TENDER_STATUS_MAP: Record<number, TenderDashboardStatus> = {
    0: 'Draft',
    1: 'Active',
    2: 'Evaluation',
    3: 'Awarded',
    4: 'Cancelled'
  };

  private static readonly APPROVAL_DECISION_MAP: Record<number, ApprovalDecisionType> = {
    0: 'Approve',
    1: 'Reject',
    2: 'ReturnForRevision'
  };

  /**
   * Get Tender Manager dashboard data
   * GET /api/dashboard/tender-manager
   */
  getTenderManagerDashboard(params?: TenderManagerDashboardParams): Observable<TenderManagerDashboard> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<TenderManagerDashboard>(`${this.endpoint}/tender-manager`, params as any).pipe(
      map(data => ({
        ...data,
        activeTenders: data.activeTenders.map(t => ({
          ...t,
          status: DashboardService.TENDER_STATUS_MAP[t.status as unknown as number] ?? t.status
        }))
      })),
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

    return this.api.get<ApproverDashboard>(`${this.endpoint}/approver`, params as any).pipe(
      map(data => ({
        ...data,
        recentDecisions: data.recentDecisions.map(d => ({
          ...d,
          decision: DashboardService.APPROVAL_DECISION_MAP[d.decision as unknown as number] ?? d.decision
        }))
      })),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load approver dashboard data');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get Overview dashboard data
   * GET /api/dashboard/overview
   */
  getOverviewDashboard(params?: OverviewDashboardParams): Observable<OverviewDashboard> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<OverviewDashboard>(`${this.endpoint}/overview`, params as any).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load overview dashboard data');
        return throwError(() => error);
      })
    );
  }

  clearError(): void {
    this._error.set(null);
  }
}
