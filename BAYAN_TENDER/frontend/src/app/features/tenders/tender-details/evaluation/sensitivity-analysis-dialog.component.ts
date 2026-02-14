import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
  inject,
  signal
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject, takeUntil } from 'rxjs';

// PrimeNG
import { DialogModule } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';

// Services and Models
import { EvaluationService } from '../../../../core/services/evaluation.service';
import {
  SensitivityAnalysis,
  SensitivityRow,
  WeightSplit,
  DEFAULT_WEIGHT_SPLITS
} from '../../../../core/models/evaluation.model';

@Component({
  selector: 'app-sensitivity-analysis-dialog',
  standalone: true,
  imports: [
    CommonModule,
    DialogModule,
    ButtonModule,
    TableModule,
    TagModule,
    TooltipModule,
    ProgressSpinnerModule,
    MessageModule,
    ToastModule
  ],
  providers: [MessageService],
  template: `
    <p-toast></p-toast>

    <p-dialog
      header="Sensitivity Analysis"
      [(visible)]="visible"
      [modal]="true"
      [style]="{ width: '900px', maxWidth: '95vw' }"
      [closable]="true"
      [draggable]="false"
      (onHide)="onClose()"
    >
      <div data-testid="sensitivity-analysis">
      @if (isLoading()) {
        <div class="loading-container">
          <p-progressSpinner
            [style]="{ width: '40px', height: '40px' }"
            strokeWidth="4"
          ></p-progressSpinner>
          <p>Loading sensitivity analysis...</p>
        </div>
      } @else if (analysis()) {
        <div class="sensitivity-content">
          <!-- Info Message -->
          <p-message
            severity="info"
            styleClass="mb-3"
          >
            <ng-template pTemplate="content">
              <div class="info-content">
                <i class="pi pi-info-circle"></i>
                <span>
                  This analysis shows how bidder rankings change across different Technical/Commercial weight scenarios.
                  Rows highlighted in <span class="highlight-winner">green</span> indicate scenarios where the bidder is the winner.
                </span>
              </div>
            </ng-template>
          </p-message>

          <!-- Sensitivity Table -->
          <div class="table-wrapper">
            <p-table
              [value]="analysis()!.rows"
              styleClass="p-datatable-sm p-datatable-gridlines sensitivity-table"
            >
              <ng-template pTemplate="header">
                <tr>
                  <th style="min-width: 180px">Bidder</th>
                  @for (split of analysis()!.weightSplits; track split) {
                    <th class="text-center weight-col">
                      <div class="weight-header">
                        <span class="tech-weight">{{ split.technicalWeight }}%</span>
                        <span class="separator">/</span>
                        <span class="comm-weight">{{ split.commercialWeight }}%</span>
                      </div>
                      <div class="weight-labels">
                        <span>Tech</span>
                        <span>Comm</span>
                      </div>
                    </th>
                  }
                  <th class="text-center" style="width: 100px">Status</th>
                </tr>
              </ng-template>
              <ng-template pTemplate="body" let-row>
                <tr [class.has-change]="row.hasRankChange">
                  <td>
                    <div class="bidder-cell">
                      <span class="bidder-name">{{ row.bidderName }}</span>
                      @if (row.winnerAtSplits.length > 0) {
                        <p-tag
                          [value]="'Winner at ' + row.winnerAtSplits.length + ' scenario(s)'"
                          severity="success"
                          styleClass="ml-2"
                        ></p-tag>
                      }
                    </div>
                  </td>
                  @for (split of analysis()!.weightSplits; track split) {
                    <td
                      class="text-center rank-cell"
                      [class.winner-cell]="isWinnerAtSplit(row, split)"
                    >
                      <span class="rank-value" [class.rank-1]="row.ranks[getSplitKey(split)] === 1">
                        #{{ row.ranks[getSplitKey(split)] }}
                      </span>
                    </td>
                  }
                  <td class="text-center">
                    @if (row.hasRankChange) {
                      <p-tag
                        value="Rank Varies"
                        severity="warn"
                        pTooltip="Rank changes based on weight configuration"
                      ></p-tag>
                    } @else {
                      <p-tag
                        value="Stable"
                        severity="secondary"
                        pTooltip="Rank is consistent across all scenarios"
                      ></p-tag>
                    }
                  </td>
                </tr>
              </ng-template>
            </p-table>
          </div>

          <!-- Winner Changes Summary -->
          @if (analysis()!.winnerChanges.length > 0) {
            <div class="winner-changes">
              <h4>
                <i class="pi pi-exclamation-triangle"></i>
                Winner Changes Detected
              </h4>
              <div class="changes-list">
                @for (change of analysis()!.winnerChanges; track change.split) {
                  <div class="change-item">
                    <span class="change-split">At {{ change.split }}:</span>
                    <span class="change-from">{{ change.previousWinner }}</span>
                    <i class="pi pi-arrow-right"></i>
                    <span class="change-to">{{ change.newWinner }}</span>
                  </div>
                }
              </div>
              <p-message
                severity="warn"
                text="The recommended winner may change depending on the weight configuration. Consider carefully when finalizing the evaluation."
                styleClass="mt-2"
              ></p-message>
            </div>
          } @else {
            <p-message
              severity="success"
              text="The recommended winner remains consistent across all tested weight scenarios."
              styleClass="mt-3"
            ></p-message>
          }
        </div>
      } @else {
        <div class="empty-state">
          <i class="pi pi-chart-line" style="font-size: 2rem; color: var(--bayan-muted-foreground, #64748B); opacity: 0.5;"></i>
          <p>Unable to load sensitivity analysis.</p>
        </div>
      }
      </div>

      <ng-template pTemplate="footer">
        <button
          pButton
          label="Close"
          icon="pi pi-times"
          class="p-button-text"
          (click)="onClose()"
        ></button>
      </ng-template>
    </p-dialog>
  `,
  styles: [`
    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem;
      gap: 1rem;
    }

    .loading-container p {
      color: var(--bayan-muted-foreground, #64748B);
      margin: 0;
    }

    .sensitivity-content {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .info-content {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
    }

    .info-content i {
      color: var(--bayan-primary, #4F46E5);
      margin-top: 0.125rem;
    }

    .highlight-winner {
      background: #DCFCE7;
      padding: 0.125rem 0.375rem;
      border-radius: var(--bayan-radius, 0.5rem);
      font-weight: 500;
      color: #15803D;
    }

    .table-wrapper {
      overflow-x: auto;
    }

    :host ::ng-deep .sensitivity-table {
      .p-datatable-thead > tr > th {
        background: var(--bayan-accent, #EEF2FF);
        padding: 0.75rem 0.5rem;
        border-color: var(--bayan-border, #E2E8F0);
      }

      .p-datatable-tbody > tr > td {
        padding: 0.75rem 0.5rem;
        border-color: var(--bayan-border, #E2E8F0);
      }
    }

    .weight-col {
      min-width: 100px;
    }

    .weight-header {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.25rem;
      font-weight: 700;
      font-size: 1rem;
    }

    .tech-weight {
      color: var(--bayan-primary, #4F46E5);
    }

    .comm-weight {
      color: var(--bayan-success, #16A34A);
    }

    .separator {
      color: var(--bayan-muted-foreground, #64748B);
    }

    .weight-labels {
      display: flex;
      justify-content: space-around;
      font-size: 0.7rem;
      color: var(--bayan-muted-foreground, #64748B);
      font-weight: 400;
      margin-top: 0.25rem;
    }

    .bidder-cell {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .bidder-name {
      font-weight: 500;
      color: var(--bayan-foreground, #0F172A);
    }

    .rank-cell {
      transition: background-color 0.2s ease;
    }

    .rank-cell.winner-cell {
      background: #DCFCE7 !important;
      color: #15803D;
    }

    .rank-value {
      font-weight: 600;
      color: var(--bayan-muted-foreground, #64748B);
      font-variant-numeric: tabular-nums;
      text-align: right;
    }

    .rank-value.rank-1 {
      color: #D97706;
      font-size: 1.125rem;
    }

    .rank-value.rank-2 {
      color: #94A3B8;
    }

    .rank-value.rank-3 {
      color: #B45309;
    }

    .has-change {
      background: #FEF2F2 !important;
    }

    .has-change.improved {
      background: #F0FDF4 !important;
    }

    .text-center {
      text-align: center;
    }

    /* Winner Changes */
    .winner-changes {
      background: #FFFBEB;
      padding: 1rem;
      border-radius: var(--bayan-radius, 0.5rem);
      border-left: 3px solid var(--bayan-warning, #D97706);
    }

    .winner-changes h4 {
      margin: 0 0 0.75rem 0;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: #B45309;
      font-size: 1rem;
    }

    .changes-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .change-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.5rem;
      background: white;
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .change-split {
      font-weight: 600;
      color: var(--bayan-muted-foreground, #64748B);
      min-width: 80px;
    }

    .change-from {
      color: #dc2626;
      text-decoration: line-through;
    }

    .change-item i {
      color: var(--bayan-muted-foreground, #64748B);
    }

    .change-to {
      color: var(--bayan-success, #16A34A);
      font-weight: 600;
    }

    /* Empty State */
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem;
      gap: 1rem;
      text-align: center;
    }

    .empty-state p {
      color: var(--bayan-muted-foreground, #64748B);
      margin: 0;
    }
  `]
})
export class SensitivityAnalysisDialogComponent implements OnInit, OnDestroy {
  @Input() tenderId!: number;
  @Input() visible = false;
  @Output() visibleChange = new EventEmitter<boolean>();

  private readonly evaluationService = inject(EvaluationService);
  private readonly messageService = inject(MessageService);
  private readonly destroy$ = new Subject<void>();

  // State signals
  analysis = signal<SensitivityAnalysis | null>(null);
  isLoading = signal<boolean>(true);

  ngOnInit(): void {
    if (this.visible) {
      this.loadAnalysis();
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadAnalysis(): void {
    this.isLoading.set(true);

    this.evaluationService.getSensitivityAnalysis(this.tenderId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (analysis) => {
          this.analysis.set(analysis);
          this.isLoading.set(false);
        },
        error: (error) => {
          this.isLoading.set(false);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to load sensitivity analysis'
          });
        }
      });
  }

  getSplitKey(split: WeightSplit): string {
    return `${split.technicalWeight}/${split.commercialWeight}`;
  }

  isWinnerAtSplit(row: SensitivityRow, split: WeightSplit): boolean {
    const key = this.getSplitKey(split);
    return row.winnerAtSplits.includes(key);
  }

  onClose(): void {
    this.visible = false;
    this.visibleChange.emit(false);
  }
}
