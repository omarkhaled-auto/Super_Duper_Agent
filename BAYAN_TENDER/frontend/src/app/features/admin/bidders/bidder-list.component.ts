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
    <div class="bidder-list-container">
      <div class="page-header">
        <div>
          <h1>Bidder Management</h1>
          <p>Manage registered bidders and their prequalification status</p>
        </div>
        <button pButton label="Add Bidder" icon="pi pi-plus" (click)="showBidderDialog()"></button>
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
                  <i class="pi pi-building" style="font-size: 3rem; color: #ccc;"></i>
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
      color: #333;
    }

    .page-header p {
      margin: 0.25rem 0 0;
      color: #666;
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
      border-radius: 8px;
      background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%);
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
      color: #333;
    }

    .company-name-ar {
      font-size: 0.875rem;
      color: #666;
      direction: rtl;
    }

    .cr-number {
      font-size: 0.75rem;
      color: #888;
    }

    .contact-info {
      display: flex;
      flex-direction: column;
    }

    .contact-info .phone {
      font-size: 0.875rem;
      color: #666;
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
      color: #1976D2;
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
      padding: 2rem;
    }

    .empty-state p {
      color: #666;
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
    // Mock data for demonstration - in production, fetch from API
    const mockBidders: Bidder[] = [
      {
        id: 1,
        companyNameEn: 'Tech Solutions Ltd',
        companyNameAr: 'حلول تقنية المحدودة',
        email: 'info@techsolutions.sa',
        phone: '+966 11 234 5678',
        crNumber: '1010123456',
        address: 'Riyadh, King Fahd Road',
        tradeSpecializations: [TradeSpecialization.IT_SERVICES, TradeSpecialization.TELECOMMUNICATIONS],
        prequalificationStatus: PrequalificationStatus.APPROVED,
        ndaStatus: NdaStatus.SIGNED,
        contactPersonName: 'Ahmed Al-Rashid',
        contactPersonEmail: 'ahmed@techsolutions.sa',
        contactPersonPhone: '+966 50 123 4567',
        isActive: true,
        createdAt: new Date('2025-01-15'),
        updatedAt: new Date('2026-01-20'),
        tendersCount: 15,
        activeTendersCount: 3
      },
      {
        id: 2,
        companyNameEn: 'Al-Bina Construction',
        companyNameAr: 'البناء للمقاولات',
        email: 'contact@albina.sa',
        phone: '+966 12 345 6789',
        crNumber: '1010234567',
        address: 'Jeddah, Al-Madinah Road',
        tradeSpecializations: [TradeSpecialization.CONSTRUCTION, TradeSpecialization.ENGINEERING, TradeSpecialization.MAINTENANCE],
        prequalificationStatus: PrequalificationStatus.APPROVED,
        ndaStatus: NdaStatus.SIGNED,
        contactPersonName: 'Mohammed Al-Harbi',
        contactPersonEmail: 'mohammed@albina.sa',
        contactPersonPhone: '+966 55 234 5678',
        isActive: true,
        createdAt: new Date('2025-03-20'),
        updatedAt: new Date('2026-01-25'),
        tendersCount: 8,
        activeTendersCount: 2
      },
      {
        id: 3,
        companyNameEn: 'Global Supplies Co',
        email: 'sales@globalsupplies.sa',
        phone: '+966 13 456 7890',
        crNumber: '1010345678',
        tradeSpecializations: [TradeSpecialization.SUPPLIES, TradeSpecialization.LOGISTICS],
        prequalificationStatus: PrequalificationStatus.PENDING,
        ndaStatus: NdaStatus.SENT,
        contactPersonName: 'Sara Al-Otaibi',
        contactPersonEmail: 'sara@globalsupplies.sa',
        isActive: true,
        createdAt: new Date('2025-06-10'),
        updatedAt: new Date('2026-02-01'),
        tendersCount: 0,
        activeTendersCount: 0
      },
      {
        id: 4,
        companyNameEn: 'Security First Services',
        companyNameAr: 'الأمان أولا للخدمات',
        email: 'info@securityfirst.sa',
        phone: '+966 11 567 8901',
        crNumber: '1010456789',
        tradeSpecializations: [TradeSpecialization.SECURITY],
        prequalificationStatus: PrequalificationStatus.REJECTED,
        ndaStatus: NdaStatus.NOT_SENT,
        isActive: false,
        createdAt: new Date('2025-08-15'),
        updatedAt: new Date('2026-01-10'),
        tendersCount: 2,
        activeTendersCount: 0
      },
      {
        id: 5,
        companyNameEn: 'Strategic Consulting Group',
        email: 'hello@strategicconsulting.sa',
        crNumber: '1010567890',
        tradeSpecializations: [TradeSpecialization.CONSULTING, TradeSpecialization.FINANCIAL],
        prequalificationStatus: PrequalificationStatus.APPROVED,
        ndaStatus: NdaStatus.SIGNED,
        contactPersonName: 'Khalid Al-Faisal',
        contactPersonEmail: 'khalid@strategicconsulting.sa',
        contactPersonPhone: '+966 54 567 8901',
        isActive: true,
        createdAt: new Date('2025-10-01'),
        updatedAt: new Date('2026-02-03'),
        tendersCount: 5,
        activeTendersCount: 1
      }
    ];

    this.bidders.set(mockBidders);
    this.filteredBidders.set(mockBidders);
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
        // In production: this.bidderService.toggleBidderStatus(bidder.id, newStatus)
        this.bidders.update(bidders =>
          bidders.map(b => b.id === bidder.id ? { ...b, isActive: newStatus } : b)
        );
        this.applyFilters();
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: `Bidder ${newStatus ? 'activated' : 'deactivated'} successfully`
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
        // In production: this.bidderService.deleteBidder(bidder.id)
        this.bidders.update(bidders => bidders.filter(b => b.id !== bidder.id));
        this.applyFilters();
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Bidder deleted successfully'
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
