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
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil, forkJoin } from 'rxjs';

// PrimeNG
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { SliderModule } from 'primeng/slider';
import { InputTextarea } from 'primeng/inputtextarea';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { TagModule } from 'primeng/tag';
import { DividerModule } from 'primeng/divider';
import { ProgressBarModule } from 'primeng/progressbar';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { RatingModule } from 'primeng/rating';
import { MessageService, ConfirmationService } from 'primeng/api';

// Services and Models
import { EvaluationService } from '../../../../core/services/evaluation.service';
import {
  BidderForScoring,
  EvaluationCriterion,
  EvaluationSetup,
  CriterionScore,
  SaveScoreDto
} from '../../../../core/models/evaluation.model';

interface CriterionScoreForm {
  criterionId: number;
  score: number;
  comment: string;
  requiresComment: boolean;
}

@Component({
  selector: 'app-technical-scoring',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule,
    SliderModule,
    InputTextarea,
    ToastModule,
    TooltipModule,
    TagModule,
    DividerModule,
    ProgressBarModule,
    ProgressSpinnerModule,
    MessageModule,
    ConfirmDialogModule,
    RatingModule
  ],
  providers: [MessageService, ConfirmationService],
  template: `
    <p-toast></p-toast>
    <p-confirmDialog></p-confirmDialog>

    <div class="technical-scoring-container">
      <!-- Loading State -->
      @if (isLoading()) {
        <div class="loading-container">
          <p-progressSpinner
            [style]="{ width: '50px', height: '50px' }"
            strokeWidth="4"
          ></p-progressSpinner>
          <p>Loading scoring data...</p>
        </div>
      } @else {
        <!-- Progress Indicator -->
        <div class="progress-section">
          <div class="progress-info">
            <span class="progress-label">Scoring Progress</span>
            <span class="progress-value">{{ scoredCount() }} of {{ totalBidders() }} bidders scored</span>
          </div>
          <p-progressBar
            [value]="progressPercentage()"
            [showValue]="false"
            styleClass="progress-bar"
          ></p-progressBar>
        </div>

        @if (currentBidder()) {
          <!-- Current Bidder Header -->
          <p-card styleClass="bidder-header-card">
            <div class="bidder-header">
              <div class="bidder-info">
                <h2>{{ getCurrentBidderDisplay() }}</h2>
                @if (currentBidder()!.isScored) {
                  <p-tag value="Scored" severity="success"></p-tag>
                } @else {
                  <p-tag value="Pending" severity="warn"></p-tag>
                }
              </div>
              <div class="bidder-navigation">
                <span class="bidder-position">{{ currentBidderIndex() + 1 }} / {{ totalBidders() }}</span>
              </div>
            </div>
          </p-card>

          <!-- Document Links -->
          <p-card header="Bidder Documents" styleClass="documents-card">
            <div class="document-links">
              @for (doc of currentBidder()!.documents; track doc.id) {
                <a
                  class="document-link"
                  [href]="doc.url"
                  target="_blank"
                  pTooltip="Click to view document"
                  tooltipPosition="top"
                >
                  <i [class]="getDocumentIcon(doc.type)"></i>
                  <span>{{ getDocumentLabel(doc.type) }}</span>
                  <i class="pi pi-external-link"></i>
                </a>
              }
            </div>
          </p-card>

          <!-- Scoring Form -->
          <div class="scoring-form">
            @for (score of scoreForm(); track score.criterionId; let i = $index) {
              <p-card styleClass="criterion-card">
                <ng-template pTemplate="header">
                  <div class="criterion-header">
                    <div class="criterion-info">
                      <h3>{{ getCriterionName(score.criterionId) }}</h3>
                      <div class="criterion-meta">
                        <span class="weight-badge">
                          <i class="pi pi-chart-pie"></i>
                          Weight: {{ getCriterionWeight(score.criterionId) }}%
                        </span>
                        <span class="max-score-badge">
                          <i class="pi pi-star"></i>
                          Max: {{ getMaxScore() }}
                        </span>
                      </div>
                    </div>
                  </div>
                </ng-template>

                <!-- Guidance Notes -->
                @if (getCriterionGuidance(score.criterionId)) {
                  <div class="guidance-notes">
                    <i class="pi pi-info-circle"></i>
                    <span>{{ getCriterionGuidance(score.criterionId) }}</span>
                  </div>
                }

                <!-- Score Input -->
                <div class="score-input-section">
                  <label>Score</label>

                  @if (scoringMethod() === 'numeric') {
                    <div class="slider-container">
                      <p-slider
                        [(ngModel)]="score.score"
                        [min]="0"
                        [max]="10"
                        [step]="1"
                        styleClass="score-slider"
                        (onChange)="onScoreChange(score)"
                      ></p-slider>
                      <div class="slider-labels">
                        <span>0</span>
                        <span class="current-score" [class.low]="score.score < 3" [class.high]="score.score > 8">
                          {{ score.score }}
                        </span>
                        <span>10</span>
                      </div>
                    </div>
                  } @else {
                    <div class="rating-container">
                      <p-rating
                        [(ngModel)]="score.score"
                        [stars]="5"
                        (onRate)="onScoreChange(score)"
                      ></p-rating>
                      <span class="rating-value">{{ score.score }} / 5</span>
                    </div>
                  }
                </div>

                <!-- Comment Box -->
                <div class="comment-section">
                  <label [class.required]="score.requiresComment">
                    Comments
                    @if (score.requiresComment) {
                      <span class="required-indicator">(Required for scores &lt;3 or &gt;8)</span>
                    }
                  </label>
                  <textarea
                    pInputTextarea
                    [(ngModel)]="score.comment"
                    [rows]="3"
                    placeholder="Enter your evaluation comments..."
                    [class.p-invalid]="score.requiresComment && !score.comment"
                    (input)="onCommentChange(score)"
                  ></textarea>
                  @if (score.requiresComment && !score.comment) {
                    <small class="p-error">Comment is required for extreme scores</small>
                  }
                </div>
              </p-card>
            }
          </div>

          <!-- Action Buttons -->
          <div class="action-bar">
            <div class="nav-buttons">
              <button
                pButton
                label="Previous Bidder"
                icon="pi pi-arrow-left"
                class="p-button-outlined"
                [disabled]="currentBidderIndex() === 0"
                (click)="previousBidder()"
              ></button>
              <button
                pButton
                label="Next Bidder"
                icon="pi pi-arrow-right"
                iconPos="right"
                class="p-button-outlined"
                [disabled]="currentBidderIndex() >= totalBidders() - 1"
                (click)="nextBidder()"
              ></button>
            </div>

            <div class="submit-buttons">
              <button
                pButton
                label="Save Draft"
                icon="pi pi-save"
                class="p-button-secondary"
                [loading]="isSaving()"
                (click)="saveDraft()"
              ></button>
              <button
                pButton
                label="Submit Score"
                icon="pi pi-check"
                class="p-button-success"
                [loading]="isSaving()"
                [disabled]="!isFormValid()"
                (click)="submitScore()"
              ></button>
            </div>
          </div>

          <!-- Validation Summary -->
          @if (!isFormValid()) {
            <p-message
              severity="warn"
              styleClass="mt-3"
            >
              <ng-template pTemplate="content">
                <div class="validation-summary">
                  <i class="pi pi-exclamation-triangle"></i>
                  <span>Please complete all required fields before submitting:</span>
                  <ul>
                    @for (error of getValidationErrors(); track error) {
                      <li>{{ error }}</li>
                    }
                  </ul>
                </div>
              </ng-template>
            </p-message>
          }
        } @else {
          <!-- No Bidders -->
          <div class="empty-state">
            <i class="pi pi-users" style="font-size: 3rem; color: #ccc;"></i>
            <h3>No Bidders Available</h3>
            <p>There are no bidders to score for this tender.</p>
          </div>
        }
      }
    </div>
  `,
  styles: [`
    .technical-scoring-container {
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

    /* Progress Section */
    .progress-section {
      background: white;
      padding: 1.25rem;
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .progress-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.75rem;
    }

    .progress-label {
      font-weight: 600;
      color: #333;
    }

    .progress-value {
      font-size: 0.9rem;
      color: #666;
    }

    :host ::ng-deep .progress-bar .p-progressbar {
      height: 8px;
      border-radius: 4px;
    }

    /* Bidder Header Card */
    :host ::ng-deep .bidder-header-card .p-card-body {
      padding: 1rem;
    }

    .bidder-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .bidder-info {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .bidder-info h2 {
      margin: 0;
      font-size: 1.5rem;
      color: #333;
    }

    .bidder-position {
      font-size: 1rem;
      color: #666;
      font-weight: 500;
    }

    /* Documents Card */
    .document-links {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
    }

    .document-link {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.75rem 1rem;
      background: #f8f9fa;
      border-radius: 6px;
      color: #333;
      text-decoration: none;
      transition: all 0.2s ease;
      border: 1px solid #e0e0e0;
    }

    .document-link:hover {
      background: #e3f2fd;
      border-color: #1976D2;
      color: #1976D2;
    }

    .document-link i:first-child {
      font-size: 1.25rem;
    }

    .document-link i:last-child {
      font-size: 0.75rem;
      opacity: 0.6;
    }

    /* Criterion Card */
    :host ::ng-deep .criterion-card {
      .p-card-header {
        background: #f8f9fa;
        padding: 1rem;
        border-bottom: 1px solid #e0e0e0;
      }

      .p-card-body {
        padding: 1.25rem;
      }
    }

    .criterion-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }

    .criterion-info h3 {
      margin: 0 0 0.5rem 0;
      font-size: 1.125rem;
      color: #333;
    }

    .criterion-meta {
      display: flex;
      gap: 1rem;
    }

    .weight-badge,
    .max-score-badge {
      display: flex;
      align-items: center;
      gap: 0.375rem;
      font-size: 0.85rem;
      color: #666;
    }

    .weight-badge i,
    .max-score-badge i {
      color: #1976D2;
    }

    /* Guidance Notes */
    .guidance-notes {
      display: flex;
      align-items: flex-start;
      gap: 0.5rem;
      padding: 0.75rem 1rem;
      background: #fff8e1;
      border-radius: 6px;
      font-size: 0.875rem;
      color: #5d4037;
      margin-bottom: 1.25rem;
    }

    .guidance-notes i {
      color: #ff9800;
      margin-top: 0.125rem;
    }

    /* Score Input */
    .score-input-section {
      margin-bottom: 1.25rem;
    }

    .score-input-section > label {
      display: block;
      font-weight: 500;
      color: #333;
      margin-bottom: 0.75rem;
    }

    .slider-container {
      padding: 0 0.5rem;
    }

    :host ::ng-deep .score-slider {
      width: 100%;
    }

    :host ::ng-deep .score-slider .p-slider-handle {
      width: 20px;
      height: 20px;
      margin-top: -8px;
      margin-left: -10px;
    }

    .slider-labels {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 0.5rem;
      font-size: 0.875rem;
      color: #666;
    }

    .current-score {
      font-size: 1.5rem;
      font-weight: 700;
      color: #333;
      padding: 0.25rem 0.75rem;
      background: #f0f0f0;
      border-radius: 6px;
    }

    .current-score.low {
      background: #ffcdd2;
      color: #c62828;
    }

    .current-score.high {
      background: #c8e6c9;
      color: #2e7d32;
    }

    .rating-container {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .rating-value {
      font-size: 1.25rem;
      font-weight: 600;
      color: #333;
    }

    /* Comment Section */
    .comment-section {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .comment-section label {
      font-weight: 500;
      color: #333;
    }

    .comment-section label.required {
      color: #c62828;
    }

    .required-indicator {
      font-size: 0.8rem;
      font-weight: 400;
      color: #c62828;
    }

    .comment-section textarea {
      width: 100%;
      resize: vertical;
    }

    /* Action Bar */
    .action-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1.25rem;
      background: white;
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      margin-top: 0.5rem;
    }

    .nav-buttons,
    .submit-buttons {
      display: flex;
      gap: 0.75rem;
    }

    /* Validation Summary */
    .validation-summary {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .validation-summary ul {
      margin: 0.5rem 0 0 1.5rem;
      padding: 0;
    }

    .validation-summary li {
      font-size: 0.875rem;
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

    /* Responsive */
    @media (max-width: 768px) {
      .bidder-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.75rem;
      }

      .document-links {
        flex-direction: column;
      }

      .document-link {
        justify-content: space-between;
      }

      .action-bar {
        flex-direction: column;
        gap: 1rem;
      }

      .nav-buttons,
      .submit-buttons {
        width: 100%;
        justify-content: stretch;
      }

      .nav-buttons button,
      .submit-buttons button {
        flex: 1;
      }
    }
  `]
})
export class TechnicalScoringComponent implements OnInit, OnDestroy {
  @Input() tenderId!: number;
  @Input() setup!: EvaluationSetup;
  @Output() scoringCompleted = new EventEmitter<void>();

