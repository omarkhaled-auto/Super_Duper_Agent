import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnChanges,
  SimpleChanges,
  inject,
  signal,
  computed
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DialogModule } from 'primeng/dialog';
import { StepsModule } from 'primeng/steps';
import { TableModule } from 'primeng/table';
import { CheckboxModule } from 'primeng/checkbox';
import { InputTextModule } from 'primeng/inputtext';
import { InputTextarea } from 'primeng/inputtextarea';
import { DatePickerModule } from 'primeng/datepicker';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { MessageModule } from 'primeng/message';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { DividerModule } from 'primeng/divider';
import { MenuItem } from 'primeng/api';

import { ClarificationService } from '../../../../core/services/clarification.service';
import {
  Clarification,
  ClarificationBulletin,
  CreateBulletinDto
} from '../../../../core/models/clarification.model';

@Component({
  selector: 'app-publish-bulletin-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    DialogModule,
    StepsModule,
    TableModule,
    CheckboxModule,
    InputTextModule,
    InputTextarea,
    DatePickerModule,
    ButtonModule,
    TagModule,
    MessageModule,
    ProgressSpinnerModule,
    DividerModule
  ],
  template: `
    <p-dialog
      header="Publish Q&A Bulletin"
      [(visible)]="visible"
      (visibleChange)="onVisibleChange($event)"
      [modal]="true"
      [style]="{ width: '900px', height: '700px' }"
      [contentStyle]="{ overflow: 'auto', display: 'flex', flexDirection: 'column' }"
      [draggable]="false"
      [resizable]="false"
    >
      <!-- Steps -->
      <p-steps
        [model]="steps"
        [activeIndex]="activeStep"
        [readonly]="true"
        styleClass="mb-4"
      ></p-steps>

      <div class="step-content">
        <!-- Step 1: Select Questions -->
        @if (activeStep === 0) {
          <div class="select-step">
            <div class="step-header">
              <h4>Select Questions to Include</h4>
              <p>Select the answered clarifications you want to include in this bulletin.</p>
            </div>

            @if (isLoadingClarifications()) {
              <div class="loading-state">
                <p-progressSpinner [style]="{ width: '40px', height: '40px' }"></p-progressSpinner>
                <p>Loading answered clarifications...</p>
              </div>
            } @else if (answeredClarifications().length === 0) {
              <p-message
                severity="warn"
                text="No answered clarifications available for publishing."
                styleClass="w-full"
              ></p-message>
            } @else {
              <p-table
                [value]="answeredClarifications()"
                [(selection)]="selectedClarifications"
                dataKey="id"
                [scrollable]="true"
                scrollHeight="350px"
                styleClass="p-datatable-sm"
              >
                <ng-template pTemplate="header">
                  <tr>
                    <th style="width: 50px">
                      <p-tableHeaderCheckbox></p-tableHeaderCheckbox>
                    </th>
                    <th style="width: 100px">Ref</th>
                    <th>Subject</th>
                    <th style="width: 150px">Bidder</th>
                    <th style="width: 120px">Answered</th>
                  </tr>
                </ng-template>
                <ng-template pTemplate="body" let-clarification>
                  <tr>
                    <td>
                      <p-tableCheckbox [value]="clarification"></p-tableCheckbox>
                    </td>
                    <td>
                      <span class="reference-badge">{{ clarification.referenceNumber }}</span>
                    </td>
                    <td>{{ clarification.subject }}</td>
                    <td>{{ clarification.bidderName || 'Internal' }}</td>
                    <td>{{ clarification.answeredAt | date:'shortDate' }}</td>
                  </tr>
                </ng-template>
              </p-table>

              <div class="selection-summary">
                <span>{{ selectedClarifications.length }} clarification(s) selected</span>
              </div>
            }
          </div>
        }

        <!-- Step 2: Bulletin Details -->
        @if (activeStep === 1) {
          <div class="details-step">
            <div class="step-header">
              <h4>Bulletin Details</h4>
              <p>Enter the bulletin information.</p>
            </div>

            <div class="form-grid">
              <div class="form-field">
                <label for="bulletinNumber">Bulletin Number <span class="required">*</span></label>
                <input
                  pInputText
                  id="bulletinNumber"
                  [(ngModel)]="bulletinNumber"
                  placeholder="e.g., QB-001"
                  class="w-full"
                />
              </div>

              <div class="form-field">
                <label for="issueDate">Issue Date <span class="required">*</span></label>
                <p-datepicker
                  id="issueDate"
                  [(ngModel)]="issueDate"
                  [showIcon]="true"
                  dateFormat="dd/mm/yy"
                  styleClass="w-full"
                ></p-datepicker>
              </div>

              <div class="form-field full-width">
                <label for="introduction">Introduction</label>
                <textarea
                  pInputTextarea
                  id="introduction"
                  [(ngModel)]="introduction"
                  [rows]="3"
                  [autoResize]="true"
                  placeholder="Optional introduction text for the bulletin..."
                  class="w-full"
                ></textarea>
              </div>

              <div class="form-field full-width">
                <label for="closingNotes">Closing Notes</label>
                <textarea
                  pInputTextarea
                  id="closingNotes"
                  [(ngModel)]="closingNotes"
                  [rows]="2"
                  [autoResize]="true"
                  placeholder="Optional closing notes..."
                  class="w-full"
                ></textarea>
              </div>
            </div>
          </div>
        }

        <!-- Step 3: Preview -->
        @if (activeStep === 2) {
          <div class="preview-step">
            <div class="step-header">
              <h4>Preview Bulletin</h4>
              <p>Review the bulletin before publishing.</p>
            </div>

            @if (isLoadingPreview()) {
              <div class="loading-state">
                <p-progressSpinner [style]="{ width: '40px', height: '40px' }"></p-progressSpinner>
                <p>Generating preview...</p>
              </div>
            } @else {
              <div class="bulletin-preview">
                <div class="preview-header">
                  <h2>Q&A Bulletin {{ bulletinNumber }}</h2>
                  <p class="issue-date">Issue Date: {{ issueDate | date:'longDate' }}</p>
                </div>

                @if (introduction) {
                  <div class="preview-intro">
                    <p>{{ introduction }}</p>
                  </div>
                }

                <p-divider></p-divider>

                <div class="qa-list">
                  @for (clarification of selectedClarifications; track clarification.id; let i = $index) {
                    <div class="qa-item">
                      <div class="qa-number">Q{{ i + 1 }}</div>
                      <div class="qa-content">
                        <div class="question">
                          <strong>Question:</strong>
                          <p>{{ clarification.question }}</p>
                        </div>
                        <div class="answer">
                          <strong>Answer:</strong>
                          <p>{{ clarification.answer }}</p>
                        </div>
                      </div>
                    </div>
                  }
                </div>

                @if (closingNotes) {
                  <p-divider></p-divider>
                  <div class="preview-closing">
                    <p>{{ closingNotes }}</p>
                  </div>
                }
              </div>
            }
          </div>
        }
      </div>

      <!-- Footer Actions -->
      <div class="dialog-footer">
        <button
          pButton
          label="Cancel"
          class="p-button-text"
          (click)="onCancel()"
        ></button>

        <div class="nav-buttons">
          @if (activeStep > 0) {
            <button
              pButton
              label="Back"
              icon="pi pi-arrow-left"
              class="p-button-outlined"
              (click)="previousStep()"
            ></button>
          }

          @if (activeStep < 2) {
            <button
              pButton
              label="Next"
              icon="pi pi-arrow-right"
              iconPos="right"
              [disabled]="!canProceed()"
              (click)="nextStep()"
            ></button>
          } @else {
            <button
              pButton
              label="Publish & Send"
              icon="pi pi-send"
              data-testid="publish-bulletin-btn"
              [loading]="isPublishing()"
              (click)="publishBulletin()"
            ></button>
          }
        </div>
      </div>
    </p-dialog>
  `,
  styles: [`
    .step-content {
      flex: 1;
      overflow: auto;
    }

    .step-header {
      margin-bottom: 1rem;
    }

    .step-header h4 {
      margin: 0 0 0.5rem;
      color: var(--bayan-foreground, #020617);
    }

    .step-header p {
      margin: 0;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .loading-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem;
      gap: 1rem;
    }

    .loading-state p {
      color: var(--bayan-muted-foreground, #64748B);
    }

    .reference-badge {
      font-family: monospace;
      font-size: 0.875rem;
      background-color: var(--bayan-accent, #EEF2FF);
      padding: 0.25rem 0.5rem;
      border-radius: var(--bayan-radius-sm, 0.375rem);
    }

    .selection-summary {
      padding: 1rem;
      background-color: var(--bayan-primary-light, #EEF2FF);
      border-radius: var(--bayan-radius, 0.5rem);
      text-align: center;
      margin-top: 1rem;
      font-weight: 500;
      color: var(--bayan-primary, #4F46E5);
    }

    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }

    .form-field {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .form-field.full-width {
      grid-column: 1 / -1;
    }

    .form-field label {
      font-weight: 600;
      font-size: 0.875rem;
      color: var(--bayan-slate-700, #334155);
    }

    .required {
      color: var(--bayan-danger, #DC2626);
    }

    .bulletin-preview {
      background-color: white;
      border: 1px solid var(--bayan-border, #E2E8F0);
      border-radius: var(--bayan-radius, 0.5rem);
      padding: 2rem;
      max-height: 400px;
      overflow: auto;
    }

    .preview-header {
      text-align: center;
      margin-bottom: 1.5rem;
    }

    .preview-header h2 {
      margin: 0 0 0.5rem;
      color: var(--bayan-slate-900, #0F172A);
    }

    .issue-date {
      margin: 0;
      color: var(--bayan-muted-foreground, #64748B);
      font-size: 0.9rem;
    }

    .preview-intro,
    .preview-closing {
      padding: 1rem;
      background-color: var(--bayan-slate-50, #F8FAFC);
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .preview-intro p,
    .preview-closing p {
      margin: 0;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .qa-list {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .qa-item {
      display: flex;
      gap: 1rem;
    }

    .qa-number {
      flex-shrink: 0;
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: var(--bayan-primary, #4F46E5);
      color: white;
      border-radius: 50%;
      font-weight: 600;
    }

    .qa-content {
      flex: 1;
    }

    .question,
    .answer {
      margin-bottom: 0.75rem;
    }

    .question strong,
    .answer strong {
      color: var(--bayan-foreground, #020617);
    }

    .question p,
    .answer p {
      margin: 0.25rem 0 0;
      color: var(--bayan-muted-foreground, #64748B);
      line-height: 1.6;
    }

    .dialog-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 1rem;
      border-top: 1px solid var(--bayan-border, #E2E8F0);
      margin-top: auto;
    }

    .nav-buttons {
      display: flex;
      gap: 0.5rem;
    }

    :host ::ng-deep {
      .p-datepicker,
      .p-inputtext,
      .p-inputtextarea {
        width: 100%;
      }
    }

    @media (max-width: 600px) {
      .form-grid {
        grid-template-columns: 1fr;
      }

      .bulletin-preview {
        padding: 1rem;
      }
    }
  `]
})
export class PublishBulletinDialogComponent implements OnChanges {
  @Input() visible = false;
  @Input() tenderId!: number;

  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() published = new EventEmitter<ClarificationBulletin>();

