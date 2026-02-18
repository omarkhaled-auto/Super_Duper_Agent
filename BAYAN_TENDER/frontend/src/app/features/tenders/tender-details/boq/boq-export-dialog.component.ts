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
import { SelectButtonModule } from 'primeng/selectbutton';
import { ButtonModule } from 'primeng/button';
import { DividerModule } from 'primeng/divider';
import { TagModule } from 'primeng/tag';

import { BoqService } from '../../../../core/services/boq.service';
import { BoqExportOptions, PricingLevel } from '../../../../core/models/boq.model';

@Component({
  selector: 'app-boq-export-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    DialogModule,
    CheckboxModule,
    DropdownModule,
    SelectButtonModule,
    ButtonModule,
    DividerModule,
    TagModule
  ],
  template: `
    <p-dialog
      header="Export BOQ Template"
      [(visible)]="visible"
      (visibleChange)="visibleChange.emit($event)"
      [modal]="true"
      [style]="{ width: '560px' }"
      [contentStyle]="{ overflow: 'auto' }"
      [draggable]="false"
      [resizable]="false"
    >
      <div class="export-options">
        <!-- Pricing Level Selection -->
        <div class="option-section">
          <h4>Export Mode</h4>
          <p-selectButton
            [options]="pricingLevelOptions"
            [(ngModel)]="selectedPricingLevel"
            (ngModelChange)="onPricingLevelChange($event)"
            optionLabel="label"
            optionValue="value"
            styleClass="w-full"
          ></p-selectButton>
          <div class="export-mode-description">
            <p-tag
              [severity]="getModeSeverity()"
              [value]="getModeDescription()"
              [style]="{ 'white-space': 'normal', 'text-align': 'left', 'max-width': '100%' }"
            ></p-tag>
          </div>
        </div>

        <p-divider></p-divider>

        <!-- Column Selection -->
        <div class="option-section">
          <h4>Columns to Include</h4>
          <div class="checkbox-grid">
            <div class="checkbox-item">
              <p-checkbox
                [(ngModel)]="options.columns.section"
                [binary]="true"
                inputId="col-section"
              ></p-checkbox>
              <label for="col-section">Section / Bill</label>
            </div>
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
            <div class="checkbox-item" *ngIf="selectedPricingLevel !== 'Bill'">
              <p-checkbox
                [(ngModel)]="options.columns.quantity"
                [binary]="true"
                inputId="col-quantity"
              ></p-checkbox>
              <label for="col-quantity">Quantity</label>
            </div>
            <div class="checkbox-item" *ngIf="selectedPricingLevel !== 'Bill'">
              <p-checkbox
                [(ngModel)]="options.columns.uom"
                [binary]="true"
                inputId="col-uom"
              ></p-checkbox>
              <label for="col-uom">Unit of Measure</label>
            </div>
            <div class="checkbox-item">
              <p-checkbox
                [(ngModel)]="options.columns.notes"
                [binary]="true"
                inputId="col-notes"
              ></p-checkbox>
              <label for="col-notes">Notes</label>
            </div>
            <div class="checkbox-item" *ngIf="selectedPricingLevel === 'SubItem'">
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
              <label for="col-totalAmount">
                {{ selectedPricingLevel === 'Bill' ? 'Amount (Empty)' :
                   selectedPricingLevel === 'Item' ? 'Rate (Empty)' :
                   'Total Amount (Formula)' }}
              </label>
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
            <label for="opt-lock">
              {{ selectedPricingLevel === 'Bill'
                ? 'Lock read-only columns (Bill #, Description)'
                : 'Lock read-only columns (Item #, Description, Qty, UOM)' }}
            </label>
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
      color: var(--bayan-slate-700, #334155);
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
      color: var(--bayan-slate-700, #334155);
    }

    .dropdown-field {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      margin-top: 1rem;
    }

    .dropdown-field label {
      font-weight: 500;
      color: var(--bayan-slate-700, #334155);
    }

    .export-mode-description {
      margin-top: 0.75rem;
    }

    .export-mode-description :host ::ng-deep .p-tag {
      font-size: 0.8125rem;
      padding: 0.375rem 0.75rem;
      line-height: 1.4;
    }

    :host ::ng-deep .p-selectbutton .p-button {
      flex: 1;
    }

    .dialog-footer {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
      margin-top: 1.5rem;
      padding-top: 1rem;
      border-top: 1px solid var(--bayan-border, #E2E8F0);
    }

    :host ::ng-deep .p-dropdown {
      width: 100%;
    }
  `]
})
export class BoqExportDialogComponent implements OnChanges {
  @Input() visible = false;
  @Input() tenderId!: number;
  @Input() pricingLevel: PricingLevel = 'SubItem';

