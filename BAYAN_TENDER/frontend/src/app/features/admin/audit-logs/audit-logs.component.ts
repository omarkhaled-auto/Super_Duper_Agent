import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { DatePickerModule } from 'primeng/datepicker';
import { ToastModule } from 'primeng/toast';
import { DialogModule } from 'primeng/dialog';
import { TooltipModule } from 'primeng/tooltip';
import { TagModule } from 'primeng/tag';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageService } from 'primeng/api';
import { TableLazyLoadEvent } from 'primeng/table';
import { ApiService } from '../../../core/services/api.service';
import { UserService } from '../../../core/services/user.service';
import { PaginatedResult } from '../../../core/models/pagination.model';

interface AuditLog {
  id: string;
  timestamp: string;
  userId: string | null;
  userEmail: string | null;
  userFullName: string | null;
  action: string;
  entityType: string;
  entityId: string | null;
  oldValues: string | null;
  newValues: string | null;
  ipAddress: string | null;
  userAgent: string | null;
}

interface UserOption {
  label: string;
  value: string | null;
}

@Component({
  selector: 'app-audit-logs',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    DropdownModule,
    DatePickerModule,
    ToastModule,
    DialogModule,
    TooltipModule,
    TagModule,
    ProgressSpinnerModule
  ],
  providers: [MessageService],
  template: `
    <p-toast></p-toast>
    <div class="audit-logs-container" data-testid="audit-logs">
      <div class="page-header">
        <div>
          <h1>Audit Logs</h1>
          <p>View and search system activity logs</p>
        </div>
        <div class="header-actions">
          <button pButton label="Export to Excel" icon="pi pi-file-excel" class="p-button-success" (click)="exportToExcel()" [loading]="isExporting()"></button>
        </div>
      </div>

      <p-card>
        <!-- Filters -->
        <div class="filters-section">
          <div class="filter-row">
            <div class="filter-item">
              <label>User</label>
              <p-dropdown
                [options]="userOptions()"
                [(ngModel)]="filters.userId"
                placeholder="All Users"
                [showClear]="true"
                styleClass="w-full"
                (onChange)="onFilterChange()"
              ></p-dropdown>
            </div>
            <div class="filter-item">
              <label>Action Type</label>
              <p-dropdown
                [options]="actionOptions"
                [(ngModel)]="filters.action"
                placeholder="All Actions"
                [showClear]="true"
                styleClass="w-full"
                (onChange)="onFilterChange()"
              ></p-dropdown>
            </div>
            <div class="filter-item">
              <label>Entity Type</label>
              <p-dropdown
                [options]="entityTypeOptions"
                [(ngModel)]="filters.entityType"
                placeholder="All Entities"
                [showClear]="true"
                styleClass="w-full"
                (onChange)="onFilterChange()"
              ></p-dropdown>
            </div>
            <div class="filter-item">
              <label>Date Range</label>
              <p-datepicker
                [(ngModel)]="filters.dateRange"
                selectionMode="range"
                [readonlyInput]="true"
                placeholder="Select date range"
                dateFormat="dd/mm/yy"
                [showButtonBar]="true"
                styleClass="w-full"
                (onSelect)="onFilterChange()"
                (onClearClick)="onFilterChange()"
              ></p-datepicker>
            </div>
          </div>
          <div class="filter-row">
            <div class="filter-item search-item">
              <label>Search</label>
              <span class="p-input-icon-left w-full">
                <i class="pi pi-search"></i>
                <input
                  pInputText
                  type="text"
                  [(ngModel)]="filters.search"
                  placeholder="Search by email, action..."
                  class="w-full"
                  (keyup.enter)="onFilterChange()"
                  data-testid="audit-logs-search"
                />
              </span>
            </div>
            <div class="filter-actions">
              <button pButton label="Search" icon="pi pi-search" (click)="onFilterChange()"></button>
              <button pButton label="Clear" icon="pi pi-times" class="p-button-secondary" (click)="clearFilters()"></button>
            </div>
          </div>
        </div>

        <!-- Table -->
        <p-table
          data-testid="audit-logs-table"
          [value]="auditLogs()"
          [lazy]="true"
          [paginator]="true"
          [rows]="pageSize"
          [totalRecords]="totalRecords()"
          [loading]="isLoading()"
          [rowsPerPageOptions]="[10, 20, 50, 100]"
          (onLazyLoad)="loadAuditLogs($event)"
          [showCurrentPageReport]="true"
          currentPageReportTemplate="Showing {first} to {last} of {totalRecords} entries"
          styleClass="p-datatable-sm"
        >
          <ng-template pTemplate="header">
            <tr>
              <th style="width: 160px">Timestamp</th>
              <th style="width: 180px">User</th>
              <th style="width: 150px">Action</th>
              <th style="width: 120px">Entity Type</th>
              <th style="width: 280px">Entity ID</th>
              <th style="width: 100px">Changes</th>
              <th style="width: 120px">IP Address</th>
            </tr>
          </ng-template>
          <ng-template pTemplate="body" let-log>
            <tr>
              <td>{{ log.timestamp | date:'dd/MM/yyyy HH:mm:ss' }}</td>
              <td>
                <div class="user-cell">
                  <span class="user-name">{{ log.userFullName || 'System' }}</span>
                  @if (log.userEmail) {
                    <span class="user-email">{{ log.userEmail }}</span>
                  }
                </div>
              </td>
              <td>
                <p-tag [value]="getActionLabel(log.action)" [severity]="getActionSeverity(log.action)"></p-tag>
              </td>
              <td>{{ log.entityType }}</td>
              <td class="entity-id-cell">
                @if (log.entityId) {
                  <span class="entity-id" [pTooltip]="log.entityId">{{ log.entityId | slice:0:8 }}...</span>
                } @else {
                  <span class="text-muted">-</span>
                }
              </td>
              <td>
                @if (log.oldValues || log.newValues) {
                  <button pButton icon="pi pi-eye" class="p-button-text p-button-sm" pTooltip="View Changes" (click)="showDiff(log)"></button>
                } @else {
                  <span class="text-muted">-</span>
                }
              </td>
              <td>{{ log.ipAddress || '-' }}</td>
            </tr>
          </ng-template>
          <ng-template pTemplate="emptymessage">
            <tr>
              <td colspan="7" class="text-center p-4">
                <i class="pi pi-inbox text-4xl text-gray-300 mb-3"></i>
                <p class="text-gray-500">No audit logs found</p>
              </td>
            </tr>
          </ng-template>
        </p-table>
      </p-card>
    </div>

    <!-- Diff Dialog -->
    <p-dialog
      header="Value Changes"
      [(visible)]="showDiffDialog"
      [modal]="true"
      [style]="{width: '800px', maxHeight: '80vh'}"
      [draggable]="false"
      [resizable]="false"
    >
      @if (selectedLog) {
        <div class="diff-container">
          <div class="diff-section">
            <h4><i class="pi pi-minus-circle text-red-500"></i> Old Values</h4>
            <pre class="json-display old-values">{{ formatJson(selectedLog.oldValues) }}</pre>
          </div>
          <div class="diff-section">
            <h4><i class="pi pi-plus-circle text-green-500"></i> New Values</h4>
            <pre class="json-display new-values">{{ formatJson(selectedLog.newValues) }}</pre>
          </div>
        </div>
      }
      <ng-template pTemplate="footer">
        <button pButton label="Close" icon="pi pi-times" class="p-button-secondary" (click)="showDiffDialog = false"></button>
      </ng-template>
    </p-dialog>
  `,
  styles: [`
    .audit-logs-container {
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

    .filters-section {
      margin-bottom: 1.5rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid #e0e0e0;
    }

    .filter-row {
      display: flex;
      gap: 1rem;
      margin-bottom: 1rem;
      flex-wrap: wrap;
    }

    .filter-row:last-child {
      margin-bottom: 0;
    }

    .filter-item {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      min-width: 200px;
      flex: 1;
    }

    .filter-item label {
      font-weight: 500;
      color: #333;
      font-size: 0.875rem;
    }

    .search-item {
      flex: 2;
      min-width: 300px;
    }

    .filter-actions {
      display: flex;
      align-items: flex-end;
      gap: 0.5rem;
    }

    .user-cell {
      display: flex;
      flex-direction: column;
    }

    .user-name {
      font-weight: 500;
    }

    .user-email {
      font-size: 0.75rem;
      color: #666;
    }

    .entity-id-cell {
      font-family: monospace;
      font-size: 0.8rem;
    }

    .entity-id {
      cursor: pointer;
    }

    .text-muted {
      color: #999;
    }

    .diff-container {
      display: flex;
      gap: 1rem;
    }

    .diff-section {
      flex: 1;
      min-width: 0;
    }

    .diff-section h4 {
      margin: 0 0 0.75rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .json-display {
      background: #f8f9fa;
      border: 1px solid #e0e0e0;
      border-radius: 4px;
      padding: 1rem;
      font-size: 0.8rem;
      overflow-x: auto;
      max-height: 400px;
      overflow-y: auto;
      white-space: pre-wrap;
      word-break: break-all;
    }

    .old-values {
      background: #fff5f5;
      border-color: #fed7d7;
    }

    .new-values {
      background: #f0fff4;
      border-color: #c6f6d5;
    }

    :host ::ng-deep {
      .p-datatable .p-datatable-header {
        background: transparent;
        border: none;
        padding: 0;
      }

      .p-datepicker {
        width: 100%;
      }

      .p-inputtext {
        width: 100%;
      }
    }

    @media (max-width: 768px) {
      .diff-container {
        flex-direction: column;
      }

      .filter-item {
        min-width: 100%;
      }

      .search-item {
        min-width: 100%;
      }
    }
  `]
})
export class AuditLogsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly userService = inject(UserService);
  private readonly messageService = inject(MessageService);

  auditLogs = signal<AuditLog[]>([]);
  totalRecords = signal(0);
  isLoading = signal(false);
  isExporting = signal(false);
  userOptions = signal<UserOption[]>([]);

  pageSize = 20;
  currentPage = 1;

  showDiffDialog = false;
  selectedLog: AuditLog | null = null;

  filters = {
    userId: null as string | null,
    action: null as string | null,
    entityType: null as string | null,
    dateRange: null as Date[] | null,
    search: ''
  };

  actionOptions = [
    { label: 'Created', value: 'Created' },
    { label: 'Updated', value: 'Updated' },
    { label: 'Deleted', value: 'Deleted' },
    { label: 'Login', value: 'Login' },
    { label: 'Logout', value: 'Logout' },
    { label: 'Submitted', value: 'Submitted' },
    { label: 'Approved', value: 'Approved' },
    { label: 'Rejected', value: 'Rejected' }
  ];

  entityTypeOptions = [
    { label: 'Tender', value: 'Tender' },
    { label: 'Bid', value: 'Bid' },
    { label: 'User', value: 'User' },
    { label: 'Client', value: 'Client' },
    { label: 'Bidder', value: 'Bidder' },
    { label: 'Document', value: 'Document' },
    { label: 'Clarification', value: 'Clarification' },
    { label: 'Addendum', value: 'Addendum' },
    { label: 'Approval', value: 'Approval' }
  ];

  ngOnInit(): void {
    this.loadUsers();
  }

  private loadUsers(): void {
    this.userService.getUsers({ page: 1, pageSize: 1000 }).subscribe({
      next: (response: any) => {
        const users = response.items || response.data || [];
        this.userOptions.set([
          { label: 'All Users', value: null },
          ...users.map((u: any) => ({
            label: `${u.firstName} ${u.lastName} (${u.email})`,
            value: u.id
          }))
        ]);
      },
      error: () => {
        this.userOptions.set([{ label: 'All Users', value: null }]);
      }
    });
  }

  loadAuditLogs(event: TableLazyLoadEvent): void {
    this.isLoading.set(true);
    this.currentPage = Math.floor((event.first || 0) / (event.rows || this.pageSize)) + 1;
    this.pageSize = event.rows || this.pageSize;

    const params = this.buildQueryParams();

    this.api.get<PaginatedResult<AuditLog>>('/admin/audit-logs', params as any).subscribe({
      next: (response) => {
        this.auditLogs.set(response.items);
        this.totalRecords.set(response.total);
        this.isLoading.set(false);
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load audit logs'
        });
        this.isLoading.set(false);
      }
    });
  }

  private buildQueryParams(): Record<string, string> {
    const params: Record<string, string> = {
      page: this.currentPage.toString(),
      pageSize: this.pageSize.toString()
    };

    if (this.filters.userId) {
      params['userId'] = this.filters.userId;
    }

    if (this.filters.action) {
      params['action'] = this.filters.action;
    }

    if (this.filters.entityType) {
      params['entityType'] = this.filters.entityType;
    }

    if (this.filters.dateRange && this.filters.dateRange.length > 0) {
      params['startDate'] = this.filters.dateRange[0].toISOString();
      if (this.filters.dateRange.length > 1 && this.filters.dateRange[1]) {
        params['endDate'] = this.filters.dateRange[1].toISOString();
      }
    }

    if (this.filters.search) {
      params['search'] = this.filters.search;
    }

    return params;
  }

  onFilterChange(): void {
    this.currentPage = 1;
    this.loadAuditLogs({ first: 0, rows: this.pageSize });
  }

  clearFilters(): void {
    this.filters = {
      userId: null,
      action: null,
      entityType: null,
      dateRange: null,
      search: ''
    };
    this.onFilterChange();
  }

  showDiff(log: AuditLog): void {
    this.selectedLog = log;
    this.showDiffDialog = true;
  }

  formatJson(jsonString: string | null): string {
    if (!jsonString) return 'No data';
    try {
      const parsed = JSON.parse(jsonString);
      return JSON.stringify(parsed, null, 2);
    } catch {
      return jsonString;
    }
  }

  getActionLabel(action: string): string {
    const parts = action.split('.');
    return parts.length > 1 ? parts[1] : action;
  }

  getActionSeverity(action: string): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' {
    const actionLower = action.toLowerCase();
    if (actionLower.includes('created') || actionLower.includes('approved')) {
      return 'success';
    }
    if (actionLower.includes('deleted') || actionLower.includes('rejected')) {
      return 'danger';
    }
    if (actionLower.includes('updated')) {
      return 'info';
    }
    if (actionLower.includes('login') || actionLower.includes('logout')) {
      return 'secondary';
    }
    return 'warn';
  }

  exportToExcel(): void {
    this.isExporting.set(true);
    const params = this.buildQueryParams();
    params['pageSize'] = '10000'; // Export all matching records

    this.api.get<PaginatedResult<AuditLog>>('/admin/audit-logs', params as any).subscribe({
      next: (response) => {
        this.generateExcel(response.items);
        this.isExporting.set(false);
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Audit logs exported successfully'
        });
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to export audit logs'
        });
        this.isExporting.set(false);
      }
    });
  }

  private generateExcel(logs: AuditLog[]): void {
    // Generate CSV content
    const headers = ['Timestamp', 'User', 'Email', 'Action', 'Entity Type', 'Entity ID', 'Old Values', 'New Values', 'IP Address'];
    const rows = logs.map(log => [
      log.timestamp,
      log.userFullName || 'System',
      log.userEmail || '',
      log.action,
      log.entityType,
      log.entityId || '',
      log.oldValues || '',
      log.newValues || '',
      log.ipAddress || ''
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    ].join('\n');

    // Download file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  }
}
