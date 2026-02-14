import {
  Component,
  OnInit,
  OnDestroy,
  inject,
  signal,
  computed
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { BadgeModule } from 'primeng/badge';
import { TooltipModule } from 'primeng/tooltip';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { DividerModule } from 'primeng/divider';

import { ApprovalService } from '../../../../core/services/approval.service';
import { PendingApprovalItem } from '../../../../core/models/approval.model';

@Component({
  selector: 'app-pending-approvals-widget',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    CardModule,
    ButtonModule,
    TagModule,
    BadgeModule,
    TooltipModule,
    ProgressSpinnerModule,
    DividerModule
  ],
  template: `
    <p-card styleClass="pending-approvals-card">
      <ng-template pTemplate="header">
        <div class="widget-header">
          <div class="header-title">
            <i class="pi pi-check-circle"></i>
            <span>Pending Approvals</span>
            @if (totalCount() > 0) {
              <p-badge [value]="totalCount().toString()" severity="contrast"></p-badge>
            }
          </div>
          @if (overdueCount() > 0) {
            <p-tag
              [value]="overdueCount() + ' overdue'"
              severity="danger"
              icon="pi pi-exclamation-triangle"
            ></p-tag>
          }
        </div>
      </ng-template>

      @if (approvalService.isLoading() && pendingApprovals().length === 0) {
        <div class="loading-container">
          <p-progressSpinner
            [style]="{ width: '40px', height: '40px' }"
            strokeWidth="4"
          ></p-progressSpinner>
        </div>
      } @else if (pendingApprovals().length === 0) {
        <div class="empty-state">
          <i class="pi pi-check-circle empty-icon"></i>
          <p>No pending approvals</p>
          <span class="empty-subtitle">You're all caught up!</span>
        </div>
      } @else {
        <div class="approvals-list">
          @for (item of pendingApprovals(); track item.id; let i = $index) {
            <div class="approval-card" [class.overdue]="item.isOverdue" [class.approaching]="item.isApproaching && !item.isOverdue">
              <div class="card-header">
                <div class="tender-info">
                  <span class="tender-title" [pTooltip]="item.tenderTitle">
                    {{ item.tenderTitle | slice:0:40 }}{{ item.tenderTitle.length > 40 ? '...' : '' }}
                  </span>
                  <span class="tender-reference">{{ item.tenderReference }}</span>
                </div>
                <div class="urgency-indicator">
                  @if (item.isOverdue) {
                    <p-tag value="Overdue" severity="danger" icon="pi pi-exclamation-circle"></p-tag>
                  } @else if (item.isApproaching) {
                    <p-tag value="Due Soon" severity="warn" icon="pi pi-clock"></p-tag>
                  }
                </div>
              </div>

              <div class="card-body">
                <div class="info-row">
                  <div class="info-item">
                    <span class="info-label">Value</span>
                    <span class="info-value value-highlight">
                      {{ item.tenderValue | number:'1.0-0' }} {{ item.currency }}
                    </span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">Level</span>
                    <span class="info-value">
                      <span class="level-badge">{{ item.level }}</span>
                    </span>
                  </div>
                </div>

                <div class="info-row">
                  <div class="info-item">
                    <span class="info-label">Submitted</span>
                    <span class="info-value">{{ item.submittedAt | date:'mediumDate' }}</span>
                  </div>
                  @if (item.deadline) {
                    <div class="info-item">
                      <span class="info-label">Deadline</span>
                      <span class="info-value" [class.overdue-text]="item.isOverdue">
                        {{ item.deadline | date:'mediumDate' }}
                      </span>
                    </div>
                  }
                </div>

                <div class="initiator-row">
                  <span class="info-label">Initiated by:</span>
                  <span class="info-value">{{ item.initiatorName }}</span>
                </div>
              </div>

              <div class="card-footer">
                <button
                  pButton
                  label="Review"
                  icon="pi pi-arrow-right"
                  iconPos="right"
                  class="p-button-sm p-button-outlined"
                  [routerLink]="['/tenders', item.tenderId]"
                  [queryParams]="{ tab: 'approval' }"
                ></button>
              </div>
            </div>

            @if (i < pendingApprovals().length - 1) {
              <p-divider></p-divider>
            }
          }
        </div>

        @if (totalCount() > 5) {
          <div class="view-all-footer">
            <button
              pButton
              label="View All Pending Approvals"
              icon="pi pi-list"
              class="p-button-text p-button-sm"
              routerLink="/approvals"
            ></button>
          </div>
        }
      }
    </p-card>
  `,
  styles: [`
    :host ::ng-deep .pending-approvals-card {
      height: 100%;
    }

    :host ::ng-deep .pending-approvals-card .p-card-header {
      padding: 1rem 1.25rem;
      background-color: var(--bayan-accent, #F1F5F9);
      border-bottom: 1px solid var(--bayan-border, #E2E8F0);
    }

    :host ::ng-deep .pending-approvals-card .p-card-body {
      padding: 0;
    }

    :host ::ng-deep .pending-approvals-card .p-card-content {
      padding: 0;
    }

    .widget-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .header-title {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: 600;
      color: var(--bayan-foreground, #0F172A);
    }

    .header-title i {
      font-size: 1.25rem;
      color: var(--bayan-primary, #4F46E5);
    }

    .loading-container {
      display: flex;
      justify-content: center;
      padding: 2rem;
    }

    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 2rem;
      text-align: center;
    }

    .empty-icon {
      font-size: 3rem;
      color: var(--bayan-success, #16A34A);
      margin-bottom: 0.5rem;
    }

    .empty-state p {
      margin: 0;
      font-weight: 500;
      color: var(--bayan-foreground, #0F172A);
    }

    .empty-subtitle {
      font-size: 0.9rem;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .approvals-list {
      max-height: 500px;
      overflow-y: auto;
    }

    .approval-card {
      padding: 1rem 1.25rem;
      transition: background-color 0.2s;
    }

    .approval-card:hover {
      background-color: var(--bayan-accent, #F1F5F9);
    }

    .approval-card.overdue {
      border-left: 4px solid var(--bayan-danger, #DC2626);
      background-color: var(--bayan-danger-bg, #FEF2F2);
    }

    .approval-card.approaching {
      border-left: 4px solid var(--bayan-warning, #D97706);
      background-color: var(--bayan-warning-bg, #FFFBEB);
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 0.75rem;
    }

    .tender-info {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .tender-title {
      font-weight: 600;
      color: var(--bayan-foreground, #0F172A);
      font-size: 0.95rem;
    }

    .tender-reference {
      font-size: 0.8rem;
      color: var(--bayan-muted-foreground, #64748B);
      font-family: monospace;
    }

    .card-body {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      margin-bottom: 0.75rem;
    }

    .info-row {
      display: flex;
      justify-content: space-between;
      gap: 1rem;
    }

    .info-item {
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
    }

    .info-label {
      font-size: 0.75rem;
      color: var(--bayan-muted-foreground, #64748B);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .info-value {
      font-size: 0.9rem;
      color: var(--bayan-foreground, #0F172A);
    }

    .value-highlight {
      font-weight: 600;
      color: var(--bayan-primary, #4F46E5);
    }

    .level-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background-color: var(--bayan-primary, #4F46E5);
      color: white;
      font-weight: 600;
      font-size: 0.8rem;
    }

    .overdue-text {
      color: var(--bayan-danger, #DC2626);
      font-weight: 500;
    }

    .initiator-row {
      display: flex;
      gap: 0.5rem;
      align-items: center;
      padding-top: 0.25rem;
    }

    .initiator-row .info-label {
      text-transform: none;
    }

    .card-footer {
      display: flex;
      justify-content: flex-end;
    }

    .view-all-footer {
      display: flex;
      justify-content: center;
      padding: 0.75rem;
      border-top: 1px solid var(--bayan-border, #E2E8F0);
      background-color: var(--bayan-accent, #F1F5F9);
    }

    :host ::ng-deep .pending-approvals-card .p-badge {
      background-color: var(--bayan-primary, #4F46E5) !important;
      color: white !important;
    }

    :host ::ng-deep .pending-approvals-card .card-footer .p-button-outlined {
      border-color: var(--bayan-primary, #4F46E5);
      color: var(--bayan-primary, #4F46E5);
    }

    :host ::ng-deep .pending-approvals-card .card-footer .p-button-outlined:hover {
      background-color: var(--bayan-primary-ring, rgba(79,70,229,0.15));
    }

    :host ::ng-deep .p-divider {
      margin: 0;
    }

    @media (max-width: 600px) {
      .widget-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
      }

      .card-header {
        flex-direction: column;
        gap: 0.5rem;
      }

      .info-row {
        flex-direction: column;
        gap: 0.5rem;
      }
    }
  `]
})
export class PendingApprovalsWidgetComponent implements OnInit, OnDestroy {
  readonly approvalService = inject(ApprovalService);
  private readonly destroy$ = new Subject<void>();

  // Data
  pendingApprovals = signal<PendingApprovalItem[]>([]);

  // Computed
  totalCount = computed(() => this.pendingApprovals().length);
  overdueCount = computed(() => this.pendingApprovals().filter(p => p.isOverdue).length);
  approachingCount = computed(() => this.pendingApprovals().filter(p => p.isApproaching && !p.isOverdue).length);

  ngOnInit(): void {
    this.loadPendingApprovals();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadPendingApprovals(): void {
    this.approvalService.getPendingApprovals()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          // Sort: overdue first, then approaching, then by date
          const sorted = response.items.sort((a, b) => {
            if (a.isOverdue && !b.isOverdue) return -1;
            if (!a.isOverdue && b.isOverdue) return 1;
            if (a.isApproaching && !b.isApproaching) return -1;
            if (!a.isApproaching && b.isApproaching) return 1;
            return new Date(a.submittedAt).getTime() - new Date(b.submittedAt).getTime();
          });
          this.pendingApprovals.set(sorted.slice(0, 5)); // Show max 5 items
        },
        error: (error) => {
          console.error('Failed to load pending approvals:', error);
        }
      });
  }

  /**
   * Refresh the pending approvals list
   */
  refresh(): void {
    this.loadPendingApprovals();
  }
}
