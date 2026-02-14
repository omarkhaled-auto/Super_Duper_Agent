import { Component, inject, OnInit, signal, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ChartModule } from 'primeng/chart';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { TimelineModule } from 'primeng/timeline';
import { TooltipModule } from 'primeng/tooltip';
import { SkeletonModule } from 'primeng/skeleton';
import { BadgeModule } from 'primeng/badge';
import { DividerModule } from 'primeng/divider';
import { AuthService } from '../../core/auth/auth.service';
import { DashboardService } from '../../core/services/dashboard.service';
import {
  ApproverDashboard,
  PendingApprovalItem,
  RecentDecision,
  ApprovalStats
} from '../../core/models/dashboard.model';
import { Subject, takeUntil, interval } from 'rxjs';

@Component({
  selector: 'app-approver-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    CardModule,
    ChartModule,
    TableModule,
    TagModule,
    ButtonModule,
    TimelineModule,
    TooltipModule,
    SkeletonModule,
    BadgeModule,
    DividerModule
  ],
  template: `
    <div class="dashboard-container">
      <!-- Header -->
      <div class="dashboard-header">
        <div class="header-left">
          <h1>Approver Dashboard</h1>
          <p>Welcome back, {{ currentUser()?.firstName }}!</p>
        </div>
        <div class="header-stats">
          @if (!isLoading() && dashboardData()?.stats) {
            <div class="stat-badge pending">
              <i class="pi pi-clock"></i>
              <span>{{ dashboardData()!.stats.pendingCount }} Pending</span>
            </div>
            @if (dashboardData()!.stats.averageResponseTimeHours) {
              <div class="stat-badge info">
                <i class="pi pi-stopwatch"></i>
                <span>Avg {{ dashboardData()!.stats.averageResponseTimeHours | number:'1.0-1' }}h Response</span>
              </div>
            }
          }
        </div>
      </div>

      <!-- Main Grid -->
      <div class="main-grid">
        <!-- Pending Approvals -->
        <div class="approvals-section">
          <p-card styleClass="pending-card">
            <ng-template pTemplate="header">
              <div class="card-header">
                <div class="header-title">
                  <h3>Pending Approvals</h3>
                  @if (!isLoading() && dashboardData()?.pendingApprovals?.length) {
                    <p-badge [value]="dashboardData()!.pendingApprovals.length.toString()" severity="danger"></p-badge>
                  }
                </div>
              </div>
            </ng-template>

            @if (isLoading()) {
              <div class="p-4">
                @for (i of [1, 2, 3]; track i) {
                  <p-skeleton width="100%" height="120px" styleClass="mb-3"></p-skeleton>
                }
              </div>
            } @else {
              <div class="approvals-list">
                @for (approval of dashboardData()?.pendingApprovals; track approval.workflowId) {
                  <div class="approval-card" [ngClass]="{'urgent': approval.isUrgent, 'overdue': approval.isOverdue}">
                    <div class="approval-header">
                      <div class="approval-reference">
                        <span class="reference">{{ approval.tenderReference }}</span>
                        <span class="level-badge">Level {{ approval.currentLevel }}/{{ approval.totalLevels }}</span>
                      </div>
                      <div class="approval-urgency">
                        @if (approval.isOverdue) {
                          <span class="urgency-tag overdue">
                            <i class="pi pi-exclamation-triangle"></i>
                            Overdue
                          </span>
                        } @else if (approval.isUrgent) {
                          <span class="urgency-tag urgent">
                            <i class="pi pi-clock"></i>
                            Urgent
                          </span>
                        } @else if (approval.daysUntilDeadline !== null && approval.daysUntilDeadline !== undefined) {
                          <span class="urgency-tag normal">
                            {{ approval.daysUntilDeadline }}d left
                          </span>
                        }
                      </div>
                    </div>

                    <h4 class="approval-title">{{ approval.tenderTitle }}</h4>

                    <div class="approval-details">
                      <div class="detail-item">
                        <i class="pi pi-building"></i>
                        <span>{{ approval.clientName }}</span>
                      </div>
                      @if (approval.tenderValue) {
                        <div class="detail-item">
                          <i class="pi pi-wallet"></i>
                          <span>{{ approval.tenderValue | currency:approval.currency:'symbol':'1.0-0' }}</span>
                        </div>
                      }
                      <div class="detail-item">
                        <i class="pi pi-user"></i>
                        <span>{{ approval.initiatedByName }}</span>
                      </div>
                      <div class="detail-item">
                        <i class="pi pi-calendar"></i>
                        <span>{{ approval.submittedAt | date:'mediumDate' }}</span>
                      </div>
                    </div>

                    <div class="approval-actions">
                      <button pButton label="Review" icon="pi pi-eye"
                              class="p-button-outlined p-button-sm"
                              [routerLink]="['/tenders', approval.tenderId]"
                              [queryParams]="{tab: 'approval'}"></button>
                      <button pButton label="Approve" icon="pi pi-check"
                              class="p-button-success p-button-sm"
                              (click)="onQuickApprove(approval)"></button>
                    </div>
                  </div>
                } @empty {
                  <div class="empty-state">
                    <i class="pi pi-check-circle"></i>
                    <h4>All Caught Up!</h4>
                    <p>No pending approvals at this time.</p>
                  </div>
                }
              </div>
            }
          </p-card>
        </div>

        <!-- Right Column: Stats + Recent Activity -->
        <div class="sidebar-section">
          <!-- Stats Card -->
          <p-card header="My Approval Stats" styleClass="stats-card">
            @if (isLoading()) {
              <p-skeleton width="100%" height="200px"></p-skeleton>
            } @else if (dashboardData()?.stats) {
              <div class="stats-chart">
                <p-chart type="bar" [data]="chartData()" [options]="chartOptions" height="200"></p-chart>
              </div>
              <p-divider></p-divider>
              <div class="stats-summary">
                <div class="summary-item">
                  <span class="summary-label">This Month</span>
                  <span class="summary-value">{{ dashboardData()!.stats.totalThisMonth }}</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">Approval Rate</span>
                  <span class="summary-value">{{ getApprovalRate() }}%</span>
                </div>
              </div>
            }
          </p-card>

          <!-- Recent Decisions -->
          <p-card styleClass="activity-card">
            <ng-template pTemplate="header">
              <div class="card-header">
                <h3>Recent Decisions</h3>
              </div>
            </ng-template>

            @if (isLoading()) {
              <p-skeleton width="100%" height="300px"></p-skeleton>
            } @else {
              <div class="decisions-list">
                @for (decision of dashboardData()?.recentDecisions; track decision.id) {
                  <div class="decision-item" [routerLink]="['/tenders', decision.tenderId]">
                    <div class="decision-icon" [ngClass]="getDecisionIconClass(decision.decision)">
                      <i class="pi" [ngClass]="getDecisionIcon(decision.decision)"></i>
                    </div>
                    <div class="decision-content">
                      <div class="decision-header">
                        <span class="decision-reference">{{ decision.tenderReference }}</span>
                        <p-tag [value]="decision.decisionText"
                               [severity]="getDecisionSeverity(decision.decision)"
                               styleClass="decision-tag"></p-tag>
                      </div>
                      <p class="decision-title">{{ decision.tenderTitle }}</p>
                      @if (decision.comment) {
                        <p class="decision-comment">"{{ decision.comment | slice:0:60 }}{{ decision.comment.length > 60 ? '...' : '' }}"</p>
                      }
                      <span class="decision-time">{{ getRelativeTime(decision.decidedAt) }}</span>
                    </div>
                  </div>
                } @empty {
                  <div class="empty-state small">
                    <i class="pi pi-history"></i>
                    <p>No recent decisions</p>
                  </div>
                }
              </div>
            }
          </p-card>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .dashboard-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .dashboard-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 1rem;
    }

    .header-left h1 {
      margin: 0;
      font-size: 1.75rem;
      color: var(--bayan-slate-900);
      font-weight: 600;
    }

    .header-left p {
      margin: 0.25rem 0 0;
      color: var(--bayan-slate-500);
    }

    .header-stats {
      display: flex;
      gap: 0.75rem;
    }

    .stat-badge {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.5rem 1rem;
      border-radius: var(--bayan-radius-full);
      font-size: 0.875rem;
      font-weight: 500;
    }

    .stat-badge.pending {
      background: var(--bayan-warning-bg);
      color: var(--bayan-warning);
    }

    .stat-badge.info {
      background: var(--bayan-primary-light);
      color: var(--bayan-primary);
    }

    /* Main Grid */
    .main-grid {
      display: grid;
      grid-template-columns: 1.5fr 1fr;
      gap: 1.5rem;
    }

    @media (max-width: 1024px) {
      .main-grid {
        grid-template-columns: 1fr;
      }
    }

    .sidebar-section {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    /* Card Headers */
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--bayan-border);
    }

    .header-title {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .card-header h3 {
      margin: 0;
      font-size: 1.125rem;
      font-weight: 600;
      color: var(--bayan-slate-900);
    }

    :host ::ng-deep .pending-card,
    :host ::ng-deep .activity-card {
      .p-card {
        background: var(--bayan-card);
        box-shadow: var(--bayan-shadow-sm);
        border-radius: var(--bayan-radius-lg);
        border: 1px solid var(--bayan-border);
      }
      .p-card-header {
        padding: 0;
      }
      .p-card-body {
        padding: 0;
      }
      .p-card-content {
        padding: 0;
      }
    }

    :host ::ng-deep .stats-card {
      .p-card {
        background: var(--bayan-card);
        box-shadow: var(--bayan-shadow-sm);
        border-radius: var(--bayan-radius-lg);
        border: 1px solid var(--bayan-border);
      }
      .p-card-title {
        color: var(--bayan-slate-900);
        font-weight: 600;
        font-size: 1.125rem;
      }
      .p-card-body {
        padding: 1rem;
      }
    }

    /* Approval Cards */
    .approvals-list {
      display: flex;
      flex-direction: column;
    }

    .approval-card {
      padding: 1.25rem;
      border-bottom: 1px solid var(--bayan-border);
      border-left: 4px solid var(--bayan-warning);
      transition: background-color var(--bayan-transition);
    }

    .approval-card:last-child {
      border-bottom: none;
    }

    .approval-card:hover {
      background-color: var(--bayan-slate-50);
    }

    .approval-card.urgent {
      background: var(--bayan-warning-bg);
      border-left: 4px solid var(--bayan-warning);
    }

    .approval-card.overdue {
      background: var(--bayan-danger-bg);
      border-left: 4px solid var(--bayan-danger);
    }

    .approval-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 0.5rem;
    }

    .approval-reference {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .reference {
      font-weight: 600;
      color: var(--bayan-slate-900);
      font-size: 0.9375rem;
    }

    .level-badge {
      background: var(--bayan-primary-light);
      color: var(--bayan-primary);
      padding: 0.125rem 0.5rem;
      border-radius: var(--bayan-radius-full);
      font-size: 0.75rem;
      font-weight: 500;
    }

    .urgency-tag {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      padding: 0.25rem 0.5rem;
      border-radius: var(--bayan-radius-full);
      font-size: 0.75rem;
      font-weight: 600;
    }

    .urgency-tag.overdue {
      background: var(--bayan-danger-bg);
      color: var(--bayan-danger);
    }

    .urgency-tag.urgent {
      background: var(--bayan-warning-bg);
      color: var(--bayan-warning);
    }

    .urgency-tag.normal {
      background: var(--bayan-slate-100);
      color: var(--bayan-slate-500);
    }

    .approval-title {
      margin: 0 0 0.75rem;
      font-size: 1rem;
      font-weight: 600;
      color: var(--bayan-slate-900);
      line-height: 1.4;
    }

    .approval-details {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .detail-item {
      display: flex;
      align-items: center;
      gap: 0.375rem;
      font-size: 0.8rem;
      color: var(--bayan-slate-500);
    }

    .detail-item i {
      font-size: 0.75rem;
      color: var(--bayan-slate-400);
    }

    .approval-actions {
      display: flex;
      gap: 0.5rem;
    }

    /* Stats Chart */
    .stats-chart {
      margin-bottom: 0.5rem;
    }

    .stats-summary {
      display: flex;
      justify-content: space-around;
      padding-top: 0.5rem;
    }

    .summary-item {
      text-align: center;
    }

    .summary-label {
      display: block;
      font-size: 0.75rem;
      color: var(--bayan-slate-500);
      margin-bottom: 0.25rem;
    }

    .summary-value {
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--bayan-slate-900);
    }

    /* Decisions List */
    .decisions-list {
      display: flex;
      flex-direction: column;
    }

    .decision-item {
      display: flex;
      gap: 0.75rem;
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--bayan-border);
      cursor: pointer;
      transition: background-color var(--bayan-transition);
    }

    .decision-item:last-child {
      border-bottom: none;
    }

    .decision-item:hover {
      background-color: var(--bayan-slate-50);
    }

    .decision-icon {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .decision-icon i {
      font-size: 0.875rem;
      color: var(--bayan-primary-foreground);
    }

    .decision-icon.approved {
      background: var(--bayan-success);
    }

    .decision-icon.rejected {
      background: var(--bayan-danger);
    }

    .decision-icon.returned {
      background: var(--bayan-warning);
    }

    .decision-content {
      flex: 1;
      min-width: 0;
    }

    .decision-header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.25rem;
    }

    .decision-reference {
      font-weight: 600;
      font-size: 0.8rem;
      color: var(--bayan-slate-900);
    }

    :host ::ng-deep .decision-tag {
      font-size: 0.625rem;
      padding: 0.125rem 0.375rem;
    }

    .decision-title {
      margin: 0 0 0.25rem;
      font-size: 0.8rem;
      color: var(--bayan-slate-500);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .decision-comment {
      margin: 0 0 0.25rem;
      font-size: 0.75rem;
      color: var(--bayan-slate-500);
      font-style: italic;
    }

    .decision-time {
      font-size: 0.6875rem;
      color: var(--bayan-slate-400);
    }

    /* Empty States */
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem 2rem;
      color: var(--bayan-slate-500);
    }

    .empty-state i {
      font-size: 2.5rem;
      margin-bottom: 1rem;
      color: var(--bayan-slate-400);
    }

    .empty-state h4 {
      margin: 0 0 0.5rem;
      font-size: 1.125rem;
      color: var(--bayan-slate-700);
    }

    .empty-state p {
      margin: 0;
      font-size: 0.875rem;
      color: var(--bayan-slate-500);
    }

    .empty-state.small {
      padding: 2rem;
    }

    .empty-state.small i {
      font-size: 2rem;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .dashboard-header {
        flex-direction: column;
        align-items: stretch;
      }

      .header-stats {
        justify-content: center;
      }

      .approval-details {
        flex-direction: column;
        gap: 0.5rem;
      }

      .approval-actions {
        flex-direction: column;
      }

      .approval-actions button {
        width: 100%;
      }
    }
  `]
})
export class ApproverDashboardComponent implements OnInit, OnDestroy {
  private readonly authService = inject(AuthService);
  private readonly dashboardService = inject(DashboardService);
  private readonly destroy$ = new Subject<void>();

