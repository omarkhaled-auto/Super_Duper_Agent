import { Component, inject, OnInit, OnDestroy, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Subject, debounceTime, distinctUntilChanged, takeUntil } from 'rxjs';
import { TableModule, TableLazyLoadEvent } from 'primeng/table';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { PanelModule } from 'primeng/panel';
import { CheckboxModule } from 'primeng/checkbox';
import { DatePickerModule } from 'primeng/datepicker';
import { MultiSelectModule } from 'primeng/multiselect';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';

import { AuthService } from '../../../core/auth/auth.service';
import { TenderService, TenderQueryParams } from '../../../core/services/tender.service';
import { ClientService } from '../../../core/services/client.service';
import {
  TenderListItem,
  TenderStatus,
  Currency,
  TENDER_STATUS_CONFIG,
  CURRENCY_OPTIONS
} from '../../../core/models/tender.model';
import { Client } from '../../../core/models/client.model';
import { UserRole } from '../../../core/models/user.model';

interface StatusOption {
  label: string;
  value: TenderStatus;
  selected: boolean;
}

@Component({
  selector: 'app-tender-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    TableModule,
    CardModule,
    ButtonModule,
    InputTextModule,
    DropdownModule,
    TagModule,
    TooltipModule,
    IconFieldModule,
    InputIconModule,
    PanelModule,
    CheckboxModule,
    DatePickerModule,
    MultiSelectModule,
    ProgressSpinnerModule,
    MessageModule
  ],
  template: `
    <div class="tender-list-container">
      <div class="page-header">
        <div class="header-content">
          <h1>Tenders</h1>
          <p>Manage and track your tender submissions</p>
        </div>
        <div class="header-actions">
          <button
            pButton
            icon="pi pi-file-excel"
            label="Export"
            class="p-button-outlined"
            data-testid="export-btn"
            (click)="exportToExcel()"
            [loading]="exporting()"
          ></button>
          @if (canManageTenders()) {
            <button
              pButton
              icon="pi pi-plus"
              label="New Tender"
              data-testid="new-tender-btn"
              (click)="navigateToNewTender()"
            ></button>
          }
        </div>
      </div>

      <!-- Search Bar -->
      <p-card styleClass="search-card">
        <p-iconField iconPosition="left" class="search-field">
          <p-inputIcon styleClass="pi pi-search"></p-inputIcon>
          <input
            pInputText
            type="text"
            [(ngModel)]="searchTerm"
            placeholder="Search by title, reference, or client..."
            data-testid="tender-search"
            (input)="onSearchInput()"
          />
        </p-iconField>
      </p-card>

      <!-- Filters Panel -->
      <p-panel
        header="Advanced Filters"
        [toggleable]="true"
        [collapsed]="filtersCollapsed"
        (collapsedChange)="filtersCollapsed = $event"
        styleClass="filter-panel"
      >
        <div class="filters-grid">
          <!-- Status Checkboxes -->
          <div class="filter-group">
            <label class="filter-label">Status</label>
            <div class="status-checkboxes">
              @for (status of statusOptions; track status.value) {
                <div class="status-checkbox">
                  <p-checkbox
                    [(ngModel)]="status.selected"
                    [binary]="true"
                    [inputId]="'status-' + status.value"
                    (onChange)="onFilterChange()"
                  ></p-checkbox>
                  <label [for]="'status-' + status.value">
                    <p-tag
                      [value]="status.label"
                      [severity]="getStatusSeverity(status.value)"
                    ></p-tag>
                  </label>
                </div>
              }
            </div>
          </div>

          <!-- Date Range -->
          <div class="filter-group">
            <label class="filter-label">Deadline Range</label>
            <div class="date-range">
              <p-datepicker
                [(ngModel)]="dateFrom"
                placeholder="From"
                [showIcon]="true"
                [showButtonBar]="true"
                dateFormat="dd/mm/yy"
                (onSelect)="onFilterChange()"
                (onClear)="onFilterChange()"
              ></p-datepicker>
              <span class="date-separator">to</span>
              <p-datepicker
                [(ngModel)]="dateTo"
                placeholder="To"
                [showIcon]="true"
                [showButtonBar]="true"
                dateFormat="dd/mm/yy"
                [minDate]="dateFrom"
                (onSelect)="onFilterChange()"
                (onClear)="onFilterChange()"
              ></p-datepicker>
            </div>
          </div>

          <!-- Client Dropdown -->
          <div class="filter-group">
            <label class="filter-label">Client</label>
            <p-dropdown
              [options]="clients()"
              [(ngModel)]="selectedClientId"
              optionLabel="name"
              optionValue="id"
              placeholder="Select Client"
              [filter]="true"
              filterPlaceholder="Search clients..."
              [showClear]="true"
              (onChange)="onFilterChange()"
              styleClass="w-full"
            ></p-dropdown>
          </div>

          <!-- Currency Dropdown -->
          <div class="filter-group">
            <label class="filter-label">Currency</label>
            <p-dropdown
              [options]="currencyOptions"
              [(ngModel)]="selectedCurrency"
              optionLabel="label"
              optionValue="value"
              placeholder="Select Currency"
              [showClear]="true"
              (onChange)="onFilterChange()"
              styleClass="w-full"
            ></p-dropdown>
          </div>
        </div>

        <div class="filter-actions">
          <button
            pButton
            icon="pi pi-filter-slash"
            label="Clear All Filters"
            class="p-button-text"
            (click)="clearFilters()"
          ></button>
          <span class="active-filters" *ngIf="activeFilterCount() > 0">
            {{ activeFilterCount() }} filter(s) active
          </span>
        </div>
      </p-panel>

      <!-- Error Message -->
      @if (tenderService.error()) {
        <p-message
          severity="error"
          [text]="tenderService.error()!"
          styleClass="w-full"
        ></p-message>
      }

      <!-- Tender Table -->
      <p-card styleClass="table-card">
        <p-table
          [value]="tenders()"
          [lazy]="true"
          (onLazyLoad)="loadTenders($event)"
          [paginator]="true"
          [rows]="pageSize"
          [totalRecords]="totalRecords()"
          [loading]="tenderService.isLoading()"
          [showCurrentPageReport]="true"
          currentPageReportTemplate="Showing {first} to {last} of {totalRecords} tenders"
          [rowsPerPageOptions]="[10, 25, 50]"
          styleClass="p-datatable-striped p-datatable-gridlines"
          [rowHover]="true"
          (onRowSelect)="onRowSelect($event)"
          selectionMode="single"
        >
          <ng-template pTemplate="header">
            <tr>
              <th pSortableColumn="title" style="width: 25%">
                Tender Name
                <p-sortIcon field="title"></p-sortIcon>
              </th>
              <th pSortableColumn="clientName" style="width: 15%">
                Client
                <p-sortIcon field="clientName"></p-sortIcon>
              </th>
              <th pSortableColumn="reference" style="width: 12%">
                Reference
                <p-sortIcon field="reference"></p-sortIcon>
              </th>
              <th pSortableColumn="submissionDeadline" style="width: 12%">
                Deadline
                <p-sortIcon field="submissionDeadline"></p-sortIcon>
              </th>
              <th pSortableColumn="status" style="width: 10%">
                Status
                <p-sortIcon field="status"></p-sortIcon>
              </th>
              <th style="width: 10%">Bids</th>
              <th style="width: 16%">Actions</th>
            </tr>
          </ng-template>

          <ng-template pTemplate="body" let-tender>
            <tr (click)="navigateToDetails(tender.id)" class="clickable-row">
              <td>
                <div class="tender-title">
                  <span class="title-text" [pTooltip]="tender.title" tooltipPosition="top">
                    {{ tender.title | slice:0:50 }}{{ tender.title.length > 50 ? '...' : '' }}
                  </span>
                  @if (tender.estimatedValue) {
                    <span class="estimated-value">
                      {{ tender.currency }} {{ tender.estimatedValue | number:'1.0-0' }}
                    </span>
                  }
                </div>
              </td>
              <td>{{ tender.clientName }}</td>
              <td>
                <span class="reference-badge">{{ tender.reference }}</span>
              </td>
              <td>
                <div class="deadline-cell">
                  <span>{{ tender.submissionDeadline | date:'mediumDate' }}</span>
                  @if (getDaysRemaining(tender.submissionDeadline) !== null) {
                    <span
                      class="days-badge"
                      [class.urgent]="getDaysRemaining(tender.submissionDeadline)! <= 7"
                      [class.warning]="getDaysRemaining(tender.submissionDeadline)! > 7 && getDaysRemaining(tender.submissionDeadline)! <= 14"
                    >
                      {{ getDaysRemaining(tender.submissionDeadline) }} days
                    </span>
                  }
                </div>
              </td>
              <td>
                <p-tag
                  [value]="getStatusLabel(tender.status)"
                  [severity]="getStatusSeverity(tender.status)"
                ></p-tag>
              </td>
              <td>
                <div class="bids-cell">
                  <span class="bids-count">{{ tender.submittedBidsCount }}/{{ tender.invitedBiddersCount }}</span>
                  <span class="bids-label">submitted</span>
                </div>
              </td>
              <td>
                <div class="action-buttons" (click)="$event.stopPropagation()">
                  <button
                    pButton
                    icon="pi pi-eye"
                    class="p-button-rounded p-button-text p-button-sm"
                    pTooltip="View Details"
                    tooltipPosition="top"
                    (click)="navigateToDetails(tender.id)"
                  ></button>
                  @if (canManageTenders()) {
                    <button
                      pButton
                      icon="pi pi-pencil"
                      class="p-button-rounded p-button-text p-button-sm"
                      pTooltip="Edit"
                      tooltipPosition="top"
                      (click)="navigateToEdit(tender.id)"
                      [disabled]="tender.status !== 'draft'"
                    ></button>
                    <button
                      pButton
                      icon="pi pi-copy"
                      class="p-button-rounded p-button-text p-button-sm"
                      pTooltip="Duplicate"
                      tooltipPosition="top"
                      (click)="duplicateTender(tender)"
                    ></button>
                  }
                </div>
              </td>
            </tr>
          </ng-template>

          <ng-template pTemplate="emptymessage">
            <tr>
              <td colspan="7" class="text-center p-4">
                <div class="empty-state">
                  <i class="pi pi-inbox" style="font-size: 3rem; color: var(--bayan-slate-300, #CBD5E1);"></i>
                  <p>No tenders found matching your criteria.</p>
                  @if (canManageTenders()) {
                    <button
                      pButton
                      label="Create New Tender"
                      icon="pi pi-plus"
                      class="p-button-outlined"
                      (click)="navigateToNewTender()"
                    ></button>
                  }
                </div>
              </td>
            </tr>
          </ng-template>

          <ng-template pTemplate="loadingbody">
            <tr>
              <td colspan="7" class="text-center p-4">
                <p-progressSpinner
                  [style]="{ width: '50px', height: '50px' }"
                  strokeWidth="4"
                ></p-progressSpinner>
                <p class="mt-2">Loading tenders...</p>
              </td>
            </tr>
          </ng-template>
        </p-table>
      </p-card>
    </div>
  `,
  styles: [`
    .tender-list-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 1rem;
    }

    .header-content h1 {
      margin: 0;
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--bayan-slate-900, #0F172A);
    }

    .header-content p {
      margin: 0.25rem 0 0;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .header-actions {
      display: flex;
      gap: 0.75rem;
    }

    :host ::ng-deep .search-card .p-card-body {
      padding: 1rem;
    }

    .search-field {
      width: 100%;
    }

    .search-field input {
      width: 100%;
    }

    :host ::ng-deep .filter-panel {
      .p-panel-header {
        background: var(--bayan-slate-50, #F8FAFC);
        border-radius: var(--bayan-radius-lg, 0.75rem);
      }

      .p-panel-content {
        padding: 1rem;
        background: var(--bayan-slate-50, #F8FAFC);
        border-radius: 0 0 var(--bayan-radius-lg, 0.75rem) var(--bayan-radius-lg, 0.75rem);
      }
    }

    .filters-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 1.5rem;
    }

    .filter-group {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .filter-label {
      font-weight: 600;
      color: var(--bayan-slate-700, #334155);
      font-size: 0.875rem;
    }

    .status-checkboxes {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
    }

    .status-checkbox {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .date-range {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
    }

    .date-separator {
      color: var(--bayan-slate-400, #94A3B8);
    }

    .filter-actions {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid var(--bayan-border, #E2E8F0);
    }

    .active-filters {
      color: var(--bayan-primary, #4F46E5);
      font-size: 0.875rem;
      font-weight: 500;
    }

    :host ::ng-deep .table-card {
      .p-card-body {
        padding: 0;
      }

      .p-card-content {
        padding: 0;
      }
    }

    .clickable-row {
      cursor: pointer;
      transition: background-color var(--bayan-transition, 200ms ease);
    }

    .clickable-row:hover {
      background-color: var(--bayan-primary-light, #EEF2FF) !important;
    }

    .tender-title {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .title-text {
      font-weight: 500;
      color: var(--bayan-slate-900, #0F172A);
    }

    .estimated-value {
      font-size: 0.8rem;
      color: var(--bayan-slate-500, #64748B);
    }

    .reference-badge {
      font-family: monospace;
      background-color: var(--bayan-slate-100, #F1F5F9);
      padding: 0.25rem 0.5rem;
      border-radius: var(--bayan-radius-sm, 0.375rem);
      font-size: 0.875rem;
      color: var(--bayan-slate-700, #334155);
    }

    .deadline-cell {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .days-badge {
      font-size: 0.75rem;
      font-weight: 500;
      padding: 0.125rem 0.5rem;
      border-radius: var(--bayan-radius-full, 9999px);
      background-color: var(--bayan-success-bg, #F0FDF4);
      color: var(--bayan-success, #16A34A);
      width: fit-content;
    }

    .days-badge.warning {
      background-color: var(--bayan-warning-bg, #FFFBEB);
      color: var(--bayan-warning, #D97706);
    }

    .days-badge.urgent {
      background-color: var(--bayan-danger-bg, #FEF2F2);
      color: var(--bayan-danger, #DC2626);
    }

    .bids-cell {
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    .bids-count {
      font-weight: 600;
      color: var(--bayan-slate-900, #0F172A);
    }

    .bids-label {
      font-size: 0.75rem;
      color: var(--bayan-slate-500, #64748B);
    }

    .action-buttons {
      display: flex;
      gap: 0.25rem;
      justify-content: center;
    }

    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      padding: 3rem;
    }

    .empty-state p {
      color: var(--bayan-slate-500, #64748B);
      margin: 0;
    }

    :host ::ng-deep .w-full {
      width: 100%;
    }

    @media (max-width: 768px) {
      .page-header {
        flex-direction: column;
      }

      .header-actions {
        width: 100%;
        justify-content: stretch;
      }

      .header-actions button {
        flex: 1;
      }

      .filters-grid {
        grid-template-columns: 1fr;
      }

      .date-range {
        flex-direction: column;
        align-items: stretch;
      }

      .date-separator {
        display: none;
      }
    }
  `]
})
export class TenderListComponent implements OnInit, OnDestroy {
  private readonly authService = inject(AuthService);
  readonly tenderService = inject(TenderService);
  private readonly clientService = inject(ClientService);
  private readonly router = inject(Router);
  private readonly destroy$ = new Subject<void>();
  private readonly searchSubject$ = new Subject<string>();

