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
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputTextarea } from 'primeng/inputtextarea';
import { DropdownModule } from 'primeng/dropdown';
import { ButtonModule } from 'primeng/button';
import { MessageModule } from 'primeng/message';

import { BoqService } from '../../../../core/services/boq.service';
import {
  BoqSection,
  CreateBoqSectionDto,
  UpdateBoqSectionDto
} from '../../../../core/models/boq.model';

@Component({
  selector: 'app-boq-section-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    DialogModule,
    InputTextModule,
    InputTextarea,
    DropdownModule,
    ButtonModule,
    MessageModule
  ],
  template: `
    <p-dialog
      [header]="mode === 'create' ? 'Add Section' : 'Edit Section'"
      [(visible)]="visible"
      (visibleChange)="visibleChange.emit($event)"
      [modal]="true"
      [style]="{ width: '500px' }"
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

      <form [formGroup]="sectionForm" (ngSubmit)="onSubmit()">
        <div class="form-grid">
          <div class="form-field">
            <label for="parentSectionId">Parent Section</label>
            <p-dropdown
              id="parentSectionId"
              [options]="parentSectionOptions"
              formControlName="parentSectionId"
              placeholder="None (Top Level)"
              [showClear]="true"
              optionLabel="label"
              optionValue="value"
              styleClass="w-full"
            ></p-dropdown>
            <small class="field-hint">Leave empty for a top-level section</small>
          </div>

          <div class="form-field">
            <label for="sectionNumber">Section Number <span class="required">*</span></label>
            <input
              pInputText
              id="sectionNumber"
              formControlName="sectionNumber"
              placeholder="e.g., 1, 1.1, 2.1.1"
              class="w-full"
              data-testid="section-number"
              [class.ng-invalid]="isFieldInvalid('sectionNumber')"
            />
            @if (isFieldInvalid('sectionNumber')) {
              <small class="p-error">Section number is required</small>
            }
          </div>

          <div class="form-field">
            <label for="title">Title <span class="required">*</span></label>
            <input
              pInputText
              id="title"
              formControlName="title"
              placeholder="Enter section title"
              class="w-full"
              data-testid="section-title"
              [class.ng-invalid]="isFieldInvalid('title')"
            />
            @if (isFieldInvalid('title')) {
              <small class="p-error">Title is required</small>
            }
          </div>

          <div class="form-field">
            <label for="description">Description</label>
            <textarea
              pInputTextarea
              id="description"
              formControlName="description"
              placeholder="Optional description"
              class="w-full"
              [rows]="3"
              [autoResize]="true"
            ></textarea>
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
            [label]="mode === 'create' ? 'Add Section' : 'Update Section'"
            [loading]="isLoading"
            [disabled]="sectionForm.invalid || isLoading"
            data-testid="section-save-btn"
          ></button>
        </div>
      </form>
    </p-dialog>
  `,
  styles: [`
    .form-grid {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .form-field {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .form-field label {
      font-weight: 600;
      font-size: 0.875rem;
      color: var(--bayan-slate-700, #334155);
    }

    .required {
      color: var(--bayan-danger, #DC2626);
    }

    .field-hint {
      color: var(--bayan-muted-foreground, #64748B);
      font-size: 0.8rem;
    }

    .dialog-actions {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
      margin-top: 1.5rem;
      padding-top: 1rem;
      border-top: 1px solid var(--bayan-border, #E2E8F0);
    }

    :host ::ng-deep {
      .p-dropdown,
      .p-inputtext,
      .p-inputtextarea {
        width: 100%;
      }
    }
  `]
})
export class BoqSectionDialogComponent implements OnInit, OnChanges {
  @Input() visible = false;
  @Input() tenderId!: number;
  @Input() section: BoqSection | null = null;
  @Input() sections: BoqSection[] = [];
  @Input() mode: 'create' | 'edit' = 'create';

  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() saved = new EventEmitter<BoqSection>();

  private readonly fb = inject(FormBuilder);
  private readonly boqService = inject(BoqService);

  sectionForm!: FormGroup;
  isLoading = false;
  errorMessage: string | null = null;

  parentSectionOptions: { label: string; value: string | number }[] = [];

  ngOnInit(): void {
    this.initForm();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && this.visible) {
      this.initForm();
      this.updateParentOptions();
      this.populateForm();
    }

    if (changes['sections']) {
      this.updateParentOptions();
    }
  }

  private initForm(): void {
    this.sectionForm = this.fb.group({
      parentSectionId: [null],
      sectionNumber: ['', Validators.required],
      title: ['', Validators.required],
      description: ['']
    });
    this.errorMessage = null;
  }

  private updateParentOptions(): void {
    // Filter out the current section and its children when editing
    let availableSections = this.sections;

    if (this.mode === 'edit' && this.section) {
      const excludeIds = this.getChildSectionIds(this.section.id);
      excludeIds.push(this.section.id);
      availableSections = this.sections.filter(s => !excludeIds.includes(s.id));
    }

    this.parentSectionOptions = availableSections.map(s => ({
      label: `${s.sectionNumber} - ${s.title}`,
      value: s.id
    }));
  }

  private getChildSectionIds(parentId: string | number): (string | number)[] {
    const children = this.sections.filter(s => s.parentSectionId === parentId);
    return children.flatMap(child => [child.id, ...this.getChildSectionIds(child.id)]);
  }

  private populateForm(): void {
    if (this.mode === 'edit' && this.section) {
      this.sectionForm.patchValue({
        parentSectionId: this.section.parentSectionId,
        sectionNumber: this.section.sectionNumber,
        title: this.section.title,
        description: this.section.description || ''
      });
    } else if (this.section?.parentSectionId) {
      // Creating a subsection - pre-select parent
      this.sectionForm.patchValue({
        parentSectionId: this.section.parentSectionId
      });
    }
  }

  isFieldInvalid(field: string): boolean {
    const control = this.sectionForm.get(field);
    return !!(control && control.invalid && (control.dirty || control.touched));
  }

  onSubmit(): void {
    if (this.sectionForm.invalid) {
      this.sectionForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;

    const formValue = this.sectionForm.value;

    if (this.mode === 'create') {
      const createDto: CreateBoqSectionDto = {
        tenderId: this.tenderId,
        parentSectionId: formValue.parentSectionId || null,
        sectionNumber: formValue.sectionNumber,
        title: formValue.title,
        description: formValue.description || undefined
      };

      this.boqService.createSection(createDto).subscribe({
        next: (section) => {
          this.isLoading = false;
          this.saved.emit(section);
        },
        error: (error) => {
          this.isLoading = false;
          this.errorMessage = error.message || 'Failed to create section';
        }
      });
    } else {
      const updateDto: UpdateBoqSectionDto = {
        parentSectionId: formValue.parentSectionId || null,
        sectionNumber: formValue.sectionNumber,
        title: formValue.title,
        description: formValue.description || undefined
      };

      this.boqService.updateSection(this.section!.id, updateDto).subscribe({
        next: (section) => {
          this.isLoading = false;
          this.saved.emit(section);
        },
        error: (error) => {
          this.isLoading = false;
          this.errorMessage = error.message || 'Failed to update section';
        }
      });
    }
  }

  onCancel(): void {
    this.visibleChange.emit(false);
  }
}
