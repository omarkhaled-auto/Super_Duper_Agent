import { Routes } from '@angular/router';

export const BIDS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./bids-tab.component').then(m => m.BidsTabComponent),
    title: 'Bids - Bayan'
  }
];
