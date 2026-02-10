import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ToastModule } from 'primeng/toast';
import { ConfirmationService, MessageService } from 'primeng/api';
import { DialogService, DynamicDialog } from 'primeng/dynamicdialog';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { MultiSelectModule } from 'primeng/multiselect';
import {
  Bidder,
  PrequalificationStatus,
  TradeSpecialization,
  NdaStatus
} from '../../../core/models/bidder.model';
import { BidderService } from '../../../core/services/bidder.service';
import { BidderFormDialogComponent, BidderFormDialogData } from './bidder-form-dialog.component';

@Component({
  selector: 'app-bidder-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    CardModule,
    ButtonModule,
    InputTextModule,
    DropdownModule,
    TagModule,
    TooltipModule,
    ConfirmDialogModule,
    ToastModule,
    DynamicDialog,
    IconFieldModule,
    InputIconModule,
    MultiSelectModule
  ],
  providers: [ConfirmationService, MessageService, DialogService],
  template: `
    <p-toast></p-toast>
    <div class="bidder-list-container" data-testid="bidder-list">
      <div class="page-header">
        <div>
          <h1>Bidder Management</h1>
          <p>Manage registered bidders and their prequalification status</p>
        </div>
        <button pButton label="Add Bidder" icon="pi pi-plus" (click)="showBidderDialog()" data-testid="create-bidder-btn"></button>
      </div>

      <!-- Filters -->
      <p-card styleClass="filter-card">
        <div class="filters">
          <p-iconField iconPosition="left" class="search-field">
            <p-inputIcon styleClass="pi pi-search"></p-inputIcon>
            <input
              pInputText
              type="text"
              [(ngModel)]="searchTerm"
              placeholder="Search by company name, email, or CR number..."
              (input)="onSearch()"
              data-testid="bidder-search"
            />
          </p-iconField>

          <p-dropdown
            [options]="tradeOptions"
            [(ngModel)]="selectedTrade"
            placeholder="Filter by Trade"
            [showClear]="true"
            (onChange)="onFilter()"
          ></p-dropdown>

          <p-dropdown
            [options]="prequalificationOptions"
            [(ngModel)]="selectedPrequalification"
            placeholder="Prequalification Status"
            [showClear]="true"
            (onChange)="onFilter()"
          ></p-dropdown>

          <button
            pButton
            icon="pi pi-filter-slash"
            label="Clear"
            class="p-button-outlined p-button-secondary"
            (click)="clearFilters()"
          ></button>
        </div>
      </p-card>

      <!-- Bidders Table -->
      <p-card styleClass="table-card">
        <p-table
          data-testid="bidder-table"
          [value]="filteredBidders()"
          [paginator]="true"
          [rows]="10"
          [showCurrentPageReport]="true"
          currentPageReportTemplate="Showing {first} to {last} of {totalRecords} bidders"
          [rowsPerPageOptions]="[10, 25, 50]"
          [loading]="isLoading()"
          styleClass="p-datatable-striped"
        >
          <ng-template pTemplate="header">
            <tr>
              <th pSortableColumn="companyNameEn">Company Name <p-sortIcon field="companyNameEn"></p-sortIcon></th>
              <th pSortableColumn="email">Email <p-sortIcon field="email"></p-sortIcon></th>
              <th>Trade Specialization</th>
              <th pSortableColumn="prequalificationStatus">Prequalification <p-sortIcon field="prequalificationStatus"></p-sortIcon></th>
              <th pSortableColumn="ndaStatus">NDA Status <p-sortIcon field="ndaStatus"></p-sortIcon></th>
              <th>Actions</th>
            </tr>
          </ng-template>
          <ng-template pTemplate="body" let-bidder>
            <tr>
              <td>
                <div class="company-info">
                  <div class="company-avatar">{{ getCompanyInitials(bidder) }}</div>
                  <div class="company-details">
                    <span class="company-name">{{ bidder.companyNameEn }}</span>
                    @if (bidder.companyNameAr) {
                      <span class="company-name-ar">{{ bidder.companyNameAr }}</span>
                    }
                    @if (bidder.crNumber) {
                      <span class="cr-number">CR: {{ bidder.crNumber }}</span>
                    }
                  </div>
                </div>
              </td>
              <td>
                <div class="contact-info">
                  <span>{{ bidder.email }}</span>
                  @if (bidder.phone) {
                    <span class="phone">{{ bidder.phone }}</span>
                  }
                </div>
              </td>
              <td>
                <div class="trade-tags">
                  @for (trade of bidder.tradeSpecializations.slice(0, 2); track trade) {
                    <p-tag [value]="getTradeLabel(trade)" severity="info" styleClass="trade-tag"></p-tag>
                  }
                  @if (bidder.tradeSpecializations.length > 2) {
                    <span class="more-trades" [pTooltip]="getAllTradesLabel(bidder.tradeSpecializations)">
                      +{{ bidder.tradeSpecializations.length - 2 }} more
                    </span>
                  }
                </div>
              </td>
              <td>
                <p-tag
                  [value]="getPrequalificationLabel(bidder.prequalificationStatus)"
                  [severity]="getPrequalificationSeverity(bidder.prequalificationStatus)"
                ></p-tag>
              </td>
              <td>
                <p-tag
                  [value]="getNdaLabel(bidder.ndaStatus)"
                  [severity]="getNdaSeverity(bidder.ndaStatus)"
                ></p-tag>
              </td>
              <td>
                <div class="action-buttons">
                  <button
                    pButton
                    icon="pi pi-eye"
                    class="p-button-text p-button-sm"
                    pTooltip="View Details"
                    tooltipPosition="top"
                    (click)="viewBidder(bidder)"
                  ></button>
                  <button
                    pButton
                    icon="pi pi-pencil"
                    class="p-button-text p-button-sm"
                    pTooltip="Edit Bidder"
                    tooltipPosition="top"
                    (click)="editBidder(bidder)"
                  ></button>
                  <button
                    pButton
                    [icon]="bidder.isActive ? 'pi pi-ban' : 'pi pi-check'"
                    class="p-button-text p-button-sm"
                    [class.p-button-warning]="bidder.isActive"
                    [class.p-button-success]="!bidder.isActive"
                    [pTooltip]="bidder.isActive ? 'Deactivate' : 'Activate'"
                    tooltipPosition="top"
                    (click)="toggleBidderStatus(bidder)"
                  ></button>
                  <button
                    pButton
                    icon="pi pi-trash"
                    class="p-button-text p-button-sm p-button-danger"
                    pTooltip="Delete Bidder"
                    tooltipPosition="top"
                    (click)="confirmDelete(bidder)"
                  ></button>
                </div>
              </td>
            </tr>
          </ng-template>
          <ng-template pTemplate="emptymessage">
            <tr>
              <td colspan="6" class="text-center p-4">
                <div class="empty-state">
                  <i class="pi pi-building" style="font-size: 3rem; color: var(--bayan-muted-foreground, #71717a);"></i>
                  <p>No bidders found.</p>
                  <button pButton label="Add First Bidder" icon="pi pi-plus" class="p-button-outlined" (click)="showBidderDialog()"></button>
                </div>
              </td>
            </tr>
          </ng-template>
        </p-table>
      </p-card>

      <p-confirmDialog></p-confirmDialog>
    </div>
  `,
  styles: [`
    .bidder-list-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .page-header h1 {
      margin: 0;
      font-size: 1.75rem;
      color: var(--bayan-foreground, #09090b);
    }

    .page-header p {
      margin: 0.25rem 0 0;
      color: var(--bayan-muted-foreground, #71717a);
    }

    :host ::ng-deep .filter-card .p-card-body {
      padding: 1rem;
    }

    .filters {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      align-items: center;
    }

    .search-field {
      flex: 1;
      min-width: 300px;
    }

    .search-field input {
      width: 100%;
    }

    :host ::ng-deep .table-card {
      .p-card-body {
        padding: 0;
      }

      .p-card-content {
        padding: 0;
      }
    }

    .company-info {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .company-avatar {
      width: 40px;
      height: 40px;
      border-radius: var(--bayan-radius, 0.5rem);
      background: var(--bayan-primary, #18181b);
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.875rem;
      font-weight: 600;
    }

    .company-details {
      display: flex;
      flex-direction: column;
    }

    .company-name {
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
    }

    .company-name-ar {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
      direction: rtl;
    }

    .cr-number {
      font-size: 0.75rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .contact-info {
      display: flex;
      flex-direction: column;
    }

    .contact-info .phone {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .trade-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 0.25rem;
      align-items: center;
    }

    :host ::ng-deep .trade-tag {
      font-size: 0.75rem;
    }

    .more-trades {
      font-size: 0.75rem;
      color: var(--bayan-primary, #18181b);
      cursor: pointer;
    }

    .action-buttons {
      display: flex;
      gap: 0.25rem;
    }

    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      padding: 3rem;
    }

    .empty-state p {
      color: var(--bayan-muted-foreground, #71717a);
      margin: 0;
    }

    @media (max-width: 768px) {
      .filters {
        flex-direction: column;
      }

      .search-field {
        width: 100%;
        min-width: unset;
      }
    }
  `]
})
export class BidderListComponent implements OnInit {
  private readonly bidderService = inject(BidderService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly messageService = inject(MessageService);
  private readonly dialogService = inject(DialogService);

  bidders = signal<Bidder[]>([]);
  filteredBidders = signal<Bidder[]>([]);
  isLoading = this.bidderService.isLoading;

  searchTerm = '';
  selectedTrade: TradeSpecialization | null = null;
  selectedPrequalification: PrequalificationStatus | null = null;

  tradeOptions = [
    { label: 'IT Services', value: TradeSpecialization.IT_SERVICES },
    { label: 'Construction', value: TradeSpecialization.CONSTRUCTION },
    { label: 'Consulting', value: TradeSpecialization.CONSULTING },
    { label: 'Supplies', value: TradeSpecialization.SUPPLIES },
    { label: 'Maintenance', value: TradeSpecialization.MAINTENANCE },
    { label: 'Security', value: TradeSpecialization.SECURITY },
    { label: 'Logistics', value: TradeSpecialization.LOGISTICS },
    { label: 'Healthcare', value: TradeSpecialization.HEALTHCARE },
    { label: 'Education', value: TradeSpecialization.EDUCATION },
    { label: 'Financial', value: TradeSpecialization.FINANCIAL },
    { label: 'Engineering', value: TradeSpecialization.ENGINEERING },
    { label: 'Telecommunications', value: TradeSpecialization.TELECOMMUNICATIONS },
    { label: 'Other', value: TradeSpecialization.OTHER }
  ];

  prequalificationOptions = [
    { label: 'Pending', value: PrequalificationStatus.PENDING },
    { label: 'Approved', value: PrequalificationStatus.APPROVED },
    { label: 'Rejected', value: PrequalificationStatus.REJECTED }
  ];

  ngOnInit(): void {
    this.loadBidders();
  }

  private loadBidders(): void {
    this.bidderService.getBidders({
      page: 1,
      pageSize: 1000
    }).subscribe({
      next: (response) => {
        const items = response?.items || [];
        this.bidders.set(items);
        this.filteredBidders.set(items);
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load bidders from the server'
        });
      }
    });
  }

  onSearch(): void {
    this.applyFilters();
  }

  onFilter(): void {
    this.applyFilters();
  }

  private applyFilters(): void {
    let result = [...this.bidders()];

    if (this.searchTerm) {
      const term = this.searchTerm.toLowerCase();
      result = result.filter(b =>
        b.companyNameEn.toLowerCase().includes(term) ||
        (b.companyNameAr && b.companyNameAr.includes(term)) ||
        b.email.toLowerCase().includes(term) ||
        (b.crNumber && b.crNumber.toLowerCase().includes(term))
      );
    }

    if (this.selectedTrade) {
      result = result.filter(b => b.tradeSpecializations.includes(this.selectedTrade!));
    }

    if (this.selectedPrequalification) {
      result = result.filter(b => b.prequalificationStatus === this.selectedPrequalification);
    }

    this.filteredBidders.set(result);
  }

  clearFilters(): void {
    this.searchTerm = '';
    this.selectedTrade = null;
    this.selectedPrequalification = null;
    this.filteredBidders.set(this.bidders());
  }

  showBidderDialog(bidder?: Bidder): void {
    const dialogData: BidderFormDialogData = {
      bidder,
      mode: bidder ? 'edit' : 'create'
    };

    const ref = this.dialogService.open(BidderFormDialogComponent, {
      header: bidder ? 'Edit Bidder' : 'Add New Bidder',
      width: '700px',
      contentStyle: { overflow: 'auto' },
      data: dialogData
    });

    ref.onClose.subscribe((result: Bidder | undefined) => {
      if (result) {
        if (bidder) {
          this.bidders.update(bidders =>
            bidders.map(b => b.id === result.id ? result : b)
          );
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Bidder updated successfully'
          });
        } else {
          this.bidders.update(bidders => [...bidders, result]);
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Bidder created successfully'
          });
        }
        this.applyFilters();
      }
    });
  }

  viewBidder(bidder: Bidder): void {
    // For now, open edit dialog in view mode - could be a separate detail view
    this.editBidder(bidder);
  }

  editBidder(bidder: Bidder): void {
    this.showBidderDialog(bidder);
  }

  toggleBidderStatus(bidder: Bidder): void {
    const newStatus = !bidder.isActive;
    const action = newStatus ? 'activate' : 'deactivate';

    this.confirmationService.confirm({
      message: `Are you sure you want to ${action} ${bidder.companyNameEn}?`,
      header: `Confirm ${action.charAt(0).toUpperCase() + action.slice(1)}`,
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.bidderService.toggleBidderStatus(bidder.id, newStatus).subscribe({
          next: () => {
            this.bidders.update(bidders =>
              bidders.map(b => b.id === bidder.id ? { ...b, isActive: newStatus } : b)
            );
            this.applyFilters();
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: `Bidder ${newStatus ? 'activated' : 'deactivated'} successfully`
            });
          },
          error: (err) => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: err.message || `Failed to ${action} bidder`
            });
          }
        });
      }
    });
  }

  confirmDelete(bidder: Bidder): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete ${bidder.companyNameEn}? This action cannot be undone.`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.bidderService.deleteBidder(bidder.id).subscribe({
          next: () => {
            this.bidders.update(bidders => bidders.filter(b => b.id !== bidder.id));
            this.applyFilters();
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Bidder deleted successfully'
            });
          },
          error: (err) => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: err.message || 'Failed to delete bidder'
            });
          }
        });
      }
    });
  }

  getCompanyInitials(bidder: Bidder): string {
    const words = bidder.companyNameEn.split(' ');
    if (words.length >= 2) {
      return `${words[0].charAt(0)}${words[1].charAt(0)}`.toUpperCase();
    }
    return bidder.companyNameEn.substring(0, 2).toUpperCase();
  }

  getTradeLabel(trade: TradeSpecialization): string {
    const option = this.tradeOptions.find(o => o.value === trade);
    return option?.label || trade;
  }

  getAllTradesLabel(trades: TradeSpecialization[]): string {
    return trades.map(t => this.getTradeLabel(t)).join(', ');
  }

  getPrequalificationLabel(status: PrequalificationStatus): string {
    const labels: Record<PrequalificationStatus, string> = {
      [PrequalificationStatus.PENDING]: 'Pending',
      [PrequalificationStatus.APPROVED]: 'Approved',
      [PrequalificationStatus.REJECTED]: 'Rejected'
    };
    return labels[status];
  }

  getPrequalificationSeverity(status: PrequalificationStatus): 'success' | 'secondary' | 'info' | 'warn' | 'danger' | 'contrast' | undefined {
    const severities: Record<PrequalificationStatus, 'success' | 'warn' | 'danger'> = {
      [PrequalificationStatus.PENDING]: 'warn',
      [PrequalificationStatus.APPROVED]: 'success',
      [PrequalificationStatus.REJECTED]: 'danger'
    };
    return severities[status];
  }

  getNdaLabel(status: NdaStatus): string {
    const labels: Record<NdaStatus, string> = {
      [NdaStatus.NOT_SENT]: 'Not Sent',
      [NdaStatus.SENT]: 'Sent',
      [NdaStatus.SIGNED]: 'Signed',
      [NdaStatus.EXPIRED]: 'Expired'
    };
    return labels[status];
  }

  getNdaSeverity(status: NdaStatus): 'success' | 'secondary' | 'info' | 'warn' | 'danger' | 'contrast' | undefined {
    const severities: Record<NdaStatus, 'success' | 'secondary' | 'info' | 'warn' | 'danger'> = {
      [NdaStatus.NOT_SENT]: 'secondary',
      [NdaStatus.SENT]: 'info',
      [NdaStatus.SIGNED]: 'success',
      [NdaStatus.EXPIRED]: 'danger'
    };
    return severities[status];
  }
}
