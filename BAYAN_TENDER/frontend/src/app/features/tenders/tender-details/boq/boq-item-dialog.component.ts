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
import { InputNumberModule } from 'primeng/inputnumber';
import { DropdownModule } from 'primeng/dropdown';
import { RadioButtonModule } from 'primeng/radiobutton';
import { ButtonModule } from 'primeng/button';
import { MessageModule } from 'primeng/message';

import { BoqService } from '../../../../core/services/boq.service';
import {
  BoqItem,
  BoqSection,
  BoqItemType,
  CreateBoqItemDto,
  UpdateBoqItemDto,
  UOM_OPTIONS,
  BOQ_ITEM_TYPE_OPTIONS
} from '../../../../core/models/boq.model';

@Component({
  selector: 'app-boq-item-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    DialogModule,
    InputTextModule,
    InputTextarea,
    InputNumberModule,
    DropdownModule,
    RadioButtonModule,
    ButtonModule,
    MessageModule
  ],
  template: `
    <p-dialog
      [header]="mode === 'create' ? 'Add Item' : 'Edit Item'"
      [(visible)]="visible"
      (visibleChange)="visibleChange.emit($event)"
      [modal]="true"
      [style]="{ width: '600px' }"
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

      <form [formGroup]="itemForm" (ngSubmit)="onSubmit()">
        <div class="form-grid">
          <div class="form-field">
            <label for="sectionId">Section <span class="required">*</span></label>
            <p-dropdown
              id="sectionId"
              [options]="sectionOptions"
              formControlName="sectionId"
              placeholder="Select section"
              optionLabel="label"
              optionValue="value"
              styleClass="w-full"
              [class.ng-invalid]="isFieldInvalid('sectionId')"
            ></p-dropdown>
            @if (isFieldInvalid('sectionId')) {
              <small class="p-error">Section is required</small>
            }
          </div>

          <div class="form-field">
            <label for="itemNumber">Item Number <span class="required">*</span></label>
            <input
              pInputText
              id="itemNumber"
              formControlName="itemNumber"
              placeholder="e.g., 1.1.1, 2.1.3"
              class="w-full"
              [class.ng-invalid]="isFieldInvalid('itemNumber')"
            />
            @if (isFieldInvalid('itemNumber')) {
              <small class="p-error">Item number is required</small>
            }
          </div>

          <div class="form-field full-width">
            <label for="description">Description <span class="required">*</span></label>
            <textarea
              pInputTextarea
              id="description"
              formControlName="description"
              placeholder="Enter item description"
              class="w-full"
              data-testid="item-description"
              [rows]="3"
              [autoResize]="true"
              [class.ng-invalid]="isFieldInvalid('description')"
            ></textarea>
            @if (isFieldInvalid('description')) {
              <small class="p-error">Description is required</small>
            }
          </div>

          <div class="form-field">
            <label for="quantity">Quantity <span class="required">*</span></label>
            <p-inputNumber
              id="quantity"
              formControlName="quantity"
              [min]="0"
              [minFractionDigits]="0"
              [maxFractionDigits]="4"
              mode="decimal"
              styleClass="w-full"
              inputStyleClass="w-full"
              data-testid="item-quantity"
              [class.ng-invalid]="isFieldInvalid('quantity')"
            ></p-inputNumber>
            @if (isFieldInvalid('quantity')) {
              <small class="p-error">Quantity is required</small>
            }
          </div>

          <div class="form-field">
            <label for="uom">Unit of Measure <span class="required">*</span></label>
            <p-dropdown
              id="uom"
              [options]="uomOptions"
              formControlName="uom"
              placeholder="Select UOM"
              optionLabel="label"
              optionValue="value"
              [filter]="true"
              filterPlaceholder="Search..."
              styleClass="w-full"
              data-testid="item-uom"
              [class.ng-invalid]="isFieldInvalid('uom')"
            ></p-dropdown>
            @if (isFieldInvalid('uom')) {
              <small class="p-error">Unit of measure is required</small>
            }
          </div>

          <div class="form-field full-width">
            <label>Type</label>
            <div class="type-options">
              @for (option of itemTypeOptions; track option.value) {
                <div class="type-option">
                  <p-radioButton
                    [inputId]="'type-' + option.value"
                    name="type"
                    [value]="option.value"
                    formControlName="type"
                  ></p-radioButton>
                  <label [for]="'type-' + option.value" class="type-label">
                    <span class="type-name">{{ option.label }}</span>
                    <span class="type-description">{{ option.description }}</span>
                  </label>
                </div>
              }
            </div>
          </div>

          <div class="form-field full-width">
            <label for="notes">Notes</label>
            <textarea
              pInputTextarea
              id="notes"
              formControlName="notes"
              placeholder="Optional notes"
              class="w-full"
              [rows]="2"
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
            [label]="mode === 'create' ? 'Add Item' : 'Update Item'"
            [loading]="isLoading"
            [disabled]="itemForm.invalid || isLoading"
            data-testid="item-save-btn"
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

    .type-options {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.75rem;
    }

    .type-option {
      display: flex;
      align-items: flex-start;
      gap: 0.5rem;
      padding: 0.75rem;
      border: 1px solid var(--bayan-border, #e4e4e7);
      border-radius: 6px;
      transition: all 0.2s;
    }

    .type-option:hover {
      border-color: var(--bayan-primary, #18181b);
      background-color: var(--bayan-accent, #f4f4f5);
    }

    .type-label {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      cursor: pointer;
    }

    .type-name {
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
    }

    .type-description {
      font-size: 0.75rem;
      color: var(--bayan-muted-foreground, #71717a);
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
      .p-inputtextarea,
      .p-inputnumber {
        width: 100%;
      }

      .p-inputnumber-input {
        width: 100%;
      }
    }

    @media (max-width: 600px) {
      .form-grid {
        grid-template-columns: 1fr;
      }

      .type-options {
        grid-template-columns: 1fr;
      }
    }
  `]
})
export class BoqItemDialogComponent implements OnInit, OnChanges {
  @Input() visible = false;
  @Input() tenderId!: number;
  @Input() item: BoqItem | null = null;
  @Input() sections: BoqSection[] = [];
  @Input() mode: 'create' | 'edit' = 'create';

  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() saved = new EventEmitter<BoqItem>();

