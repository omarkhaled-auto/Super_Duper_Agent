import { Routes } from '@angular/router';
import { roleGuard } from '../../core/auth/auth.guard';
import { UserRole } from '../../core/models/user.model';

export const TENDERS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./tender-list/tender-list.component').then(m => m.TenderListComponent),
    title: 'Tenders - Bayan'
  },
  {
    path: 'new',
    loadComponent: () => import('./tender-wizard/tender-wizard.component').then(m => m.TenderWizardComponent),
    canActivate: [roleGuard],
    data: { roles: [UserRole.ADMIN, UserRole.TENDER_MANAGER] },
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
    canActivate: [roleGuard],
    data: { roles: [UserRole.ADMIN, UserRole.TENDER_MANAGER] },
    title: 'Edit Tender - Bayan'
  }
];
