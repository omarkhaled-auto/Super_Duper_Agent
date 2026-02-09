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
import { StepsModule } from 'primeng/steps';
import { FileUploadModule, FileSelectEvent } from 'primeng/fileupload';
import { TableModule } from 'primeng/table';
import { DropdownModule } from 'primeng/dropdown';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { MessageModule } from 'primeng/message';
import { ProgressBarModule } from 'primeng/progressbar';
import { TooltipModule } from 'primeng/tooltip';
import { CheckboxModule } from 'primeng/checkbox';
import { MenuItem } from 'primeng/api';

import { BoqService } from '../../../../core/services/boq.service';
import { BoqImportRow } from '../../../../core/models/boq.model';

/** Backend BoqField enum values */
const BOQ_FIELD: Record<string, number> = {
  itemNumber: 1,
  description: 2,
  quantity: 3,
  uom: 4,
  sectionTitle: 5,
  notes: 6,
  unitRate: 7,
  totalAmount: 8
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
                    <th style="width: 80px">Row</th>
                    <th style="width: 100px">Status</th>
                    <th>Data Preview</th>
                    <th>Issues</th>
                  </tr>
                </ng-template>
                <ng-template pTemplate="body" let-row>
                  <tr [class]="'status-' + row.status">
                    <td>{{ row.rowNumber }}</td>
                    <td>
                      <p-tag
                        [value]="row.status | titlecase"
                        [severity]="getStatusSeverity(row.status)"
                      ></p-tag>
                    </td>
                    <td>
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
      color: var(--bayan-foreground, #09090b);
    }

    .upload-instructions p {
      margin: 0;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .template-link {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      margin-top: 1rem;
      color: var(--bayan-primary, #18181b);
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
        border: 2px dashed var(--bayan-border, #e4e4e7);
        border-radius: var(--bayan-radius, 0.5rem);
        transition: all 0.2s;
      }

      .p-fileupload-content:hover {
        border-color: var(--bayan-primary, #18181b);
        background-color: var(--bayan-muted, #f4f4f5);
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
      color: var(--bayan-primary, #18181b);
    }

    .upload-text {
      margin: 0;
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
    }

    .upload-hint {
      margin: 0;
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .file-icon {
      font-size: 3rem;
      color: var(--bayan-success, #22c55e);
    }

    .file-name {
      margin: 0;
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
    }

    .file-size {
      margin: 0;
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
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
      color: var(--bayan-foreground, #09090b);
    }

    .mapping-header p {
      flex: 1 1 100%;
      margin: 0;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .column-header {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .excel-col {
      font-weight: 600;
      color: var(--bayan-primary, #18181b);
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
      color: var(--bayan-foreground, #09090b);
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
      color: #16a34a;
    }

    .summary-badge.warning {
      background-color: var(--bayan-warning-bg, #fffbeb);
      color: #d97706;
    }

    .summary-badge.error {
      background-color: var(--bayan-danger-bg, #fef2f2);
      color: #dc2626;
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
      color: var(--bayan-muted-foreground, #71717a);
    }

    .detected-sections {
      padding: 1rem;
      background-color: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .detected-sections h5 {
      margin: 0 0 0.5rem;
      color: var(--bayan-foreground, #09090b);
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
    }

    .data-preview {
      font-family: monospace;
      font-size: 0.8rem;
    }

    .error-text {
      color: #dc2626;
      font-size: 0.8rem;
    }

    .warning-text {
      color: #d97706;
      font-size: 0.8rem;
    }

    .import-options {
      padding: 0.75rem 1rem;
      background-color: var(--bayan-accent, #f4f4f5);
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
      color: var(--bayan-foreground, #09090b);
      font-size: 0.875rem;
    }

    .dialog-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 1rem;
      border-top: 1px solid var(--bayan-border, #e4e4e7);
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
    { label: 'Notes', value: 'notes' },
    { label: 'Unit Rate', value: 'unitRate' },
    { label: 'Total Amount', value: 'totalAmount' },
    { label: 'Section Title', value: 'sectionTitle' }
  ];

  // Step 3: Validation
  isValidating = signal<boolean>(false);
  validationResult = signal<any | null>(null);
  validationRows = signal<BoqImportRow[]>([]);
  isImporting = signal<boolean>(false);
  clearExisting = true;

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
    this.columnMappings = {};

    // Use backend suggestedMappings if available
    if (this.uploadPreview?.suggestedMappings?.length) {
      for (const mapping of this.uploadPreview.suggestedMappings) {
        const fieldKey = BOQ_FIELD_REVERSE[mapping.boqField];
        if (fieldKey && mapping.excelColumn) {
          this.columnMappings[mapping.excelColumn] = fieldKey;
        }
      }
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
