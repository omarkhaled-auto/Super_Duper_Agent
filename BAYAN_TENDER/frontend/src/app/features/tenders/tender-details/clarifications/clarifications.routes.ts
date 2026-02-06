import { Routes } from '@angular/router';

export const CLARIFICATIONS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./clarifications-tab.component').then(m => m.ClarificationsTabComponent),
    title: 'Clarifications - Bayan'
  }
];
