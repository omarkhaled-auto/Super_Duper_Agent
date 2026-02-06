import { Routes } from '@angular/router';

export const TENDER_DETAILS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./tender-details.component').then(m => m.TenderDetailsComponent),
    title: 'Tender Details - Bayan',
    children: [
      {
        path: 'boq',
        loadChildren: () => import('./boq/boq.routes').then(m => m.BOQ_ROUTES)
      },
      {
        path: 'clarifications',
        loadChildren: () => import('./clarifications/clarifications.routes').then(m => m.CLARIFICATIONS_ROUTES)
      },
      {
        path: 'bids',
        loadChildren: () => import('./bids/bids.routes').then(m => m.BIDS_ROUTES)
      },
      {
        path: 'evaluation',
        loadChildren: () => import('./evaluation/evaluation.routes').then(m => m.EVALUATION_ROUTES)
      },
      {
        path: 'approval',
        loadChildren: () => import('./approval/approval.routes').then(m => m.APPROVAL_ROUTES)
      }
    ]
  }
];