  // Data signals
  tenders = signal<TenderListItem[]>([]);
  totalRecords = signal<number>(0);
  clients = signal<Client[]>([]);
  exporting = signal<boolean>(false);

  canManageTenders = computed(() => this.authService.hasRole([UserRole.ADMIN, UserRole.TENDER_MANAGER]));

  // Filter state
  searchTerm = '';
  filtersCollapsed = true;
  selectedClientId: number | null = null;
  selectedCurrency: Currency | null = null;
  dateFrom: Date | null = null;
  dateTo: Date | null = null;

  statusOptions: StatusOption[] = [
    { label: 'Draft', value: 'draft', selected: false },
    { label: 'Active', value: 'active', selected: false },
    { label: 'Evaluation', value: 'evaluation', selected: false },
    { label: 'Awarded', value: 'awarded', selected: false },
    { label: 'Closed', value: 'closed', selected: false },
    { label: 'Cancelled', value: 'cancelled', selected: false }
  ];

  currencyOptions = CURRENCY_OPTIONS;

  // Pagination state
  pageSize = 10;
  currentPage = 1;
  sortField = '';
  sortOrder: 'asc' | 'desc' = 'desc';

  // Computed values
  activeFilterCount = computed(() => {
    let count = 0;
    if (this.searchTerm) count++;
    if (this.statusOptions.some(s => s.selected)) count++;
    if (this.selectedClientId) count++;
    if (this.selectedCurrency) count++;
    if (this.dateFrom || this.dateTo) count++;
    return count;
  });

