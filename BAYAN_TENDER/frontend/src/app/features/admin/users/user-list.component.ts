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
import { User, UserRole } from '../../../core/models/user.model';
import { UserService } from '../../../core/services/user.service';
import { UserFormDialogComponent, UserFormDialogData } from './user-form-dialog.component';

@Component({
  selector: 'app-user-list',
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
    <div class="user-list-container" data-testid="user-list">
      <div class="page-header">
        <div>
          <h1>User Management</h1>
          <p>Manage system users and their roles</p>
        </div>
        <button pButton label="Add User" icon="pi pi-plus" (click)="showUserDialog()" data-testid="create-user-btn"></button>
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
              placeholder="Search users..."
              (input)="onSearch()"
              data-testid="user-search"
            />
          </p-iconField>

          <p-dropdown
            [options]="roleOptions"
            [(ngModel)]="selectedRole"
            placeholder="Filter by Role"
            [showClear]="true"
            (onChange)="onFilter()"
          ></p-dropdown>

          <p-dropdown
            [options]="statusOptions"
            [(ngModel)]="selectedStatus"
            placeholder="Filter by Status"
            [showClear]="true"
            (onChange)="onFilter()"
          ></p-dropdown>
        </div>
      </p-card>

      <!-- Users Table -->
      <p-card styleClass="table-card">
        <p-table
          data-testid="user-table"
          [value]="filteredUsers()"
          [paginator]="true"
          [rows]="10"
          [showCurrentPageReport]="true"
          currentPageReportTemplate="Showing {first} to {last} of {totalRecords} users"
          [rowsPerPageOptions]="[10, 25, 50]"
          [loading]="isLoading()"
          styleClass="p-datatable-striped"
        >
          <ng-template pTemplate="header">
            <tr>
              <th pSortableColumn="firstName">Name <p-sortIcon field="firstName"></p-sortIcon></th>
              <th pSortableColumn="email">Email <p-sortIcon field="email"></p-sortIcon></th>
              <th pSortableColumn="role">Role <p-sortIcon field="role"></p-sortIcon></th>
              <th pSortableColumn="isActive">Status <p-sortIcon field="isActive"></p-sortIcon></th>
              <th pSortableColumn="lastLogin">Last Login <p-sortIcon field="lastLogin"></p-sortIcon></th>
              <th>Actions</th>
            </tr>
          </ng-template>
          <ng-template pTemplate="body" let-user>
            <tr>
              <td>
                <div class="user-name">
                  <div class="avatar">{{ getInitials(user) }}</div>
                  <span>{{ user.firstName }} {{ user.lastName }}</span>
                </div>
              </td>
              <td>{{ user.email }}</td>
              <td>
                <p-tag [value]="getRoleLabel(user.role)" [severity]="getRoleSeverity(user.role)"></p-tag>
              </td>
              <td>
                <p-tag
                  [value]="user.isActive ? 'Active' : 'Inactive'"
                  [severity]="user.isActive ? 'success' : 'danger'"
                ></p-tag>
              </td>
              <td>{{ user.lastLogin | date:'medium' }}</td>
              <td>
                <div class="action-buttons">
                  <button
                    pButton
                    icon="pi pi-pencil"
                    class="p-button-text p-button-sm"
                    pTooltip="Edit User"
                    tooltipPosition="top"
                    (click)="editUser(user)"
                  ></button>
                  <button
                    pButton
                    [icon]="user.isActive ? 'pi pi-ban' : 'pi pi-check'"
                    class="p-button-text p-button-sm"
                    [class.p-button-warning]="user.isActive"
                    [class.p-button-success]="!user.isActive"
                    [pTooltip]="user.isActive ? 'Deactivate' : 'Activate'"
                    tooltipPosition="top"
                    (click)="toggleUserStatus(user)"
                  ></button>
                  <button
                    pButton
                    icon="pi pi-trash"
                    class="p-button-text p-button-sm p-button-danger"
                    pTooltip="Delete User"
                    tooltipPosition="top"
                    (click)="confirmDelete(user)"
                  ></button>
                </div>
              </td>
            </tr>
          </ng-template>
          <ng-template pTemplate="emptymessage">
            <tr>
              <td colspan="6" class="text-center p-4">
                <div class="empty-state">
                  <i class="pi pi-users" style="font-size: 3rem; color: var(--bayan-muted-foreground, #71717a);"></i>
                  <p>No users found.</p>
                  <button pButton label="Add First User" icon="pi pi-plus" class="p-button-outlined" (click)="showUserDialog()"></button>
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
    .user-list-container {
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

    .user-name {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: var(--bayan-primary, #18181b);
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.875rem;
      font-weight: 600;
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
export class UserListComponent implements OnInit {
  private readonly userService = inject(UserService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly messageService = inject(MessageService);
  private readonly dialogService = inject(DialogService);

  users = signal<User[]>([]);
  filteredUsers = signal<User[]>([]);
  isLoading = this.userService.isLoading;

  searchTerm = '';
  selectedRole: string | null = null;
  selectedStatus: boolean | null = null;

  roleOptions = [
    { label: 'Admin', value: UserRole.ADMIN },
    { label: 'Tender Manager', value: UserRole.TENDER_MANAGER },
    { label: 'Commercial Analyst', value: UserRole.COMMERCIAL_ANALYST },
    { label: 'Technical Panelist', value: UserRole.TECHNICAL_PANELIST },
    { label: 'Approver', value: UserRole.APPROVER },
    { label: 'Auditor', value: UserRole.AUDITOR },
    { label: 'Bidder', value: UserRole.BIDDER },
    { label: 'Viewer', value: UserRole.VIEWER }
  ];

  statusOptions = [
    { label: 'Active', value: true },
    { label: 'Inactive', value: false }
  ];

  ngOnInit(): void {
    this.loadUsers();
  }

  private loadUsers(): void {
    // For demo purposes, using mock data
    // In production, this would call: this.userService.getUsers()
    const mockUsers: User[] = [
      {
        id: 1,
        email: 'admin@bayan.sa',
        firstName: 'Ahmed',
        lastName: 'Al-Rashid',
        role: UserRole.ADMIN,
        isActive: true,
        createdAt: new Date('2025-01-01'),
        updatedAt: new Date('2026-01-15'),
        lastLogin: new Date('2026-02-05')
      },
      {
        id: 2,
        email: 'manager@bayan.sa',
        firstName: 'Fatima',
        lastName: 'Al-Saud',
        role: UserRole.TENDER_MANAGER,
        isActive: true,
        createdAt: new Date('2025-03-15'),
        updatedAt: new Date('2026-01-20'),
        lastLogin: new Date('2026-02-04')
      },
      {
        id: 3,
        email: 'bidder@company.sa',
        firstName: 'Mohammed',
        lastName: 'Al-Harbi',
        role: UserRole.BIDDER,
        isActive: true,
        createdAt: new Date('2025-06-01'),
        updatedAt: new Date('2026-01-10'),
        lastLogin: new Date('2026-02-03')
      },
      {
        id: 4,
        email: 'viewer@org.sa',
        firstName: 'Sara',
        lastName: 'Al-Otaibi',
        role: UserRole.VIEWER,
        isActive: false,
        createdAt: new Date('2025-09-15'),
        updatedAt: new Date('2026-01-05'),
        lastLogin: new Date('2025-12-20')
      }
    ];

    this.users.set(mockUsers);
    this.filteredUsers.set(mockUsers);
  }

  onSearch(): void {
    this.applyFilters();
  }

  onFilter(): void {
    this.applyFilters();
  }

  private applyFilters(): void {
    let result = [...this.users()];

    if (this.searchTerm) {
      const term = this.searchTerm.toLowerCase();
      result = result.filter(u =>
        u.firstName.toLowerCase().includes(term) ||
        u.lastName.toLowerCase().includes(term) ||
        u.email.toLowerCase().includes(term)
      );
    }

    if (this.selectedRole) {
      result = result.filter(u => u.role === this.selectedRole);
    }

    if (this.selectedStatus !== null) {
      result = result.filter(u => u.isActive === this.selectedStatus);
    }

    this.filteredUsers.set(result);
  }

  showUserDialog(user?: User): void {
    const dialogData: UserFormDialogData = {
      user,
      mode: user ? 'edit' : 'create'
    };

    const ref = this.dialogService.open(UserFormDialogComponent, {
      header: user ? 'Edit User' : 'Create New User',
      width: '550px',
      contentStyle: { overflow: 'auto' },
      data: dialogData
    });

    ref.onClose.subscribe((result: User | undefined) => {
      if (result) {
        if (user) {
          // Update existing user in list
          this.users.update(users =>
            users.map(u => u.id === result.id ? result : u)
          );
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'User updated successfully'
          });
        } else {
          // Add new user to list
          this.users.update(users => [...users, result]);
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'User created successfully'
          });
        }
        this.applyFilters();
      }
    });
  }

  editUser(user: User): void {
    this.showUserDialog(user);
  }

  toggleUserStatus(user: User): void {
    const newStatus = !user.isActive;
    const action = newStatus ? 'activate' : 'deactivate';

    this.confirmationService.confirm({
      message: `Are you sure you want to ${action} ${user.firstName} ${user.lastName}?`,
      header: `Confirm ${action.charAt(0).toUpperCase() + action.slice(1)}`,
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        // In production: this.userService.toggleUserStatus(user.id, newStatus)
        this.users.update(users =>
          users.map(u => u.id === user.id ? { ...u, isActive: newStatus } : u)
        );
        this.applyFilters();
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: `User ${newStatus ? 'activated' : 'deactivated'} successfully`
        });
      }
    });
  }

  confirmDelete(user: User): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete ${user.firstName} ${user.lastName}? This action cannot be undone.`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        // In production: this.userService.deleteUser(user.id)
        this.users.update(users => users.filter(u => u.id !== user.id));
        this.applyFilters();
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'User deleted successfully'
        });
      }
    });
  }

  getInitials(user: User): string {
    return `${user.firstName.charAt(0)}${user.lastName.charAt(0)}`.toUpperCase();
  }

  getRoleLabel(role: UserRole): string {
    const labels: Record<UserRole, string> = {
      [UserRole.ADMIN]: 'Admin',
      [UserRole.TENDER_MANAGER]: 'Tender Manager',
      [UserRole.COMMERCIAL_ANALYST]: 'Commercial Analyst',
      [UserRole.TECHNICAL_PANELIST]: 'Technical Panelist',
      [UserRole.APPROVER]: 'Approver',
      [UserRole.AUDITOR]: 'Auditor',
      [UserRole.BIDDER]: 'Bidder',
      [UserRole.VIEWER]: 'Viewer'
    };
    return labels[role];
  }

  getRoleSeverity(role: UserRole): 'success' | 'secondary' | 'info' | 'warn' | 'danger' | 'contrast' | undefined {
    const severities: Record<UserRole, 'success' | 'secondary' | 'info' | 'warn' | 'danger' | 'contrast'> = {
      [UserRole.ADMIN]: 'danger',
      [UserRole.TENDER_MANAGER]: 'warn',
      [UserRole.COMMERCIAL_ANALYST]: 'info',
      [UserRole.TECHNICAL_PANELIST]: 'info',
      [UserRole.APPROVER]: 'success',
      [UserRole.AUDITOR]: 'contrast',
      [UserRole.BIDDER]: 'info',
      [UserRole.VIEWER]: 'secondary'
    };
    return severities[role];
  }
}
