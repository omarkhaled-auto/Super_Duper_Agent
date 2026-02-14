import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
  inject,
  signal,
  computed
} from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { Subject, takeUntil } from 'rxjs';

// PrimeNG
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { TagModule } from 'primeng/tag';
import { DividerModule } from 'primeng/divider';
import { ProgressBarModule } from 'primeng/progressbar';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';
import { DialogModule } from 'primeng/dialog';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { MessageService, ConfirmationService } from 'primeng/api';

// Services and Models
import { AuthService } from '../../../../core/auth/auth.service';
import { EvaluationService } from '../../../../core/services/evaluation.service';
import {
  TechnicalSummary,
  PanelistComment,
  EvaluationCriterion,
  BidderAggregatedScore
} from '../../../../core/models/evaluation.model';
import { UserRole } from '../../../../core/models/user.model';

@Component({
  selector: 'app-technical-summary',
  standalone: true,
  imports: [
    CommonModule,
    CardModule,
    ButtonModule,
    TableModule,
    ToastModule,
    TooltipModule,
    TagModule,
    DividerModule,
    ProgressBarModule,
    ProgressSpinnerModule,
    MessageModule,
    DialogModule,
    ConfirmDialogModule
  ],
  providers: [MessageService, ConfirmationService, DecimalPipe],
  template: `
    <p-toast></p-toast>
    <p-confirmDialog></p-confirmDialog>

    <div class="technical-summary-container">
      <!-- Loading State -->
      @if (isLoading()) {
        <div class="loading-container">
          <p-progressSpinner
            [style]="{ width: '50px', height: '50px' }"
            strokeWidth="4"
          ></p-progressSpinner>
          <p>Loading technical summary...</p>
        </div>
      } @else if (summary()) {
        <!-- Status Header -->
        <p-card styleClass="status-card">
          <div class="status-header">
            <div class="status-info">
              <span class="status-label">Panelist Completion Status</span>
              <span class="status-value">
                {{ summary()!.completedPanelists }} / {{ summary()!.totalPanelists }} completed
              </span>
            </div>
            <p-progressBar
              [value]="completionPercentage()"
              [showValue]="false"
              styleClass="completion-bar"
            ></p-progressBar>
            @if (summary()!.completedPanelists === summary()!.totalPanelists) {
              <p-tag value="All Panelists Completed" severity="success" styleClass="mt-2"></p-tag>
            } @else {
              <p-tag value="In Progress" severity="info" styleClass="mt-2"></p-tag>
            }
          </div>
        </p-card>

        <!-- Raw Scores Matrix -->
        <p-card header="Raw Scores (Panelist x Bidder x Criteria)" styleClass="matrix-card">
          <div class="table-wrapper">
            <p-table [value]="summary()!.panelistScores" styleClass="p-datatable-sm p-datatable-gridlines">
              <ng-template pTemplate="header">
                <tr>
                  <th rowspan="2" style="min-width: 150px">Panelist</th>
                  @for (bidder of summary()!.bidders; track bidder.bidderId) {
                    <th [attr.colspan]="summary()!.criteria.length" class="text-center bidder-header">
                      {{ blindMode ? bidder.blindCode : bidder.bidderName }}
                    </th>
                  }
                </tr>
                <tr>
                  @for (bidder of summary()!.bidders; track bidder.bidderId) {
                    @for (criterion of summary()!.criteria; track criterion.id) {
                      <th class="text-center criterion-header" [pTooltip]="criterion.name">
                        {{ getCriterionShortName(criterion) }}
                      </th>
                    }
                  }
                </tr>
              </ng-template>
              <ng-template pTemplate="body" let-panelist>
                <tr>
                  <td>
                    <div class="panelist-cell">
                      <span class="panelist-name">{{ panelist.panelistName }}</span>
                      @if (panelist.completedAt) {
                        <i class="pi pi-check-circle text-green-500" pTooltip="Completed"></i>
                      } @else {
                        <i class="pi pi-clock text-orange-500" pTooltip="Pending"></i>
                      }
                    </div>
                  </td>
                  @for (bidder of summary()!.bidders; track bidder.bidderId) {
                    @for (criterion of summary()!.criteria; track criterion.id) {
                      <td class="text-center score-cell">
                        {{ panelist.scores[bidder.bidderId]?.[criterion.id] ?? '-' }}
                      </td>
                    }
                  }
                </tr>
              </ng-template>
            </p-table>
          </div>
        </p-card>

        <!-- Aggregated Scores -->
        <p-card header="Aggregated Scores" styleClass="aggregated-card">
          <p-table
            [value]="summary()!.aggregatedScores"
            styleClass="p-datatable-sm p-datatable-striped"
            [sortField]="'rank'"
            [sortOrder]="1"
          >
            <ng-template pTemplate="header">
              <tr>
                <th style="width: 60px">Rank</th>
                <th style="min-width: 180px">Bidder</th>
                @for (criterion of summary()!.criteria; track criterion.id) {
                  <th class="text-center">
                    <div class="criterion-col-header">
                      <span>{{ criterion.name }}</span>
                      <span class="weight-label">({{ criterion.weight }}%)</span>
                    </div>
                  </th>
                }
                <th class="text-center" style="width: 100px">Average</th>
                <th class="text-center" style="width: 80px">Alerts</th>
              </tr>
            </ng-template>
            <ng-template pTemplate="body" let-score>
              <tr [class.winner-row]="score.rank === 1">
                <td class="text-center">
                  <span class="rank-badge" [class.rank-1]="score.rank === 1">
                    #{{ score.rank }}
                  </span>
                </td>
                <td>
                  <div class="bidder-cell">
                    <span class="bidder-name">{{ blindMode ? score.blindCode : score.bidderName }}</span>
                    @if (score.rank === 1) {
                      <p-tag value="Top Ranked" severity="success" styleClass="ml-2"></p-tag>
                    }
                  </div>
                </td>
                @for (criterion of summary()!.criteria; track criterion.id) {
                  <td class="text-center">
                    <div class="criterion-score-cell">
                      <span
                        class="avg-score"
                        [class.has-variance]="score.criteriaScores[criterion.id]?.hasVarianceAlert"
                      >
                        {{ score.criteriaScores[criterion.id]?.average | number:'1.2-2' }}
                      </span>
                      @if (score.criteriaScores[criterion.id]?.hasVarianceAlert) {
                        <i
                          class="pi pi-exclamation-triangle variance-alert"
                          [pTooltip]="'StdDev: ' + (score.criteriaScores[criterion.id]?.stdDev | number:'1.2-2')"
                        ></i>
                      }
                    </div>
                  </td>
                }
                <td class="text-center">
                  <span class="total-average">{{ score.totalAverage | number:'1.2-2' }}</span>
                </td>
                <td class="text-center">
                  @if (score.hasVarianceAlerts) {
                    <p-tag
                      value="Variance"
                      severity="warn"
                      pTooltip="One or more criteria have StdDev > {{ summary()!.varianceThreshold }}"
                    ></p-tag>
                  } @else {
                    <span class="no-alerts">-</span>
                  }
                </td>
              </tr>
            </ng-template>
          </p-table>

          <!-- Variance Alert Info -->
          @if (hasAnyVarianceAlerts()) {
            <p-message
              severity="warn"
              styleClass="mt-3"
            >
              <ng-template pTemplate="content">
                <div class="variance-info">
                  <i class="pi pi-exclamation-triangle"></i>
                  <span>
                    <strong>Variance Alerts Detected:</strong> Some criteria have a standard deviation > {{ summary()!.varianceThreshold }},
                    indicating significant disagreement among panelists. Consider reviewing comments and discussing with the panel.
                  </span>
                </div>
              </ng-template>
            </p-message>
          }
        </p-card>

        <!-- Action Buttons -->
        <div class="action-bar">
          <button
            pButton
            label="View Detailed Comments"
            icon="pi pi-comments"
            class="p-button-outlined"
            (click)="showCommentsDialog = true; loadComments()"
          ></button>

          @if (canLockScores()) {
            <button
              pButton
              label="Lock Scores"
              icon="pi pi-lock"
              class="p-button-warning"
              [loading]="isLocking()"
              [disabled]="summary()!.completedPanelists < summary()!.totalPanelists || summary()!.status === 'locked'"
              (click)="confirmLockScores()"
            ></button>
          }
        </div>

        @if (summary()!.status === 'locked') {
          <p-message
            severity="info"
            text="Technical scores have been locked and cannot be modified."
            styleClass="mt-3"
          ></p-message>
        }
      } @else {
        <!-- No Data -->
        <div class="empty-state">
          <i class="pi pi-chart-bar" style="font-size: 3rem; color: var(--bayan-slate-300, #CBD5E1);"></i>
          <h3>No Summary Available</h3>
          <p>Technical evaluation data is not yet available.</p>
        </div>
      }
    </div>

    <!-- Comments Dialog -->
    <p-dialog
      header="Detailed Comments"
      [(visible)]="showCommentsDialog"
      [modal]="true"
      [style]="{ width: '800px', maxHeight: '80vh' }"
      [closable]="true"
      [draggable]="false"
    >
      @if (isLoadingComments()) {
        <div class="loading-container">
          <p-progressSpinner [style]="{ width: '40px', height: '40px' }"></p-progressSpinner>
          <p>Loading comments...</p>
        </div>
      } @else if (comments().length > 0) {
        <div class="comments-list">
          @for (comment of comments(); track comment) {
            <div class="comment-item">
              <div class="comment-header">
                <div class="comment-meta">
                  <span class="panelist-name">{{ comment.panelistName }}</span>
                  <i class="pi pi-arrow-right"></i>
                  <span class="bidder-name">{{ comment.bidderName }}</span>
                  <span class="criterion-name">{{ comment.criterionName }}</span>
                </div>
                <div class="comment-score">
                  <p-tag [value]="'Score: ' + comment.score" [severity]="getScoreSeverity(comment.score)"></p-tag>
                </div>
              </div>
              <div class="comment-body">
                {{ comment.comment }}
              </div>
              <div class="comment-footer">
                <span class="comment-date">{{ comment.submittedAt | date:'medium' }}</span>
              </div>
            </div>
          }
        </div>
      } @else {
        <div class="empty-comments">
          <i class="pi pi-comments" style="font-size: 2rem; color: var(--bayan-slate-300, #CBD5E1);"></i>
          <p>No comments have been submitted yet.</p>
        </div>
      }

      <ng-template pTemplate="footer">
        <button
          pButton
          label="Close"
          class="p-button-text"
          (click)="showCommentsDialog = false"
        ></button>
      </ng-template>
    </p-dialog>
  `,
  styles: [`
    .technical-summary-container {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem;
      gap: 1rem;
    }

    .loading-container p {
      color: var(--bayan-muted-foreground, #64748B);
      margin: 0;
    }

    /* Status Card — KPI-style with indigo left border */
    :host ::ng-deep .status-card .p-card {
      border-left: 4px solid var(--bayan-primary, #4F46E5);
    }

    .status-header {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .status-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .status-info .status-label {
      font-weight: 500;
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .status-info .status-value {
      font-size: 1.125rem;
      font-weight: 700;
      color: var(--bayan-foreground, #0F172A);
    }

    :host ::ng-deep .completion-bar .p-progressbar {
      height: 10px;
      border-radius: 5px;
    }

    :host ::ng-deep .completion-bar .p-progressbar-value {
      background: var(--bayan-primary, #4F46E5);
    }

    /* Matrix Card */
    .table-wrapper {
      overflow-x: auto;
    }

    :host ::ng-deep .matrix-card .p-datatable th {
      color: var(--bayan-foreground-secondary, #475569);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 0.75rem;
      letter-spacing: 0.025em;
    }

    .bidder-header {
      background: var(--bayan-accent, #EEF2FF) !important;
      border-bottom: 2px solid var(--bayan-primary, #4F46E5);
    }

    .criterion-header {
      font-size: 0.75rem;
      background: var(--bayan-muted, #F8FAFC);
      min-width: 50px;
    }

    .panelist-cell {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .panelist-name {
      font-weight: 500;
    }

    .score-cell {
      min-width: 40px;
    }

    /* Aggregated Card */
    .criterion-col-header {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.25rem;
    }

    .weight-label {
      font-size: 0.75rem;
      color: var(--bayan-muted-foreground, #64748B);
      font-weight: 400;
    }

    .winner-row {
      background: var(--bayan-success-bg, #f0fdf4) !important;
    }

    .rank-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: var(--bayan-border, #E2E8F0);
      font-weight: 600;
      font-size: 0.875rem;
      color: var(--bayan-foreground, #0F172A);
    }

    .rank-badge.rank-1 {
      background: #FFFBEB;
      border: 2px solid #D97706;
      color: #92400E;
    }

    .rank-badge.rank-2 {
      background: #F8FAFC;
      border: 2px solid #94A3B8;
      color: #475569;
    }

    .rank-badge.rank-3 {
      background: #FFFBEB;
      border: 2px solid #B45309;
      color: #78350F;
    }

    .bidder-cell {
      display: flex;
      align-items: center;
    }

    .bidder-name {
      font-weight: 500;
    }

    .criterion-score-cell {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.25rem;
    }

    .avg-score {
      font-weight: 500;
    }

    .avg-score.has-variance {
      color: #D97706;
    }

    .variance-alert {
      background: #FFFBEB;
      border-left: 3px solid #D97706;
      color: #92400E;
      font-size: 0.875rem;
      padding: 0.125rem 0.375rem;
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .total-average {
      font-size: 1.125rem;
      font-weight: 700;
      color: var(--bayan-primary, #4F46E5);
    }

    .no-alerts {
      color: var(--bayan-muted-foreground, #64748B);
    }

    .variance-info {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
    }

    .variance-info i {
      color: #D97706;
      margin-top: 0.125rem;
    }

    /* Pass/Fail indicators */
    .pi-check-circle {
      color: #16A34A;
    }

    .pi-times-circle {
      color: #DC2626;
    }

    /* Action Bar */
    .action-bar {
      display: flex;
      justify-content: flex-end;
      gap: 1rem;
      padding: 1rem 0;
    }

    /* Empty State */
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem;
      gap: 1rem;
      text-align: center;
    }

    .empty-state h3 {
      margin: 0;
      color: var(--bayan-foreground, #0F172A);
    }

    .empty-state p {
      margin: 0;
      color: var(--bayan-muted-foreground, #64748B);
    }

    /* Comments Dialog */
    .comments-list {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      max-height: 60vh;
      overflow-y: auto;
    }

    .comment-item {
      padding: 1rem;
      background: var(--bayan-accent, #F8FAFC);
      border-radius: var(--bayan-radius, 0.5rem);
      border-left: 3px solid var(--bayan-primary, #4F46E5);
    }

    .comment-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.75rem;
    }

    .comment-meta {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.9rem;
    }

    .comment-meta .panelist-name {
      font-weight: 600;
      color: var(--bayan-primary, #4F46E5);
    }

    .comment-meta i {
      color: var(--bayan-muted-foreground, #64748B);
      font-size: 0.75rem;
    }

    .comment-meta .bidder-name {
      font-weight: 500;
    }

    .comment-meta .criterion-name {
      color: var(--bayan-muted-foreground, #64748B);
      background: var(--bayan-border, #E2E8F0);
      padding: 0.125rem 0.5rem;
      border-radius: var(--bayan-radius-sm, 0.375rem);
      font-size: 0.8rem;
    }

    .comment-body {
      color: var(--bayan-foreground, #0F172A);
      line-height: 1.5;
      margin-bottom: 0.5rem;
    }

    .comment-footer {
      font-size: 0.8rem;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .empty-comments {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem;
      gap: 1rem;
      text-align: center;
    }

    .empty-comments p {
      color: var(--bayan-muted-foreground, #64748B);
      margin: 0;
    }

    /* Card titles → slate-900 */
    :host ::ng-deep .p-card .p-card-title {
      color: var(--bayan-foreground, #0F172A);
    }

    /* All border-radius overrides to use CSS var */
    :host ::ng-deep .p-card {
      border-radius: var(--bayan-radius, 0.5rem);
    }

    /* Responsive */
    @media (max-width: 768px) {
      .action-bar {
        flex-direction: column;
      }

      .action-bar button {
        width: 100%;
      }

      .comment-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
      }

      .comment-meta {
        flex-wrap: wrap;
      }
    }
  `]
})
export class TechnicalSummaryComponent implements OnInit, OnDestroy {
  @Input() tenderId!: number;
  @Input() blindMode = true;
  @Output() scoresLocked = new EventEmitter<void>();

