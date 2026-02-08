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
import { Subject, takeUntil } from 'rxjs';
import { DialogModule } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { DividerModule } from 'primeng/divider';
import { PanelModule } from 'primeng/panel';
import { TooltipModule } from 'primeng/tooltip';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { InputTextarea } from 'primeng/inputtextarea';
import { MessageModule } from 'primeng/message';

import { BidService } from '../../../../core/services/bid.service';
import {
  BidSubmission,
  BidDocument,
  BidDocumentCategory,
  BidStatus,
  BID_STATUS_CONFIG,
  BID_DOCUMENT_TYPE_LABELS,
  BID_DOCUMENT_CATEGORY_LABELS
} from '../../../../core/models/bid.model';

@Component({
  selector: 'app-bid-details-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    DialogModule,
    ButtonModule,
    TagModule,
    DividerModule,
    PanelModule,
    TooltipModule,
    ProgressSpinnerModule,
    InputTextarea,
    MessageModule
  ],
  template: `
    <p-dialog
      [header]="bid()?.bidderName || 'Bid Details'"
      [(visible)]="visible"
      (visibleChange)="onVisibleChange($event)"
      [modal]="true"
      [style]="{ width: '800px', maxHeight: '90vh' }"
      [contentStyle]="{ overflow: 'auto' }"
      [draggable]="false"
      [resizable]="false"
    >
      @if (isLoading()) {
        <div class="loading-container">
          <p-progressSpinner
            [style]="{ width: '50px', height: '50px' }"
            strokeWidth="4"
          ></p-progressSpinner>
          <p>Loading bid details...</p>
        </div>
      } @else if (bid()) {
        <div class="bid-details-content">
          <!-- Header Section -->
          <div class="bid-header">
            <div class="header-info">
              <h3>{{ bid()!.bidderName }}</h3>
              @if (bid()!.bidderNameAr) {
                <span class="bidder-name-ar">{{ bid()!.bidderNameAr }}</span>
              }
              <span class="bidder-email">{{ bid()!.bidderEmail }}</span>
            </div>
            <div class="header-status">
              <p-tag
                [value]="getStatusLabel(bid()!.status)"
                [severity]="getStatusSeverity(bid()!.status)"
              ></p-tag>
            </div>
          </div>

          <!-- Submission Info -->
          <div class="submission-info">
            <div class="info-item">
              <label>Submission Time</label>
              <span>{{ bid()!.submissionTime | date:'medium' }}</span>
            </div>
            @if (bid()!.isLate) {
              <div class="info-item">
                <label>Late Reason</label>
                <span class="late-reason">{{ bid()!.lateReason }}</span>
              </div>
            }
            @if (bid()!.openedAt) {
              <div class="info-item">
                <label>Opened</label>
                <span>{{ bid()!.openedAt | date:'medium' }} by {{ bid()!.openedByName }}</span>
              </div>
            }
          </div>

          <p-divider></p-divider>

          <!-- Documents Section -->
          <div class="documents-section">
            <h4>Documents ({{ bid()!.filesCount }})</h4>

            @for (category of documentCategories; track category) {
              @if (getDocumentsByCategory(category).length > 0) {
                <p-panel
                  [header]="getCategoryLabel(category)"
                  [toggleable]="true"
                  [collapsed]="false"
                  styleClass="documents-panel"
                >
                  <div class="documents-list">
                    @for (doc of getDocumentsByCategory(category); track doc.id) {
                      <div class="document-item">
                        <div class="document-info">
                          <i [class]="getDocumentIcon(doc)"></i>
                          <div class="document-details">
                            <span class="document-name">{{ doc.originalFilename }}</span>
                            <span class="document-meta">
                              {{ getDocumentTypeLabel(doc.documentType) }}
                              <span class="separator">|</span>
                              {{ formatFileSize(doc.fileSize) }}
                            </span>
                          </div>
                        </div>
                        <div class="document-actions">
                          @if (doc.isPreviewable) {
                            <button
                              pButton
                              icon="pi pi-external-link"
                              class="p-button-text p-button-sm"
                              pTooltip="Preview"
                              (click)="previewDocument(doc)"
                            ></button>
                          }
                          <button
                            pButton
                            icon="pi pi-download"
                            class="p-button-text p-button-sm"
                            pTooltip="Download"
                            (click)="downloadDocument(doc)"
                          ></button>
                        </div>
                      </div>
                    }
                  </div>
                </p-panel>
              }
            }
          </div>

          <!-- Bid Summary (if imported) -->
          @if (bid()!.bidSummary) {
            <p-divider></p-divider>
            <div class="bid-summary-section">
              <h4>Bid Summary</h4>
              <div class="summary-grid">
                <div class="summary-item">
                  <label>Total Amount</label>
                  <span class="amount">
                    {{ bid()!.bidSummary!.totalAmount | number:'1.0-0' }}
                    {{ bid()!.bidSummary!.currency }}
                  </span>
                </div>
                <div class="summary-item">
                  <label>Validity</label>
                  <span>{{ bid()!.bidSummary!.validityDays }} days</span>
                </div>
                <div class="summary-item">
                  <label>Valid Until</label>
                  <span>{{ bid()!.bidSummary!.validUntil | date:'mediumDate' }}</span>
                </div>
                @if (bid()!.bidSummary!.paymentTerms) {
                  <div class="summary-item full-width">
                    <label>Payment Terms</label>
                    <span>{{ bid()!.bidSummary!.paymentTerms }}</span>
                  </div>
                }
                @if (bid()!.bidSummary!.exceptions && bid()!.bidSummary!.exceptions!.length > 0) {
                  <div class="summary-item full-width">
                    <label>Exceptions</label>
                    <ul class="exceptions-list">
                      @for (exception of bid()!.bidSummary!.exceptions; track exception) {
                        <li>{{ exception }}</li>
                      }
                    </ul>
                  </div>
                }
              </div>
            </div>
          }

          <!-- Disqualification Info -->
          @if (bid()!.status === 'disqualified') {
            <p-divider></p-divider>
            <p-message
              severity="error"
              styleClass="w-full"
            >
              <ng-template pTemplate="content">
                <div class="disqualification-info">
                  <strong>Disqualified</strong>
                  <p>{{ bid()!.disqualificationReason }}</p>
                  <span class="meta">
                    By {{ bid()!.disqualifiedByName }} on {{ bid()!.disqualifiedAt | date:'medium' }}
                  </span>
                </div>
              </ng-template>
            </p-message>
          }

          <!-- Disqualification Form -->
          @if (showDisqualifyForm) {
            <p-divider></p-divider>
            <div class="disqualify-form">
              <h4>Disqualify Bid</h4>
              <div class="form-field">
                <label for="disqualifyReason">Reason <span class="required">*</span></label>
                <textarea
                  pInputTextarea
                  id="disqualifyReason"
                  [(ngModel)]="disqualifyReason"
                  [rows]="3"
                  [autoResize]="true"
                  class="w-full"
                  placeholder="Enter reason for disqualification..."
                ></textarea>
              </div>
              <div class="form-actions">
                <button
                  pButton
                  label="Cancel"
                  class="p-button-text"
                  (click)="showDisqualifyForm = false; disqualifyReason = ''"
                ></button>
                <button
                  pButton
                  label="Confirm Disqualify"
                  class="p-button-danger"
                  icon="pi pi-ban"
                  [disabled]="!disqualifyReason.trim()"
                  [loading]="isDisqualifying()"
                  (click)="confirmDisqualify()"
                ></button>
              </div>
            </div>
          }
        </div>
      }

      <!-- Dialog Footer -->
      <ng-template pTemplate="footer">
        <div class="dialog-footer">
          <button
            pButton
            label="Download All"
            icon="pi pi-download"
            class="p-button-outlined"
            (click)="downloadAllFiles()"
          ></button>

          @if (bidsOpened && bid()?.status !== 'imported' && bid()?.status !== 'disqualified') {
            <button
              pButton
              label="Import BOQ"
              icon="pi pi-file-import"
              class="p-button-success"
              [loading]="isImporting()"
              (click)="importBoq()"
            ></button>
          }

          @if (bid()?.status !== 'disqualified' && !showDisqualifyForm) {
            <button
              pButton
              label="Disqualify"
              icon="pi pi-ban"
              class="p-button-danger p-button-outlined"
              (click)="showDisqualifyForm = true"
            ></button>
          }
        </div>
      </ng-template>
    </p-dialog>
  `,
  styles: [`
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

    .bid-details-content {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .bid-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 1rem;
    }

    .header-info {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .header-info h3 {
      margin: 0;
      color: var(--bayan-foreground, #09090b);
    }

    .bidder-name-ar {
      font-size: 0.95rem;
      color: var(--bayan-muted-foreground, #71717a);
      direction: rtl;
    }

    .bidder-email {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .submission-info {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      padding: 1rem;
      background-color: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .info-item {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .info-item label {
      font-size: 0.75rem;
      font-weight: 500;
      color: var(--bayan-muted-foreground, #71717a);
      text-transform: uppercase;
    }

    .info-item span {
      color: var(--bayan-foreground, #09090b);
    }

    .late-reason {
      color: #d97706 !important;
    }

    .documents-section h4 {
      margin: 0 0 1rem;
      color: var(--bayan-foreground, #09090b);
    }

    :host ::ng-deep .documents-panel {
      margin-bottom: 0.75rem;
    }

    :host ::ng-deep .documents-panel .p-panel-header {
      padding: 0.75rem 1rem;
      background-color: var(--bayan-accent, #f4f4f5);
    }

    :host ::ng-deep .documents-panel .p-panel-content {
      padding: 0.75rem 1rem;
    }

    .documents-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .document-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.75rem;
      background-color: #fff;
      border: 1px solid var(--bayan-border, #e4e4e7);
      border-radius: var(--bayan-radius-sm, 0.375rem);
    }

    .document-info {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .document-info > i {
      font-size: 1.5rem;
      color: var(--bayan-primary, #18181b);
    }

    .document-details {
      display: flex;
      flex-direction: column;
    }

    .document-name {
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
    }

    .document-meta {
      font-size: 0.8rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .separator {
      margin: 0 0.5rem;
    }

    .document-actions {
      display: flex;
      gap: 0.25rem;
    }

    .bid-summary-section h4 {
      margin: 0 0 1rem;
      color: var(--bayan-foreground, #09090b);
    }

    .summary-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1rem;
      padding: 1rem;
      background-color: var(--bayan-success-bg, #f0fdf4);
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .summary-item {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .summary-item.full-width {
      grid-column: 1 / -1;
    }

    .summary-item label {
      font-size: 0.75rem;
      font-weight: 500;
      color: var(--bayan-muted-foreground, #71717a);
      text-transform: uppercase;
    }

    .summary-item .amount {
      font-size: 1.25rem;
      font-weight: 600;
      color: #16a34a;
    }

    .exceptions-list {
      margin: 0;
      padding-left: 1.25rem;
      color: var(--bayan-foreground, #09090b);
    }

    .disqualification-info {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .disqualification-info p {
      margin: 0;
    }

    .disqualification-info .meta {
      font-size: 0.8rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .disqualify-form {
      padding: 1rem;
      background-color: var(--bayan-danger-bg, #fef2f2);
      border: 1px solid #ef5350;
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .disqualify-form h4 {
      margin: 0 0 1rem;
      color: #dc2626;
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

    .required {
      color: #ef4444;
    }

    .form-actions {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
      margin-top: 1rem;
    }

    .dialog-footer {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
    }

    @media (max-width: 600px) {
      .summary-grid {
        grid-template-columns: 1fr;
      }
    }
  `]
})
export class BidDetailsDialogComponent implements OnChanges {
  @Input() visible = false;
  @Input() tenderId!: number;
  @Input() bidId: number | null = null;
  @Input() bidsOpened = false;

  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() imported = new EventEmitter<number>();
  @Output() disqualified = new EventEmitter<number>();

