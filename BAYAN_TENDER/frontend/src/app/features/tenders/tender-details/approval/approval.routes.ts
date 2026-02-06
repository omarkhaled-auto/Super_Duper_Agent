import { Routes } from '@angular/router';

export const APPROVAL_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./approval-tab.component').then(m => m.ApprovalTabComponent),
    title: 'Approval - Bayan'
  }
];
