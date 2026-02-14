import { Component, inject, OnInit, signal, computed, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ChartModule } from 'primeng/chart';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { TimelineModule } from 'primeng/timeline';
import { ProgressBarModule } from 'primeng/progressbar';
import { TooltipModule } from 'primeng/tooltip';
import { SkeletonModule } from 'primeng/skeleton';
import { AuthService } from '../../core/auth/auth.service';
import { DashboardService } from '../../core/services/dashboard.service';
import {
  TenderManagerDashboard,
  DashboardKpi,
  ActiveTender,
  DeadlineItem,
  ActivityFeedItem
} from '../../core/models/dashboard.model';
import { Subject, takeUntil, interval } from 'rxjs';

@Component({
  selector: 'app-dashboard',
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
    ProgressBarModule,
    TooltipModule,
    SkeletonModule
  ],
  template: `
    <div class="dashboard-container">
      <!-- Header with Quick Actions -->
      <div class="dashboard-header">
        <div class="header-left">
          <h1>Tender Manager Dashboard</h1>
          <p>Welcome back, {{ currentUser()?.firstName }}!</p>
        </div>
        <div class="header-actions">
          <button pButton label="New Tender" icon="pi pi-plus"
                  class="p-button-primary" routerLink="/tenders/new"></button>
          <button pButton label="Import Bidders" icon="pi pi-upload"
                  class="p-button-outlined" routerLink="/admin/bidders"></button>
        </div>
      </div>

      <!-- Error Banner -->
      @if (loadError()) {
        <div class="error-banner" data-testid="dashboard-error">
          <i class="pi pi-exclamation-triangle"></i>
          <span>{{ loadError() }}</span>
          <button pButton label="Retry" icon="pi pi-refresh" class="p-button-text p-button-sm" (click)="retryLoad()"></button>
        </div>
      }

      <!-- KPI Cards -->
      <div class="kpi-grid" data-testid="kpi-grid">
        @if (isLoading()) {
          @for (i of [1, 2, 3, 4]; track i) {
            <p-card styleClass="kpi-card">
              <p-skeleton width="100%" height="80px"></p-skeleton>
            </p-card>
          }
        } @else {
          @for (kpi of dashboardData()?.kpis; track kpi.name) {
            <p-card [styleClass]="'kpi-card kpi-' + kpi.color" [attr.data-testid]="'kpi-card-' + kpi.name">
              <div class="kpi-content">
                <div class="kpi-info">
                  <span class="kpi-title">{{ kpi.name }}</span>
                  <span class="kpi-value">{{ kpi.value }}</span>
                  @if (kpi.change !== undefined && kpi.change !== null) {
                    <span class="kpi-change" [class.positive]="kpi.changeIsPositive" [class.negative]="!kpi.changeIsPositive">
                      <i class="pi" [ngClass]="kpi.changeIsPositive ? 'pi-arrow-up' : 'pi-arrow-down'"></i>
                      {{ kpi.change > 0 ? '+' : '' }}{{ kpi.change }}% from last month
                    </span>
                  }
                </div>
                <div class="kpi-icon" [ngClass]="'icon-' + kpi.color">
                  <i class="pi" [ngClass]="kpi.icon"></i>
                </div>
              </div>
            </p-card>
          }
        }
      </div>

      <!-- Main Content Grid -->
      <div class="main-grid">
        <!-- Left Column: Active Tenders Table + Upcoming Deadlines -->
        <div class="left-column">
          <!-- Active Tenders Table -->
          <p-card styleClass="table-card" data-testid="active-tenders-card">
            <ng-template pTemplate="header">
              <div class="card-header">
                <h3>Active Tenders</h3>
                <button pButton label="View All" icon="pi pi-arrow-right" iconPos="right"
                        class="p-button-text p-button-sm" routerLink="/tenders"></button>
              </div>
            </ng-template>
            @if (isLoading()) {
              <p-skeleton width="100%" height="300px"></p-skeleton>
            } @else {
              <p-table [value]="dashboardData()?.activeTenders || []" [paginator]="false"
                       styleClass="p-datatable-sm p-datatable-striped">
                <ng-template pTemplate="header">
                  <tr>
                    <th>Reference</th>
                    <th>Title</th>
                    <th>Client</th>
                    <th>Status</th>
                    <th>Bids</th>
                    <th>Deadline</th>
                    <th></th>
                  </tr>
                </ng-template>
                <ng-template pTemplate="body" let-tender>
                  <tr>
                    <td class="font-semibold">{{ tender.reference }}</td>
                    <td>
                      <span class="tender-title" [pTooltip]="tender.title">{{ tender.title | slice:0:30 }}{{ tender.title.length > 30 ? '...' : '' }}</span>
                    </td>
                    <td>{{ tender.clientName }}</td>
                    <td>
                      <p-tag [value]="tender.statusText" [severity]="getStatusSeverity(tender.status)"></p-tag>
                    </td>
                    <td>
                      <span class="bid-count">{{ tender.bidsReceived }}/{{ tender.invitedBidders }}</span>
                    </td>
                    <td>
                      <span [ngClass]="{'text-danger': tender.daysRemaining < 0, 'text-warning': tender.daysRemaining >= 0 && tender.daysRemaining <= 3}">
                        {{ tender.daysRemaining >= 0 ? tender.daysRemaining + ' days' : 'Overdue' }}
                      </span>
                    </td>
                    <td>
                      <button pButton icon="pi pi-eye" class="p-button-text p-button-sm p-button-rounded"
                              [routerLink]="['/tenders', tender.id]" pTooltip="View Details"></button>
                    </td>
                  </tr>
                </ng-template>
                <ng-template pTemplate="emptymessage">
                  <tr>
                    <td colspan="7" class="text-center p-4">
                      <i class="pi pi-inbox" style="font-size: 2.5rem; color: var(--bayan-slate-300); margin-bottom: 0.5rem; display: block;"></i>
                      <p style="color: var(--bayan-slate-500); margin: 0;">No active tenders found</p>
                    </td>
                  </tr>
                </ng-template>
              </p-table>
            }
          </p-card>

          <!-- Upcoming Deadlines Widget -->
          <p-card styleClass="deadlines-card">
            <ng-template pTemplate="header">
              <div class="card-header">
                <h3>Upcoming Deadlines</h3>
                <span class="badge">Next 7 Days</span>
              </div>
            </ng-template>
            @if (isLoading()) {
              <p-skeleton width="100%" height="200px"></p-skeleton>
            } @else {
              <div class="deadlines-list">
                @for (deadline of dashboardData()?.upcomingDeadlines; track deadline.tenderId + deadline.deadlineType) {
                  <div class="deadline-item" [ngClass]="{'urgent': deadline.isUrgent, 'overdue': deadline.isOverdue}">
                    <div class="deadline-icon">
                      <i class="pi" [ngClass]="getDeadlineIcon(deadline.deadlineType)"></i>
                    </div>
                    <div class="deadline-info">
                      <div class="deadline-header">
                        <span class="deadline-reference">{{ deadline.tenderReference }}</span>
                        <span class="deadline-type">{{ deadline.deadlineType }}</span>
                      </div>
                      <span class="deadline-title">{{ deadline.tenderTitle }}</span>
                    </div>
                    <div class="deadline-countdown">
                      @if (deadline.isOverdue) {
                        <span class="countdown overdue">Overdue</span>
                      } @else if (deadline.isUrgent) {
                        <span class="countdown urgent">
                          <i class="pi pi-clock"></i>
                          {{ deadline.hoursRemaining }}h
                        </span>
                      } @else {
                        <span class="countdown">{{ deadline.daysRemaining }}d</span>
                      }
                    </div>
                  </div>
                } @empty {
                  <div class="empty-state">
                    <i class="pi pi-calendar-times"></i>
                    <p>No upcoming deadlines</p>
                  </div>
                }
              </div>
            }
          </p-card>
        </div>

        <!-- Right Column: Activity Feed -->
        <div class="right-column">
          <p-card styleClass="activity-card">
            <ng-template pTemplate="header">
              <div class="card-header">
                <h3>Recent Activity</h3>
              </div>
            </ng-template>
            @if (isLoading()) {
              <p-skeleton width="100%" height="400px"></p-skeleton>
            } @else {
              <div class="activity-feed" data-testid="activity-feed">
                @for (activity of dashboardData()?.recentActivity; track activity.id) {
                  <div class="activity-item" [routerLink]="getActivityLink(activity)"
                       [class.clickable]="!!activity.entityId">
                    <div class="activity-icon" [ngClass]="'icon-' + activity.color">
                      <i class="pi" [ngClass]="activity.icon"></i>
                    </div>
                    <div class="activity-content">
                      <p class="activity-description">{{ activity.description }}</p>
                      <div class="activity-meta">
                        <span class="activity-user">
                          <i class="pi pi-user"></i>
                          {{ activity.performedBy || 'System' }}
                        </span>
                        <span class="activity-time">{{ getRelativeTime(activity.occurredAt) }}</span>
                      </div>
                    </div>
                  </div>
                } @empty {
                  <div class="empty-state">
                    <i class="pi pi-history"></i>
                    <p>No recent activity</p>
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

    .error-banner {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem 1rem;
      background: var(--bayan-red-50, #fef2f2);
      border: 1px solid var(--bayan-red-200, #fecaca);
      border-radius: 8px;
      color: var(--bayan-red-700, #b91c1c);
      font-size: 0.875rem;
    }

    .error-banner i {
      font-size: 1.25rem;
    }

    .error-banner span {
      flex: 1;
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

    .header-actions {
      display: flex;
      gap: 0.75rem;
    }

    /* KPI Cards */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem;
    }

    @media (max-width: 1200px) {
      .kpi-grid {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    @media (max-width: 640px) {
      .kpi-grid {
        grid-template-columns: 1fr;
      }
    }

    :host ::ng-deep .kpi-card {
      .p-card {
        background: var(--bayan-card);
        box-shadow: var(--bayan-shadow-sm);
        border-radius: var(--bayan-radius-lg);
        border: 1px solid var(--bayan-border);
        overflow: hidden;
      }
      .p-card-body {
        padding: 1.25rem;
      }
    }

    :host ::ng-deep .kpi-blue .p-card {
      border-left: 4px solid var(--bayan-primary);
    }
    :host ::ng-deep .kpi-green .p-card {
      border-left: 4px solid var(--bayan-success);
    }
    :host ::ng-deep .kpi-orange .p-card {
      border-left: 4px solid var(--bayan-warning);
    }
    :host ::ng-deep .kpi-red .p-card {
      border-left: 4px solid var(--bayan-danger);
    }
    :host ::ng-deep .kpi-purple .p-card {
      border-left: 4px solid var(--bayan-primary);
    }
    :host ::ng-deep .kpi-gray .p-card {
      border-left: 4px solid var(--bayan-slate-400);
    }
    :host ::ng-deep .kpi-gold .p-card {
      border-left: 4px solid var(--bayan-warning);
    }

    .kpi-content {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }

    .kpi-info {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .kpi-title {
      font-size: 0.8rem;
      color: var(--bayan-slate-500);
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .kpi-value {
      font-size: 1.5rem;
      font-weight: 600;
      color: var(--bayan-slate-900);
    }

    .kpi-change {
      font-size: 0.75rem;
      display: flex;
      align-items: center;
      gap: 0.25rem;
    }

    .kpi-change.positive {
      color: var(--bayan-success);
    }

    .kpi-change.negative {
      color: var(--bayan-danger);
    }

    .kpi-icon {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .kpi-icon i {
      font-size: 1.25rem;
      color: var(--bayan-primary-foreground);
    }

    .icon-blue { background: var(--bayan-primary); }
    .icon-blue i { color: var(--bayan-primary-foreground); }
    .icon-green { background: var(--bayan-success); }
    .icon-green i { color: var(--bayan-primary-foreground); }
    .icon-orange { background: var(--bayan-warning); }
    .icon-orange i { color: var(--bayan-primary-foreground); }
    .icon-red { background: var(--bayan-danger); }
    .icon-red i { color: var(--bayan-primary-foreground); }
    .icon-purple { background: var(--bayan-primary); }
    .icon-purple i { color: var(--bayan-primary-foreground); }
    .icon-gray { background: var(--bayan-slate-400); }
    .icon-gray i { color: var(--bayan-primary-foreground); }
    .icon-gold { background: var(--bayan-warning); }
    .icon-gold i { color: var(--bayan-primary-foreground); }

    /* Main Grid */
    .main-grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 1.5rem;
    }

    @media (max-width: 1024px) {
      .main-grid {
        grid-template-columns: 1fr;
      }
    }

    .left-column, .right-column {
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

    .card-header h3 {
      margin: 0;
      font-size: 1rem;
      font-weight: 600;
      color: var(--bayan-slate-900);
    }

    .card-header .badge {
      background: var(--bayan-primary-light);
      color: var(--bayan-primary);
      padding: 0.25rem 0.5rem;
      border-radius: var(--bayan-radius-full);
      font-size: 0.75rem;
      font-weight: 500;
    }

    :host ::ng-deep .table-card,
    :host ::ng-deep .deadlines-card,
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

    /* Table Styles */
    :host ::ng-deep .p-datatable {
      .p-datatable-thead > tr > th {
        background: var(--bayan-slate-50);
        font-weight: 600;
        color: var(--bayan-slate-600);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 0.75rem 1rem;
      }
      .p-datatable-tbody > tr > td {
        padding: 0.75rem 1rem;
        font-size: 0.875rem;
        color: var(--bayan-slate-700);
      }
      .p-datatable-tbody > tr:hover > td {
        background: var(--bayan-slate-50);
      }
    }

    .tender-title {
      color: var(--bayan-slate-900);
    }

    .bid-count {
      font-weight: 500;
      color: var(--bayan-slate-900);
    }

    .text-danger {
      color: var(--bayan-danger) !important;
      font-weight: 600;
    }

    .text-warning {
      color: var(--bayan-warning) !important;
      font-weight: 500;
    }

    /* Deadlines Widget */
    .deadlines-list {
      display: flex;
      flex-direction: column;
    }

    .deadline-item {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--bayan-border);
      transition: background-color var(--bayan-transition);
    }

    .deadline-item:last-child {
      border-bottom: none;
    }

    .deadline-item:hover {
      background-color: var(--bayan-slate-50);
    }

    .deadline-item.urgent {
      background-color: var(--bayan-warning-bg);
    }

    .deadline-item.overdue {
      background-color: var(--bayan-danger-bg);
    }

    .deadline-icon {
      width: 40px;
      height: 40px;
      border-radius: var(--bayan-radius);
      background: var(--bayan-slate-100);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .deadline-icon i {
      font-size: 1rem;
      color: var(--bayan-slate-500);
    }

    .deadline-item.urgent .deadline-icon {
      background: var(--bayan-warning-bg);
    }

    .deadline-item.urgent .deadline-icon i {
      color: var(--bayan-warning);
    }

    .deadline-item.overdue .deadline-icon {
      background: var(--bayan-danger-bg);
    }

    .deadline-item.overdue .deadline-icon i {
      color: var(--bayan-danger);
    }

    .deadline-info {
      flex: 1;
      min-width: 0;
    }

    .deadline-header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.25rem;
    }

    .deadline-reference {
      font-weight: 600;
      color: var(--bayan-slate-900);
      font-size: 0.875rem;
    }

    .deadline-type {
      font-size: 0.75rem;
      color: var(--bayan-slate-500);
      background: var(--bayan-slate-100);
      padding: 0.125rem 0.375rem;
      border-radius: var(--bayan-radius-sm);
    }

    .deadline-title {
      font-size: 0.8rem;
      color: var(--bayan-slate-500);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .deadline-countdown {
      flex-shrink: 0;
    }

    .countdown {
      font-weight: 600;
      font-size: 0.875rem;
      color: var(--bayan-slate-500);
      display: flex;
      align-items: center;
      gap: 0.25rem;
    }

    .countdown.urgent {
      color: var(--bayan-warning);
    }

    .countdown.overdue {
      color: var(--bayan-danger);
    }

    /* Activity Feed — Timeline Pattern */
    .activity-feed {
      display: flex;
      flex-direction: column;
      max-height: 500px;
      overflow-y: auto;
      position: relative;
    }

    .activity-feed::before {
      content: '';
      position: absolute;
      left: calc(1.25rem + 18px);
      top: 1rem;
      bottom: 1rem;
      width: 2px;
      background: var(--bayan-slate-200);
    }

    .activity-item {
      display: flex;
      gap: 0.75rem;
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--bayan-border);
      transition: background-color var(--bayan-transition);
      position: relative;
    }

    .activity-item:last-child {
      border-bottom: none;
    }

    .activity-item.clickable {
      cursor: pointer;
    }

    .activity-item.clickable:hover {
      background-color: var(--bayan-slate-50);
    }

    .activity-icon {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      z-index: 1;
    }

    .activity-icon i {
      font-size: 0.875rem;
      color: var(--bayan-primary-foreground);
    }

    .activity-content {
      flex: 1;
      min-width: 0;
    }

    .activity-description {
      margin: 0 0 0.25rem;
      font-size: 0.875rem;
      color: var(--bayan-slate-700);
      line-height: 1.4;
    }

    .activity-description a,
    .activity-description .entity-link {
      color: var(--bayan-primary);
      text-decoration: none;
    }

    .activity-description a:hover,
    .activity-description .entity-link:hover {
      text-decoration: underline;
    }

    .activity-meta {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      font-size: 0.75rem;
      color: var(--bayan-slate-400);
    }

    .activity-user {
      display: flex;
      align-items: center;
      gap: 0.25rem;
    }

    .activity-user i {
      font-size: 0.625rem;
    }

    .activity-time {
      color: var(--bayan-slate-400);
    }

    /* Empty States */
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem;
      color: var(--bayan-slate-500);
    }

    .empty-state i {
      font-size: 2.5rem;
      margin-bottom: 0.75rem;
      color: var(--bayan-slate-300);
    }

    .empty-state p {
      margin: 0;
      font-size: 0.875rem;
      color: var(--bayan-slate-500);
    }

    /* Responsive */
    @media (max-width: 768px) {
      .dashboard-header {
        flex-direction: column;
        align-items: stretch;
      }

      .header-actions {
        justify-content: stretch;
      }

      .header-actions button {
        flex: 1;
      }
    }
  `]
})
export class DashboardComponent implements OnInit, OnDestroy {
  private readonly authService = inject(AuthService);
  private readonly dashboardService = inject(DashboardService);
  private readonly destroy$ = new Subject<void>();

