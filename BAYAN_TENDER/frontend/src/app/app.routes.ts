import { Routes } from '@angular/router';
import { authGuard } from './core/auth/auth.guard';
import { LayoutComponent } from './layout/layout.component';

export const routes: Routes = [
  // Public routes (auth)
  {
    path: 'auth',
    loadChildren: () => import('./features/auth/auth.routes').then(m => m.AUTH_ROUTES)
  },

  // Bidder Portal routes (separate from admin)
  {
    path: 'portal',
    loadChildren: () => import('./features/portal/portal.routes').then(m => m.PORTAL_ROUTES)
  },

  // Protected routes (with layout) - Admin/Internal users
  {
    path: '',
    component: LayoutComponent,
    canActivate: [authGuard],
    children: [
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      },
      {
        path: 'dashboard',
        loadChildren: () => import('./features/dashboard/dashboard.routes').then(m => m.DASHBOARD_ROUTES)
      },
      {
        path: 'tenders',
        loadChildren: () => import('./features/tenders/tenders.routes').then(m => m.TENDERS_ROUTES)
      },
      {
        path: 'admin',
        loadChildren: () => import('./features/admin/admin.routes').then(m => m.ADMIN_ROUTES)
      },
      {
        path: 'settings',
        children: [
          {
            path: 'notifications',
            loadComponent: () => import('./features/settings/notification-settings.component').then(m => m.NotificationSettingsComponent),
            title: 'Notification Settings - Bayan'
          }
        ]
      }
    ]
  },

  // Unauthorized page
  {
    path: 'unauthorized',
    loadComponent: () => import('./features/auth/login/login.component').then(m => m.LoginComponent)
  },

  // Catch-all redirect
  {
    path: '**',
    redirectTo: 'dashboard'
  }
];
