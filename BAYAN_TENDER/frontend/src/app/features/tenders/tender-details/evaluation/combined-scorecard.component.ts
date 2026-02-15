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
import { InitiateApprovalDialogComponent } from '../approval/initiate-approval-dialog.component';

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
    SensitivityAnalysisDialogComponent,
    InitiateApprovalDialogComponent
  ],
  providers: [MessageService, ConfirmationService, DecimalPipe],
  template: `
    <p-toast></p-toast>
    <p-confirmDialog></p-confirmDialog>

    <div class="combined-scorecard-container" data-testid="combined-scorecard">
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
              (click)="startApproval()"
            ></button>
          </div>
        </div>
      } @else {
        <!-- No Data -->
        <div class="empty-state">
          <i class="pi pi-chart-bar" style="font-size: 3rem; color: var(--bayan-slate-300, #CBD5E1);"></i>
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

    <!-- Initiate Approval Dialog -->
    @if (showApprovalDialog) {
      <app-initiate-approval-dialog
        [visible]="showApprovalDialog"
        [tenderId]="tenderId"
        (visibleChange)="showApprovalDialog = $event"
        (initiated)="onApprovalInitiated()"
      ></app-initiate-approval-dialog>
    }
  `,
  styleUrl: './combined-scorecard.component.scss'
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

  // Weight form
  technicalWeight = 40;
  commercialWeight = 60;

  // Dialog state
  showSensitivityDialog = false;
  showApprovalDialog = false;

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
    this.showApprovalDialog = true;
  }

  onApprovalInitiated(): void {
    this.showApprovalDialog = false;
    this.messageService.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Approval workflow started successfully'
    });
    this.approvalStarted.emit();
  }
}
