import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { DynamicDialogRef, DynamicDialogConfig } from 'primeng/dynamicdialog';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { InputTextarea } from 'primeng/inputtextarea';
import { DropdownModule } from 'primeng/dropdown';
import { CheckboxModule } from 'primeng/checkbox';
import { MessageModule } from 'primeng/message';
import { PortalService } from '../../../core/services/portal.service';
import { BoqSectionOption, SubmitQuestionDto } from '../../../core/models/portal.model';

interface DialogData {
  tenderId: string | number;
  clarificationDeadline?: Date | string;
}

@Component({
  selector: 'app-submit-question-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    ButtonModule,
    InputTextModule,
    InputTextarea,
    DropdownModule,
    CheckboxModule,
    MessageModule
  ],
  template: `
    <div class="submit-question-dialog">
      <!-- Deadline Warning -->
      @if (isDeadlinePassed()) {
        <p-message
          severity="error"
          [text]="'The clarification deadline has passed. Questions can no longer be submitted.'"
          styleClass="w-full mb-4"
        ></p-message>
      } @else if (isDeadlineNear()) {
        <p-message
          severity="warn"
          [text]="'Clarification deadline is approaching: ' + (data.clarificationDeadline | date:'medium')"
          styleClass="w-full mb-4"
        ></p-message>
      }

      @if (error()) {
        <p-message
          severity="error"
          [text]="error()!"
          styleClass="w-full mb-4"
        ></p-message>
      }

      <form [formGroup]="questionForm" (ngSubmit)="onSubmit()">
        <!-- Subject -->
        <div class="form-field">
          <label for="subject">Subject *</label>
          <input
            pInputText
            id="subject"
            formControlName="subject"
            placeholder="Brief subject of your question"
            class="w-full"
            [class.ng-invalid]="isFieldInvalid('subject')"
          />
          @if (isFieldInvalid('subject')) {
            <small class="p-error">
              @if (questionForm.get('subject')?.errors?.['required']) {
                Subject is required
              }
              @if (questionForm.get('subject')?.errors?.['maxlength']) {
                Subject cannot exceed 200 characters
              }
            </small>
          }
        </div>

        <!-- Question -->
        <div class="form-field">
          <label for="question">Question *</label>
          <textarea
            pInputTextarea
            id="question"
            formControlName="question"
            placeholder="Please provide your question in detail..."
            [rows]="5"
            class="w-full"
            [class.ng-invalid]="isFieldInvalid('question')"
          ></textarea>
          <div class="field-footer">
            @if (isFieldInvalid('question')) {
              <small class="p-error">
                @if (questionForm.get('question')?.errors?.['required']) {
                  Question is required
                }
                @if (questionForm.get('question')?.errors?.['minlength']) {
                  Question must be at least 20 characters
                }
                @if (questionForm.get('question')?.errors?.['maxlength']) {
                  Question cannot exceed 2000 characters
                }
              </small>
            }
            <small class="char-count">
              {{ questionForm.get('question')?.value?.length || 0 }} / 2000
            </small>
          </div>
        </div>

        <!-- Related BOQ Section -->
        <div class="form-field">
          <label for="boqSection">Related BOQ Section (Optional)</label>
          <p-dropdown
            id="boqSection"
            formControlName="relatedBoqSection"
            [options]="boqSections()"
            optionLabel="title"
            optionValue="title"
            placeholder="Select related BOQ section"
            [showClear]="true"
            styleClass="w-full"
            [filter]="true"
            filterPlaceholder="Search sections..."
          >
            <ng-template let-section pTemplate="item">
              <div class="boq-option">
                <span class="section-number">{{ section.sectionNumber }}</span>
                <span class="section-title">{{ section.title }}</span>
              </div>
            </ng-template>
          </p-dropdown>
          <small class="field-hint">
            Selecting a BOQ section helps us respond more accurately
          </small>
        </div>

        <!-- Anonymous -->
        <div class="form-field checkbox-field">
          <p-checkbox
            formControlName="isAnonymous"
            [binary]="true"
            inputId="anonymous"
          ></p-checkbox>
          <label for="anonymous" class="checkbox-label">
            Submit anonymously
            <small class="hint-text">
              Your company name will not be visible to other bidders in published Q&A
            </small>
          </label>
        </div>

        <!-- Actions -->
        <div class="dialog-actions">
          <button
            pButton
            type="button"
            label="Cancel"
            class="p-button-text"
            (click)="onCancel()"
          ></button>
          <button
            pButton
            type="submit"
            label="Submit Question"
            icon="pi pi-send"
            [loading]="isSubmitting()"
            [disabled]="questionForm.invalid || isSubmitting() || isDeadlinePassed()"
          ></button>
        </div>
      </form>
    </div>
  `,
  styles: [`
    .submit-question-dialog {
      padding: 0.5rem;
    }

    .form-field {
      margin-bottom: 1.5rem;
    }

    .form-field label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
    }

    .field-footer {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-top: 0.25rem;
    }

    .char-count {
      color: var(--bayan-muted-foreground, #71717a);
      font-size: 0.75rem;
      margin-left: auto;
    }

    .field-hint {
      display: block;
      margin-top: 0.25rem;
      color: var(--bayan-muted-foreground, #71717a);
      font-size: 0.8rem;
    }

    .checkbox-field {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
    }

    .checkbox-label {
      display: flex;
      flex-direction: column;
      cursor: pointer;
      margin-bottom: 0 !important;
    }

    .hint-text {
      font-weight: 400;
      color: var(--bayan-muted-foreground, #71717a);
      font-size: 0.8rem;
      margin-top: 0.25rem;
    }

    .boq-option {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .section-number {
      font-weight: 600;
      color: var(--bayan-primary, #18181b);
      min-width: 60px;
    }

    .section-title {
      color: var(--bayan-foreground, #09090b);
    }

    .dialog-actions {
      display: flex;
      justify-content: flex-end;
      gap: 0.75rem;
      margin-top: 2rem;
      padding-top: 1rem;
      border-top: 1px solid var(--bayan-border, #e4e4e7);
    }

    .p-error {
      display: block;
    }

    :host ::ng-deep {
      .p-inputtextarea {
        resize: vertical;
        min-height: 120px;
      }

      .p-dropdown {
        width: 100%;
      }
    }
  `]
})
export class SubmitQuestionDialogComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly portalService = inject(PortalService);
  private readonly dialogRef = inject(DynamicDialogRef);
  private readonly config = inject(DynamicDialogConfig);

  questionForm!: FormGroup;
  boqSections = signal<BoqSectionOption[]>([]);
  isSubmitting = signal(false);
  error = signal<string | null>(null);

  data: DialogData;

  constructor() {
    this.data = this.config.data as DialogData;
  }

  ngOnInit(): void {
    this.initForm();
    this.loadBoqSections();
  }

  private initForm(): void {
    this.questionForm = this.fb.group({
      subject: ['', [Validators.required, Validators.maxLength(200)]],
      question: ['', [Validators.required, Validators.minLength(20), Validators.maxLength(2000)]],
      relatedBoqSection: [null],
      isAnonymous: [false]
    });
  }

  private loadBoqSections(): void {
    this.portalService.getBoqSections(this.data.tenderId).subscribe({
      next: (sections) => this.boqSections.set(sections),
      error: () => {
        // Silently fail - BOQ sections are optional
      }
    });
  }

  isFieldInvalid(field: string): boolean {
    const control = this.questionForm.get(field);
    return !!(control && control.invalid && (control.dirty || control.touched));
  }

  isDeadlinePassed(): boolean {
    if (!this.data.clarificationDeadline) return false;
    return new Date(this.data.clarificationDeadline) < new Date();
  }

  isDeadlineNear(): boolean {
    if (!this.data.clarificationDeadline) return false;
    const deadline = new Date(this.data.clarificationDeadline);
    const now = new Date();
    const hoursRemaining = (deadline.getTime() - now.getTime()) / (1000 * 60 * 60);
    return hoursRemaining > 0 && hoursRemaining <= 24;
  }

  onSubmit(): void {
    if (this.questionForm.invalid || this.isDeadlinePassed()) {
      this.questionForm.markAllAsTouched();
      return;
    }

    this.isSubmitting.set(true);
    this.error.set(null);

    const dto: SubmitQuestionDto = {
      tenderId: this.data.tenderId,
      subject: this.questionForm.value.subject,
      question: this.questionForm.value.question,
      relatedBoqSection: this.questionForm.value.relatedBoqSection || undefined,
      isAnonymous: this.questionForm.value.isAnonymous
    };

    this.portalService.submitQuestion(dto).subscribe({
      next: (clarification) => {
        this.isSubmitting.set(false);
        this.dialogRef.close(clarification);
      },
      error: (err) => {
        this.isSubmitting.set(false);
        this.error.set(err.message || 'Failed to submit question. Please try again.');
      }
    });
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
