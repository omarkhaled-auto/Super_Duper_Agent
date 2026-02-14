import {
  Component,
  Input,
  OnInit,
  OnDestroy,
  inject,
  signal,
  computed
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil, forkJoin } from 'rxjs';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { DropdownModule } from 'primeng/dropdown';
import { InputTextModule } from 'primeng/inputtext';
import { InputTextarea } from 'primeng/inputtextarea';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { DialogModule } from 'primeng/dialog';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';
import { DividerModule } from 'primeng/divider';
import { MessageService, ConfirmationService } from 'primeng/api';

import { ClarificationService } from '../../../../core/services/clarification.service';
import { BoqService } from '../../../../core/services/boq.service';
import {
  Clarification,
  ClarificationStatus,
  ClarificationSummary,
  CLARIFICATION_STATUS_CONFIG,
  CLARIFICATION_PRIORITY_CONFIG,
  CLARIFICATION_SOURCE_CONFIG,
  CLARIFICATION_STATUS_OPTIONS
} from '../../../../core/models/clarification.model';
import { BoqSection } from '../../../../core/models/boq.model';
import { InternalRfiDialogComponent } from './internal-rfi-dialog.component';
import { PublishBulletinDialogComponent } from './publish-bulletin-dialog.component';

@Component({
  selector: 'app-clarifications-tab',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    CardModule,
    TagModule,
    TooltipModule,
    DropdownModule,
    InputTextModule,
    InputTextarea,
    IconFieldModule,
    InputIconModule,
    DialogModule,
    ToastModule,
    ConfirmDialogModule,
    ProgressSpinnerModule,
    MessageModule,
    DividerModule,
    InternalRfiDialogComponent,
    PublishBulletinDialogComponent
  ],
  providers: [MessageService, ConfirmationService],
  template: `
    <p-toast></p-toast>
    <p-confirmDialog></p-confirmDialog>

    <div class="clarifications-tab-container" data-testid="clarifications-tab">
      <!-- Toolbar -->
      <div class="clarifications-toolbar">
        <div class="toolbar-left">
          <button
            pButton
            icon="pi pi-plus"
            label="New Internal RFI"
            data-testid="create-question-btn"
            (click)="showRfiDialog = true"
          ></button>
          <button
            pButton
            icon="pi pi-send"
            label="Publish Q&A Bulletin"
            class="p-button-outlined"
            [disabled]="!hasAnsweredClarifications()"
            (click)="showBulletinDialog = true"
          ></button>
        </div>

        <!-- Summary Stats -->
        @if (summary()) {
          <div class="summary-stats">
            <span class="stat">
              <span class="stat-value">{{ summary()!.total }}</span>
              <span class="stat-label">Total</span>
            </span>
            <span class="stat pending">
              <span class="stat-value">{{ summary()!.pendingAnswers }}</span>
              <span class="stat-label">Pending</span>
            </span>
            <span class="stat answered">
              <span class="stat-value">{{ summary()!.byStatus.answered }}</span>
              <span class="stat-label">Answered</span>
            </span>
          </div>
        }
      </div>

      <!-- Filters -->
      <div class="filters-row">
        <p-dropdown
          data-testid="clarification-status-filter"
          [options]="statusOptions"
          [(ngModel)]="filterStatus"
          placeholder="All Statuses"
          [showClear]="true"
          (onChange)="loadClarifications()"
          styleClass="filter-dropdown"
        ></p-dropdown>

        <p-dropdown
          [options]="sectionOptions()"
          [(ngModel)]="filterSection"
          placeholder="All Sections"
          [showClear]="true"
          (onChange)="loadClarifications()"
          optionLabel="label"
          optionValue="value"
          styleClass="filter-dropdown"
        ></p-dropdown>

        <p-iconField iconPosition="left" class="search-field">
          <p-inputIcon styleClass="pi pi-search"></p-inputIcon>
          <input
            pInputText
            type="text"
            [(ngModel)]="searchTerm"
            placeholder="Search clarifications..."
            (input)="onSearch()"
          />
        </p-iconField>
      </div>

      <!-- Error Message -->
      @if (clarificationService.error()) {
        <p-message
          severity="error"
          [text]="clarificationService.error()!"
          styleClass="w-full"
        ></p-message>
      }

      <!-- Loading State -->
      @if (clarificationService.isLoading() && clarifications().length === 0) {
        <div class="loading-container">
          <p-progressSpinner
            [style]="{ width: '50px', height: '50px' }"
            strokeWidth="4"
          ></p-progressSpinner>
          <p>Loading clarifications...</p>
        </div>
      } @else if (clarifications().length === 0) {
        <!-- Empty State -->
        <div class="empty-state">
          <i class="pi pi-comments" style="font-size: 3rem; color: var(--bayan-border, #E2E8F0);"></i>
          <h3>No Clarifications Yet</h3>
          <p>Create an internal RFI or wait for bidder questions.</p>
          <button
            pButton
            icon="pi pi-plus"
            label="New Internal RFI"
            (click)="showRfiDialog = true"
          ></button>
        </div>
      } @else {
        <!-- Clarifications Table with Row Expansion -->
        <p-table
          data-testid="clarifications-table"
          [value]="clarifications()"
          dataKey="id"
          [expandedRowKeys]="expandedRows"
          [loading]="clarificationService.isLoading()"
          [paginator]="true"
          [rows]="10"
          [showCurrentPageReport]="true"
          currentPageReportTemplate="Showing {first} to {last} of {totalRecords} clarifications"
          styleClass="p-datatable-sm"
        >
          <ng-template pTemplate="header">
            <tr>
              <th style="width: 50px"></th>
              <th style="width: 100px">Ref</th>
              <th>Subject</th>
              <th style="width: 150px">Bidder</th>
              <th style="width: 120px">Date</th>
              <th style="width: 120px">Status</th>
            </tr>
          </ng-template>

          <ng-template pTemplate="body" let-clarification let-expanded="expanded">
            <tr>
              <td>
                <button
                  type="button"
                  pButton
                  [pRowToggler]="clarification"
                  class="p-button-text p-button-rounded p-button-sm"
                  [icon]="expanded ? 'pi pi-chevron-down' : 'pi pi-chevron-right'"
                ></button>
              </td>
              <td>
                <span class="reference-badge">{{ clarification.referenceNumber }}</span>
              </td>
              <td>
                <div class="subject-cell">
                  <span class="subject-text">{{ clarification.subject }}</span>
                  @if (clarification.relatedBoqSectionTitle) {
                    <span class="section-link">
                      <i class="pi pi-link"></i>
                      {{ clarification.relatedBoqSectionTitle }}
                    </span>
                  }
                </div>
              </td>
              <td>
                @if (clarification.bidderName) {
                  <span>{{ clarification.bidderName }}</span>
                } @else {
                  <span class="internal-badge">
                    <i class="pi pi-building"></i>
                    Internal
                  </span>
                }
              </td>
              <td>{{ clarification.createdAt | date:'mediumDate' }}</td>
              <td>
                <p-tag
                  [value]="getStatusLabel(clarification.status)"
                  [severity]="getStatusSeverity(clarification.status)"
                ></p-tag>
              </td>
            </tr>
          </ng-template>

          <ng-template pTemplate="rowexpansion" let-clarification>
            <tr>
              <td colspan="6">
                <div class="expansion-content">
                  <div class="qa-section">
                    <div class="question-block">
                      <h5>
                        <i class="pi pi-question-circle"></i>
                        Question
                      </h5>
                      <p>{{ clarification.question }}</p>
                      @if (clarification.submittedByName) {
                        <span class="meta">
                          Submitted by {{ clarification.submittedByName }}
                          on {{ clarification.submittedAt | date:'medium' }}
                        </span>
                      }
                    </div>

                    @if (clarification.answer) {
                      <p-divider></p-divider>
                      <div class="answer-block">
                        <h5>
                          <i class="pi pi-check-circle"></i>
                          Answer
                        </h5>
                        <p>{{ clarification.answer }}</p>
                        <span class="meta">
                          Answered by {{ clarification.answeredByName }}
                          on {{ clarification.answeredAt | date:'medium' }}
                        </span>
                      </div>
                    }
                  </div>

                  <div class="action-buttons">
                    @switch (clarification.status) {
                      @case ('draft') {
                        <button
                          pButton
                          label="Edit"
                          icon="pi pi-pencil"
                          class="p-button-outlined p-button-sm"
                          (click)="editClarification(clarification)"
                        ></button>
                        <button
                          pButton
                          label="Submit for Review"
                          icon="pi pi-send"
                          class="p-button-sm"
                          (click)="submitClarification(clarification)"
                        ></button>
                        <button
                          pButton
                          label="Delete"
                          icon="pi pi-trash"
                          class="p-button-outlined p-button-danger p-button-sm"
                          (click)="confirmDelete(clarification)"
                        ></button>
                      }
                      @case ('submitted') {
                        <button
                          pButton
                          label="Start Review"
                          icon="pi pi-play"
                          class="p-button-outlined p-button-sm"
                          (click)="startReview(clarification)"
                        ></button>
                        <button
                          pButton
                          label="Answer"
                          icon="pi pi-reply"
                          class="p-button-sm"
                          (click)="openAnswerDialog(clarification)"
                        ></button>
                      }
                      @case ('under_review') {
                        <button
                          pButton
                          label="Answer"
                          icon="pi pi-reply"
                          class="p-button-sm"
                          (click)="openAnswerDialog(clarification)"
                        ></button>
                        <button
                          pButton
                          label="Reject"
                          icon="pi pi-times"
                          class="p-button-outlined p-button-danger p-button-sm"
                          (click)="confirmReject(clarification)"
                        ></button>
                      }
                      @case ('answered') {
                        <button
                          pButton
                          label="Edit Answer"
                          icon="pi pi-pencil"
                          class="p-button-outlined p-button-sm"
                          (click)="openAnswerDialog(clarification)"
                        ></button>
                        <p-tag value="Ready for bulletin" severity="info" styleClass="ml-2"></p-tag>
                      }
                      @case ('published') {
                        <p-tag
                          [value]="'Published in ' + clarification.bulletinNumber"
                          severity="success"
                        ></p-tag>
                      }
                    }
                  </div>
                </div>
              </td>
            </tr>
          </ng-template>

          <ng-template pTemplate="emptymessage">
            <tr>
              <td colspan="6" class="text-center p-4">
                No clarifications found matching your criteria.
              </td>
            </tr>
          </ng-template>
        </p-table>
      }
    </div>

    <!-- Internal RFI Dialog -->
    <app-internal-rfi-dialog
      [visible]="showRfiDialog"
      [tenderId]="tenderId"
      [clarification]="selectedClarification"
      [sections]="boqSections()"
      [mode]="rfiDialogMode"
      (visibleChange)="showRfiDialog = $event"
      (saved)="onClarificationSaved($event)"
    ></app-internal-rfi-dialog>

    <!-- Publish Bulletin Dialog -->
    <app-publish-bulletin-dialog
      [visible]="showBulletinDialog"
      [tenderId]="tenderId"
      (visibleChange)="showBulletinDialog = $event"
      (published)="onBulletinPublished()"
    ></app-publish-bulletin-dialog>

    <!-- Answer Dialog -->
    <p-dialog
      header="Answer Clarification"
      [(visible)]="showAnswerDialog"
      [modal]="true"
      [style]="{ width: '600px' }"
      [draggable]="false"
    >
      @if (selectedClarification) {
        <div class="answer-dialog-content">
          <div class="original-question">
            <h5>Question</h5>
            <p>{{ selectedClarification.question }}</p>
          </div>

          <div class="answer-input">
            <label for="answer">Your Answer <span class="required">*</span></label>
            <textarea
              pInputTextarea
              id="answer"
              [(ngModel)]="answerText"
              [rows]="5"
              [autoResize]="true"
              class="w-full"
              placeholder="Enter your answer..."
            ></textarea>
          </div>
        </div>
      }

      <div class="dialog-footer">
        <button
          pButton
          label="Cancel"
          class="p-button-text"
          (click)="showAnswerDialog = false"
        ></button>
        <button
          pButton
          label="Save Answer"
          icon="pi pi-check"
          [disabled]="!answerText.trim()"
          [loading]="isSavingAnswer()"
          (click)="saveAnswer()"
        ></button>
      </div>
    </p-dialog>
  `,
  styles: [`
    .clarifications-tab-container {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .clarifications-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
      padding: 1rem;
      background-color: var(--bayan-slate-50, #F8FAFC);
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .toolbar-left {
      display: flex;
      gap: 0.5rem;
    }

    .summary-stats {
      display: flex;
      gap: 1.5rem;
    }

    .stat {
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    .stat-value {
      font-size: 1.25rem;
      font-weight: 600;
      color: var(--bayan-foreground, #020617);
    }

    .stat-label {
      font-size: 0.75rem;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .stat.pending .stat-value {
      color: var(--bayan-warning, #D97706);
    }

    .stat.answered .stat-value {
      color: var(--bayan-success, #16A34A);
    }

    .filters-row {
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
    }

    :host ::ng-deep .filter-dropdown {
      min-width: 150px;
    }

    .search-field {
      flex: 1;
      min-width: 200px;
    }

    .search-field input {
      width: 100%;
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
    }

    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem;
      text-align: center;
      gap: 1rem;
    }

    .empty-state h3 {
      margin: 0;
      color: var(--bayan-foreground, #020617);
    }

    .empty-state p {
      margin: 0;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .reference-badge {
      font-family: monospace;
      font-size: 0.875rem;
      background-color: var(--bayan-accent, #EEF2FF);
      padding: 0.25rem 0.5rem;
      border-radius: var(--bayan-radius-sm, 0.375rem);
    }

    .subject-cell {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .subject-text {
      font-weight: 500;
      color: var(--bayan-slate-700, #334155);
    }

    .section-link {
      font-size: 0.8rem;
      color: var(--bayan-primary, #4F46E5);
      display: flex;
      align-items: center;
      gap: 0.25rem;
    }

    .internal-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .expansion-content {
      padding: 1rem 2rem;
      background-color: var(--bayan-slate-50, #F8FAFC);
    }

    .qa-section {
      max-width: 800px;
    }

    .question-block {
      padding: 1rem;
      background-color: white;
      border-radius: var(--bayan-radius, 0.5rem);
      border-left: 4px solid var(--bayan-warning, #D97706);
    }

    .answer-block {
      padding: 1rem;
      background-color: white;
      border-radius: var(--bayan-radius, 0.5rem);
      border-left: 4px solid var(--bayan-success, #16A34A);
      margin-left: 1.5rem;
    }

    .question-block h5 {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin: 0 0 0.5rem;
      color: var(--bayan-slate-900, #0F172A);
    }

    .answer-block h5 {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin: 0 0 0.5rem;
      color: var(--bayan-foreground, #020617);
    }

    .question-block p {
      margin: 0 0 0.5rem;
      color: var(--bayan-slate-700, #334155);
      line-height: 1.6;
    }

    .answer-block p {
      margin: 0 0 0.5rem;
      color: var(--bayan-slate-700, #334155);
      line-height: 1.6;
    }

    .meta {
      font-size: 0.75rem;
      color: var(--bayan-slate-400, #94A3B8);
    }

    .action-buttons {
      display: flex;
      gap: 0.5rem;
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid var(--bayan-border, #E2E8F0);
    }

    .answer-dialog-content {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .original-question {
      padding: 1rem;
      background-color: var(--bayan-slate-50, #F8FAFC);
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .original-question h5 {
      margin: 0 0 0.5rem;
      color: var(--bayan-foreground, #020617);
    }

    .original-question p {
      margin: 0;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .answer-input {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .answer-input label {
      font-weight: 600;
      color: var(--bayan-slate-700, #334155);
    }

    .required {
      color: var(--bayan-danger, #DC2626);
    }

    .dialog-footer {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid var(--bayan-border, #E2E8F0);
    }

    @media (max-width: 768px) {
      .clarifications-toolbar {
        flex-direction: column;
        align-items: stretch;
      }

      .toolbar-left {
        justify-content: center;
      }

      .summary-stats {
        justify-content: center;
      }

      .filters-row {
        flex-direction: column;
      }
    }
  `]
})
export class ClarificationsTabComponent implements OnInit, OnDestroy {
  @Input() tenderId!: number;