  private readonly clarificationService = inject(ClarificationService);

  activeStep = 0;
  steps: MenuItem[] = [
    { label: 'Select Questions' },
    { label: 'Bulletin Details' },
    { label: 'Preview' }
  ];

  // Step 1
  answeredClarifications = signal<Clarification[]>([]);
  isLoadingClarifications = signal<boolean>(false);
  selectedClarifications: Clarification[] = [];

  // Step 2
  bulletinNumber = '';
  issueDate: Date = new Date();
  introduction = '';
  closingNotes = '';

  // Step 3
  isLoadingPreview = signal<boolean>(false);
  isPublishing = signal<boolean>(false);

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && this.visible) {
      this.reset();
      this.loadAnsweredClarifications();
      this.generateBulletinNumber();
    }
  }

  private reset(): void {
    this.activeStep = 0;
    this.selectedClarifications = [];
    this.bulletinNumber = '';
    this.issueDate = new Date();
    this.introduction = '';
    this.closingNotes = '';
  }

  private loadAnsweredClarifications(): void {
    this.isLoadingClarifications.set(true);

    this.clarificationService.getAnsweredClarifications(this.tenderId).subscribe({
      next: (clarifications) => {
        this.answeredClarifications.set(clarifications);
        this.isLoadingClarifications.set(false);
      },
      error: () => {
        this.isLoadingClarifications.set(false);
      }
    });
  }

  private generateBulletinNumber(): void {
    this.clarificationService.generateBulletinNumber(this.tenderId).subscribe({
      next: (number) => {
        this.bulletinNumber = number;
      }
    });
  }

  canProceed(): boolean {
    switch (this.activeStep) {
      case 0:
        return this.selectedClarifications.length > 0;
      case 1:
        return !!this.bulletinNumber.trim() && !!this.issueDate;
      default:
        return false;
    }
  }

  nextStep(): void {
    if (this.activeStep === 1) {
      // Generate preview
      this.activeStep++;
      this.isLoadingPreview.set(true);
      // Simulate preview generation
      setTimeout(() => {
        this.isLoadingPreview.set(false);
      }, 500);
    } else {
      this.activeStep++;
    }
  }

  previousStep(): void {
    this.activeStep--;
  }

  publishBulletin(): void {
    this.isPublishing.set(true);

    const createDto: CreateBulletinDto = {
      tenderId: this.tenderId,
      bulletinNumber: this.bulletinNumber,
      issueDate: this.issueDate,
      introduction: this.introduction || undefined,
      closingNotes: this.closingNotes || undefined,
      clarificationIds: this.selectedClarifications.map(c => c.id)
    };

    this.clarificationService.createBulletin(createDto).subscribe({
      next: (bulletin) => {
        // Now publish it
        this.clarificationService.publishBulletin(this.tenderId, bulletin.id).subscribe({
          next: (publishedBulletin) => {
            this.isPublishing.set(false);
            this.published.emit(publishedBulletin);
          },
          error: () => {
            this.isPublishing.set(false);
          }
        });
      },
      error: () => {
        this.isPublishing.set(false);
      }
    });
  }

  onVisibleChange(visible: boolean): void {
    this.visibleChange.emit(visible);
  }

  onCancel(): void {
    this.visibleChange.emit(false);
  }
}
