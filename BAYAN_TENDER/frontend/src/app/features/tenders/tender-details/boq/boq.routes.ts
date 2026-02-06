import { Routes } from '@angular/router';

export const BOQ_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./boq-tab.component').then(m => m.BoqTabComponent),
    title: 'BOQ - Bayan'
  }
];