  private readonly evaluationService = inject(EvaluationService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly destroy$ = new Subject<void>();

  // State signals
  bidders = signal<BidderForScoring[]>([]);
  criteria = signal<EvaluationCriterion[]>([]);
  scoreForm = signal<CriterionScoreForm[]>([]);
  currentBidderIndex = signal<number>(0);
  isLoading = signal<boolean>(true);
  isSaving = signal<boolean>(false);

  // Computed
  totalBidders = computed(() => this.bidders().length);

  scoredCount = computed(() => {
    return this.bidders().filter(b => b.isScored).length;
  });

  progressPercentage = computed(() => {
    const total = this.totalBidders();
    if (total === 0) return 0;
    return Math.round((this.scoredCount() / total) * 100);
  });

  currentBidder = computed(() => {
    const index = this.currentBidderIndex();
    const allBidders = this.bidders();
    return index < allBidders.length ? allBidders[index] : null;
  });

  scoringMethod = computed(() => this.setup?.scoringMethod || 'numeric');

  ngOnInit(): void {
    this.loadData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadData(): void {
    this.isLoading.set(true);

    forkJoin({
      bidders: this.evaluationService.getBiddersForScoring(this.tenderId),
      criteria: this.evaluationService.getEvaluationCriteria(this.tenderId)
    }).pipe(takeUntil(this.destroy$))
      .subscribe({
        next: ({ bidders, criteria }) => {
          this.bidders.set(bidders);
          this.criteria.set(criteria);
          this.initializeScoreForm();
          this.isLoading.set(false);
        },
        error: (error) => {
          this.isLoading.set(false);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to load scoring data'
          });
        }
      });
  }

