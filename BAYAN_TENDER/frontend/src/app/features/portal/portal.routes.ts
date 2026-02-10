import { Routes } from '@angular/router';
import { portalAuthGuard, portalLoginGuard } from './portal-auth.guard';
import { PortalLayoutComponent } from './layout/portal-layout.component';

export const PORTAL_ROUTES: Routes = [
  // Public portal routes (login)
  {
    path: 'login',
    canActivate: [portalLoginGuard],
    loadComponent: () =>
      import('./auth/portal-login.component').then(m => m.PortalLoginComponent)
  },

  // Tender selection / landing page
  {
    path: 'tenders',
    canActivate: [portalAuthGuard],
    loadComponent: () =>
      import('./tenders/portal-tenders.component').then(m => m.PortalTendersComponent)
  },

  // Protected portal routes (with layout)
  {
    path: 'tenders/:tenderId',
    component: PortalLayoutComponent,
    canActivate: [portalAuthGuard],
    children: [
      {
        path: '',
        redirectTo: 'documents',
        pathMatch: 'full'
      },
      {
        path: 'documents',
        loadComponent: () =>
          import('./documents/portal-documents.component').then(m => m.PortalDocumentsComponent)
      },
      {
        path: 'clarifications',
        loadComponent: () =>
          import('./clarifications/portal-clarifications.component').then(m => m.PortalClarificationsComponent)
      },
      {
        path: 'submit',
        loadComponent: () =>
          import('./submit/portal-submit.component').then(m => m.PortalSubmitComponent)
      }
    ]
  },

  // Bid receipt route (protected but outside tender layout)
  {
    path: 'bids/:bidId/receipt',
    canActivate: [portalAuthGuard],
    loadComponent: () =>
      import('./receipt/portal-receipt.component').then(m => m.PortalReceiptComponent)
  },

  // Account activation route (public)
  {
    path: 'activate',
    loadComponent: () =>
      import('./activate/portal-activate.component').then(m => m.PortalActivateComponent)
  },

  // Default redirect
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
  },

  // Catch-all redirect
  {
    path: '**',
    redirectTo: 'login'
  }
];