  @Output() visibleChange = new EventEmitter<boolean>();

  private readonly boqService = inject(BoqService);

  isExporting = signal<boolean>(false);
  selectedPricingLevel: PricingLevel = 'SubItem';

  options: BoqExportOptions = {
    columns: {
      section: true,
      itemNumber: true,
      description: true,
      quantity: true,
      uom: true,
      notes: true,
      unitRate: true,
      totalAmount: true
    },
    lockColumns: true,
    includeInstructions: true,
    language: 'en',
    pricingLevel: 'SubItem'
  };

  pricingLevelOptions = [
    { label: 'Sub-Item', value: 'SubItem' as PricingLevel },
    { label: 'Item', value: 'Item' as PricingLevel },
    { label: 'Bill', value: 'Bill' as PricingLevel }
  ];

  languageOptions = [
    { label: 'English', value: 'en' },
    { label: 'Arabic', value: 'ar' },
    { label: 'Bilingual (English & Arabic)', value: 'both' }
  ];

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && this.visible) {
      this.selectedPricingLevel = this.pricingLevel || 'SubItem';
      this.resetOptions();
    }
  }

  onPricingLevelChange(level: PricingLevel): void {
    this.selectedPricingLevel = level;
    this.options.pricingLevel = level;
    this.applyPricingLevelDefaults(level);
  }

  getModeSeverity(): 'info' | 'success' | 'warn' {
    switch (this.selectedPricingLevel) {
      case 'SubItem': return 'info';
      case 'Item': return 'success';
      case 'Bill': return 'warn';
      default: return 'info';
    }
  }

  getModeDescription(): string {
    switch (this.selectedPricingLevel) {
      case 'SubItem':
        return 'Full detail: Units, Qty, Rate for each sub-item. Totals roll up to items and bills.';
      case 'Item':
        return 'Item-level: Items with rate column. Sub-items shown as read-only detail rows.';
      case 'Bill':
        return 'Bill-level: Bills with a single amount column. No item-level breakdown.';
      default:
        return '';
    }
  }

  private applyPricingLevelDefaults(level: PricingLevel): void {
    switch (level) {
      case 'SubItem':
        this.options.columns.quantity = true;
        this.options.columns.uom = true;
        this.options.columns.unitRate = true;
        this.options.columns.totalAmount = true;
        break;
      case 'Item':
        this.options.columns.quantity = true;
        this.options.columns.uom = true;
        this.options.columns.unitRate = false;
        this.options.columns.totalAmount = true;
        break;
      case 'Bill':
        this.options.columns.quantity = false;
        this.options.columns.uom = false;
        this.options.columns.unitRate = false;
        this.options.columns.totalAmount = true;
        break;
    }
  }

  private resetOptions(): void {
    this.options = {
      columns: {
        section: true,
        itemNumber: true,
        description: true,
        quantity: true,
        uom: true,
        notes: true,
        unitRate: true,
        totalAmount: true
      },
      lockColumns: true,
      includeInstructions: true,
      language: 'en',
      pricingLevel: this.selectedPricingLevel
    };
    this.applyPricingLevelDefaults(this.selectedPricingLevel);
  }

  exportBoq(): void {
    this.isExporting.set(true);
    this.options.pricingLevel = this.selectedPricingLevel;

    this.boqService.exportToExcel(String(this.tenderId), this.options).subscribe({
      next: (blob) => {
        this.isExporting.set(false);

        const levelSuffix = this.selectedPricingLevel.toLowerCase();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `boq-template-${this.tenderId}-${levelSuffix}-${new Date().toISOString().split('T')[0]}.xlsx`;
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
