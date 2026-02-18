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
import { FileUploadModule, FileSelectEvent } from 'primeng/fileupload';
import { TableModule } from 'primeng/table';
import { DropdownModule } from 'primeng/dropdown';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { MessageModule } from 'primeng/message';
import { MessagesModule } from 'primeng/messages';
import { ProgressBarModule } from 'primeng/progressbar';
import { TooltipModule } from 'primeng/tooltip';
import { CheckboxModule } from 'primeng/checkbox';
import { MenuItem } from 'primeng/api';

import { BoqService } from '../../../../core/services/boq.service';
import { BoqImportRow } from '../../../../core/models/boq.model';

/** Hierarchy level types for BOQ rows */
type HierarchyLevel = 'Bill' | 'Item Group' | 'Item' | 'Sub-Item';

/** Regex patterns for hierarchy detection (mirrors backend logic) */
const BILL_PATTERN = /^bill\s*(no\.?\s*)?(\d+)/i;
const ITEM_NUMBER_PATTERN = /^\d+(\.\d+)+$/;
const SUB_ITEM_LABEL_PATTERN = /^[a-zA-Z][\.\)\-]?\s|^[ivxIVX]+[\.\)]\s|^[a-z]\)/;

/** Backend BoqField enum values */
const BOQ_FIELD: Record<string, number> = {
  itemNumber: 1,
  description: 2,
  quantity: 3,
  uom: 4,
  sectionTitle: 5,
  notes: 6,
  unitRate: 7,
  amount: 8,  // Backend enum is "Amount", not "TotalAmount"
  specification: 9,
  billNumber: 10,
  subItemLabel: 11
};

/** Reverse map: BoqField numeric value → frontend field key */
const BOQ_FIELD_REVERSE: Record<number, string> = {};
for (const [key, val] of Object.entries(BOQ_FIELD)) {
  BOQ_FIELD_REVERSE[val] = key;
}

