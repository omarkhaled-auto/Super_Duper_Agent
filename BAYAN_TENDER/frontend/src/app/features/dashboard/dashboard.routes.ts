import { Routes } from '@angular/router';

export const DASHBOARD_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./dashboard.component').then(m => m.DashboardComponent)
  },
  {
    path: 'approver',
    loadComponent: () => import('./approver-dashboard.component').then(m => m.ApproverDashboardComponent)
  }
];