  ngOnInit(): void {
    this.loadClients();
    this.setupSearchDebounce();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private setupSearchDebounce(): void {
    this.searchSubject$.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      takeUntil(this.destroy$)
    ).subscribe(() => {
      this.currentPage = 1;
      this.fetchTenders();
    });
  }

  private loadClients(): void {
    this.clientService.getClients({ pageSize: 100 }).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (response) => {
        this.clients.set(response.items);
      }
    });
  }

  loadTenders(event: TableLazyLoadEvent): void {
    this.currentPage = Math.floor((event.first || 0) / (event.rows || 10)) + 1;
    this.pageSize = event.rows || 10;

    if (event.sortField) {
      this.sortField = event.sortField as string;
      this.sortOrder = event.sortOrder === 1 ? 'asc' : 'desc';
    }

    this.fetchTenders();
  }

  private fetchTenders(): void {
    const selectedStatuses = this.statusOptions
      .filter(s => s.selected)
      .map(s => s.value);

    const params: TenderQueryParams = {
      page: this.currentPage,
      pageSize: this.pageSize,
      search: this.searchTerm || undefined,
      status: selectedStatuses.length > 0 ? selectedStatuses : undefined,
      clientId: this.selectedClientId || undefined,
      currency: this.selectedCurrency || undefined,
      dateFrom: this.dateFrom ? this.formatDate(this.dateFrom) : undefined,
      dateTo: this.dateTo ? this.formatDate(this.dateTo) : undefined,
      sortBy: this.sortField || undefined,
      sortOrder: this.sortField ? this.sortOrder : undefined
    };

    this.tenderService.getTenders(params).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (response) => {
        this.tenders.set(response.items);
        this.totalRecords.set(response.pagination.totalItems);
      }
    });
  }

  private formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  onSearchInput(): void {
    this.searchSubject$.next(this.searchTerm);
  }

  onFilterChange(): void {
    this.currentPage = 1;
    this.fetchTenders();
  }

  clearFilters(): void {
    this.searchTerm = '';
    this.statusOptions.forEach(s => s.selected = false);
    this.selectedClientId = null;
    this.selectedCurrency = null;
    this.dateFrom = null;
    this.dateTo = null;
    this.currentPage = 1;
    this.fetchTenders();
  }

  navigateToNewTender(): void {
    this.router.navigate(['/tenders/new']);
  }

  navigateToDetails(id: string | number): void {
    this.router.navigate(['/tenders', id]);
  }

  navigateToEdit(id: string | number): void {
    this.router.navigate(['/tenders', id, 'edit']);
  }

  duplicateTender(tender: TenderListItem): void {
    // Navigate to new tender with pre-filled data
    this.router.navigate(['/tenders/new'], {
      queryParams: { duplicate: tender.id }
    });
  }

  onRowSelect(event: any): void {
    this.navigateToDetails(event.data.id);
  }

  exportToExcel(): void {
    this.exporting.set(true);
    const selectedStatuses = this.statusOptions
      .filter(s => s.selected)
      .map(s => s.value);

    this.tenderService.exportToExcel({
      search: this.searchTerm || undefined,
      status: selectedStatuses.length > 0 ? selectedStatuses : undefined,
      clientId: this.selectedClientId || undefined,
      currency: this.selectedCurrency || undefined,
      dateFrom: this.dateFrom ? this.formatDate(this.dateFrom) : undefined,
      dateTo: this.dateTo ? this.formatDate(this.dateTo) : undefined
    }).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `tenders-export-${new Date().toISOString().split('T')[0]}.xlsx`;
        link.click();
        window.URL.revokeObjectURL(url);
        this.exporting.set(false);
      },
      error: () => {
        this.exporting.set(false);
      }
    });
  }

  getStatusLabel(status: TenderStatus): string {
    return TENDER_STATUS_CONFIG[status]?.label || status;
  }

  getStatusSeverity(status: TenderStatus): 'success' | 'secondary' | 'info' | 'warn' | 'danger' | 'contrast' {
    return TENDER_STATUS_CONFIG[status]?.severity || 'secondary';
  }

  getDaysRemaining(deadline: Date | string): number | null {
    const deadlineDate = new Date(deadline);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    deadlineDate.setHours(0, 0, 0, 0);

    const diff = deadlineDate.getTime() - today.getTime();
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));

    return days > 0 ? days : null;
  }
}