  private initializeScoreForm(): void {
    const form: CriterionScoreForm[] = this.criteria().map(c => ({
      criterionId: c.id,
      score: this.getDefaultScore(),
      comment: '',
      requiresComment: false
    }));
    this.scoreForm.set(form);
  }

  private getDefaultScore(): number {
    return this.scoringMethod() === 'numeric' ? 5 : 3;
  }

  getMaxScore(): number {
    return this.scoringMethod() === 'numeric' ? 10 : 5;
  }

  getCurrentBidderDisplay(): string {
    const bidder = this.currentBidder();
    if (!bidder) return '';
    return this.setup.blindMode ? bidder.blindCode : bidder.bidderName;
  }

  getCriterionName(criterionId: number): string {
    const criterion = this.criteria().find(c => c.id === criterionId);
    return criterion?.name || '';
  }

  getCriterionWeight(criterionId: number): number {
    const criterion = this.criteria().find(c => c.id === criterionId);
    return criterion?.weight || 0;
  }

  getCriterionGuidance(criterionId: number): string {
    const criterion = this.criteria().find(c => c.id === criterionId);
    return criterion?.guidanceNotes || '';
  }

  getDocumentIcon(type: string): string {
    switch (type) {
      case 'methodology': return 'pi pi-file-pdf';
      case 'team_cvs': return 'pi pi-users';
      case 'work_program': return 'pi pi-calendar';
      case 'hse_plan': return 'pi pi-shield';
      default: return 'pi pi-file';
    }
  }

