import { Routes } from '@angular/router';
import { roleGuard } from '../../core/auth/auth.guard';
import { UserRole } from '../../core/models/user.model';

export const DASHBOARD_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./dashboard.component').then(m => m.DashboardComponent),
    canActivate: [roleGuard],
    data: { roles: [UserRole.ADMIN, UserRole.TENDER_MANAGER] },
    title: 'Dashboard - Bayan'
  },
  {
    path: 'overview',
    loadComponent: () => import('./overview-dashboard.component').then(m => m.OverviewDashboardComponent),
    canActivate: [roleGuard],
    data: { roles: [UserRole.ADMIN, UserRole.TENDER_MANAGER, UserRole.COMMERCIAL_ANALYST, UserRole.AUDITOR] },
    title: 'Overview - Bayan'
  },
  {
    path: 'approver',
    loadComponent: () => import('./approver-dashboard.component').then(m => m.ApproverDashboardComponent),
    canActivate: [roleGuard],
    data: { roles: [UserRole.APPROVER] },
    title: 'Approver Dashboard - Bayan'
  }
];