@Component({
  selector: 'app-boq-import-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    DialogModule,
    StepsModule,
    FileUploadModule,
    TableModule,
    DropdownModule,
    ButtonModule,
    TagModule,
    MessageModule,
    MessagesModule,
    ProgressBarModule,
    TooltipModule,
    CheckboxModule
  ],
  template: `
    <p-dialog
      header="Import BOQ from Excel"
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
        <!-- Step 1: Upload -->
        @if (activeStep === 0) {
          <div class="upload-step">
            <div class="upload-instructions">
              <h4>Upload Excel File</h4>
              <p>Upload an Excel file (.xlsx or .xls) containing your BOQ data. Maximum file size is 50MB.</p>
              <a href="javascript:void(0)" class="template-link" (click)="downloadTemplate()">
                <i class="pi pi-download"></i>
                Download sample template
              </a>
            </div>

            <p-fileUpload
              mode="advanced"
              name="boqFile"
              [accept]="'.xlsx,.xls'"
              [maxFileSize]="52428800"
              [auto]="false"
              [showUploadButton]="false"
              [showCancelButton]="false"
              (onSelect)="onFileSelect($event)"
              (onRemove)="onFileRemove()"
              styleClass="upload-zone"
              data-testid="boq-import-upload"
            >
              <ng-template pTemplate="content">
                <div class="upload-content">
                  @if (!selectedFile()) {
                    <i class="pi pi-cloud-upload upload-icon"></i>
                    <p class="upload-text">Drag and drop your Excel file here</p>
                    <p class="upload-hint">or click to browse</p>
                  } @else {
                    <i class="pi pi-file-excel file-icon"></i>
                    <p class="file-name">{{ selectedFile()?.name }}</p>
                    <p class="file-size">{{ formatFileSize(selectedFile()?.size || 0) }}</p>
                  }
                </div>
              </ng-template>
            </p-fileUpload>

            @if (uploadError()) {
              <p-message
                severity="error"
                [text]="uploadError()!"
                styleClass="w-full mt-3"
              ></p-message>
            }
          </div>
        }

        <!-- Step 2: Map Columns -->
        @if (activeStep === 1) {
          <div class="mapping-step">
            <div class="mapping-header">
              <h4>Map Columns</h4>
              <p>Map the columns from your Excel file to the corresponding BOQ fields.</p>
              <button
                pButton
                label="Auto-Map"
                icon="pi pi-magic"
                class="p-button-outlined p-button-sm"
                (click)="autoMapColumns()"
              ></button>
            </div>

            <div class="preview-table">
              <p-table
                [value]="previewRows"
                [scrollable]="true"
                scrollHeight="200px"
                styleClass="p-datatable-sm"
              >
                <ng-template pTemplate="header">
                  <tr>
                    @for (col of excelColumns; track col) {
                      <th>
                        <div class="column-header">
                          <span class="excel-col">{{ col }}</span>
                          <p-dropdown
                            [options]="boqFieldOptions"
                            [(ngModel)]="columnMappings[col]"
                            placeholder="Select field"
                            [showClear]="true"
                            optionLabel="label"
                            optionValue="value"
                            styleClass="mapping-dropdown"
                          ></p-dropdown>
                        </div>
                      </th>
                    }
                  </tr>
                </ng-template>
                <ng-template pTemplate="body" let-row>
                  <tr>
                    @for (col of excelColumns; track col) {
                      <td>{{ row[col] }}</td>
                    }
                  </tr>
                </ng-template>
              </p-table>
            </div>

            @if (mappingError()) {
              <p-message
                severity="warn"
                [text]="mappingError()!"
                styleClass="w-full mt-3"
              ></p-message>
            }
          </div>
        }

        <!-- Step 3: Validate -->
        @if (activeStep === 2) {
          <div class="validation-step">
            <div class="validation-header">
              <h4>Validation Results</h4>
              @if (validationResult()) {
                <div class="validation-summary">
                  <div class="summary-badge valid">
                    <i class="pi pi-check-circle"></i>
                    <span>{{ validationResult()!.validCount }} Valid</span>
                  </div>
                  <div class="summary-badge warning">
                    <i class="pi pi-exclamation-triangle"></i>
                    <span>{{ validationResult()!.warningCount }} Warnings</span>
                  </div>
                  <div class="summary-badge error">
                    <i class="pi pi-times-circle"></i>
                    <span>{{ validationResult()!.errorCount }} Errors</span>
                  </div>
                </div>
              }
            </div>

            @if (isValidating()) {
              <div class="validating-state">
                <p-progressBar mode="indeterminate" [style]="{ height: '6px' }"></p-progressBar>
                <p>Validating data...</p>
              </div>
            } @else if (validationResult()) {
              <!-- Hierarchy Summary -->
              @if (hierarchySummary(); as summary) {
                <div class="hierarchy-summary">
                  <i class="pi pi-sitemap"></i>
                  <span class="hierarchy-label">Hierarchy:</span>
                  <p-tag [value]="summary.bills + ' Bills'" severity="info"></p-tag>
                  <p-tag [value]="summary.itemGroups + ' Item Groups'" severity="success"></p-tag>
                  <p-tag [value]="summary.items + ' Items'" severity="success"></p-tag>
                  <p-tag [value]="summary.subItems + ' Sub-Items'" severity="secondary"></p-tag>
                </div>
              }

              <!-- Hierarchy Integrity Warnings -->
              @if (hierarchyWarnings().length > 0) {
                <div class="hierarchy-warnings">
                  @for (warning of hierarchyWarnings(); track warning) {
                    <p-message
                      severity="warn"
                      [text]="warning"
                      styleClass="w-full"
                    ></p-message>
                  }
                </div>
              }

              <!-- Detected Sections -->
              @if (validationResult()!.detectedSections?.length) {
                <div class="detected-sections">
                  <h5>Detected Sections</h5>
                  <div class="section-tags">
                    @for (section of validationResult()!.detectedSections; track section.sectionNumber) {
                      <p-tag [value]="section.sectionNumber + ' - ' + section.title" severity="info"></p-tag>
                    }
                  </div>
                </div>
              }

              <!-- Import Options -->
              <div class="import-options">
                <div class="checkbox-item">
                  <p-checkbox
                    [(ngModel)]="clearExisting"
                    [binary]="true"
                    inputId="opt-clear"
                  ></p-checkbox>
                  <label for="opt-clear">Replace existing BOQ (delete all current sections &amp; items before import)</label>
                </div>
              </div>

              <!-- Validation Table -->
              <p-table
                [value]="validationRows()"
                [scrollable]="true"
                scrollHeight="250px"
                styleClass="p-datatable-sm validation-table"
              >
                <ng-template pTemplate="header">
                  <tr>
                    <th style="width: 60px">Row</th>
                    <th style="width: 80px">Status</th>
                    <th style="width: 100px">Level</th>
                    <th>Data Preview</th>
                    <th>Issues</th>
                  </tr>
                </ng-template>
                <ng-template pTemplate="body" let-row>
                  <tr [class]="getRowCssClasses(row)">
                    <td>{{ row.rowNumber }}</td>
                    <td>
                      <p-tag
                        [value]="row.status | titlecase"
                        [severity]="getStatusSeverity(row.status)"
                      ></p-tag>
                    </td>
                    <td>
                      <p-tag
                        [value]="inferRowLevel(row)"
                        [severity]="inferRowLevelSeverity(row)"
                      ></p-tag>
                    </td>
                    <td [style.padding-left]="getRowIndent(row)">
                      <span class="data-preview" [pTooltip]="getRowPreview(row)">
                        {{ getRowPreview(row) | slice:0:50 }}{{ getRowPreview(row).length > 50 ? '...' : '' }}
                      </span>
                    </td>
                    <td>
                      @if (row.errors?.length) {
                        <span class="error-text">{{ row.errors.join(', ') }}</span>
                      }
                      @if (row.warnings?.length) {
                        <span class="warning-text">{{ row.warnings.join(', ') }}</span>
                      }
                    </td>
                  </tr>
                </ng-template>
              </p-table>
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
              [disabled]="isUploading()"
            ></button>
          }

          @if (activeStep < 2) {
            <button
              pButton
              [label]="activeStep === 0 && isUploading() ? 'Uploading...' : 'Next'"
              icon="pi pi-arrow-right"
              iconPos="right"
              [disabled]="!canProceed()"
              [loading]="isUploading()"
              (click)="nextStep()"
            ></button>
          } @else {
            <button
              pButton
              label="Import Valid Items"
              icon="pi pi-check"
              [disabled]="!canImport()"
              [loading]="isImporting()"
              data-testid="boq-import-execute"
              (click)="importItems()"
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

    .upload-step {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .upload-instructions {
      text-align: center;
    }

    .upload-instructions h4 {
      margin: 0 0 0.5rem;
      color: var(--bayan-foreground, #020617);
    }

    .upload-instructions p {
      margin: 0;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .template-link {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      margin-top: 1rem;
      color: var(--bayan-primary, #4F46E5);
      text-decoration: none;
    }

    .template-link:hover {
      text-decoration: underline;
    }

    :host ::ng-deep .upload-zone {
      .p-fileupload-content {
        min-height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px dashed var(--bayan-slate-300, #CBD5E1);
        border-radius: var(--bayan-radius, 0.5rem);
        transition: all 0.2s;
      }

      .p-fileupload-content:hover {
        border-color: var(--bayan-primary, #4F46E5);
        background-color: var(--bayan-primary-light, #EEF2FF);
      }
    }

    .upload-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.5rem;
      padding: 2rem;
    }

    .upload-icon {
      font-size: 3rem;
      color: var(--bayan-slate-400, #94A3B8);
    }

    .upload-text {
      margin: 0;
      font-weight: 500;
      color: var(--bayan-slate-500, #64748B);
    }

    .upload-hint {
      margin: 0;
      font-size: 0.875rem;
      color: var(--bayan-slate-400, #94A3B8);
    }

    .file-icon {
      font-size: 3rem;
      color: var(--bayan-success, #22c55e);
    }

    .file-name {
      margin: 0;
      font-weight: 500;
      color: var(--bayan-foreground, #020617);
    }

    .file-size {
      margin: 0;
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .mapping-step {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .mapping-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1rem;
    }

    .mapping-header h4 {
      margin: 0;
      color: var(--bayan-foreground, #020617);
    }

    .mapping-header p {
      flex: 1 1 100%;
      margin: 0;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .column-header {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .excel-col {
      font-weight: 600;
      color: var(--bayan-primary, #4F46E5);
    }

    :host ::ng-deep .mapping-dropdown {
      width: 140px;

      .p-dropdown-label {
        font-size: 0.8rem;
      }
    }

    .validation-step {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .validation-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1rem;
    }

    .validation-header h4 {
      margin: 0;
      color: var(--bayan-foreground, #020617);
    }

    .validation-summary {
      display: flex;
      gap: 1rem;
    }

    .summary-badge {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.5rem 1rem;
      border-radius: 20px;
      font-size: 0.875rem;
      font-weight: 500;
    }

    .summary-badge.valid {
      background-color: var(--bayan-success-bg, #f0fdf4);
      color: var(--bayan-success, #16A34A);
    }

    .summary-badge.warning {
      background-color: var(--bayan-warning-bg, #fffbeb);
      color: var(--bayan-warning, #D97706);
    }

    .summary-badge.error {
      background-color: var(--bayan-danger-bg, #fef2f2);
      color: var(--bayan-danger, #DC2626);
    }

    .validating-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      padding: 2rem;
    }

    .validating-state p {
      margin: 0;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .hierarchy-summary {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem 1rem;
      background-color: var(--bayan-accent, #EEF2FF);
      border-radius: var(--bayan-radius, 0.5rem);
      border: 1px solid var(--bayan-primary-light, #C7D2FE);
    }

    .hierarchy-summary .pi-sitemap {
      color: var(--bayan-primary, #4F46E5);
      font-size: 1.1rem;
    }

    .hierarchy-label {
      font-weight: 600;
      color: var(--bayan-foreground, #020617);
      font-size: 0.875rem;
    }

    .hierarchy-warnings {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .detected-sections {
      padding: 1rem;
      background-color: var(--bayan-accent, #EEF2FF);
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .detected-sections h5 {
      margin: 0 0 0.5rem;
      color: var(--bayan-foreground, #020617);
    }

    .section-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    :host ::ng-deep .validation-table {
      .status-error {
        background-color: var(--bayan-danger-bg, #fef2f2) !important;
      }

      .status-warning {
        background-color: var(--bayan-warning-bg, #fffbeb) !important;
      }

      .level-bill {
        font-weight: 700;
        background-color: var(--bayan-primary-light, #EEF2FF) !important;
      }

      .level-item-group {
        font-weight: 600;
        background-color: var(--bayan-accent, #F1F5F9) !important;
      }

      .level-sub-item {
        color: var(--bayan-muted-foreground, #64748B);
      }
    }

    .data-preview {
      font-family: monospace;
      font-size: 0.8rem;
    }

    .error-text {
      color: var(--bayan-danger, #DC2626);
      font-size: 0.8rem;
    }

    .warning-text {
      color: var(--bayan-warning, #D97706);
      font-size: 0.8rem;
    }

    .import-options {
      padding: 0.75rem 1rem;
      background-color: var(--bayan-accent, #EEF2FF);
      border-radius: var(--bayan-radius, 0.5rem);
      margin-bottom: 0.5rem;
    }

    .checkbox-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .checkbox-item label {
      cursor: pointer;
      color: var(--bayan-foreground, #020617);
      font-size: 0.875rem;
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
  `]
})
export class BoqImportDialogComponent implements OnChanges {
  @Input() visible = false;
  @Input() tenderId!: number;

  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() imported = new EventEmitter<{ imported: number; failed: number }>();

