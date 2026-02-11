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
import { Client } from '../../../core/models/client.model';
import { ClientService } from '../../../core/services/client.service';
import { ClientFormDialogComponent, ClientFormDialogData } from './client-form-dialog.component';

@Component({
  selector: 'app-client-list',
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
    InputIconModule
  ],
  providers: [ConfirmationService, MessageService, DialogService],
  template: `
    <p-toast></p-toast>
    <div class="client-list-container" data-testid="client-list">
      <div class="page-header">
        <div>
          <h1>Client Management</h1>
          <p>Manage client organizations and contacts</p>
        </div>
        <button pButton label="Add Client" icon="pi pi-plus" (click)="showClientDialog()" data-testid="create-client-btn"></button>
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
              placeholder="Search clients..."
              (input)="onSearch()"
              data-testid="client-search"
            />
          </p-iconField>

          <p-dropdown
            [options]="statusOptions"
            [(ngModel)]="selectedStatus"
            placeholder="Filter by Status"
            [showClear]="true"
            (onChange)="onFilter()"
          ></p-dropdown>

          <p-dropdown
            [options]="cityOptions"
            [(ngModel)]="selectedCity"
            placeholder="Filter by City"
            [showClear]="true"
            (onChange)="onFilter()"
          ></p-dropdown>
        </div>
      </p-card>

      <!-- Clients Table -->
      <p-card styleClass="table-card">
        <p-table
          data-testid="client-table"
          [value]="filteredClients()"
          [paginator]="true"
          [rows]="10"
          [showCurrentPageReport]="true"
          currentPageReportTemplate="Showing {first} to {last} of {totalRecords} clients"
          [rowsPerPageOptions]="[10, 25, 50]"
          [loading]="isLoading()"
          styleClass="p-datatable-striped"
        >
          <ng-template pTemplate="header">
            <tr>
              <th pSortableColumn="name">Company Name <p-sortIcon field="name"></p-sortIcon></th>
              <th pSortableColumn="email">Email <p-sortIcon field="email"></p-sortIcon></th>
              <th>Contact Person</th>
              <th pSortableColumn="city">City <p-sortIcon field="city"></p-sortIcon></th>
              <th pSortableColumn="isActive">Status <p-sortIcon field="isActive"></p-sortIcon></th>
              <th pSortableColumn="tendersCount">Tenders <p-sortIcon field="tendersCount"></p-sortIcon></th>
              <th>Actions</th>
            </tr>
          </ng-template>
          <ng-template pTemplate="body" let-client>
            <tr>
              <td>
                <div class="client-name">
                  <div class="avatar">{{ getInitials(client) }}</div>
                  <div class="name-details">
                    <span class="primary-name">{{ client.name }}</span>
                    @if (client.nameAr) {
                      <span class="secondary-name">{{ client.nameAr }}</span>
                    }
                  </div>
                </div>
              </td>
              <td>{{ client.email }}</td>
              <td>
                @if (client.contactPerson) {
                  <div class="contact-info">
                    <span>{{ client.contactPerson }}</span>
                    @if (client.contactPhone) {
                      <small>{{ client.contactPhone }}</small>
                    }
                  </div>
                } @else {
                  <span class="no-data">-</span>
                }
              </td>
              <td>{{ client.city || '-' }}</td>
              <td>
                <p-tag
                  [value]="client.isActive ? 'Active' : 'Inactive'"
                  [severity]="client.isActive ? 'success' : 'danger'"
                ></p-tag>
              </td>
              <td>
                <span class="tender-count">{{ client.tendersCount || 0 }}</span>
              </td>
              <td>
                <div class="action-buttons">
                  <button
                    pButton
                    icon="pi pi-eye"
                    class="p-button-text p-button-sm"
                    pTooltip="View Details"
                    tooltipPosition="top"
                    (click)="viewClient(client)"
                  ></button>
                  <button
                    pButton
                    icon="pi pi-pencil"
                    class="p-button-text p-button-sm"
                    pTooltip="Edit Client"
                    tooltipPosition="top"
                    (click)="editClient(client)"
                  ></button>
                  <button
                    pButton
                    [icon]="client.isActive ? 'pi pi-ban' : 'pi pi-check'"
                    class="p-button-text p-button-sm"
                    [class.p-button-warning]="client.isActive"
                    [class.p-button-success]="!client.isActive"
                    [pTooltip]="client.isActive ? 'Deactivate' : 'Activate'"
                    tooltipPosition="top"
                    (click)="toggleClientStatus(client)"
                  ></button>
                  <button
                    pButton
                    icon="pi pi-trash"
                    class="p-button-text p-button-sm p-button-danger"
                    pTooltip="Delete Client"
                    tooltipPosition="top"
                    (click)="confirmDelete(client)"
                  ></button>
                </div>
              </td>
            </tr>
          </ng-template>
          <ng-template pTemplate="emptymessage">
            <tr>
              <td colspan="7" class="text-center p-4">
                <div class="empty-state">
                  <i class="pi pi-building" style="font-size: 3rem; color: var(--bayan-muted-foreground, #71717a);"></i>
                  <p>No clients found.</p>
                  <button pButton label="Add First Client" icon="pi pi-plus" class="p-button-outlined" (click)="showClientDialog()"></button>
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
    .client-list-container {
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
      min-width: 250px;
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

    .client-name {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .avatar {
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

    .name-details {
      display: flex;
      flex-direction: column;
    }

    .primary-name {
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
    }

    .secondary-name {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
      direction: rtl;
    }

    .contact-info {
      display: flex;
      flex-direction: column;
    }

    .contact-info small {
      color: var(--bayan-muted-foreground, #71717a);
    }

    .no-data {
      color: var(--bayan-muted-foreground, #71717a);
    }

    .tender-count {
      font-weight: 600;
      color: var(--bayan-primary, #18181b);
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
  `]
})
export class ClientListComponent implements OnInit {
  private readonly clientService = inject(ClientService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly messageService = inject(MessageService);
  private readonly dialogService = inject(DialogService);

  clients = signal<Client[]>([]);
  filteredClients = signal<Client[]>([]);
  isLoading = this.clientService.isLoading;

  searchTerm = '';
  selectedStatus: boolean | null = null;
  selectedCity: string | null = null;

  statusOptions = [
    { label: 'Active', value: true },
    { label: 'Inactive', value: false }
  ];

  cityOptions: { label: string; value: string }[] = [];

  ngOnInit(): void {
    this.loadClients();
  }

  private loadClients(): void {
    this.clientService.getClients({
      page: 1,
      pageSize: 1000
    }).subscribe({
      next: (response) => {
        const items = response?.items || [];
        this.clients.set(items);
        this.filteredClients.set(items);
        this.updateCityOptions();
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load clients from the server'
        });
      }
    });
  }

  private updateCityOptions(): void {
    const cities = [...new Set(this.clients().map(c => c.city).filter(Boolean))] as string[];
    this.cityOptions = cities.map(city => ({ label: city, value: city }));
  }

  onSearch(): void {
    this.applyFilters();
  }

  onFilter(): void {
    this.applyFilters();
  }

  private applyFilters(): void {
    let result = [...this.clients()];

    if (this.searchTerm) {
      const term = this.searchTerm.toLowerCase();
      result = result.filter(c =>
        c.name.toLowerCase().includes(term) ||
        (c.nameAr && c.nameAr.includes(term)) ||
        c.email.toLowerCase().includes(term) ||
        (c.contactPerson && c.contactPerson.toLowerCase().includes(term))
      );
    }

    if (this.selectedStatus !== null) {
      result = result.filter(c => c.isActive === this.selectedStatus);
    }

    if (this.selectedCity) {
      result = result.filter(c => c.city === this.selectedCity);
    }

    this.filteredClients.set(result);
  }

  showClientDialog(client?: Client): void {
    const dialogData: ClientFormDialogData = {
      client,
      mode: client ? 'edit' : 'create'
    };

    const ref = this.dialogService.open(ClientFormDialogComponent, {
      header: client ? 'Edit Client' : 'Create New Client',
      width: '700px',
      contentStyle: { overflow: 'auto' },
      data: dialogData
    });

    ref.onClose.subscribe((result: Client | undefined) => {
      if (result) {
        if (client) {
          this.clients.update(clients =>
            clients.map(c => c.id === result.id ? result : c)
          );
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Client updated successfully'
          });
        } else {
          this.clients.update(clients => [...clients, result]);
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Client created successfully'
          });
        }
        this.updateCityOptions();
        this.applyFilters();
      }
    });
  }

  viewClient(client: Client): void {
    const dialogData: ClientFormDialogData = {
      client,
      mode: 'view'
    };

    const ref = this.dialogService.open(ClientFormDialogComponent, {
      header: `Client: ${client.name}`,
      width: '700px',
      contentStyle: { overflow: 'auto' },
      data: dialogData
    });

    ref.onClose.subscribe((result: Client | undefined) => {
      if (result) {
        this.clients.update(clients =>
          clients.map(c => c.id === result.id ? result : c)
        );
        this.applyFilters();
      }
    });
  }

  editClient(client: Client): void {
    this.showClientDialog(client);
  }

  toggleClientStatus(client: Client): void {
    const newStatus = !client.isActive;
    const action = newStatus ? 'activate' : 'deactivate';

    this.confirmationService.confirm({
      message: `Are you sure you want to ${action} ${client.name}?`,
      header: `Confirm ${action.charAt(0).toUpperCase() + action.slice(1)}`,
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.clientService.toggleClientStatus(client.id, newStatus).subscribe({
          next: () => {
            this.clients.update(clients =>
              clients.map(c => c.id === client.id ? { ...c, isActive: newStatus } : c)
            );
            this.applyFilters();
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: `Client ${newStatus ? 'activated' : 'deactivated'} successfully`
            });
          },
          error: (err) => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: err.message || `Failed to ${action} client`
            });
          }
        });
      }
    });
  }

  confirmDelete(client: Client): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete ${client.name}? This action cannot be undone.`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.clientService.deleteClient(client.id).subscribe({
          next: () => {
            this.clients.update(clients => clients.filter(c => c.id !== client.id));
            this.updateCityOptions();
            this.applyFilters();
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Client deleted successfully'
            });
          },
          error: (err) => {
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: err.message || 'Failed to delete client'
            });
          }
        });
      }
    });
  }

  getInitials(client: Client): string {
    const words = client.name.split(' ');
    if (words.length >= 2) {
      return `${words[0].charAt(0)}${words[1].charAt(0)}`.toUpperCase();
    }
    return client.name.substring(0, 2).toUpperCase();
  }
}
