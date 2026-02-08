import {
  Component,
  Input,
  OnInit,
  OnDestroy,
  inject,
  signal
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { DialogModule } from 'primeng/dialog';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';
import { DropdownModule } from 'primeng/dropdown';
import { FileUploadModule } from 'primeng/fileupload';
import { InputTextModule } from 'primeng/inputtext';
import { MessageService, ConfirmationService } from 'primeng/api';

import {
  DocumentService,
  TenderDocument,
  DocumentQueryParams
} from '../../../../core/services/document.service';

interface CategoryOption {
  label: string;
  value: string;
}

const DOCUMENT_CATEGORIES: CategoryOption[] = [
  { label: 'Technical Specifications', value: 'Technical Specifications' },
  { label: 'Drawings', value: 'Drawings' },
  { label: 'Terms & Conditions', value: 'Terms & Conditions' },
  { label: 'Contract Documents', value: 'Contract Documents' },
  { label: 'General', value: 'General' }
];

@Component({
  selector: 'app-documents-tab',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    TagModule,
    TooltipModule,
    DialogModule,
    ToastModule,
    ConfirmDialogModule,
    ProgressSpinnerModule,
    MessageModule,
    DropdownModule,
    FileUploadModule,
    InputTextModule
  ],
  providers: [MessageService, ConfirmationService],
  template: `
    <p-toast></p-toast>
    <p-confirmDialog></p-confirmDialog>

    <div class="documents-tab-container" data-testid="documents-tab">
      <!-- Toolbar -->
      <div class="documents-toolbar">
        <div class="toolbar-left">
          <span class="p-input-icon-left">
            <i class="pi pi-search"></i>
            <input
              type="text"
              pInputText
              placeholder="Search documents..."
              [(ngModel)]="searchTerm"
              (input)="onSearch()"
              data-testid="document-search-input"
            />
          </span>
          <p-dropdown
            [options]="filterCategories"
            [(ngModel)]="selectedFilterCategory"
            placeholder="All Categories"
            [showClear]="true"
            (onChange)="onFilterCategory()"
            data-testid="category-filter"
          ></p-dropdown>
        </div>
        <div class="toolbar-right">
          <button
            pButton
            icon="pi pi-upload"
            label="Upload Document"
            data-testid="upload-document-btn"
            (click)="showUploadDialog = true"
          ></button>
        </div>
      </div>

      <!-- Error Message -->
      @if (documentService.error()) {
        <p-message
          severity="error"
          [text]="documentService.error()!"
          styleClass="w-full"
        ></p-message>
      }

      <!-- Loading State -->
      @if (documentService.isLoading() && documents().length === 0) {
        <div class="loading-container">
          <p-progressSpinner
            [style]="{ width: '50px', height: '50px' }"
            strokeWidth="4"
          ></p-progressSpinner>
          <p>Loading documents...</p>
        </div>
      } @else if (documents().length === 0) {
        <!-- Empty State -->
        <div class="empty-state">
          <i class="pi pi-file" style="font-size: 3rem; color: var(--bayan-border, #e4e4e7);"></i>
          <h3>No Documents</h3>
          <p>No documents have been uploaded for this tender yet.</p>
          <button
            pButton
            icon="pi pi-upload"
            label="Upload First Document"
            class="p-button-outlined"
            (click)="showUploadDialog = true"
          ></button>
        </div>
      } @else {
        <!-- Documents Table -->
        <p-table
          data-testid="documents-table"
          [value]="documents()"
          [loading]="documentService.isLoading()"
          [paginator]="true"
          [rows]="10"
          [showCurrentPageReport]="true"
          currentPageReportTemplate="Showing {first} to {last} of {totalRecords} documents"
          [rowsPerPageOptions]="[10, 25, 50]"
          styleClass="p-datatable-sm p-datatable-striped"
        >
          <ng-template pTemplate="header">
            <tr>
              <th pSortableColumn="fileName" style="width: 30%">
                Name
                <p-sortIcon field="fileName"></p-sortIcon>
              </th>
              <th pSortableColumn="folderPath" style="width: 20%">
                Category / Folder
                <p-sortIcon field="folderPath"></p-sortIcon>
              </th>
              <th pSortableColumn="fileSize" style="width: 12%">
                Size
                <p-sortIcon field="fileSize"></p-sortIcon>
              </th>
              <th pSortableColumn="uploadedAt" style="width: 18%">
                Uploaded Date
                <p-sortIcon field="uploadedAt"></p-sortIcon>
              </th>
              <th style="width: 20%">Actions</th>
            </tr>
          </ng-template>

          <ng-template pTemplate="body" let-doc>
            <tr>
              <td>
                <div class="doc-name-cell">
                  <i [class]="getFileIcon(doc.fileName)" class="doc-icon"></i>
                  <div class="doc-name-info">
                    <span
                      class="doc-name"
                      [pTooltip]="doc.fileName"
                      tooltipPosition="top"
                    >{{ doc.fileName }}</span>
                    @if (doc.version > 1) {
                      <span class="doc-version">v{{ doc.version }}</span>
                    }
                  </div>
                </div>
              </td>
              <td>
                <p-tag
                  [value]="doc.folderPath || 'General'"
                  [severity]="getCategorySeverity(doc.folderPath)"
                ></p-tag>
              </td>
              <td>{{ formatFileSize(doc.fileSize) }}</td>
              <td>{{ doc.uploadedAt | date:'medium' }}</td>
              <td>
                <div class="action-buttons">
                  <button
                    pButton
                    icon="pi pi-download"
                    class="p-button-text p-button-sm"
                    pTooltip="Download"
                    data-testid="download-doc-btn"
                    (click)="downloadDocument(doc)"
                  ></button>
                  <button
                    pButton
                    icon="pi pi-trash"
                    class="p-button-text p-button-sm p-button-danger"
                    pTooltip="Delete"
                    data-testid="delete-doc-btn"
                    (click)="confirmDelete(doc)"
                  ></button>
                </div>
              </td>
            </tr>
          </ng-template>

          <ng-template pTemplate="emptymessage">
            <tr>
              <td colspan="5" class="text-center p-4">
                No documents found.
              </td>
            </tr>
          </ng-template>
        </p-table>

        <!-- Summary Footer -->
        <div class="documents-summary">
          <div class="summary-item">
            <span class="summary-label">Total Documents:</span>
            <span class="summary-value">{{ totalRecords() }}</span>
          </div>
          <div class="summary-divider"></div>
          <div class="summary-item">
            <span class="summary-label">Total Size:</span>
            <span class="summary-value">{{ formatFileSize(totalSize()) }}</span>
          </div>
        </div>
      }
    </div>

    <!-- Upload Dialog -->
    <p-dialog
      header="Upload Document"
      [(visible)]="showUploadDialog"
      [modal]="true"
      [style]="{ width: '500px' }"
      [contentStyle]="{ overflow: 'visible' }"
      data-testid="upload-dialog"
    >
      <div class="upload-form">
        <div class="form-field">
          <label for="category">Category</label>
          <p-dropdown
            id="category"
            [options]="categories"
            [(ngModel)]="uploadCategory"
            placeholder="Select a category"
            [style]="{ width: '100%' }"
            data-testid="upload-category-dropdown"
          ></p-dropdown>
        </div>

        <div class="form-field">
          <label>File</label>
          <p-fileUpload
            mode="advanced"
            [auto]="false"
            [customUpload]="true"
            (uploadHandler)="onFileSelect($event)"
            [maxFileSize]="104857600"
            chooseLabel="Choose File"
            uploadLabel="Upload"
            cancelLabel="Cancel"
            [showUploadButton]="false"
            [showCancelButton]="false"
            data-testid="file-upload"
            (onSelect)="onFileSelected($event)"
          >
            <ng-template pTemplate="content">
              @if (!selectedFile) {
                <div class="upload-placeholder">
                  <i class="pi pi-cloud-upload" style="font-size: 2rem; color: var(--bayan-muted-foreground, #71717a);"></i>
                  <p>Drag and drop a file here or click to browse</p>
                  <span class="upload-hint">Maximum file size: 100MB</span>
                </div>
              }
            </ng-template>
          </p-fileUpload>
        </div>
      </div>

      <ng-template pTemplate="footer">
        <button
          pButton
          label="Cancel"
          icon="pi pi-times"
          class="p-button-text"
          (click)="cancelUpload()"
        ></button>
        <button
          pButton
          label="Upload"
          icon="pi pi-upload"
          [loading]="isUploading()"
          [disabled]="!selectedFile || !uploadCategory"
          data-testid="confirm-upload-btn"
          (click)="uploadDocument()"
        ></button>
      </ng-template>
    </p-dialog>
  `,
  styles: [`
    .documents-tab-container {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .documents-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
      padding: 1rem;
      background-color: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .toolbar-left,
    .toolbar-right {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      align-items: center;
    }

    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem;
      gap: 1rem;
    }

    .loading-container p {
      color: var(--bayan-muted-foreground, #71717a);
    }

    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem;
      text-align: center;
      gap: 1rem;
    }

    .empty-state h3 {
      margin: 0;
      color: var(--bayan-foreground, #09090b);
    }

    .empty-state p {
      margin: 0;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .doc-name-cell {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .doc-icon {
      font-size: 1.25rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .doc-name-info {
      display: flex;
      flex-direction: column;
    }

    .doc-name {
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 250px;
    }

    .doc-version {
      font-size: 0.75rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .action-buttons {
      display: flex;
      gap: 0.25rem;
    }

    .documents-summary {
      display: flex;
      align-items: center;
      gap: 1.5rem;
      padding: 1rem;
      background-color: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius, 0.5rem);
      flex-wrap: wrap;
    }

    .summary-item {
      display: flex;
      gap: 0.5rem;
      align-items: center;
    }

    .summary-label {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .summary-value {
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
    }

    .summary-divider {
      width: 1px;
      height: 20px;
      background-color: var(--bayan-border, #e4e4e7);
    }

    /* Upload Dialog */
    .upload-form {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .form-field {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .form-field label {
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
    }

    .upload-placeholder {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.5rem;
      padding: 2rem;
      text-align: center;
    }

    .upload-placeholder p {
      margin: 0;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .upload-hint {
      font-size: 0.8rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .text-center {
      text-align: center;
    }

    @media (max-width: 768px) {
      .documents-toolbar {
        flex-direction: column;
        align-items: stretch;
      }

      .toolbar-left,
      .toolbar-right {
        justify-content: center;
      }

      .documents-summary {
        flex-direction: column;
        align-items: flex-start;
      }

      .summary-divider {
        display: none;
      }
    }
  `]
})
export class DocumentsTabComponent implements OnInit, OnDestroy {
  @Input() tenderId!: number;

