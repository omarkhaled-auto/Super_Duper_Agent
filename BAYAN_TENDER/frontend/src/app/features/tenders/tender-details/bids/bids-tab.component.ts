import {
  Component,
  Input,
  OnInit,
  OnDestroy,
  inject,
  signal,
  computed
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil, forkJoin } from 'rxjs';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { CheckboxModule } from 'primeng/checkbox';
import { PanelModule } from 'primeng/panel';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';
import { DividerModule } from 'primeng/divider';
import { MessageService, ConfirmationService } from 'primeng/api';

import { BidService } from '../../../../core/services/bid.service';
import {
  BidListItem,
  BidStatistics,
  BidStatus,
  BID_STATUS_CONFIG
} from '../../../../core/models/bid.model';
import { OpenBidsDialogComponent } from './open-bids-dialog.component';
import { BidDetailsDialogComponent } from './bid-details-dialog.component';
import { LateBidRejectionDialogComponent } from './late-bid-rejection-dialog.component';
import { BidImportDialogComponent } from './bid-import-dialog.component';

@Component({
  selector: 'app-bids-tab',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    CardModule,
    TagModule,
    TooltipModule,
    CheckboxModule,
    PanelModule,
    ToastModule,
    ConfirmDialogModule,
    ProgressSpinnerModule,
    MessageModule,
    DividerModule,
    OpenBidsDialogComponent,
    BidDetailsDialogComponent,
    LateBidRejectionDialogComponent,
    BidImportDialogComponent
  ],
  providers: [MessageService, ConfirmationService],
  template: `
    <p-toast></p-toast>
    <p-confirmDialog></p-confirmDialog>

    <div class="bids-tab-container" data-testid="bids-tab">
      <!-- Header Stats & Actions -->
      <div class="bids-header">
        <div class="header-stats">
          @if (statistics()) {
            <span class="stat-text">
              <strong>{{ statistics()!.totalBids - statistics()!.lateBids }}</strong> bids received
              @if (statistics()!.lateBids > 0) {
                <span class="late-indicator">
                  | <strong>{{ statistics()!.lateBids }}</strong> late bids
                </span>
              }
            </span>
          }
        </div>

        <div class="header-actions">
          <button
            pButton
            icon="pi pi-download"
            label="Download All Bids"
            class="p-button-outlined"
            data-testid="download-all-bids-btn"
            [disabled]="bids().length === 0"
            [loading]="isDownloading()"
            (click)="downloadAllBids()"
          ></button>

          @if (!statistics()?.bidsOpened) {
            <button
              pButton
              icon="pi pi-eye"
              label="Open Bids"
              class="p-button-warning"
              data-testid="open-bids-btn"
              [disabled]="regularBids().length === 0"
              (click)="showOpenBidsDialog = true"
            ></button>
          } @else {
            <p-tag value="Bids Opened" severity="success" icon="pi pi-check-circle"></p-tag>
          }
        </div>
      </div>

      <!-- Error Message -->
      @if (bidService.error()) {
        <p-message
          severity="error"
          [text]="bidService.error()!"
          styleClass="w-full"
        ></p-message>
      }

      <!-- Loading State -->
      @if (bidService.isLoading() && bids().length === 0) {
        <div class="loading-container">
          <p-progressSpinner
            [style]="{ width: '50px', height: '50px' }"
            strokeWidth="4"
          ></p-progressSpinner>
          <p>Loading bids...</p>
        </div>
      } @else if (bids().length === 0) {
        <!-- Empty State -->
        <div class="empty-state">
          <i class="pi pi-inbox" style="font-size: 3rem; color: var(--bayan-border, #e4e4e7);"></i>
          <h3>No Bids Received</h3>
          <p>No bids have been submitted for this tender yet.</p>
        </div>
      } @else {
        <!-- Bids Table -->
        <p-table
          data-testid="bids-table"
          [value]="regularBids()"
          [(selection)]="selectedBids"
          dataKey="id"
          [loading]="bidService.isLoading()"
          [paginator]="true"
          [rows]="10"
          [showCurrentPageReport]="true"
          currentPageReportTemplate="Showing {first} to {last} of {totalRecords} bids"
          styleClass="p-datatable-sm p-datatable-striped"
        >
          <ng-template pTemplate="header">
            <tr>
              <th style="width: 50px">
                <p-tableHeaderCheckbox></p-tableHeaderCheckbox>
              </th>
              <th pSortableColumn="bidderName">
                Bidder Name
                <p-sortIcon field="bidderName"></p-sortIcon>
              </th>
              <th pSortableColumn="submissionTime">
                Submission Time
                <p-sortIcon field="submissionTime"></p-sortIcon>
              </th>
              <th style="width: 120px">Status</th>
              <th style="width: 150px">Bid Amount</th>
              <th style="width: 100px">Files</th>
              <th style="width: 150px">Actions</th>
            </tr>
          </ng-template>

          <ng-template pTemplate="body" let-bid>
            <tr>
              <td>
                <p-tableCheckbox [value]="bid"></p-tableCheckbox>
              </td>
              <td>
                <div class="bidder-info">
                  <span class="bidder-name">{{ bid.bidderName }}</span>
                </div>
              </td>
              <td>{{ bid.submissionTime | date:'medium' }}</td>
              <td>
                <p-tag
                  [value]="getStatusLabel(bid.status)"
                  [severity]="getStatusSeverity(bid.status)"
                ></p-tag>
              </td>
              <td>
                @if (bid.bidAmount !== undefined && statistics()?.bidsOpened) {
                  <span class="bid-amount">
                    {{ bid.bidAmount | number:'1.0-0' }} {{ bid.currency }}
                  </span>
                } @else {
                  <span class="hidden-amount">
                    <i class="pi pi-lock"></i> Hidden
                  </span>
                }
              </td>
              <td>
                <span class="files-count">
                  <i class="pi pi-file"></i> {{ bid.filesCount }}
                </span>
              </td>
              <td>
                <div class="action-buttons">
                  <button
                    pButton
                    icon="pi pi-eye"
                    class="p-button-text p-button-sm"
                    pTooltip="View Details"
                    (click)="viewBidDetails(bid)"
                  ></button>
                  <button
                    pButton
                    icon="pi pi-download"
                    class="p-button-text p-button-sm"
                    pTooltip="Download Files"
                    (click)="downloadBidFiles(bid)"
                  ></button>
                  @if (statistics()?.bidsOpened && bid.status !== 'imported') {
                    <button
                      pButton
                      icon="pi pi-file-import"
                      class="p-button-text p-button-sm"
                      pTooltip="Import BOQ"
                      (click)="importBoq(bid)"
                    ></button>
                  }
                </div>
              </td>
            </tr>
          </ng-template>

          <ng-template pTemplate="emptymessage">
            <tr>
              <td colspan="7" class="text-center p-4">
                No regular bids found.
              </td>
            </tr>
          </ng-template>
        </p-table>

        <!-- Late Bids Section -->
        @if (lateBids().length > 0) {
          <p-panel
            header="Late Bids"
            [toggleable]="true"
            [collapsed]="false"
            styleClass="late-bids-panel"
          >
            <ng-template pTemplate="header">
              <div class="late-bids-header">
                <span>
                  <i class="pi pi-clock"></i>
                  Late Bids ({{ lateBids().length }})
                </span>
              </div>
            </ng-template>

            <div class="late-bids-list">
              @for (bid of lateBids(); track bid.id) {
                <div class="late-bid-item">
                  <div class="late-bid-info">
                    <div class="late-bid-header">
                      <span class="bidder-name">{{ bid.bidderName }}</span>
                      <p-tag
                        [value]="getStatusLabel(bid.status)"
                        [severity]="getStatusSeverity(bid.status)"
                      ></p-tag>
                    </div>
                    <div class="late-bid-meta">
                      <span>
                        <i class="pi pi-calendar"></i>
                        Submitted: {{ bid.submissionTime | date:'medium' }}
                      </span>
                      <span>
                        <i class="pi pi-file"></i>
                        {{ bid.filesCount }} files
                      </span>
                    </div>
                  </div>

                  <div class="late-bid-actions">
                    @if (bid.status === 'late') {
                      <button
                        pButton
                        label="Accept"
                        icon="pi pi-check"
                        class="p-button-success p-button-sm"
                        (click)="acceptLateBid(bid)"
                      ></button>
                      <button
                        pButton
                        label="Reject"
                        icon="pi pi-times"
                        class="p-button-danger p-button-outlined p-button-sm"
                        (click)="openRejectDialog(bid)"
                      ></button>
                    }
                    <button
                      pButton
                      icon="pi pi-eye"
                      class="p-button-text p-button-sm"
                      pTooltip="View Details"
                      (click)="viewBidDetails(bid)"
                    ></button>
                  </div>
                </div>
              }
            </div>
          </p-panel>
        }
      }
    </div>

    <!-- Open Bids Dialog -->
    <app-open-bids-dialog
      [visible]="showOpenBidsDialog"
      [bidsCount]="regularBids().length"
      (visibleChange)="showOpenBidsDialog = $event"
      (confirmed)="onOpenBidsConfirmed()"
    ></app-open-bids-dialog>

    <!-- Bid Details Dialog -->
    <app-bid-details-dialog
      [visible]="showBidDetailsDialog"
      [tenderId]="tenderId"
      [bidId]="selectedBidId"
      [bidsOpened]="statistics()?.bidsOpened || false"
      (visibleChange)="showBidDetailsDialog = $event"
      (imported)="onBidImported($event)"
      (disqualified)="onBidDisqualified($event)"
    ></app-bid-details-dialog>

    <!-- Late Bid Rejection Dialog -->
    <app-late-bid-rejection-dialog
      [visible]="showRejectDialog"
      [bidderName]="selectedLateBid?.bidderName || ''"
      (visibleChange)="showRejectDialog = $event"
      (rejected)="onLateBidRejected($event)"
    ></app-late-bid-rejection-dialog>

    <!-- Bid Import Wizard Dialog -->
    @if (showImportDialog && selectedImportBidId) {
      <app-bid-import-dialog
        [visible]="showImportDialog"
        [tenderId]="tenderId"
        [bidId]="selectedImportBidId"
        [bidDocument]="null"
        (visibleChange)="showImportDialog = $event"
        (imported)="onImportWizardComplete($event)"
      ></app-bid-import-dialog>
    }
  `,
  styles: [`
    .bids-tab-container {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .bids-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem;
      background-color: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius, 0.5rem);
      flex-wrap: wrap;
      gap: 1rem;
    }

    .header-stats {
      font-size: 1rem;
      color: var(--bayan-foreground, #09090b);
    }

    .late-indicator {
      color: #d97706;
    }

    .header-actions {
      display: flex;
      gap: 0.5rem;
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

    .bidder-info {
      display: flex;
      flex-direction: column;
    }

    .bidder-name {
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
    }

    .bid-amount {
      font-weight: 600;
      color: var(--bayan-primary, #18181b);
    }

    .hidden-amount {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      color: var(--bayan-muted-foreground, #71717a);
      font-size: 0.875rem;
    }

    .files-count {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .action-buttons {
      display: flex;
      gap: 0.25rem;
    }

    /* Late Bids Panel */
    :host ::ng-deep .late-bids-panel {
      margin-top: 1rem;
    }

    :host ::ng-deep .late-bids-panel .p-panel-header {
      background-color: var(--bayan-warning-bg, #fffbeb);
      border-color: #ffcc02;
    }

    .late-bids-header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: #d97706;
      font-weight: 600;
    }

    .late-bids-list {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .late-bid-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem;
      background-color: #fff;
      border: 1px solid var(--bayan-border, #e4e4e7);
      border-radius: var(--bayan-radius, 0.5rem);
      flex-wrap: wrap;
      gap: 1rem;
    }

    .late-bid-info {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .late-bid-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .late-bid-meta {
      display: flex;
      gap: 1rem;
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .late-bid-meta span {
      display: flex;
      align-items: center;
      gap: 0.25rem;
    }

    .late-bid-actions {
      display: flex;
      gap: 0.5rem;
    }

    @media (max-width: 768px) {
      .bids-header {
        flex-direction: column;
        align-items: stretch;
      }

      .header-actions {
        justify-content: center;
      }

      .late-bid-item {
        flex-direction: column;
        align-items: stretch;
      }

      .late-bid-actions {
        justify-content: flex-end;
      }
    }
  `]
})
export class BidsTabComponent implements OnInit, OnDestroy {
  @Input() tenderId!: number;

