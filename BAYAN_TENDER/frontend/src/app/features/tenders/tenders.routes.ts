import { Routes } from '@angular/router';

export const TENDERS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./tender-list/tender-list.component').then(m => m.TenderListComponent),
    title: 'Tenders - Bayan'
  },
  {
    path: 'new',
    loadComponent: () => import('./tender-wizard/tender-wizard.component').then(m => m.TenderWizardComponent),
    title: 'Create Tender - Bayan'
  },
  {
    path: 'my-bids',
    loadComponent: () => import('./tender-list/tender-list.component').then(m => m.TenderListComponent),
    data: { filter: 'my-bids' },
    title: 'My Bids - Bayan'
  },
  {
    path: 'saved',
    loadComponent: () => import('./tender-list/tender-list.component').then(m => m.TenderListComponent),
    data: { filter: 'saved' },
    title: 'Saved Tenders - Bayan'
  },
  {
    path: ':id',
    loadChildren: () => import('./tender-details/tender-details.routes').then(m => m.TENDER_DETAILS_ROUTES)
  },
  {
    path: ':id/edit',
    loadComponent: () => import('./tender-wizard/tender-wizard.component').then(m => m.TenderWizardComponent),
    title: 'Edit Tender - Bayan'
  }
];