  readonly clarificationService = inject(ClarificationService);
  private readonly boqService = inject(BoqService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly destroy$ = new Subject<void>();

  // Data signals
  clarifications = signal<Clarification[]>([]);
  summary = signal<ClarificationSummary | null>(null);
  boqSections = signal<BoqSection[]>([]);

  // Filter state
  filterStatus: ClarificationStatus | null = null;
  filterSection: number | null = null;
  searchTerm = '';
  statusOptions = CLARIFICATION_STATUS_OPTIONS;

  // Table expansion
  expandedRows: Record<number, boolean> = {};

  // Dialog states
  showRfiDialog = false;
  showBulletinDialog = false;
  showAnswerDialog = false;
  selectedClarification: Clarification | null = null;
  rfiDialogMode: 'create' | 'edit' = 'create';
  answerText = '';
  isSavingAnswer = signal<boolean>(false);

  // Computed
  sectionOptions = computed(() => {
    return this.boqSections().map(s => ({
      label: `${s.sectionNumber} - ${s.title}`,
      value: s.id
    }));
  });

  hasAnsweredClarifications = computed(() => {
    return this.clarifications().some(c => c.status === 'answered');
  });

  ngOnInit(): void {
    this.loadData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadData(): void {
    forkJoin({
      clarifications: this.clarificationService.getClarifications(this.tenderId),
      summary: this.clarificationService.getSummary(this.tenderId),
      sections: this.boqService.getSections(this.tenderId)
    }).pipe(takeUntil(this.destroy$)).subscribe({
      next: (result) => {
        this.clarifications.set(result.clarifications.items);
        this.summary.set(result.summary);
        this.boqSections.set(result.sections);
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to load data'
        });
      }
    });
  }

