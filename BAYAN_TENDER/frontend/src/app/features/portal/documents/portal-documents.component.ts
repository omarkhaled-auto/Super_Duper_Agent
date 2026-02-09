import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { AccordionModule } from 'primeng/accordion';
import { TagModule } from 'primeng/tag';
import { TableModule } from 'primeng/table';
import { TooltipModule } from 'primeng/tooltip';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';
import { DividerModule } from 'primeng/divider';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ConfirmationService, MessageService } from 'primeng/api';
import { ToastModule } from 'primeng/toast';
import { forkJoin } from 'rxjs';
import { PortalService } from '../../../core/services/portal.service';
import {
  DocumentFolder,
  TenderAddendum,
  TenderDocument,
  DOCUMENT_CATEGORY_CONFIG
} from '../../../core/models/portal.model';

@Component({
  selector: 'app-portal-documents',
  standalone: true,
  imports: [
    CommonModule,
    CardModule,
    ButtonModule,
    AccordionModule,
    TagModule,
    TableModule,
    TooltipModule,
    ProgressSpinnerModule,
    MessageModule,
    DividerModule,
    ConfirmDialogModule,
    ToastModule
  ],
  providers: [ConfirmationService, MessageService],
  template: `
    <div class="portal-documents">
      <!-- Loading State -->
      @if (isLoading()) {
        <div class="loading-container">
          <p-progressSpinner></p-progressSpinner>
          <p>Loading documents...</p>
        </div>
      }

      <!-- Error State -->
      @if (error()) {
        <p-message severity="error" [text]="error()!" styleClass="w-full mb-4"></p-message>
      }

      <!-- Documents Content -->
      @if (!isLoading() && !error()) {
        <!-- Addenda Section (High Priority) -->
        @if (addenda().length > 0) {
          <p-card styleClass="addenda-card mb-4">
            <ng-template pTemplate="header">
              <div class="card-header addenda-header">
                <div class="header-left">
                  <i class="pi pi-exclamation-circle"></i>
                  <h3>Important: Addenda</h3>
                </div>
                <p-tag
                  [value]="addenda().length + ' Addend' + (addenda().length > 1 ? 'a' : 'um')"
                  severity="warn"
                ></p-tag>
              </div>
            </ng-template>

            <p class="addenda-info">
              <i class="pi pi-info-circle"></i>
              Please review and acknowledge all addenda before submitting your bid.
            </p>

            <div class="addenda-list">
              @for (addendum of addenda(); track addendum.id) {
                <div class="addendum-item" [class.acknowledged]="addendum.acknowledged">
                  <div class="addendum-header">
                    <div class="addendum-title">
                      <strong>Addendum #{{ addendum.addendumNumber }}</strong>
                      <span class="addendum-date">
                        Issued: {{ addendum.issueDate | date:'mediumDate' }}
                      </span>
                    </div>
                    <div class="addendum-status">
                      @if (addendum.acknowledged) {
                        <p-tag severity="success" value="Acknowledged" icon="pi pi-check"></p-tag>
                      } @else {
                        <p-tag severity="warn" value="Pending Acknowledgment"></p-tag>
                      }
                    </div>
                  </div>

                  <p class="addendum-description" *ngIf="addendum.title">{{ addendum.title }}</p>

                  <div class="addendum-documents" *ngIf="addendum.documents?.length">
                    <span class="documents-label">Attached Documents:</span>
                    <div class="document-chips">
                      @for (doc of addendum.documents; track doc.id) {
                        <button
                          pButton
                          [label]="doc.fileName"
                          icon="pi pi-download"
                          class="p-button-sm p-button-outlined"
                          (click)="downloadDocument(doc)"
                        ></button>
                      }
                    </div>
                  </div>

                  @if (!addendum.acknowledged) {
                    <div class="addendum-actions">
                      <button
                        pButton
                        label="I Acknowledge This Addendum"
                        icon="pi pi-check"
                        class="p-button-success"
                        [loading]="acknowledgingId() === addendum.id"
                        (click)="acknowledgeAddendum(addendum)"
                      ></button>
                    </div>
                  } @else {
                    <div class="acknowledged-info">
                      <i class="pi pi-check-circle"></i>
                      Acknowledged on {{ addendum.acknowledgedAt | date:'medium' }}
                    </div>
                  }
                </div>
              }
            </div>
          </p-card>
        }

        <!-- Document Folders -->
        <p-card styleClass="documents-card">
          <ng-template pTemplate="header">
            <div class="card-header">
              <h3><i class="pi pi-folder"></i> Tender Documents</h3>
              <span class="total-size">
                Total: {{ getTotalDocumentCount() }} files ({{ getTotalSize() }})
              </span>
            </div>
          </ng-template>

          @if (folders().length === 0) {
            <div class="empty-state">
              <i class="pi pi-inbox"></i>
              <p>No documents available yet.</p>
            </div>
          } @else {
            <p-accordion [multiple]="true" [activeIndex]="[0]">
              @for (folder of folders(); track folder.category; let i = $index) {
                <p-accordionTab>
                  <ng-template pTemplate="header">
                    <div class="folder-header">
                      <i class="pi {{ folder.icon }}"></i>
                      <span class="folder-name">{{ folder.displayName }}</span>
                      <p-tag
                        [value]="folder.documents.length + ' file' + (folder.documents.length > 1 ? 's' : '')"
                        [severity]="'info'"
                      ></p-tag>
                    </div>
                  </ng-template>

                  <p-table
                    [value]="folder.documents"
                    [tableStyle]="{ 'min-width': '50rem' }"
                    styleClass="p-datatable-sm"
                  >
                    <ng-template pTemplate="header">
                      <tr>
                        <th style="width: 50%">File Name</th>
                        <th style="width: 15%">Size</th>
                        <th style="width: 20%">Uploaded</th>
                        <th style="width: 15%">Actions</th>
                      </tr>
                    </ng-template>
                    <ng-template pTemplate="body" let-doc>
                      <tr>
                        <td>
                          <div class="file-info">
                            <i class="pi {{ getFileIcon(doc.contentType) }}"></i>
                            <span class="file-name" [pTooltip]="doc.fileName" tooltipPosition="top">
                              {{ doc.fileName }}
                            </span>
                            @if (doc.version > 1) {
                              <p-tag
                                [value]="'v' + doc.version"
                                severity="secondary"
                                [rounded]="true"
                              ></p-tag>
                            }
                          </div>
                        </td>
                        <td>{{ doc.fileSizeDisplay }}</td>
                        <td>{{ doc.createdAt | date:'mediumDate' }}</td>
                        <td>
                          <button
                            pButton
                            icon="pi pi-download"
                            pTooltip="Download"
                            tooltipPosition="top"
                            class="p-button-sm p-button-text"
                            [loading]="downloadingId() === doc.id"
                            (click)="downloadDocument(doc)"
                          ></button>
                          <button
                            pButton
                            icon="pi pi-eye"
                            pTooltip="Preview"
                            tooltipPosition="top"
                            class="p-button-sm p-button-text"
                            (click)="previewDocument(doc)"
                            *ngIf="canPreview(doc.contentType)"
                          ></button>
                        </td>
                      </tr>
                    </ng-template>
                  </p-table>
                </p-accordionTab>
              }
            </p-accordion>
          }
        </p-card>
      }
    </div>

    <p-confirmDialog></p-confirmDialog>
    <p-toast></p-toast>
  `,
  styles: [`
    .portal-documents {
      animation: fadeIn 0.3s ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 4rem 2rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .loading-container p {
      margin-top: 1rem;
    }

    /* Card Headers */
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 1.5rem;
      background: var(--bayan-accent, #f4f4f5);
      border-bottom: 1px solid var(--bayan-border, #e4e4e7);
    }

    .card-header h3 {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin: 0;
      font-size: 1.125rem;
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
    }

    .card-header h3 i {
      color: var(--bayan-primary, #18181b);
    }

    .total-size {
      color: var(--bayan-muted-foreground, #71717a);
      font-size: 0.875rem;
    }

    /* Addenda Styles */
    .addenda-header {
      background: #fffbeb !important;
      border-bottom-color: #fcd34d !important;
    }

    .addenda-header .header-left {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .addenda-header i {
      color: #d97706;
      font-size: 1.25rem;
    }

    .addenda-header h3 {
      color: #92400e;
    }

    .addenda-info {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.75rem 1rem;
      background: #fffbeb;
      border-radius: var(--bayan-radius-sm, 0.375rem);
      margin-bottom: 1.5rem;
      color: #92400e;
      font-size: 0.875rem;
    }

    .addenda-list {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .addendum-item {
      border: 1px solid var(--bayan-border, #e4e4e7);
      border-radius: var(--bayan-radius-sm, 0.375rem);
      padding: 1.25rem;
      background: var(--bayan-card, #ffffff);
      transition: all 0.2s ease;
    }

    .addendum-item.acknowledged {
      border-color: #86efac;
      background: #f0fdf4;
    }

    .addendum-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 0.75rem;
    }

    .addendum-title {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .addendum-title strong {
      font-size: 1rem;
      color: var(--bayan-foreground, #09090b);
    }

    .addendum-date {
      font-size: 0.8rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .addendum-description {
      color: var(--bayan-muted-foreground, #71717a);
      margin: 0.75rem 0;
      font-size: 0.9375rem;
    }

    .addendum-documents {
      margin: 1rem 0;
    }

    .documents-label {
      display: block;
      font-size: 0.8rem;
      color: var(--bayan-muted-foreground, #71717a);
      margin-bottom: 0.5rem;
    }

    .document-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .addendum-actions {
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid var(--bayan-border, #e4e4e7);
    }

    .acknowledged-info {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-top: 0.75rem;
      color: #16a34a;
      font-size: 0.8rem;
    }

    /* Documents Table */
    .folder-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      width: 100%;
    }

    .folder-header i {
      font-size: 1.25rem;
      color: var(--bayan-primary, #18181b);
    }

    .folder-name {
      flex: 1;
      font-weight: 500;
    }

    .file-info {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .file-info i {
      font-size: 1.25rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .file-name {
      max-width: 300px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* Empty State */
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 4rem 2rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .empty-state i {
      font-size: 3rem;
      margin-bottom: 1rem;
    }

    .empty-state p {
      margin: 0;
      font-size: 1rem;
    }

    :host ::ng-deep {
      .addenda-card .p-card-body {
        padding: 1.5rem;
      }

      .documents-card .p-card-body {
        padding: 0;
      }

      .p-accordion .p-accordion-header .p-accordion-header-link {
        padding: 1rem 1.25rem;
      }

      .p-accordion .p-accordion-content {
        padding: 0;
      }

      .p-datatable .p-datatable-tbody > tr > td {
        padding: 0.75rem 1rem;
      }
    }

    /* Responsive */
    @media (max-width: 768px) {
      .addendum-header {
        flex-direction: column;
        gap: 0.5rem;
      }

      .file-name {
        max-width: 150px;
      }
    }
  `]
})
export class PortalDocumentsComponent implements OnInit {
  private readonly portalService = inject(PortalService);
  private readonly route = inject(ActivatedRoute);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly messageService = inject(MessageService);