  getDocumentLabel(type: string): string {
    switch (type) {
      case 'methodology': return 'View Methodology';
      case 'team_cvs': return 'View Team CVs';
      case 'work_program': return 'View Program';
      case 'hse_plan': return 'View HSE Plan';
      default: return 'View Document';
    }
  }

  onScoreChange(scoreItem: CriterionScoreForm): void {
    const maxScore = this.getMaxScore();
    const threshold = this.scoringMethod() === 'numeric' ? { low: 3, high: 8 } : { low: 2, high: 4 };
    scoreItem.requiresComment = scoreItem.score < threshold.low || scoreItem.score > threshold.high;
    this.scoreForm.update(form => [...form]);
  }

  onCommentChange(scoreItem: CriterionScoreForm): void {
    this.scoreForm.update(form => [...form]);
  }

  isFormValid(): boolean {
    return this.scoreForm().every(s => {
      if (s.requiresComment && !s.comment.trim()) {
        return false;
      }
      return true;
    });
  }

  getValidationErrors(): string[] {
    const errors: string[] = [];
    this.scoreForm().forEach(s => {
      if (s.requiresComment && !s.comment.trim()) {
        const criterionName = this.getCriterionName(s.criterionId);
        errors.push(`Comment required for "${criterionName}" (score: ${s.score})`);
      }
    });
    return errors;
  }

