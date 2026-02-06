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
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';

// PrimeNG
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { InputNumberModule } from 'primeng/inputnumber';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { TagModule } from 'primeng/tag';
import { DividerModule } from 'primeng/divider';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';
import { DialogModule } from 'primeng/dialog';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { MessageService, ConfirmationService } from 'primeng/api';

// Services and Models
import { EvaluationService } from '../../../../core/services/evaluation.service';
import {
  CombinedScorecard,
  ScorecardBidder,
  SensitivityAnalysis,
  AwardPack
} from '../../../../core/models/evaluation.model';

// Child Components
import { SensitivityAnalysisDialogComponent } from './sensitivity-analysis-dialog.component';

@Component({
  selector: 'app-combined-scorecard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule,
    TableModule,
    InputNumberModule,
    ToastModule,
    TooltipModule,
    TagModule,
    DividerModule,
    ProgressSpinnerModule,
    MessageModule,
    DialogModule,
    ConfirmDialogModule,
    SensitivityAnalysisDialogComponent
  ],
  providers: [MessageService, ConfirmationService, DecimalPipe],
  template: `
    <p-toast></p-toast>
    <p-confirmDialog></p-confirmDialog>

    <div class="combined-scorecard-container">
      <!-- Loading State -->
      @if (isLoading()) {
        <div class="loading-container">
          <p-progressSpinner
            [style]="{ width: '50px', height: '50px' }"
            strokeWidth="4"
          ></p-progressSpinner>
          <p>Loading scorecard...</p>
        </div>
      } @else if (scorecard()) {
        <!-- Weight Adjuster -->
        <p-card header="Weight Configuration" styleClass="weight-card">
          <div class="weight-adjuster">
            <div class="weight-field">
              <label>Technical Weight (%)</label>
              <p-inputNumber
                [(ngModel)]="technicalWeight"
                [min]="0"
                [max]="100"
                [showButtons]="true"
                suffix="%"
                styleClass="weight-input"
                (onInput)="onWeightChange('technical')"
              ></p-inputNumber>
            </div>

            <div class="weight-divider">
              <i class="pi pi-arrows-h"></i>
            </div>

            <div class="weight-field">
              <label>Commercial Weight (%)</label>
              <p-inputNumber
                [(ngModel)]="commercialWeight"
                [min]="0"
                [max]="100"
                [showButtons]="true"
                suffix="%"
                styleClass="weight-input"
                (onInput)="onWeightChange('commercial')"
              ></p-inputNumber>
            </div>

            <div class="weight-total" [class.invalid]="!isWeightValid()">
              <span class="total-label">Total:</span>
              <span class="total-value">{{ totalWeight() }}%</span>
              @if (!isWeightValid()) {
                <small class="p-error">Must equal 100%</small>
              }
            </div>

            <button
              pButton
              label="Apply"
              icon="pi pi-check"
              class="p-button-sm"
              [disabled]="!isWeightValid() || isRecalculating()"
              [loading]="isRecalculating()"
              (click)="applyWeights()"
            ></button>
          </div>

          <div class="preset-weights">
            <span class="preset-label">Quick Presets:</span>
            <button pButton label="30/70" class="p-button-sm p-button-outlined" (click)="applyPreset(30, 70)"></button>
            <button pButton label="40/60" class="p-button-sm p-button-outlined" (click)="applyPreset(40, 60)"></button>
            <button pButton label="50/50" class="p-button-sm p-button-outlined" (click)="applyPreset(50, 50)"></button>
            <button pButton label="60/40" class="p-button-sm p-button-outlined" (click)="applyPreset(60, 40)"></button>
            <button pButton label="70/30" class="p-button-sm p-button-outlined" (click)="applyPreset(70, 30)"></button>
          </div>
        </p-card>

        <!-- Scorecard Table -->
        <p-card header="Combined Scorecard" styleClass="scorecard-card">
          <p-table
            [value]="scorecard()!.bidders"
            styleClass="p-datatable-sm p-datatable-striped"
          >
            <ng-template pTemplate="header">
              <tr>
                <th style="width: 60px">Rank</th>
                <th style="min-width: 200px">Bidder</th>
                <th class="text-center" style="width: 120px">
                  <div class="col-header">
                    <span>Technical Score</span>
                    <span class="weight-badge">{{ scorecard()!.technicalWeight }}%</span>
                  </div>
                </th>
                <th class="text-center" style="width: 80px">Tech Rank</th>
                <th class="text-center" style="width: 120px">
                  <div class="col-header">
                    <span>Commercial Score</span>
                    <span class="weight-badge">{{ scorecard()!.commercialWeight }}%</span>
                  </div>
                </th>
                <th class="text-center" style="width: 80px">Comm Rank</th>
                <th class="text-center" style="width: 120px">Combined Score</th>
                <th class="text-center" style="width: 80px">Final Rank</th>
              </tr>
            </ng-template>
            <ng-template pTemplate="body" let-bidder>
              <tr [class.winner-row]="bidder.isWinner" [class.disqualified-row]="bidder.isDisqualified">
                <td class="text-center">
                  <span class="rank-badge" [class.rank-1]="bidder.finalRank === 1">
                    #{{ bidder.finalRank }}
                  </span>
                </td>
                <td>
                  <div class="bidder-cell">
                    <span class="bidder-name">{{ bidder.bidderName }}</span>
                    @if (bidder.isWinner) {
                      <p-tag value="Recommended" severity="success" styleClass="ml-2"></p-tag>
                    }
                    @if (bidder.isDisqualified) {
                      <p-tag value="Disqualified" severity="danger" styleClass="ml-2"></p-tag>
                    }
                  </div>
                </td>
                <td class="text-center">
                  <span class="score-value">{{ bidder.technicalScore | number:'1.2-2' }}</span>
                </td>
                <td class="text-center">
                  <span class="rank-value">#{{ bidder.technicalRank }}</span>
                </td>
                <td class="text-center">
                  <span class="score-value">{{ bidder.commercialScore | number:'1.2-2' }}</span>
                </td>
                <td class="text-center">
                  <span class="rank-value">#{{ bidder.commercialRank }}</span>
                </td>
                <td class="text-center">
                  <span class="combined-score" [class.winner]="bidder.isWinner">
                    {{ bidder.combinedScore | number:'1.2-2' }}
                  </span>
                </td>
                <td class="text-center">
                  <span class="final-rank" [class.rank-1]="bidder.finalRank === 1">
                    #{{ bidder.finalRank }}
                  </span>
                </td>
              </tr>
            </ng-template>
          </p-table>
        </p-card>

        <!-- Recommendation -->
        <p-card styleClass="recommendation-card">
          <div class="recommendation">
            <div class="recommendation-icon">
              <i class="pi pi-trophy"></i>
            </div>
            <div class="recommendation-text">
              <h3>Recommended Award</h3>
              <p class="recommended-bidder">{{ scorecard()!.recommendedBidderName }}</p>
              <p class="recommendation-score">
                Combined Score: {{ getWinnerScore() | number:'1.2-2' }}
              </p>
            </div>
          </div>
        </p-card>

        <!-- Action Buttons -->
        <div class="action-bar">
          <button
            pButton
            label="Sensitivity Analysis"
            icon="pi pi-chart-line"
            class="p-button-outlined"
            (click)="openSensitivityDialog()"
          ></button>

          <div class="primary-actions">
            <button
              pButton
              label="Generate Award Pack"
              icon="pi pi-file-pdf"
              class="p-button-info"
              [loading]="isGeneratingPack()"
              (click)="generateAwardPack()"
            ></button>

            <button
              pButton
              label="Start Approval"
              icon="pi pi-send"
              class="p-button-success"
              [loading]="isStartingApproval()"
              (click)="startApproval()"
            ></button>
          </div>
        </div>
      } @else {
        <!-- No Data -->
        <div class="empty-state">
          <i class="pi pi-chart-bar" style="font-size: 3rem; color: #ccc;"></i>
          <h3>No Scorecard Available</h3>
          <p>Combined scorecard data is not yet available. Please complete technical and commercial evaluation first.</p>
        </div>
      }
    </div>

    <!-- Sensitivity Analysis Dialog -->
    @if (showSensitivityDialog) {
      <app-sensitivity-analysis-dialog
        [tenderId]="tenderId"
        [visible]="showSensitivityDialog"
        (visibleChange)="showSensitivityDialog = $event"
      ></app-sensitivity-analysis-dialog>
    }
  `,
  styles: [`
    .combined-scorecard-container {
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

    /* Weight Card */
    .weight-adjuster {
      display: flex;
      align-items: flex-end;
      gap: 1.5rem;
      flex-wrap: wrap;
    }

    .weight-field {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .weight-field label {
      font-weight: 500;
      color: #333;
    }

    :host ::ng-deep .weight-input {
      width: 120px;
    }

    .weight-divider {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0.5rem;
      color: #999;
    }

    .weight-total {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 0.5rem 1rem;
      background: #f0f7ff;
      border-radius: 6px;
      border: 2px solid #1976D2;
    }

    .weight-total.invalid {
      background: #ffebee;
      border-color: #c62828;
    }

    .total-label {
      font-size: 0.8rem;
      color: #666;
    }

    .total-value {
      font-size: 1.25rem;
      font-weight: 700;
      color: #1976D2;
    }

    .weight-total.invalid .total-value {
      color: #c62828;
    }

    .preset-weights {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid #e0e0e0;
      flex-wrap: wrap;
    }

    .preset-label {
      font-size: 0.9rem;
      color: #666;
    }

    /* Scorecard Table */
    .col-header {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.25rem;
    }

    .weight-badge {
      font-size: 0.75rem;
      color: #666;
      background: #f0f0f0;
      padding: 0.125rem 0.5rem;
      border-radius: 4px;
      font-weight: 400;
    }

    .winner-row {
      background: #e8f5e9 !important;
    }

    .disqualified-row {
      background: #ffebee !important;
      opacity: 0.7;
    }

    .rank-badge,
    .final-rank {
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

    .rank-badge.rank-1,
    .final-rank.rank-1 {
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

    .score-value {
      font-weight: 500;
    }

    .rank-value {
      color: #666;
    }

    .combined-score {
      font-size: 1.125rem;
      font-weight: 700;
      color: #333;
    }

    .combined-score.winner {
      color: #2e7d32;
    }

    /* Recommendation Card */
    :host ::ng-deep .recommendation-card {
      background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
    }

    .recommendation {
      display: flex;
      align-items: center;
      gap: 1.5rem;
    }

    .recommendation-icon {
      width: 64px;
      height: 64px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #ffd700, #ffaa00);
      border-radius: 50%;
    }

    .recommendation-icon i {
      font-size: 2rem;
      color: #333;
    }

    .recommendation-text h3 {
      margin: 0 0 0.5rem 0;
      font-size: 1rem;
      color: #666;
      font-weight: 500;
    }

    .recommended-bidder {
      margin: 0;
      font-size: 1.5rem;
      font-weight: 700;
      color: #2e7d32;
    }

    .recommendation-score {
      margin: 0.25rem 0 0 0;
      font-size: 0.9rem;
      color: #666;
    }

    /* Action Bar */
    .action-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 0;
    }

    .primary-actions {
      display: flex;
      gap: 0.75rem;
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
      max-width: 400px;
    }

    .text-center {
      text-align: center;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .weight-adjuster {
        flex-direction: column;
        align-items: stretch;
      }

      .weight-field {
        width: 100%;
      }

      :host ::ng-deep .weight-input {
        width: 100%;
      }

      .weight-divider {
        display: none;
      }

      .recommendation {
        flex-direction: column;
        text-align: center;
      }

      .action-bar {
        flex-direction: column;
        gap: 1rem;
      }

      .action-bar button,
      .primary-actions {
        width: 100%;
      }

      .primary-actions {
        flex-direction: column;
      }
    }
  `]
})
export class CombinedScorecardComponent implements OnInit, OnDestroy {
  @Input() tenderId!: number;
  @Output() approvalStarted = new EventEmitter<void>();
  @Output() awardPackGenerated = new EventEmitter<AwardPack>();

