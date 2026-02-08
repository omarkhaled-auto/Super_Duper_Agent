import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { DividerModule } from 'primeng/divider';
import { TableModule } from 'primeng/table';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { PortalService } from '../../../core/services/portal.service';
import { PortalBidReceipt, PORTAL_BID_DOCUMENT_TYPE_CONFIG } from '../../../core/models/portal.model';

@Component({
  selector: 'app-portal-receipt',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    CardModule,
    ButtonModule,
    TagModule,
    DividerModule,
    TableModule,
    ProgressSpinnerModule,
    MessageModule,
    ToastModule
  ],
  providers: [MessageService],
  template: `
    <div class="portal-receipt">
      <!-- Loading State -->
      @if (isLoading()) {
        <div class="loading-container">
          <p-progressSpinner></p-progressSpinner>
          <p>Loading receipt...</p>
        </div>
      }

      <!-- Error State -->
      @if (error()) {
        <p-message severity="error" [text]="error()!" styleClass="w-full mb-4"></p-message>
      }

      @if (!isLoading() && !error() && receipt()) {
        <div class="receipt-container">
          <!-- Success Animation -->
          <div class="success-header" [class.late]="receipt()!.isLateSubmission">
            <div class="success-icon">
              @if (receipt()!.isLateSubmission) {
                <i class="pi pi-exclamation-triangle"></i>
              } @else {
                <i class="pi pi-check-circle"></i>
              }
            </div>
            <h1>
              @if (receipt()!.isLateSubmission) {
                Late Submission Received
              } @else {
                Bid Submitted Successfully
              }
            </h1>
            <p>Your bid has been received and recorded in our system.</p>
          </div>

          <!-- Late Submission Warning -->
          @if (receipt()!.isLateSubmission) {
            <p-message
              severity="warn"
              styleClass="w-full mb-4"
            >
              <ng-template pTemplate="content">
                <div class="late-warning">
                  <i class="pi pi-exclamation-triangle"></i>
                  <div>
                    <strong>Late Submission Notice</strong>
                    <p>
                      This bid was submitted after the official deadline. Late submissions may be
                      disqualified at the discretion of the tender committee. Please contact the
                      procurement team if you believe this was submitted in error.
                    </p>
                  </div>
                </div>
              </ng-template>
            </p-message>
          }

          <!-- Receipt Card -->
          <p-card styleClass="receipt-card">
            <ng-template pTemplate="header">
              <div class="receipt-header">
                <div class="receipt-title">
                  <h2>Bid Submission Receipt</h2>
                  <span class="receipt-number">{{ receipt()!.receiptNumber }}</span>
                </div>
                <div class="receipt-logo">
                  <img src="assets/images/logo.png" alt="Bayan" />
                </div>
              </div>
            </ng-template>

            <!-- Tender Information -->
            <div class="info-section">
              <h3>Tender Information</h3>
              <div class="info-grid">
                <div class="info-row">
                  <span class="info-label">Tender Title</span>
                  <span class="info-value">{{ receipt()!.tenderTitle }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">Reference</span>
                  <span class="info-value reference">{{ receipt()!.tenderReference }}</span>
                </div>
              </div>
            </div>

            <p-divider></p-divider>

            <!-- Bidder Information -->
            <div class="info-section">
              <h3>Bidder Information</h3>
              <div class="info-grid">
                <div class="info-row">
                  <span class="info-label">Company Name</span>
                  <span class="info-value">{{ receipt()!.bidderName }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">Email</span>
                  <span class="info-value">{{ receipt()!.bidderEmail }}</span>
                </div>
              </div>
            </div>

            <p-divider></p-divider>

            <!-- Submission Details -->
            <div class="info-section">
              <h3>Submission Details</h3>
              <div class="info-grid">
                <div class="info-row">
                  <span class="info-label">Submission Time</span>
                  <span class="info-value timestamp">{{ receipt()!.submittedAt | date:'EEEE, MMMM d, y - h:mm:ss a' }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">Status</span>
                  <span class="info-value">
                    @if (receipt()!.isLateSubmission) {
                      <p-tag value="Late Submission" severity="warn"></p-tag>
                    } @else {
                      <p-tag value="Submitted On Time" severity="success"></p-tag>
                    }
                  </span>
                </div>
                <div class="info-row">
                  <span class="info-label">Receipt Number</span>
                  <span class="info-value receipt-code">{{ receipt()!.receiptNumber }}</span>
                </div>
              </div>
            </div>

            <p-divider></p-divider>

            <!-- Submitted Files -->
            <div class="info-section">
              <h3>Submitted Documents</h3>
              <p-table [value]="receipt()!.documents" styleClass="p-datatable-sm">
                <ng-template pTemplate="header">
                  <tr>
                    <th style="width: 40%">Document Type</th>
                    <th style="width: 40%">File Name</th>
                    <th style="width: 20%">Size</th>
                  </tr>
                </ng-template>
                <ng-template pTemplate="body" let-doc>
                  <tr>
                    <td>
                      <div class="doc-type">
                        <i class="pi {{ getDocumentIcon(doc.type) }}"></i>
                        {{ getDocumentLabel(doc.type) }}
                      </div>
                    </td>
                    <td class="file-name">{{ doc.fileName }}</td>
                    <td>{{ formatFileSize(doc.fileSize) }}</td>
                  </tr>
                </ng-template>
                <ng-template pTemplate="footer">
                  <tr>
                    <td colspan="2" class="text-right font-bold">Total Size:</td>
                    <td class="font-bold">{{ formatFileSize(receipt()!.totalFileSize) }}</td>
                  </tr>
                </ng-template>
              </p-table>
            </div>

            <!-- Legal Notice -->
            <div class="legal-notice">
              <i class="pi pi-info-circle"></i>
              <p>
                This receipt confirms that your bid has been received by the Bayan Tender Management System.
                Please retain this receipt for your records. The evaluation of your bid will be conducted
                in accordance with the tender terms and conditions. You will be notified of the outcome
                through the registered email address.
              </p>
            </div>
          </p-card>

          <!-- Actions -->
          <div class="receipt-actions">
            <button
              pButton
              label="Download Receipt PDF"
              icon="pi pi-download"
              class="p-button-lg"
              [loading]="isDownloading()"
              (click)="downloadPdf()"
            ></button>
            <button
              pButton
              label="Return to Portal"
              icon="pi pi-arrow-left"
              class="p-button-lg p-button-outlined"
              [routerLink]="['/portal/tenders', receipt()!.tenderId, 'documents']"
            ></button>
          </div>
        </div>
      }
    </div>

    <p-toast></p-toast>
  `,
  styles: [`
    .portal-receipt {
      max-width: 800px;
      margin: 0 auto;
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

    /* Success Header */
    .success-header {
      text-align: center;
      padding: 3rem 2rem;
      background: #f0fdf4;
      border-radius: var(--bayan-radius, 0.5rem);
      margin-bottom: 2rem;
      border: 1px solid var(--bayan-border, #e4e4e7);
    }

    .success-header.late {
      background: #fffbeb;
    }

    .success-icon {
      width: 100px;
      height: 100px;
      margin: 0 auto 1.5rem;
      background: var(--bayan-card, #ffffff);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 1px solid var(--bayan-border, #e4e4e7);
      box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05);
      animation: scaleIn 0.5s ease;
    }

    @keyframes scaleIn {
      from { transform: scale(0); }
      to { transform: scale(1); }
    }

    .success-icon i {
      font-size: 3.5rem;
      color: #16a34a;
    }

    .success-header.late .success-icon i {
      color: #d97706;
    }

    .success-header h1 {
      margin: 0 0 0.5rem 0;
      font-size: 1.75rem;
      font-weight: 700;
      color: #15803d;
    }

    .success-header.late h1 {
      color: #b45309;
    }

    .success-header p {
      margin: 0;
      color: #166534;
      font-size: 1.125rem;
    }

    .success-header.late p {
      color: #92400e;
    }

    /* Late Warning */
    .late-warning {
      display: flex;
      align-items: flex-start;
      gap: 1rem;
    }

    .late-warning i {
      font-size: 1.5rem;
      color: #d97706;
      margin-top: 2px;
    }

    .late-warning strong {
      display: block;
      margin-bottom: 0.25rem;
      color: #92400e;
    }

    .late-warning p {
      margin: 0;
      color: #a16207;
      font-size: 0.9375rem;
    }

    /* Receipt Card */
    .receipt-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding: 1.5rem;
      background: var(--bayan-accent, #f4f4f5);
      border-bottom: 1px solid var(--bayan-border, #e4e4e7);
    }

    .receipt-title h2 {
      margin: 0 0 0.25rem 0;
      font-size: 1.25rem;
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
    }

    .receipt-number {
      font-family: monospace;
      font-size: 1rem;
      color: var(--bayan-primary, #18181b);
      font-weight: 600;
    }

    .receipt-logo img {
      height: 40px;
    }

    /* Info Sections */
    .info-section {
      padding: 1.5rem;
    }

    .info-section h3 {
      margin: 0 0 1rem 0;
      font-size: 0.875rem;
      font-weight: 600;
      color: var(--bayan-muted-foreground, #71717a);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .info-grid {
      display: grid;
      gap: 0.75rem;
    }

    .info-row {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding: 0.5rem 0;
    }

    .info-label {
      color: var(--bayan-muted-foreground, #71717a);
      font-size: 0.9375rem;
    }

    .info-value {
      color: var(--bayan-foreground, #09090b);
      font-weight: 500;
      text-align: right;
      max-width: 60%;
    }

    .info-value.reference {
      font-family: monospace;
      color: var(--bayan-primary, #18181b);
    }

    .info-value.timestamp {
      color: #059669;
      font-weight: 600;
    }

    .info-value.receipt-code {
      font-family: monospace;
      font-size: 1.125rem;
      color: var(--bayan-primary, #18181b);
      background: var(--bayan-accent, #f4f4f5);
      padding: 0.25rem 0.75rem;
      border-radius: var(--bayan-radius-sm, 0.375rem);
    }

    /* Documents Table */
    .doc-type {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .doc-type i {
      color: var(--bayan-primary, #18181b);
    }

    .file-name {
      max-width: 250px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* Legal Notice */
    .legal-notice {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
      padding: 1.5rem;
      background: var(--bayan-accent, #f4f4f5);
      border-top: 1px solid var(--bayan-border, #e4e4e7);
      margin-top: 1rem;
    }

    .legal-notice i {
      color: var(--bayan-muted-foreground, #71717a);
      margin-top: 2px;
    }

    .legal-notice p {
      margin: 0;
      color: var(--bayan-muted-foreground, #71717a);
      font-size: 0.8rem;
      line-height: 1.6;
    }

    /* Actions */
    .receipt-actions {
      display: flex;
      justify-content: center;
      gap: 1rem;
      margin-top: 2rem;
    }

    :host ::ng-deep {
      .receipt-card .p-card-body {
        padding: 0;
      }

      .p-datatable .p-datatable-tbody > tr > td {
        padding: 0.75rem 1rem;
      }

      .p-datatable .p-datatable-tfoot > tr > td {
        padding: 0.75rem 1rem;
        background: var(--bayan-accent, #f4f4f5);
      }

      .text-right {
        text-align: right;
      }

      .font-bold {
        font-weight: 600;
      }
    }

    @media (max-width: 768px) {
      .success-header {
        padding: 2rem 1rem;
      }

      .success-icon {
        width: 80px;
        height: 80px;
      }

      .success-icon i {
        font-size: 2.5rem;
      }

      .success-header h1 {
        font-size: 1.5rem;
      }

      .receipt-header {
        flex-direction: column;
        gap: 1rem;
      }

      .receipt-logo {
        display: none;
      }

      .info-row {
        flex-direction: column;
        gap: 0.25rem;
      }

      .info-value {
        text-align: left;
        max-width: 100%;
      }

      .receipt-actions {
        flex-direction: column;
      }
    }

    @media print {
      .receipt-actions {
        display: none;
      }

      .portal-receipt {
        max-width: 100%;
      }
    }
  `]
})
export class PortalReceiptComponent implements OnInit {
  private readonly portalService = inject(PortalService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly messageService = inject(MessageService);

  receipt = signal<PortalBidReceipt | null>(null);
  isLoading = signal(true);
  isDownloading = signal(false);
  error = signal<string | null>(null);

  private bidId!: number;

  ngOnInit(): void {
    this.bidId = parseInt(this.route.snapshot.params['bidId'], 10);
    this.loadReceipt();
  }

  private loadReceipt(): void {
    this.isLoading.set(true);
    this.error.set(null);

    this.portalService.getBidReceipt(this.bidId).subscribe({
      next: (receipt) => {
        this.receipt.set(receipt);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.error.set(err.message || 'Failed to load receipt');
        this.isLoading.set(false);
      }
    });
  }

  downloadPdf(): void {
    this.isDownloading.set(true);

    this.portalService.downloadReceiptPdf(this.bidId).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `Bid_Receipt_${this.receipt()?.receiptNumber}.pdf`;
        link.click();
        window.URL.revokeObjectURL(url);
        this.isDownloading.set(false);
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Download Failed',
          detail: 'Failed to download receipt PDF. Please try again.'
        });
        this.isDownloading.set(false);
      }
    });
  }

  getDocumentLabel(type: string): string {
    const config = PORTAL_BID_DOCUMENT_TYPE_CONFIG[type as keyof typeof PORTAL_BID_DOCUMENT_TYPE_CONFIG];
    return config?.label || type;
  }

  getDocumentIcon(type: string): string {
    const config = PORTAL_BID_DOCUMENT_TYPE_CONFIG[type as keyof typeof PORTAL_BID_DOCUMENT_TYPE_CONFIG];
    return config?.icon || 'pi-file';
  }

  formatFileSize(bytes: number): string {
    return this.portalService.formatFileSize(bytes);
  }
}