  previousBidder(): void {
    if (this.currentBidderIndex() > 0) {
      this.currentBidderIndex.update(i => i - 1);
      this.initializeScoreForm();
    }
  }

  nextBidder(): void {
    if (this.currentBidderIndex() < this.totalBidders() - 1) {
      this.currentBidderIndex.update(i => i + 1);
      this.initializeScoreForm();
    }
  }

  saveDraft(): void {
    this.saveScore(true);
  }

  submitScore(): void {
    if (!this.isFormValid()) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Validation Error',
        detail: 'Please complete all required fields'
      });
      return;
    }

    this.confirmationService.confirm({
      message: 'Are you sure you want to submit this score? You will not be able to modify it after submission.',
      header: 'Submit Score',
      icon: 'pi pi-check',
      acceptLabel: 'Submit',
      rejectLabel: 'Cancel',
      accept: () => {
        this.saveScore(false);
      }
    });
  }

  private saveScore(isDraft: boolean): void {
    const bidder = this.currentBidder();
    if (!bidder) return;

    this.isSaving.set(true);

    const criteriaScores: CriterionScore[] = this.scoreForm().map(s => ({
      criterionId: s.criterionId,
      score: s.score,
      comment: s.comment || undefined,
      isDraft
    }));

    const dto: SaveScoreDto = {
      tenderId: this.tenderId,
      bidderId: bidder.bidderId,
      criteriaScores,
      isDraft
    };

    this.evaluationService.saveScore(dto)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.isSaving.set(false);

          if (!isDraft) {
            // Update local state
            this.bidders.update(bidders =>
              bidders.map(b =>
                b.bidderId === bidder.bidderId ? { ...b, isScored: true } : b
              )
            );
          }

          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: isDraft ? 'Draft saved successfully' : 'Score submitted successfully'
          });

          // Check if all bidders are scored
          if (!isDraft && this.scoredCount() === this.totalBidders()) {
            this.scoringCompleted.emit();
          } else if (!isDraft && this.currentBidderIndex() < this.totalBidders() - 1) {
            // Move to next bidder
            this.nextBidder();
          }
        },
        error: (error) => {
          this.isSaving.set(false);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to save score'
          });
        }
      });
  }
}