  currentUser = this.authService.currentUser;
  isLoading = this.dashboardService.isLoading;

  dashboardData = signal<ApproverDashboard | null>(null);

  chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      x: {
        grid: {
          display: false
        },
        ticks: { color: '#64748B', font: { size: 11 } }
      },
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 5,
          color: '#64748B',
          font: { size: 11 }
        },
        grid: { color: '#E2E8F0' }
      }
    }
  };

  chartData = signal<any>({
    labels: ['Approved', 'Rejected', 'Returned'],
    datasets: [
      {
        data: [0, 0, 0],
        backgroundColor: ['#16A34A', '#DC2626', '#D97706'],
        borderRadius: 6,
        barThickness: 40
      }
    ]
  });

  ngOnInit(): void {
    this.loadDashboardData();

    // Refresh data every 2 minutes for approvals (more frequent)
    interval(2 * 60 * 1000)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => this.loadDashboardData());
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadDashboardData(): void {
    this.dashboardService.getApproverDashboard()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.dashboardData.set(data);
          this.updateChartData(data.stats);
        },
        error: (error) => console.error('Failed to load approver dashboard data:', error)
      });
  }

  private updateChartData(stats: ApprovalStats): void {
    this.chartData.set({
      labels: ['Approved', 'Rejected', 'Returned'],
      datasets: [
        {
          data: [stats.approvedCount, stats.rejectedCount, stats.returnedCount],
          backgroundColor: ['#16A34A', '#DC2626', '#D97706'],
          borderRadius: 6,
          barThickness: 40
        }
      ]
    });
  }

  getApprovalRate(): number {
    const stats = this.dashboardData()?.stats;
    if (!stats) return 0;
    const total = stats.approvedCount + stats.rejectedCount + stats.returnedCount;
    if (total === 0) return 0;
    return Math.round((stats.approvedCount / total) * 100);
  }

  getDecisionIcon(decision: string): string {
    switch (decision) {
      case 'Approve':
        return 'pi-check';
      case 'Reject':
        return 'pi-times';
      case 'ReturnForRevision':
        return 'pi-replay';
      default:
        return 'pi-question';
    }
  }

  getDecisionIconClass(decision: string): string {
    switch (decision) {
      case 'Approve':
        return 'approved';
      case 'Reject':
        return 'rejected';
      case 'ReturnForRevision':
        return 'returned';
      default:
        return '';
    }
  }

  getDecisionSeverity(decision: string): 'success' | 'danger' | 'warn' | 'info' | 'secondary' | 'contrast' | undefined {
    switch (decision) {
      case 'Approve':
        return 'success';
      case 'Reject':
        return 'danger';
      case 'ReturnForRevision':
        return 'warn';
      default:
        return 'info';
    }
  }

  getRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  }

  onQuickApprove(approval: PendingApprovalItem): void {
    // This would typically open a confirmation dialog
    // For now, navigate to the tender detail page
    console.log('Quick approve:', approval.workflowId);
  }
}
