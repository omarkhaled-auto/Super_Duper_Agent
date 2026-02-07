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
import { MenuItem } from 'primeng/api';

import { BoqService } from '../../../../core/services/boq.service';
import { BoqImportMapping, BoqImportResult, BoqImportRow } from '../../../../core/models/boq.model';

interface ColumnMapping {
  excelColumn: string;
  boqField: string | null;
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
    TooltipModule
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
              @if (importResult()) {
                <div class="validation-summary">
                  <div class="summary-badge valid">
                    <i class="pi pi-check-circle"></i>
                    <span>{{ importResult()!.validRows }} Valid</span>
                  </div>
                  <div class="summary-badge warning">
                    <i class="pi pi-exclamation-triangle"></i>
                    <span>{{ importResult()!.warningRows }} Warnings</span>
                  </div>
                  <div class="summary-badge error">
                    <i class="pi pi-times-circle"></i>
                    <span>{{ importResult()!.errorRows }} Errors</span>
                  </div>
                </div>
              }
            </div>

            @if (isValidating()) {
              <div class="validating-state">
                <p-progressBar mode="indeterminate" [style]="{ height: '6px' }"></p-progressBar>
                <p>Validating data...</p>
              </div>
            } @else if (importResult()) {
              <!-- Detected Sections -->
              @if (importResult()!.detectedSections.length > 0) {
                <div class="detected-sections">
                  <h5>Detected Sections</h5>
                  <div class="section-tags">
                    @for (section of importResult()!.detectedSections; track section) {
                      <p-tag [value]="section" severity="info"></p-tag>
                    }
                  </div>
                </div>
              }

              <!-- Validation Table -->
              <p-table
                [value]="importResult()!.rows"
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
                        {{ getRowPreview(row) | slice:0:50 }}...
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
      color: #333;
    }

    .upload-instructions p {
      margin: 0;
      color: #666;
    }

    .template-link {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      margin-top: 1rem;
      color: #1976D2;
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
        border: 2px dashed #ddd;
        border-radius: 8px;
        transition: all 0.2s;
      }

      .p-fileupload-content:hover {
        border-color: #1976D2;
        background-color: #f0f7ff;
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
      color: #1976D2;
    }

    .upload-text {
      margin: 0;
      font-weight: 500;
      color: #333;
    }

    .upload-hint {
      margin: 0;
      font-size: 0.875rem;
      color: #666;
    }

    .file-icon {
      font-size: 3rem;
      color: #4caf50;
    }

    .file-name {
      margin: 0;
      font-weight: 500;
      color: #333;
    }

    .file-size {
      margin: 0;
      font-size: 0.875rem;
      color: #666;
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
      color: #333;
    }

    .mapping-header p {
      flex: 1 1 100%;
      margin: 0;
      color: #666;
    }

    .column-header {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .excel-col {
      font-weight: 600;
      color: #1976D2;
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
      color: #333;
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
      background-color: #e8f5e9;
      color: #2e7d32;
    }

    .summary-badge.warning {
      background-color: #fff3e0;
      color: #ef6c00;
    }

    .summary-badge.error {
      background-color: #ffebee;
      color: #c62828;
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
      color: #666;
    }

    .detected-sections {
      padding: 1rem;
      background-color: #f8f9fa;
      border-radius: 8px;
    }

    .detected-sections h5 {
      margin: 0 0 0.5rem;
      color: #333;
    }

    .section-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    :host ::ng-deep .validation-table {
      .status-error {
        background-color: #ffebee !important;
      }

      .status-warning {
        background-color: #fff3e0 !important;
      }
    }

    .data-preview {
      font-family: monospace;
      font-size: 0.8rem;
    }

    .error-text {
      color: #c62828;
      font-size: 0.8rem;
    }

    .warning-text {
      color: #ef6c00;
      font-size: 0.8rem;
    }

    .dialog-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 1rem;
      border-top: 1px solid #e0e0e0;
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

  // Step 2: Mapping
  excelColumns: string[] = ['A', 'B', 'C', 'D', 'E', 'F'];
  previewRows: Record<string, any>[] = [];
  columnMappings: Record<string, string | null> = {};
  mappingError = signal<string | null>(null);

  boqFieldOptions = [
    { label: 'Item Number', value: 'itemNumber' },
    { label: 'Description', value: 'description' },
    { label: 'Quantity', value: 'quantity' },
    { label: 'UOM', value: 'uom' },
    { label: 'Type', value: 'type' },
    { label: 'Notes', value: 'notes' },
    { label: 'Section Number', value: 'sectionNumber' },
    { label: 'Section Title', value: 'sectionTitle' }
  ];

  // Step 3: Validation
  isValidating = signal<boolean>(false);
  importResult = signal<BoqImportResult | null>(null);
  isImporting = signal<boolean>(false);

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && this.visible) {
      this.reset();
    }
  }

  private reset(): void {
    this.activeStep = 0;
    this.selectedFile.set(null);
    this.uploadError.set(null);
    this.columnMappings = {};
    this.mappingError.set(null);
    this.importResult.set(null);
    this.isValidating.set(false);
    this.isImporting.set(false);

    // Mock preview data
    this.previewRows = [
      { A: '1.1.1', B: 'Sample item description', C: '10', D: 'EA', E: 'Base', F: '' },
      { A: '1.1.2', B: 'Another item', C: '5', D: 'LS', E: 'Alternate', F: 'Notes here' },
      { A: '1.1.3', B: 'Third item', C: '100', D: 'M2', E: 'Base', F: '' }
    ];
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

  autoMapColumns(): void {
    // Auto-map based on common patterns
    const autoMappings: Record<string, string> = {
      'A': 'itemNumber',
      'B': 'description',
      'C': 'quantity',
      'D': 'uom',
      'E': 'type',
      'F': 'notes'
    };

    this.columnMappings = { ...autoMappings };
  }

  canProceed(): boolean {
    switch (this.activeStep) {
      case 0:
        return !!this.selectedFile();
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
    const result = this.importResult();
    return !!result && result.validRows > 0;
  }

  nextStep(): void {
    if (this.activeStep === 1) {
      // Validate mapping
      if (!this.hasRequiredMappings()) {
        this.mappingError.set('Please map all required fields: Item Number, Description, Quantity, and UOM');
        return;
      }
      this.mappingError.set(null);

      // Start validation
      this.activeStep++;
      this.validateData();
    } else {
      this.activeStep++;
    }
  }

  previousStep(): void {
    this.activeStep--;
  }

  private validateData(): void {
    this.isValidating.set(true);
    this.importResult.set(null);

    const mapping: BoqImportMapping = {};
    Object.entries(this.columnMappings).forEach(([col, field]) => {
      if (field) {
        (mapping as any)[field] = col;
      }
    });

    this.boqService.validateImport(this.tenderId, this.selectedFile()!, mapping).subscribe({
      next: (result) => {
        this.isValidating.set(false);
        this.importResult.set(result);
      },
      error: (error) => {
        this.isValidating.set(false);
        this.importResult.set({
          totalRows: 0,
          validRows: 0,
          warningRows: 0,
          errorRows: 0,
          rows: [],
          detectedSections: []
        });
      }
    });
  }

  importItems(): void {
    const result = this.importResult();
    if (!result) return;

    this.isImporting.set(true);

    const validRows = result.rows.filter(r => r.status === 'valid' || r.status === 'warning');

    this.boqService.importItems(this.tenderId, validRows).subscribe({
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
    return Object.values(row.data).filter(v => v).join(' | ');
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