  currentUser = this.authService.currentUser;
  isLoading = this.dashboardService.isLoading;

  dashboardData = signal<TenderManagerDashboard | null>(null);
  loadError = signal<string | null>(null);

  ngOnInit(): void {
    this.loadDashboardData();

    // Refresh data every 5 minutes
    interval(5 * 60 * 1000)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => this.loadDashboardData());
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadDashboardData(): void {
    this.loadError.set(null);
    this.dashboardService.getTenderManagerDashboard()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => this.dashboardData.set(data),
        error: (error) => {
          console.error('Failed to load dashboard data:', error);
          this.loadError.set(error?.message || 'Failed to load dashboard data. Please try again.');
        }
      });
  }

  retryLoad(): void {
    this.loadDashboardData();
  }

  getStatusSeverity(status: string): 'success' | 'secondary' | 'info' | 'warn' | 'danger' | 'contrast' | undefined {
    switch (status) {
      case 'Active':
        return 'info';
      case 'Draft':
        return 'secondary';
      case 'Evaluation':
        return 'warn';
      case 'Awarded':
        return 'success';
      case 'Cancelled':
        return 'danger';
      default:
        return undefined;
    }
  }

  getDeadlineIcon(type: string): string {
    switch (type) {
      case 'Submission':
        return 'pi-upload';
      case 'Clarification':
        return 'pi-question-circle';
      case 'Opening':
        return 'pi-folder-open';
      default:
        return 'pi-calendar';
    }
  }

  getActivityLink(activity: ActivityFeedItem): string[] | null {
    if (!activity.entityId) return null;

    switch (activity.entityType) {
      case 'Tender':
        return ['/tenders', activity.entityId];
      case 'BidSubmission':
        return null; // Navigate to bid details
      case 'ApprovalWorkflow':
        return null; // Navigate to approval details
      default:
        return null;
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
}
