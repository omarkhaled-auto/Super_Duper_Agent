import { Routes } from '@angular/router';
import { roleGuard } from '../../core/auth/auth.guard';
import { UserRole } from '../../core/models/user.model';

export const ADMIN_ROUTES: Routes = [
  {
    path: '',
    redirectTo: 'users',
    pathMatch: 'full'
  },
  {
    path: 'users',
    loadComponent: () => import('./users/user-list.component').then(m => m.UserListComponent),
    canActivate: [roleGuard],
    data: { roles: [UserRole.ADMIN] },
    title: 'User Management - Bayan'
  },
  {
    path: 'clients',
    loadComponent: () => import('./clients/client-list.component').then(m => m.ClientListComponent),
    canActivate: [roleGuard],
    data: { roles: [UserRole.ADMIN, UserRole.TENDER_MANAGER] },
    title: 'Client Management - Bayan'
  },
  {
    path: 'bidders',
    loadComponent: () => import('./bidders/bidder-list.component').then(m => m.BidderListComponent),
    canActivate: [roleGuard],
    data: { roles: [UserRole.ADMIN, UserRole.TENDER_MANAGER] },
    title: 'Bidder Management - Bayan'
  },
  {
    path: 'settings',
    loadComponent: () => import('./settings/settings.component').then(m => m.SettingsComponent),
    canActivate: [roleGuard],
    data: { roles: [UserRole.ADMIN] },
    title: 'System Settings - Bayan'
  },
  {
    path: 'audit-logs',
    loadComponent: () => import('./audit-logs/audit-logs.component').then(m => m.AuditLogsComponent),
    canActivate: [roleGuard],
    data: { roles: [UserRole.ADMIN, UserRole.AUDITOR] },
    title: 'Audit Logs - Bayan'
  }
];