  readonly documentService = inject(DocumentService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly destroy$ = new Subject<void>();

  // Data signals
  documents = signal<TenderDocument[]>([]);
  totalRecords = signal<number>(0);
  totalSize = signal<number>(0);

  // Filter state
  searchTerm = '';
  selectedFilterCategory: string | null = null;

  // Upload dialog state
  showUploadDialog = false;
  uploadCategory: string | null = null;
  selectedFile: File | null = null;
  isUploading = signal<boolean>(false);

  // Category options
  categories: CategoryOption[] = DOCUMENT_CATEGORIES;
  filterCategories: CategoryOption[] = DOCUMENT_CATEGORIES;

  ngOnInit(): void {
    this.loadDocuments();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadDocuments(): void {
    const params: DocumentQueryParams = {
      page: 1,
      pageSize: 50,
      latestOnly: true
    };

    if (this.searchTerm) {
      params.search = this.searchTerm;
    }

    if (this.selectedFilterCategory) {
      params.folder = this.selectedFilterCategory;
    }

    this.documentService.getDocuments(this.tenderId, params).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (result) => {
        this.documents.set(result.items);
        this.totalRecords.set(result.pagination?.totalItems ?? result.items.length);
        const size = result.items.reduce((sum, doc) => sum + (doc.fileSize || 0), 0);
        this.totalSize.set(size);
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to load documents'
        });
      }
    });
  }

  onSearch(): void {
    this.loadDocuments();
  }

  onFilterCategory(): void {
    this.loadDocuments();
  }

  onFileSelect(event: any): void {
    // Custom upload handler - not used since we handle upload ourselves
  }

  onFileSelected(event: any): void {
    if (event.files && event.files.length > 0) {
      this.selectedFile = event.files[0];
    }
  }

  uploadDocument(): void {
    if (!this.selectedFile || !this.uploadCategory) return;

    this.isUploading.set(true);

    this.documentService.uploadDocument(
      this.tenderId,
      this.selectedFile,
      this.uploadCategory
    ).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: () => {
        this.isUploading.set(false);
        this.showUploadDialog = false;
        this.selectedFile = null;
        this.uploadCategory = null;

        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Document uploaded successfully'
        });
        this.loadDocuments();
      },
      error: (error) => {
        this.isUploading.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to upload document'
        });
      }
    });
  }

  cancelUpload(): void {
    this.showUploadDialog = false;
    this.selectedFile = null;
    this.uploadCategory = null;
  }

  downloadDocument(doc: TenderDocument): void {
    this.documentService.downloadDocument(this.tenderId, doc.id).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (result) => {
        // Open the presigned URL in a new tab to trigger download
        window.open(result.url, '_blank');
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to download document'
        });
      }
    });
  }

  confirmDelete(doc: TenderDocument): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete "${doc.fileName}"?`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => this.deleteDocument(doc)
    });
  }

  private deleteDocument(doc: TenderDocument): void {
    this.documentService.deleteDocument(this.tenderId, doc.id).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Document deleted successfully'
        });
        this.loadDocuments();
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to delete document'
        });
      }
    });
  }

  getFileIcon(fileName: string): string {
    if (!fileName) return 'pi pi-file';
    const ext = fileName.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf':
        return 'pi pi-file-pdf';
      case 'doc':
      case 'docx':
        return 'pi pi-file-word';
      case 'xls':
      case 'xlsx':
        return 'pi pi-file-excel';
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
      case 'svg':
        return 'pi pi-image';
      case 'zip':
      case 'rar':
      case '7z':
        return 'pi pi-box';
      case 'dwg':
      case 'dxf':
        return 'pi pi-compass';
      default:
        return 'pi pi-file';
    }
  }

  getCategorySeverity(folderPath: string): 'success' | 'secondary' | 'info' | 'warn' | 'danger' {
    switch (folderPath) {
      case 'Technical Specifications':
        return 'info';
      case 'Drawings':
        return 'warn';
      case 'Terms & Conditions':
        return 'danger';
      case 'Contract Documents':
        return 'success';
      case 'General':
      default:
        return 'secondary';
    }
  }

  formatFileSize(bytes: number): string {
    if (!bytes || bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return parseFloat((bytes / Math.pow(1024, i)).toFixed(1)) + ' ' + units[i];
  }
}