  private readonly boqService = inject(BoqService);

  activeStep = 0;
  steps: MenuItem[] = [
    { label: 'Upload' },
    { label: 'Map Columns' },
    { label: 'Validate' }
  ];

  // Step 1: Upload
  selectedFile = signal<File | null>(null);
  uploadError = signal<string | null>(null);
  isUploading = signal<boolean>(false);

  // Step 2: Mapping — populated from backend preview
  excelColumns: string[] = [];
  previewRows: Record<string, any>[] = [];
  columnMappings: Record<string, string | null> = {};
  mappingError = signal<string | null>(null);

  /** Stored backend preview response (ExcelPreviewDto) */
  private uploadPreview: any = null;

  boqFieldOptions = [
    { label: 'Item Number', value: 'itemNumber' },
    { label: 'Description', value: 'description' },
    { label: 'Quantity', value: 'quantity' },
    { label: 'UOM', value: 'uom' },
    { label: 'Section Title', value: 'sectionTitle' },
    { label: 'Notes', value: 'notes' },
    { label: 'Unit Rate', value: 'unitRate' },
    { label: 'Amount', value: 'amount' },
    { label: 'Specification', value: 'specification' },
    { label: 'Bill Number', value: 'billNumber' },
    { label: 'Sub-Item Label', value: 'subItemLabel' }
  ];