  readonly bidService = inject(BidService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly destroy$ = new Subject<void>();

  // Data signals
  bids = signal<BidListItem[]>([]);
  statistics = signal<BidStatistics | null>(null);

  // Selection
  selectedBids: BidListItem[] = [];

  // Dialog states
  showOpenBidsDialog = false;
  showBidDetailsDialog = false;
  showRejectDialog = false;
  showImportDialog = false;
  selectedBidId: number | null = null;
  selectedLateBid: BidListItem | null = null;
  selectedImportBidId: number | null = null;

  // Loading states
  isDownloading = signal<boolean>(false);

  // Computed
  regularBids = computed(() => this.bids().filter(b => !b.isLate));
  lateBids = computed(() => this.bids().filter(b => b.isLate));

  ngOnInit(): void {
    this.loadData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadData(): void {
    forkJoin({
      bids: this.bidService.getBids(this.tenderId),
      statistics: this.bidService.getStatistics(this.tenderId)
    }).pipe(takeUntil(this.destroy$)).subscribe({
      next: (result) => {
        this.bids.set(result.bids.items);
        this.statistics.set(result.statistics);
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to load bids'
        });
      }
    });
  }

  getStatusLabel(status: BidStatus): string {
    return BID_STATUS_CONFIG[status]?.label || status;
  }