  private readonly evaluationService = inject(EvaluationService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly decimalPipe = inject(DecimalPipe);
  private readonly destroy$ = new Subject<void>();

  // State signals
  scorecard = signal<CombinedScorecard | null>(null);
  isLoading = signal<boolean>(true);
  isRecalculating = signal<boolean>(false);
  isGeneratingPack = signal<boolean>(false);
  isStartingApproval = signal<boolean>(false);

  // Weight form
  technicalWeight = 40;
  commercialWeight = 60;

  // Dialog state
  showSensitivityDialog = false;

  // Computed
  totalWeight = computed(() => this.technicalWeight + this.commercialWeight);

  ngOnInit(): void {
    this.loadScorecard();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadScorecard(): void {
    this.isLoading.set(true);

    this.evaluationService.getCombinedScorecard(this.tenderId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (scorecard) => {
          this.scorecard.set(scorecard);
          this.technicalWeight = scorecard.technicalWeight;
          this.commercialWeight = scorecard.commercialWeight;
          this.isLoading.set(false);
        },
        error: (error) => {
          this.isLoading.set(false);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to load scorecard'
          });
        }
      });
  }

  isWeightValid(): boolean {
    return this.totalWeight() === 100;
  }

  onWeightChange(changedField: 'technical' | 'commercial'): void {
    // Auto-adjust the other field to maintain 100%
    if (changedField === 'technical') {
      this.commercialWeight = Math.max(0, Math.min(100, 100 - this.technicalWeight));
    } else {
      this.technicalWeight = Math.max(0, Math.min(100, 100 - this.commercialWeight));
    }
  }

  applyPreset(tech: number, comm: number): void {
    this.technicalWeight = tech;
    this.commercialWeight = comm;
    this.applyWeights();
  }

  applyWeights(): void {
    if (!this.isWeightValid()) return;

    this.isRecalculating.set(true);

    this.evaluationService.updateWeights({
      tenderId: this.tenderId,
      technicalWeight: this.technicalWeight,
      commercialWeight: this.commercialWeight
    })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (scorecard) => {
          this.scorecard.set(scorecard);
          this.isRecalculating.set(false);
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Scorecard recalculated with new weights'
          });
        },
        error: (error) => {
          this.isRecalculating.set(false);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to update weights'
          });
        }
      });
  }

  getRowClass = (bidder: ScorecardBidder): string => {
    if (bidder.isWinner) return 'winner-row';
    if (bidder.isDisqualified) return 'disqualified-row';
    return '';
  };

  getWinnerScore(): number {
    const winner = this.scorecard()?.bidders.find(b => b.isWinner);
    return winner?.combinedScore || 0;
  }

  openSensitivityDialog(): void {
    this.showSensitivityDialog = true;
  }

  generateAwardPack(): void {
    this.confirmationService.confirm({
      message: 'Generate the award recommendation pack? This will create a comprehensive document for approval.',
      header: 'Generate Award Pack',
      icon: 'pi pi-file-pdf',
      acceptLabel: 'Generate',
      rejectLabel: 'Cancel',
      accept: () => {
        this.isGeneratingPack.set(true);

        this.evaluationService.generateAwardPack(this.tenderId)
          .pipe(takeUntil(this.destroy$))
          .subscribe({
            next: (pack) => {
              this.isGeneratingPack.set(false);
              this.messageService.add({
                severity: 'success',
                summary: 'Success',
                detail: 'Award pack generated successfully'
              });
              this.awardPackGenerated.emit(pack);
            },
            error: (error) => {
              this.isGeneratingPack.set(false);
              this.messageService.add({
                severity: 'error',
                summary: 'Error',
                detail: error.message || 'Failed to generate award pack'
              });
            }
          });
      }
    });
  }

  startApproval(): void {
    this.confirmationService.confirm({
      message: 'Start the approval workflow? The recommendation will be sent to the designated approvers.',
      header: 'Start Approval',
      icon: 'pi pi-send',
      acceptLabel: 'Start Approval',
      rejectLabel: 'Cancel',
      accept: () => {
        this.isStartingApproval.set(true);

        this.evaluationService.startApproval(this.tenderId)
          .pipe(takeUntil(this.destroy$))
          .subscribe({
            next: () => {
              this.isStartingApproval.set(false);
              this.messageService.add({
                severity: 'success',
                summary: 'Success',
                detail: 'Approval workflow started successfully'
              });
              this.approvalStarted.emit();
            },
            error: (error) => {
              this.isStartingApproval.set(false);
              this.messageService.add({
                severity: 'error',
                summary: 'Error',
                detail: error.message || 'Failed to start approval'
              });
            }
          });
      }
    });
  }
}
