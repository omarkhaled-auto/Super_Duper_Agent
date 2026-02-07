import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnChanges,
  SimpleChanges,
  inject,
  signal
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DialogModule } from 'primeng/dialog';
import { CheckboxModule } from 'primeng/checkbox';
import { DropdownModule } from 'primeng/dropdown';
import { ButtonModule } from 'primeng/button';
import { DividerModule } from 'primeng/divider';

import { BoqService } from '../../../../core/services/boq.service';
import { BoqExportOptions } from '../../../../core/models/boq.model';

@Component({
  selector: 'app-boq-export-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    DialogModule,
    CheckboxModule,
    DropdownModule,
    ButtonModule,
    DividerModule
  ],
  template: `
    <p-dialog
      header="Export BOQ Template"
      [(visible)]="visible"
      (visibleChange)="visibleChange.emit($event)"
      [modal]="true"
      [style]="{ width: '500px' }"
      [contentStyle]="{ overflow: 'auto' }"
      [draggable]="false"
      [resizable]="false"
    >
      <div class="export-options">
        <!-- Column Selection -->
        <div class="option-section">
          <h4>Columns to Include</h4>
          <div class="checkbox-grid">
            <div class="checkbox-item">
              <p-checkbox
                [(ngModel)]="options.columns.itemNumber"
                [binary]="true"
                inputId="col-itemNumber"
              ></p-checkbox>
              <label for="col-itemNumber">Item Number</label>
            </div>
            <div class="checkbox-item">
              <p-checkbox
                [(ngModel)]="options.columns.description"
                [binary]="true"
                inputId="col-description"
              ></p-checkbox>
              <label for="col-description">Description</label>
            </div>
            <div class="checkbox-item">
              <p-checkbox
                [(ngModel)]="options.columns.quantity"
                [binary]="true"
                inputId="col-quantity"
              ></p-checkbox>
              <label for="col-quantity">Quantity</label>
            </div>
            <div class="checkbox-item">
              <p-checkbox
                [(ngModel)]="options.columns.uom"
                [binary]="true"
                inputId="col-uom"
              ></p-checkbox>
              <label for="col-uom">Unit of Measure</label>
            </div>
            <div class="checkbox-item">
              <p-checkbox
                [(ngModel)]="options.columns.type"
                [binary]="true"
                inputId="col-type"
              ></p-checkbox>
              <label for="col-type">Item Type</label>
            </div>
            <div class="checkbox-item">
              <p-checkbox
                [(ngModel)]="options.columns.notes"
                [binary]="true"
                inputId="col-notes"
              ></p-checkbox>
              <label for="col-notes">Notes</label>
            </div>
            <div class="checkbox-item">
              <p-checkbox
                [(ngModel)]="options.columns.unitRate"
                [binary]="true"
                inputId="col-unitRate"
              ></p-checkbox>
              <label for="col-unitRate">Unit Rate (Empty)</label>
            </div>
            <div class="checkbox-item">
              <p-checkbox
                [(ngModel)]="options.columns.totalAmount"
                [binary]="true"
                inputId="col-totalAmount"
              ></p-checkbox>
              <label for="col-totalAmount">Total Amount (Formula)</label>
            </div>
          </div>
        </div>

        <p-divider></p-divider>

        <!-- Protection Options -->
        <div class="option-section">
          <h4>Protection Options</h4>
          <div class="checkbox-item">
            <p-checkbox
              [(ngModel)]="options.lockColumns"
              [binary]="true"
              inputId="opt-lock"
            ></p-checkbox>
            <label for="opt-lock">Lock read-only columns (Item #, Description, Qty, UOM)</label>
          </div>
        </div>

        <p-divider></p-divider>

        <!-- Additional Options -->
        <div class="option-section">
          <h4>Additional Options</h4>
          <div class="checkbox-item">
            <p-checkbox
              [(ngModel)]="options.includeInstructions"
              [binary]="true"
              inputId="opt-instructions"
            ></p-checkbox>
            <label for="opt-instructions">Include instructions sheet</label>
          </div>

          <div class="dropdown-field">
            <label for="language">Language</label>
            <p-dropdown
              id="language"
              [options]="languageOptions"
              [(ngModel)]="options.language"
              optionLabel="label"
              optionValue="value"
              styleClass="w-full"
              data-testid="boq-export-language"
            ></p-dropdown>
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <button
          pButton
          label="Cancel"
          class="p-button-text"
          (click)="onCancel()"
        ></button>
        <button
          pButton
          label="Download"
          icon="pi pi-download"
          [loading]="isExporting()"
          data-testid="boq-export-btn"
          (click)="exportBoq()"
        ></button>
      </div>
    </p-dialog>
  `,
  styles: [`
    .export-options {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .option-section h4 {
      margin: 0 0 1rem;
      color: #333;
      font-size: 1rem;
    }

    .checkbox-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.75rem;
    }

    .checkbox-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .checkbox-item label {
      cursor: pointer;
      color: #333;
    }

    .dropdown-field {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      margin-top: 1rem;
    }

    .dropdown-field label {
      font-weight: 500;
      color: #333;
    }

    .dialog-footer {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
      margin-top: 1.5rem;
      padding-top: 1rem;
      border-top: 1px solid #e0e0e0;
    }

    :host ::ng-deep .p-dropdown {
      width: 100%;
    }
  `]
})
export class BoqExportDialogComponent implements OnChanges {
  @Input() visible = false;
  @Input() tenderId!: number;

  @Output() visibleChange = new EventEmitter<boolean>();

  private readonly boqService = inject(BoqService);

  isExporting = signal<boolean>(false);

  options: BoqExportOptions = {
    columns: {
      itemNumber: true,
      description: true,
      quantity: true,
      uom: true,
      type: true,
      notes: true,
      unitRate: true,
      totalAmount: true
    },
    lockColumns: true,
    includeInstructions: true,
    language: 'en'
  };

  languageOptions = [
    { label: 'English', value: 'en' },
    { label: 'Arabic', value: 'ar' },
    { label: 'Bilingual (English & Arabic)', value: 'both' }
  ];

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && this.visible) {
      this.resetOptions();
    }
  }

  private resetOptions(): void {
    this.options = {
      columns: {
        itemNumber: true,
        description: true,
        quantity: true,
        uom: true,
        type: true,
        notes: true,
        unitRate: true,
        totalAmount: true
      },
      lockColumns: true,
      includeInstructions: true,
      language: 'en'
    };
  }

  exportBoq(): void {
    this.isExporting.set(true);

    this.boqService.exportToExcel(this.tenderId, this.options).subscribe({
      next: (blob) => {
        this.isExporting.set(false);

        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `boq-template-${this.tenderId}-${new Date().toISOString().split('T')[0]}.xlsx`;
        link.click();
        window.URL.revokeObjectURL(url);

        this.visibleChange.emit(false);
      },
      error: (error) => {
        this.isExporting.set(false);
      }
    });
  }

  onCancel(): void {
    this.visibleChange.emit(false);
  }
}