  private readonly bidService = inject(BidService);
  private readonly destroy$ = new Subject<void>();

  bid = signal<BidSubmission | null>(null);
  isLoading = signal<boolean>(false);
  isImporting = signal<boolean>(false);
  isDisqualifying = signal<boolean>(false);

  showDisqualifyForm = false;
  disqualifyReason = '';

  documentCategories: BidDocumentCategory[] = ['commercial', 'technical', 'supporting'];

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && this.visible && this.bidId) {
      this.loadBidDetails();
    }
  }

  private loadBidDetails(): void {
    if (!this.bidId) return;

    this.isLoading.set(true);
    this.bidService.getBidDetails(this.tenderId, this.bidId).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (bid) => {
        this.bid.set(bid);
        this.isLoading.set(false);
      },
      error: () => {
        this.isLoading.set(false);
      }
    });
  }

  onVisibleChange(visible: boolean): void {
    if (!visible) {
      this.showDisqualifyForm = false;
      this.disqualifyReason = '';
    }
    this.visibleChange.emit(visible);
  }

  getStatusLabel(status: BidStatus): string {
    return BID_STATUS_CONFIG[status]?.label || status;
  }

  getStatusSeverity(status: BidStatus): 'secondary' | 'success' | 'info' | 'warn' | 'danger' | 'contrast' {
    return BID_STATUS_CONFIG[status]?.severity || 'secondary';
  }

  getCategoryLabel(category: BidDocumentCategory): string {
    return BID_DOCUMENT_CATEGORY_LABELS[category];
  }

  getDocumentTypeLabel(type: string): string {
    return BID_DOCUMENT_TYPE_LABELS[type as keyof typeof BID_DOCUMENT_TYPE_LABELS] || type;
  }

  getDocumentsByCategory(category: BidDocumentCategory): BidDocument[] {
    return this.bid()?.documents.filter(d => d.category === category) || [];
  }

  getDocumentIcon(doc: BidDocument): string {
    const mimeType = doc.mimeType.toLowerCase();
    if (mimeType.includes('pdf')) return 'pi pi-file-pdf';
    if (mimeType.includes('spreadsheet') || mimeType.includes('excel')) return 'pi pi-file-excel';
    if (mimeType.includes('word') || mimeType.includes('document')) return 'pi pi-file-word';
    if (mimeType.includes('image')) return 'pi pi-image';
    return 'pi pi-file';
  }

  formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  previewDocument(doc: BidDocument): void {
    const url = this.bidService.getDocumentPreviewUrl(doc.id);
    window.open(url, '_blank');
  }

  downloadDocument(doc: BidDocument): void {
    this.bidService.downloadDocument(doc.id).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = doc.originalFilename;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    });
  }

  downloadAllFiles(): void {
    if (!this.bid()) return;

    this.bidService.downloadBidFiles(this.tenderId, this.bid()!.id).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bid_${this.bid()!.id}_all_files.zip`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    });
  }

  importBoq(): void {
    if (!this.bid()) return;

    this.isImporting.set(true);
    this.bidService.importBoq(this.tenderId, this.bid()!.id).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (updatedBid) => {
        this.isImporting.set(false);
        this.bid.set(updatedBid);
        this.imported.emit(updatedBid.id);
      },
      error: () => {
        this.isImporting.set(false);
      }
    });
  }

  confirmDisqualify(): void {
    if (!this.bid() || !this.disqualifyReason.trim()) return;

    this.isDisqualifying.set(true);
    this.bidService.disqualifyBid(this.tenderId, this.bid()!.id, { reason: this.disqualifyReason.trim() }).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (updatedBid) => {
        this.isDisqualifying.set(false);
        this.showDisqualifyForm = false;
        this.disqualifyReason = '';
        this.bid.set(updatedBid);
        this.disqualified.emit(updatedBid.id);
      },
      error: () => {
        this.isDisqualifying.set(false);
      }
    });
  }
}
