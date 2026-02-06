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
import { EvaluationService } from '../../../../core/services/evaluation.service';
import {
  TechnicalSummary,
  PanelistComment,
  EvaluationCriterion,
  BidderAggregatedScore
} from '../../../../core/models/evaluation.model';

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
            (click)="showCommentsDialog = true"
          ></button>

          <button
            pButton
            label="Lock Scores"
            icon="pi pi-lock"
            class="p-button-warning"
            [loading]="isLocking()"
            [disabled]="summary()!.completedPanelists < summary()!.totalPanelists || summary()!.status === 'locked'"
            (click)="confirmLockScores()"
          ></button>
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
          <i class="pi pi-chart-bar" style="font-size: 3rem; color: #ccc;"></i>
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
          <i class="pi pi-comments" style="font-size: 2rem; color: #ccc;"></i>
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
      color: #666;
      margin: 0;
    }

    /* Status Card */
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

    .status-label {
      font-weight: 600;
      color: #333;
    }

    .status-value {
      font-size: 1.125rem;
      font-weight: 600;
      color: #1976D2;
    }

    :host ::ng-deep .completion-bar .p-progressbar {
      height: 10px;
      border-radius: 5px;
    }

    /* Matrix Card */
    .table-wrapper {
      overflow-x: auto;
    }

    .bidder-header {
      background: #f0f7ff !important;
      border-bottom: 2px solid #1976D2;
    }

    .criterion-header {
      font-size: 0.75rem;
      background: #fafafa;
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
      color: #666;
      font-weight: 400;
    }

    .winner-row {
      background: #e8f5e9 !important;
    }

    .rank-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: #e0e0e0;
      font-weight: 600;
      font-size: 0.875rem;
    }

    .rank-badge.rank-1 {
      background: linear-gradient(135deg, #ffd700, #ffaa00);
      color: #333;
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
      color: #ed6c02;
    }

    .variance-alert {
      color: #ed6c02;
      font-size: 0.875rem;
    }

    .total-average {
      font-size: 1.125rem;
      font-weight: 700;
      color: #1976D2;
    }

    .no-alerts {
      color: #999;
    }

    .variance-info {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
    }

    .variance-info i {
      color: #ed6c02;
      margin-top: 0.125rem;
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
      color: #333;
    }

    .empty-state p {
      margin: 0;
      color: #666;
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
      background: #f8f9fa;
      border-radius: 8px;
      border-left: 3px solid #1976D2;
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
      color: #1976D2;
    }

    .comment-meta i {
      color: #999;
      font-size: 0.75rem;
    }

    .comment-meta .bidder-name {
      font-weight: 500;
    }

    .comment-meta .criterion-name {
      color: #666;
      background: #e0e0e0;
      padding: 0.125rem 0.5rem;
      border-radius: 4px;
      font-size: 0.8rem;
    }

    .comment-body {
      color: #333;
      line-height: 1.5;
      margin-bottom: 0.5rem;
    }

    .comment-footer {
      font-size: 0.8rem;
      color: #999;
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
      color: #666;
      margin: 0;
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