  getStatusSeverity(status: BidStatus): 'secondary' | 'success' | 'info' | 'warn' | 'danger' | 'contrast' {
    return BID_STATUS_CONFIG[status]?.severity || 'secondary';
  }

  viewBidDetails(bid: BidListItem): void {
    this.selectedBidId = bid.id;
    this.showBidDetailsDialog = true;
  }

  downloadBidFiles(bid: BidListItem): void {
    this.bidService.downloadBidFiles(this.tenderId, bid.id).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (blob) => {
        // Trigger download
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bid_${bid.id}_files.zip`;
        a.click();
        window.URL.revokeObjectURL(url);

        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Files downloaded successfully'
        });
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to download files'
        });
      }
    });
  }

  downloadAllBids(): void {
    this.isDownloading.set(true);

    this.bidService.downloadAllBids(this.tenderId).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (blob) => {
        this.isDownloading.set(false);

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tender_${this.tenderId}_all_bids.zip`;
        a.click();
        window.URL.revokeObjectURL(url);

        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'All bids downloaded successfully'
        });
      },
      error: (error) => {
        this.isDownloading.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to download bids'
        });
      }
    });
  }

  importBoq(bid: BidListItem): void {
    this.selectedImportBidId = bid.id;
    this.showImportDialog = true;
  }

  onImportWizardComplete(result: any): void {
    this.showImportDialog = false;
    this.selectedImportBidId = null;
    this.messageService.add({
      severity: 'success',
      summary: 'Import Complete',
      detail: `BOQ imported successfully — ${result.importedCount || 0} items`
    });
    this.loadData();
  }

  onOpenBidsConfirmed(): void {
    this.bidService.openBids(this.tenderId).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (response) => {
        this.showOpenBidsDialog = false;
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: `${response.openedCount} bids opened successfully`
        });
        this.loadData();
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to open bids'
        });
      }
    });
  }

  acceptLateBid(bid: BidListItem): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to accept the late bid from ${bid.bidderName}?`,
      header: 'Accept Late Bid',
      icon: 'pi pi-check',
      acceptButtonStyleClass: 'p-button-success',
      accept: () => {
        this.bidService.acceptLateBid(this.tenderId, bid.id).pipe(
          takeUntil(this.destroy$)
        ).subscribe({
          next: () => {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Late bid accepted'
            });
            this.loadData();
          },
          error: (error) => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: error.message || 'Failed to accept late bid'
            });
          }
        });
      }
    });
  }

  openRejectDialog(bid: BidListItem): void {
    this.selectedLateBid = bid;
    this.showRejectDialog = true;
  }

  onLateBidRejected(reason: string): void {
    if (!this.selectedLateBid) return;

    this.bidService.rejectLateBid(this.tenderId, this.selectedLateBid.id, { reason }).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: () => {
        this.showRejectDialog = false;
        this.selectedLateBid = null;
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Late bid rejected'
        });
        this.loadData();
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to reject late bid'
        });
      }
    });
  }

  onBidImported(bidId: number): void {
    this.showBidDetailsDialog = false;
    this.messageService.add({
      severity: 'success',
      summary: 'Success',
      detail: 'BOQ imported successfully'
    });
    this.loadData();
  }

  onBidDisqualified(bidId: number): void {
    this.showBidDetailsDialog = false;
    this.messageService.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Bid disqualified'
    });
    this.loadData();
  }
}