  private readonly authService = inject(AuthService);
  private readonly evaluationService = inject(EvaluationService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly decimalPipe = inject(DecimalPipe);
  private readonly destroy$ = new Subject<void>();

  // State signals
  summary = signal<TechnicalSummary | null>(null);
  comments = signal<PanelistComment[]>([]);
  isLoading = signal<boolean>(true);
  isLoadingComments = signal<boolean>(false);
  isLocking = signal<boolean>(false);

  // Dialog state
  showCommentsDialog = false;

  // Computed
  canLockScores = computed(() => this.authService.hasRole([UserRole.ADMIN, UserRole.TENDER_MANAGER]));

  completionPercentage = computed(() => {
    const s = this.summary();
    if (!s || s.totalPanelists === 0) return 0;
    return Math.round((s.completedPanelists / s.totalPanelists) * 100);
  });

  ngOnInit(): void {
    this.loadSummary();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadSummary(): void {
    this.isLoading.set(true);

    this.evaluationService.getTechnicalSummary(this.tenderId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (summary) => {
          this.summary.set(summary);
          this.isLoading.set(false);
        },
        error: (error) => {
          this.isLoading.set(false);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to load technical summary'
          });
        }
      });
  }

  getCriterionShortName(criterion: EvaluationCriterion): string {
    // Return abbreviation or first few characters
    const words = criterion.name.split(' ');
    if (words.length === 1) {
      return criterion.name.substring(0, 3).toUpperCase();
    }
    return words.map(w => w[0]).join('').toUpperCase();
  }

  hasAnyVarianceAlerts(): boolean {
    const s = this.summary();
    if (!s) return false;
    return s.aggregatedScores.some(score => score.hasVarianceAlerts);
  }

  getScoreSeverity(score: number): 'success' | 'info' | 'warn' | 'danger' {
    if (score >= 8) return 'success';
    if (score >= 6) return 'info';
    if (score >= 4) return 'warn';
    return 'danger';
  }

  loadComments(): void {
    if (this.comments().length > 0) return;

    this.isLoadingComments.set(true);

    this.evaluationService.getDetailedComments(this.tenderId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (comments) => {
          this.comments.set(comments);
          this.isLoadingComments.set(false);
        },
        error: (error) => {
          this.isLoadingComments.set(false);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to load comments'
          });
        }
      });
  }

  confirmLockScores(): void {
    this.confirmationService.confirm({
      message: 'Are you sure you want to lock the technical scores? This action is irreversible and no further modifications will be allowed.',
      header: 'Lock Technical Scores',
      icon: 'pi pi-lock',
      acceptLabel: 'Lock Scores',
      rejectLabel: 'Cancel',
      acceptButtonStyleClass: 'p-button-warning',
      accept: () => {
        this.lockScores();
      }
    });
  }

  private lockScores(): void {
    this.isLocking.set(true);

    this.evaluationService.lockTechnicalScores(this.tenderId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.isLocking.set(false);
          this.summary.update(s => s ? { ...s, status: 'locked' } : null);
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Technical scores have been locked successfully'
          });
          this.scoresLocked.emit();
        },
        error: (error) => {
          this.isLocking.set(false);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to lock scores'
          });
        }
      });
  }
}