  loadClarifications(): void {
    this.clarificationService.getClarifications(this.tenderId, {
      status: this.filterStatus || undefined,
      boqSectionId: this.filterSection || undefined,
      search: this.searchTerm || undefined
    }).pipe(takeUntil(this.destroy$)).subscribe({
      next: (result) => {
        this.clarifications.set(result.items);
      }
    });
  }

  onSearch(): void {
    // Debounce would be nice here, but for simplicity we'll just call loadClarifications
    this.loadClarifications();
  }

  editClarification(clarification: Clarification): void {
    this.selectedClarification = clarification;
    this.rfiDialogMode = 'edit';
    this.showRfiDialog = true;
  }

  submitClarification(clarification: Clarification): void {
    this.clarificationService.submitClarification(this.tenderId, clarification.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Clarification submitted for review'
          });
          this.loadData();
        },
        error: (error) => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to submit clarification'
          });
        }
      });
  }

  startReview(clarification: Clarification): void {
    this.clarificationService.startReview(this.tenderId, clarification.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Review started'
          });
          this.loadData();
        }
      });
  }

  openAnswerDialog(clarification: Clarification): void {
    this.selectedClarification = clarification;
    this.answerText = clarification.answer || '';
    this.showAnswerDialog = true;
  }

  saveAnswer(): void {
    if (!this.selectedClarification || !this.answerText.trim()) return;

    this.isSavingAnswer.set(true);

    this.clarificationService.answerClarification(this.tenderId, this.selectedClarification.id, {
      answer: this.answerText.trim()
    }).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.isSavingAnswer.set(false);
        this.showAnswerDialog = false;
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Answer saved successfully'
        });
        this.loadData();
      },
      error: (error) => {
        this.isSavingAnswer.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to save answer'
        });
      }
    });
  }

  confirmDelete(clarification: Clarification): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete clarification "${clarification.referenceNumber}"?`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.clarificationService.deleteClarification(this.tenderId, clarification.id)
          .pipe(takeUntil(this.destroy$))
          .subscribe({
            next: () => {
              this.messageService.add({
                severity: 'success',
                summary: 'Success',
                detail: 'Clarification deleted'
              });
              this.loadData();
            }
          });
      }
    });
  }

  confirmReject(clarification: Clarification): void {
    this.confirmationService.confirm({
      message: 'Are you sure you want to reject this clarification?',
      header: 'Confirm Reject',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.clarificationService.rejectClarification(this.tenderId, clarification.id)
          .pipe(takeUntil(this.destroy$))
          .subscribe({
            next: () => {
              this.messageService.add({
                severity: 'success',
                summary: 'Success',
                detail: 'Clarification rejected'
              });
              this.loadData();
            }
          });
      }
    });
  }

  onClarificationSaved(clarification: Clarification): void {
    this.showRfiDialog = false;
    this.selectedClarification = null;
    this.messageService.add({
      severity: 'success',
      summary: 'Success',
      detail: this.rfiDialogMode === 'create' ? 'RFI created successfully' : 'RFI updated successfully'
    });
    this.loadData();
  }

  onBulletinPublished(): void {
    this.showBulletinDialog = false;
    this.messageService.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Q&A Bulletin published and sent to bidders'
    });
    this.loadData();
  }

  getStatusLabel(status: ClarificationStatus): string {
    return CLARIFICATION_STATUS_CONFIG[status]?.label || status;
  }

  getStatusSeverity(status: ClarificationStatus): 'success' | 'secondary' | 'info' | 'warn' | 'danger' | 'contrast' {
    return CLARIFICATION_STATUS_CONFIG[status]?.severity || 'secondary';
  }
}
