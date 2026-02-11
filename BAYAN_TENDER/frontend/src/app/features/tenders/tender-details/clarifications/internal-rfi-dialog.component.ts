import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnChanges,
  SimpleChanges,
  inject
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  Validators,
  ReactiveFormsModule
} from '@angular/forms';
import { forkJoin, of } from 'rxjs';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputTextarea } from 'primeng/inputtextarea';
import { DropdownModule } from 'primeng/dropdown';
import { DatePickerModule } from 'primeng/datepicker';
import { FileUploadModule } from 'primeng/fileupload';
import { ButtonModule } from 'primeng/button';
import { MessageModule } from 'primeng/message';
import { EditorModule } from 'primeng/editor';

import { ClarificationService } from '../../../../core/services/clarification.service';
import {
  Clarification,
  ClarificationPriority,
  CreateClarificationDto,
  UpdateClarificationDto,
  CLARIFICATION_PRIORITY_OPTIONS
} from '../../../../core/models/clarification.model';
import { BoqSection } from '../../../../core/models/boq.model';

@Component({
  selector: 'app-internal-rfi-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    DialogModule,
    InputTextModule,
    InputTextarea,
    DropdownModule,
    DatePickerModule,
    FileUploadModule,
    ButtonModule,
    MessageModule,
    EditorModule
  ],
  template: `
    <p-dialog
      [header]="mode === 'create' ? 'New Internal RFI' : 'Edit Internal RFI'"
      [(visible)]="visible"
      (visibleChange)="visibleChange.emit($event)"
      [modal]="true"
      [style]="{ width: '700px' }"
      [contentStyle]="{ overflow: 'auto' }"
      [draggable]="false"
      [resizable]="false"
    >
      @if (errorMessage) {
        <p-message
          severity="error"
          [text]="errorMessage"
          styleClass="w-full mb-3"
        ></p-message>
      }

      <form [formGroup]="rfiForm" (ngSubmit)="onSubmit()">
        <div class="form-grid">
          <div class="form-field full-width">
            <label for="subject">Subject <span class="required">*</span></label>
            <input
              pInputText
              id="subject"
              formControlName="subject"
              placeholder="Enter a concise subject"
              class="w-full"
              data-testid="rfi-subject"
              [class.ng-invalid]="isFieldInvalid('subject')"
            />
            @if (isFieldInvalid('subject')) {
              <small class="p-error">Subject is required</small>
            }
          </div>

          <div class="form-field">
            <label for="relatedBoqSectionId">Related BOQ Section</label>
            <p-dropdown
              id="relatedBoqSectionId"
              [options]="sectionOptions"
              formControlName="relatedBoqSectionId"
              placeholder="Select section (optional)"
              [showClear]="true"
              [filter]="true"
              filterPlaceholder="Search sections..."
              optionLabel="label"
              optionValue="value"
              styleClass="w-full"
            ></p-dropdown>
          </div>

          <div class="form-field">
            <label for="priority">Priority</label>
            <p-dropdown
              id="priority"
              [options]="priorityOptions"
              formControlName="priority"
              optionLabel="label"
              optionValue="value"
              styleClass="w-full"
            ></p-dropdown>
          </div>

          <div class="form-field full-width">
            <label for="question">Question <span class="required">*</span></label>
            <p-editor
              id="question"
              formControlName="question"
              [style]="{ height: '200px' }"
              placeholder="Enter your question or request for information..."
            >
              <ng-template pTemplate="header">
                <span class="ql-formats">
                  <button type="button" class="ql-bold" aria-label="Bold"></button>
                  <button type="button" class="ql-italic" aria-label="Italic"></button>
                  <button type="button" class="ql-underline" aria-label="Underline"></button>
                </span>
                <span class="ql-formats">
                  <button type="button" class="ql-list" value="ordered" aria-label="Ordered List"></button>
                  <button type="button" class="ql-list" value="bullet" aria-label="Unordered List"></button>
                </span>
              </ng-template>
            </p-editor>
            @if (isFieldInvalid('question')) {
              <small class="p-error">Question is required</small>
            }
          </div>

          <div class="form-field">
            <label for="dueDate">Due Date</label>
            <p-datepicker
              id="dueDate"
              formControlName="dueDate"
              [showIcon]="true"
              [showButtonBar]="true"
              [minDate]="minDate"
              dateFormat="dd/mm/yy"
              placeholder="Select due date (optional)"
              styleClass="w-full"
            ></p-datepicker>
          </div>

          <div class="form-field full-width">
            <label>Attachments</label>
            <p-fileUpload
              mode="basic"
              name="attachments"
              [multiple]="true"
              [auto]="false"
              chooseLabel="Add Files"
              chooseIcon="pi pi-paperclip"
              [maxFileSize]="10485760"
              (onSelect)="onFileSelect($event)"
            ></p-fileUpload>
            @if (selectedFiles.length > 0) {
              <div class="attached-files">
                @for (file of selectedFiles; track file.name) {
                  <div class="file-item">
                    <i class="pi pi-file"></i>
                    <span>{{ file.name }}</span>
                    <button
                      type="button"
                      pButton
                      icon="pi pi-times"
                      class="p-button-text p-button-danger p-button-sm"
                      (click)="removeFile(file)"
                    ></button>
                  </div>
                }
              </div>
            }
          </div>
        </div>

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
            [label]="mode === 'create' ? 'Create RFI' : 'Update RFI'"
            data-testid="rfi-submit-btn"
            [loading]="isLoading"
            [disabled]="rfiForm.invalid || isLoading"
          ></button>
        </div>
      </form>
    </p-dialog>
  `,
  styles: [`
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
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
    }

    .required {
      color: #ef4444;
    }

    .attached-files {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      margin-top: 0.5rem;
    }

    .file-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.5rem;
      background-color: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius-sm, 0.375rem);
    }

    .file-item span {
      flex: 1;
      font-size: 0.875rem;
      color: var(--bayan-foreground, #09090b);
    }

    .dialog-actions {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
      margin-top: 1.5rem;
      padding-top: 1rem;
      border-top: 1px solid var(--bayan-border, #e4e4e7);
    }

    :host ::ng-deep {
      .p-dropdown,
      .p-inputtext,
      .p-datepicker {
        width: 100%;
      }

      .p-editor-container {
        .p-editor-toolbar {
          background-color: var(--bayan-accent, #f4f4f5);
        }
      }
    }

    @media (max-width: 600px) {
      .form-grid {
        grid-template-columns: 1fr;
      }
    }
  `]
})
export class InternalRfiDialogComponent implements OnInit, OnChanges {
  @Input() visible = false;
  @Input() tenderId!: number;
  @Input() clarification: Clarification | null = null;
  @Input() sections: BoqSection[] = [];
  @Input() mode: 'create' | 'edit' = 'create';

  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() saved = new EventEmitter<Clarification>();