  // Step 3: Validation
  isValidating = signal<boolean>(false);
  validationResult = signal<any | null>(null);
  validationRows = signal<BoqImportRow[]>([]);
  isImporting = signal<boolean>(false);
  clearExisting = true;

  /** Cached hierarchy level per row number (computed after validation) */
  private rowLevelCache = new Map<number, HierarchyLevel>();

  /** Hierarchy summary computed from validated rows */
  hierarchySummary = computed(() => {
    const rows = this.validationRows();
    if (rows.length === 0) return null;

    let bills = 0;
    let itemGroups = 0;
    let items = 0;
    let subItems = 0;

    for (const row of rows) {
      const level = this.inferRowLevel(row);
      switch (level) {
        case 'Bill': bills++; break;
        case 'Item Group': itemGroups++; break;
        case 'Item': items++; break;
        case 'Sub-Item': subItems++; break;
      }
    }

    return { bills, itemGroups, items, subItems };
  });

  /** Hierarchy integrity warnings computed from validated rows */
  hierarchyWarnings = computed(() => {
    const rows = this.validationRows();
    if (rows.length === 0) return [];

    const warnings: string[] = [];
    let lastBillRow: number | null = null;
    let lastItemGroupRow: number | null = null;
    let hasAnyBill = false;
    let hasAnyItemGroup = false;
    let orphanSubItems = 0;
    let orphanItems = 0;

    for (const row of rows) {
      const level = this.inferRowLevel(row);

      if (level === 'Bill') {
        hasAnyBill = true;
        lastBillRow = row.rowNumber;
        lastItemGroupRow = null; // reset within new bill
      } else if (level === 'Item Group') {
        hasAnyItemGroup = true;
        lastItemGroupRow = row.rowNumber;
        if (hasAnyBill && lastBillRow === null) {
          orphanItems++;
        }
      } else if (level === 'Item') {
        // Standalone items without a bill when bills exist
        if (hasAnyBill && lastBillRow === null) {
          orphanItems++;
        }
      } else if (level === 'Sub-Item') {
        if (lastItemGroupRow === null && !hasAnyItemGroup) {
          orphanSubItems++;
        } else if (hasAnyItemGroup && lastItemGroupRow === null) {
          orphanSubItems++;
        }
      }
    }

    if (orphanSubItems > 0) {
      warnings.push(
        `${orphanSubItems} sub-item(s) found without a preceding item group parent. ` +
        `These rows may not be correctly associated in the hierarchy.`
      );
    }
    if (orphanItems > 0) {
      warnings.push(
        `${orphanItems} item(s) found without a preceding bill. ` +
        `Consider mapping the Bill Number column for proper hierarchy detection.`
      );
    }

    // Check for empty bills (bills with no items after them)
    const levelSequence = rows.map(r => this.inferRowLevel(r));
    for (let i = 0; i < levelSequence.length; i++) {
      if (levelSequence[i] === 'Bill') {
        const nextLevel = i + 1 < levelSequence.length ? levelSequence[i + 1] : null;
        if (nextLevel === 'Bill' || nextLevel === null) {
          warnings.push(
            `Bill at row ${rows[i].rowNumber} has no items. ` +
            `Empty bills will be imported as section headers only.`
          );
        }
      }
    }

    return warnings;
  });

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && this.visible) {
      this.reset();
    }
  }

  private reset(): void {
    this.activeStep = 0;
    this.selectedFile.set(null);
    this.uploadError.set(null);
    this.isUploading.set(false);
    this.columnMappings = {};
    this.mappingError.set(null);
    this.validationResult.set(null);
    this.validationRows.set([]);
    this.isValidating.set(false);
    this.isImporting.set(false);
    this.clearExisting = true;
    this.uploadPreview = null;
    this.excelColumns = [];
    this.previewRows = [];
    this.rowLevelCache.clear();
  }

  onFileSelect(event: FileSelectEvent): void {
    const file = event.files[0];
    if (file) {
      if (file.size > 52428800) {
        this.uploadError.set('File size exceeds 50MB limit');
        return;
      }
      this.selectedFile.set(file);
      this.uploadError.set(null);
    }
  }

  onFileRemove(): void {
    this.selectedFile.set(null);
    this.uploadError.set(null);
  }

  downloadTemplate(): void {
    this.boqService.downloadTemplate().subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'boq-import-template.xlsx';
        link.click();
        window.URL.revokeObjectURL(url);
      }
    });
  }

  /**
   * Auto-map columns using the backend's suggested mappings,
   * or fall back to header-name matching.
   */
  autoMapColumns(): void {
    console.log('🔍 [AUTO-MAP] Button clicked');
    console.log('🔍 [AUTO-MAP] uploadPreview:', this.uploadPreview);
    console.log('🔍 [AUTO-MAP] suggestedMappings:', this.uploadPreview?.suggestedMappings);

    this.columnMappings = {};

    // Use backend suggestedMappings if available
    if (this.uploadPreview?.suggestedMappings?.length) {
      console.log('✅ [AUTO-MAP] Found', this.uploadPreview.suggestedMappings.length, 'suggested mappings');

      for (const mapping of this.uploadPreview.suggestedMappings) {
        const fieldKey = BOQ_FIELD_REVERSE[mapping.boqField];
        console.log(`   Mapping: "${mapping.excelColumn}" (BoqField=${mapping.boqField}) → fieldKey="${fieldKey}"`);

        if (fieldKey && mapping.excelColumn) {
          this.columnMappings[mapping.excelColumn] = fieldKey;
        }
      }

      console.log('✅ [AUTO-MAP] Final columnMappings:', this.columnMappings);
      console.log('✅ [AUTO-MAP] hasRequiredMappings:', this.hasRequiredMappings());
    } else {
      console.warn('⚠️ [AUTO-MAP] No suggested mappings available!');
      console.log('   uploadPreview:', this.uploadPreview);
    }
  }

  canProceed(): boolean {
    switch (this.activeStep) {
      case 0:
        return !!this.selectedFile() && !this.isUploading();
      case 1:
        return this.hasRequiredMappings();
      default:
        return false;
    }
  }

  private hasRequiredMappings(): boolean {
    const required = ['itemNumber', 'description', 'quantity', 'uom'];
    const mapped = Object.values(this.columnMappings).filter(v => v !== null);
    return required.every(field => mapped.includes(field));
  }

  canImport(): boolean {
    const result = this.validationResult();
    return !!result && (result.validCount > 0 || result.warningCount > 0);
  }

  nextStep(): void {
    if (this.activeStep === 0) {
      // Upload file to backend, then move to mapping step
      this.uploadFile();
    } else if (this.activeStep === 1) {
      // Validate mapping
      if (!this.hasRequiredMappings()) {
        this.mappingError.set('Please map all required fields: Item Number, Description, Quantity, and UOM');
        return;
      }
      this.mappingError.set(null);

      // Move to validation step and run validation
      this.activeStep++;
      this.validateData();
    }
  }

  previousStep(): void {
    this.activeStep--;
  }

  /**
   * Upload the file to the backend, parse the preview response,
   * populate excelColumns/previewRows/suggestedMappings, then advance.
   */
  private uploadFile(): void {
    const file = this.selectedFile();
    if (!file) return;

    this.isUploading.set(true);
    this.uploadError.set(null);

    this.boqService.uploadForPreview(this.tenderId, file).subscribe({
      next: (preview) => {
        this.isUploading.set(false);
        this.uploadPreview = preview;

        // Extract column headers from the backend preview
        const columns: any[] = preview.columns ?? [];
        this.excelColumns = columns.map((c: any) => c.header);

        // Extract preview rows — backend sends Dict<string, object?>[]
        this.previewRows = (preview.previewRows ?? []).map((row: any) => {
          const mapped: Record<string, any> = {};
          for (const col of this.excelColumns) {
            mapped[col] = row[col] ?? '';
          }
          return mapped;
        });

        // Auto-apply suggested mappings
        this.columnMappings = {};
        this.autoMapColumns();

        // Advance to mapping step
        this.activeStep = 1;
      },
      error: (error) => {
        this.isUploading.set(false);
        this.uploadError.set(error.message || 'Failed to upload and parse file');
      }
    });
  }

  /**
   * Build column mappings from the user's selections and send to the validate endpoint.
   */
  private validateData(): void {
    this.isValidating.set(true);
    this.validationResult.set(null);
    this.validationRows.set([]);
    this.rowLevelCache.clear();

    const sessionId = this.uploadPreview?.importSessionId;
    if (!sessionId) {
      this.isValidating.set(false);
      return;
    }

    // Build ColumnMappingDto[] from the user's selections
    const mappings: any[] = [];
    for (const [excelColumn, fieldKey] of Object.entries(this.columnMappings)) {
      if (fieldKey && BOQ_FIELD[fieldKey] !== undefined) {
        mappings.push({
          excelColumn,
          boqField: BOQ_FIELD[fieldKey],
          confidence: null,
          isAutoDetected: false
        });
      }
    }

    this.boqService.validateSession(this.tenderId, sessionId, mappings).subscribe({
      next: (validation) => {
        this.isValidating.set(false);
        this.validationResult.set(validation);

        // Build row-level display from the validation issues
        const issues: any[] = validation.issues ?? [];
        const totalRows = validation.totalRows ?? 0;
        const rows: BoqImportRow[] = [];

        // Group issues by row number
        const issuesByRow = new Map<number, any[]>();
        for (const issue of issues) {
          const rn = issue.rowNumber ?? 0;
          if (!issuesByRow.has(rn)) issuesByRow.set(rn, []);
          issuesByRow.get(rn)!.push(issue);
        }

        // Build rows using preview data for display
        const previewData = this.uploadPreview?.previewRows ?? [];
        for (let i = 0; i < totalRows; i++) {
          const rowNum = i + 1;
          const rowIssues = issuesByRow.get(rowNum) ?? [];
          const errors = rowIssues.filter((iss: any) => iss.severity === 2).map((iss: any) => iss.message);
          const warnings = rowIssues.filter((iss: any) => iss.severity === 1).map((iss: any) => iss.message);
          const status: 'valid' | 'warning' | 'error' = errors.length > 0 ? 'error' : warnings.length > 0 ? 'warning' : 'valid';

          rows.push({
            rowNumber: rowNum,
            data: previewData[i] ?? {},
            status,
            errors: errors.length > 0 ? errors : undefined,
            warnings: warnings.length > 0 ? warnings : undefined
          });
        }

        this.validationRows.set(rows);
      },
      error: (error) => {
        this.isValidating.set(false);
        this.validationResult.set({
          validCount: 0,
          warningCount: 0,
          errorCount: 0,
          totalRows: 0,
          issues: [],
          detectedSections: []
        });
        this.validationRows.set([]);
      }
    });
  }

  importItems(): void {
    const result = this.validationResult();
    if (!result) return;

    this.isImporting.set(true);

    const validRows = this.validationRows().filter(r => r.status === 'valid' || r.status === 'warning');

    this.boqService.importItems(this.tenderId, validRows, this.clearExisting).subscribe({
      next: (importResult) => {
        this.isImporting.set(false);
        this.imported.emit(importResult);
      },
      error: (error) => {
        this.isImporting.set(false);
      }
    });
  }

  getStatusSeverity(status: string): 'success' | 'warn' | 'danger' {
    switch (status) {
      case 'valid': return 'success';
      case 'warning': return 'warn';
      case 'error': return 'danger';
      default: return 'warn';
    }
  }

  /**
   * Infer the hierarchy level of a validation row based on mapped data.
   * Detection logic mirrors the backend's hierarchy detection:
   *   - Row with a bill pattern (BILL NO. X) or explicit billNumber mapping → Bill
   *   - Row with X.XX item number + no qty/uom → Item Group
   *   - Row with X.XX item number + has qty/uom → Item (standalone)
   *   - Row with letter/code sub-item label following a group → Sub-Item
   *   - Row with explicit subItemLabel mapping → Sub-Item
   */
  inferRowLevel(row: BoqImportRow): HierarchyLevel {
    // Check cache first
    const cached = this.rowLevelCache.get(row.rowNumber);
    if (cached) return cached;

    const level = this.detectRowLevel(row);
    this.rowLevelCache.set(row.rowNumber, level);
    return level;
  }

  private detectRowLevel(row: BoqImportRow): HierarchyLevel {
    const data = row.data;
    if (!data) return 'Item';

    const billCol = this.getMappedColumnForField('billNumber');
    const subItemCol = this.getMappedColumnForField('subItemLabel');
    const sectionCol = this.getMappedColumnForField('sectionTitle');
    const itemNumCol = this.getMappedColumnForField('itemNumber');
    const qtyCol = this.getMappedColumnForField('quantity');
    const uomCol = this.getMappedColumnForField('uom');
    const descCol = this.getMappedColumnForField('description');

    // 1. Explicit billNumber mapped and has value → Bill
    if (billCol && data[billCol]) {
      const billVal = String(data[billCol]).trim();
      if (billVal.length > 0) {
        return 'Bill';
      }
    }

    // 2. Check description or section title for bill pattern (BILL NO. X)
    const descVal = descCol ? String(data[descCol] ?? '').trim() : '';
    const sectionVal = sectionCol ? String(data[sectionCol] ?? '').trim() : '';
    if (BILL_PATTERN.test(descVal) || BILL_PATTERN.test(sectionVal)) {
      return 'Bill';
    }

    // 3. Section title present without item number data → Bill
    if (sectionCol && sectionVal && (!itemNumCol || !data[itemNumCol])) {
      return 'Bill';
    }

    // 4. Explicit subItemLabel mapped and has value → Sub-Item
    if (subItemCol && data[subItemCol]) {
      const subVal = String(data[subItemCol]).trim();
      if (subVal.length > 0) {
        return 'Sub-Item';
      }
    }

    // 5. Item number pattern analysis
    const itemNumVal = itemNumCol ? String(data[itemNumCol] ?? '').trim() : '';
    const hasQty = qtyCol && data[qtyCol] != null && data[qtyCol] !== '' && Number(data[qtyCol]) !== 0;
    const hasUom = uomCol && data[uomCol] != null && String(data[uomCol]).trim() !== '';

    if (itemNumVal && ITEM_NUMBER_PATTERN.test(itemNumVal)) {
      // Has item number pattern (X.XX)
      if (!hasQty && !hasUom) {
        // No qty/uom → this is an Item Group header
        return 'Item Group';
      }
      // Has qty/uom → standalone item
      return 'Item';
    }

    // 6. Check for sub-item label pattern (a., b., i., ii., etc.)
    if (itemNumVal && SUB_ITEM_LABEL_PATTERN.test(itemNumVal)) {
      return 'Sub-Item';
    }

    // 7. Check description for sub-item label pattern as fallback
    if (descVal && SUB_ITEM_LABEL_PATTERN.test(descVal) && !itemNumVal) {
      return 'Sub-Item';
    }

    // Default: treat as Item
    return 'Item';
  }

  inferRowLevelSeverity(row: BoqImportRow): 'info' | 'success' | 'secondary' | 'warn' {
    const level = this.inferRowLevel(row);
    switch (level) {
      case 'Bill': return 'info';
      case 'Item Group': return 'warn';
      case 'Item': return 'success';
      case 'Sub-Item': return 'secondary';
      default: return 'secondary';
    }
  }

  getRowIndent(row: BoqImportRow): string {
    const level = this.inferRowLevel(row);
    switch (level) {
      case 'Bill': return '0';
      case 'Item Group': return '1rem';
      case 'Item': return '1.5rem';
      case 'Sub-Item': return '2.5rem';
      default: return '0';
    }
  }

  /** Returns CSS classes for the row based on status and hierarchy level */
  getRowCssClasses(row: BoqImportRow): string {
    const classes: string[] = [];
    classes.push('status-' + row.status);

    const level = this.inferRowLevel(row);
    switch (level) {
      case 'Bill': classes.push('level-bill'); break;
      case 'Item Group': classes.push('level-item-group'); break;
      case 'Sub-Item': classes.push('level-sub-item'); break;
    }

    return classes.join(' ');
  }

  private getMappedColumnForField(field: string): string | null {
    for (const [col, mappedField] of Object.entries(this.columnMappings)) {
      if (mappedField === field) return col;
    }
    return null;
  }

  getRowPreview(row: BoqImportRow): string {
    if (!row.data) return '';
    return Object.values(row.data).filter(v => v != null && v !== '').join(' | ');
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  onVisibleChange(visible: boolean): void {
    this.visibleChange.emit(visible);
  }

  onCancel(): void {
    this.visibleChange.emit(false);
  }
}