  folders = signal<DocumentFolder[]>([]);
  addenda = signal<TenderAddendum[]>([]);
  isLoading = signal(true);
  error = signal<string | null>(null);
  downloadingId = signal<string | number | null>(null);
  acknowledgingId = signal<number | null>(null);

  private tenderId!: string | number;

  ngOnInit(): void {
    this.tenderId = this.route.parent?.snapshot.params['tenderId'] || this.route.snapshot.params['tenderId'];
    this.loadData();
  }

  private loadData(): void {
    this.isLoading.set(true);
    this.error.set(null);

    forkJoin({
      folders: this.portalService.getDocumentsByFolder(this.tenderId),
      addenda: this.portalService.getAddenda(this.tenderId)
    }).subscribe({
      next: (result) => {
        this.folders.set(result.folders);
        this.addenda.set(result.addenda);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.error.set(err.message || 'Failed to load documents');
        this.isLoading.set(false);
      }
    });
  }

  downloadDocument(doc: TenderDocument): void {
    this.downloadingId.set(doc.id);

    this.portalService.downloadDocument(this.tenderId, doc.id).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = doc.fileName;
        link.click();
        window.URL.revokeObjectURL(url);
        this.downloadingId.set(null);
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Download Failed',
          detail: 'Failed to download the document. Please try again.'
        });
        this.downloadingId.set(null);
      }
    });
  }

  previewDocument(doc: TenderDocument): void {
    // Download and open in new tab for preview
    this.portalService.downloadDocument(this.tenderId, doc.id).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank');
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Preview Failed',
          detail: 'Failed to preview the document.'
        });
      }
    });
  }

  acknowledgeAddendum(addendum: TenderAddendum): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to acknowledge Addendum #${addendum.addendumNumber}? This action cannot be undone.`,
      header: 'Confirm Acknowledgment',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.acknowledgingId.set(addendum.id);

        this.portalService.acknowledgeAddendum(this.tenderId, addendum.id).subscribe({
          next: (updated) => {
            // Update the addenda list
            const currentAddenda = this.addenda();
            const index = currentAddenda.findIndex(a => a.id === addendum.id);
            if (index !== -1) {
              currentAddenda[index] = updated;
              this.addenda.set([...currentAddenda]);
            }

            this.messageService.add({
              severity: 'success',
              summary: 'Acknowledged',
              detail: `Addendum #${addendum.addendumNumber} has been acknowledged.`
            });
            this.acknowledgingId.set(null);
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to acknowledge addendum. Please try again.'
            });
            this.acknowledgingId.set(null);
          }
        });
      }
    });
  }

  getTotalDocumentCount(): number {
    return this.folders().reduce((sum, folder) => sum + folder.documents.length, 0);
  }

  getTotalSize(): string {
    const totalBytes = this.folders().reduce((sum, folder) => sum + folder.totalSize, 0);
    return this.formatFileSize(totalBytes);
  }

  formatFileSize(bytes: number): string {
    return this.portalService.formatFileSize(bytes);
  }

  getFileIcon(mimeType: string): string {
    if (mimeType.includes('pdf')) return 'pi-file-pdf';
    if (mimeType.includes('word') || mimeType.includes('document')) return 'pi-file-word';
    if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return 'pi-file-excel';
    if (mimeType.includes('image')) return 'pi-image';
    if (mimeType.includes('zip') || mimeType.includes('compressed')) return 'pi-folder';
    return 'pi-file';
  }

  canPreview(mimeType: string): boolean {
    return mimeType.includes('pdf') || mimeType.includes('image');
  }
}