  private readonly fb = inject(FormBuilder);
  private readonly boqService = inject(BoqService);

  itemForm!: FormGroup;
  isLoading = false;
  errorMessage: string | null = null;

  sectionOptions: { label: string; value: number }[] = [];
  uomOptions = UOM_OPTIONS;
  itemTypeOptions = BOQ_ITEM_TYPE_OPTIONS;

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
    this.itemForm = this.fb.group({
      sectionId: [null, Validators.required],
      itemNumber: ['', Validators.required],
      description: ['', Validators.required],
      quantity: [1, [Validators.required, Validators.min(0)]],
      uom: ['', Validators.required],
      type: ['base' as BoqItemType],
      notes: ['']
    });
    this.errorMessage = null;
  }

  private updateSectionOptions(): void {
    this.sectionOptions = this.sections.map(s => ({
      label: `${s.sectionNumber} - ${s.title}`,
      value: s.id
    }));
  }

  private populateForm(): void {
    if (this.mode === 'edit' && this.item) {
      this.itemForm.patchValue({
        sectionId: this.item.sectionId,
        itemNumber: this.item.itemNumber,
        description: this.item.description,
        quantity: this.item.quantity,
        uom: this.item.uom,
        type: this.item.type,
        notes: this.item.notes || ''
      });
    } else if (this.item?.sectionId) {
      // Pre-select section when adding item to specific section
      this.itemForm.patchValue({
        sectionId: this.item.sectionId
      });
    }
  }

  isFieldInvalid(field: string): boolean {
    const control = this.itemForm.get(field);
    return !!(control && control.invalid && (control.dirty || control.touched));
  }

  onSubmit(): void {
    if (this.itemForm.invalid) {
      this.itemForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;

    const formValue = this.itemForm.value;

    if (this.mode === 'create') {
      const createDto: CreateBoqItemDto = {
        tenderId: this.tenderId,
        sectionId: formValue.sectionId,
        itemNumber: formValue.itemNumber,
        description: formValue.description,
        quantity: formValue.quantity,
        uom: formValue.uom,
        type: formValue.type,
        notes: formValue.notes || undefined
      };

      this.boqService.createItem(createDto).subscribe({
        next: (item) => {
          this.isLoading = false;
          this.saved.emit(item);
        },
        error: (error) => {
          this.isLoading = false;
          this.errorMessage = error.message || 'Failed to create item';
        }
      });
    } else {
      const updateDto: UpdateBoqItemDto = {
        sectionId: formValue.sectionId,
        itemNumber: formValue.itemNumber,
        description: formValue.description,
        quantity: formValue.quantity,
        uom: formValue.uom,
        type: formValue.type,
        notes: formValue.notes || undefined
      };

      this.boqService.updateItem(this.item!.id, updateDto).subscribe({
        next: (item) => {
          this.isLoading = false;
          this.saved.emit(item);
        },
        error: (error) => {
          this.isLoading = false;
          this.errorMessage = error.message || 'Failed to update item';
        }
      });
    }
  }

  onCancel(): void {
    this.visibleChange.emit(false);
  }
}