  private readonly fb = inject(FormBuilder);
  private readonly clarificationService = inject(ClarificationService);

  rfiForm!: FormGroup;
  isLoading = false;
  errorMessage: string | null = null;
  selectedFiles: File[] = [];
  minDate = new Date();

  sectionOptions: { label: string; value: number }[] = [];
  priorityOptions = CLARIFICATION_PRIORITY_OPTIONS;

  ngOnInit(): void {
    this.initForm();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && this.visible) {
      this.initForm();
      this.updateSectionOptions();
      this.populateForm();
    }

    if (changes['sections']) {
      this.updateSectionOptions();
    }
  }

  private initForm(): void {
    this.rfiForm = this.fb.group({
      subject: ['', Validators.required],
      question: ['', Validators.required],
      relatedBoqSectionId: [null],
      priority: ['medium' as ClarificationPriority],
      dueDate: [null]
    });
    this.errorMessage = null;
    this.selectedFiles = [];
  }

  private updateSectionOptions(): void {
    this.sectionOptions = this.sections.map(s => ({
      label: `${s.sectionNumber} - ${s.title}`,
      value: s.id
    }));
  }

  private populateForm(): void {
    if (this.mode === 'edit' && this.clarification) {
      this.rfiForm.patchValue({
        subject: this.clarification.subject,
        question: this.clarification.question,
        relatedBoqSectionId: this.clarification.relatedBoqSectionId,
        priority: this.clarification.priority,
        dueDate: this.clarification.dueDate ? new Date(this.clarification.dueDate) : null
      });
    }
  }

  isFieldInvalid(field: string): boolean {
    const control = this.rfiForm.get(field);
    return !!(control && control.invalid && (control.dirty || control.touched));
  }

  onFileSelect(event: any): void {
    if (event.files) {
      this.selectedFiles = [...this.selectedFiles, ...event.files];
    }
  }

  removeFile(file: File): void {
    this.selectedFiles = this.selectedFiles.filter(f => f !== file);
  }

  onSubmit(): void {
    if (this.rfiForm.invalid) {
      this.rfiForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;

    const formValue = this.rfiForm.value;

    // Strip HTML tags for plain text storage (or keep HTML depending on backend)
    const questionText = this.stripHtml(formValue.question);

    if (this.mode === 'create') {
      const createDto: CreateClarificationDto = {
        tenderId: this.tenderId,
        subject: formValue.subject,
        question: questionText,
        source: 'internal',
        priority: formValue.priority,
        relatedBoqSectionId: formValue.relatedBoqSectionId || undefined,
        dueDate: formValue.dueDate || undefined
      };

      this.clarificationService.createClarification(createDto).subscribe({
        next: (clarification) => {
          // Upload attachments if any
          if (this.selectedFiles.length > 0) {
            const uploads$ = this.selectedFiles.map(file =>
              this.clarificationService.uploadAttachment(this.tenderId, clarification.id as any, file)
            );
            forkJoin(uploads$).subscribe({
              next: () => {
                this.isLoading = false;
                this.saved.emit(clarification);
              },
              error: () => {
                // RFI created successfully, but some attachments failed — still emit success
                this.isLoading = false;
                this.saved.emit(clarification);
              }
            });
          } else {
            this.isLoading = false;
            this.saved.emit(clarification);
          }
        },
        error: (error) => {
          this.isLoading = false;
          this.errorMessage = error.message || 'Failed to create RFI';
        }
      });
    } else {
      const updateDto: UpdateClarificationDto = {
        subject: formValue.subject,
        question: questionText,
        priority: formValue.priority,
        relatedBoqSectionId: formValue.relatedBoqSectionId || null,
        dueDate: formValue.dueDate || null
      };

      this.clarificationService.updateClarification(this.tenderId, this.clarification!.id, updateDto).subscribe({
        next: (clarification) => {
          this.isLoading = false;
          this.saved.emit(clarification);
        },
        error: (error) => {
          this.isLoading = false;
          this.errorMessage = error.message || 'Failed to update RFI';
        }
      });
    }
  }

  private stripHtml(html: string): string {
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
  }

  onCancel(): void {
    this.visibleChange.emit(false);
  }
}
