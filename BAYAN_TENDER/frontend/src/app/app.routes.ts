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
        redirectTo: 'home',
        pathMatch: 'full'
      },
      {
        path: 'home',
        loadComponent: () => import('./features/home/home.component').then(m => m.HomeComponent),
        title: 'Home - Bayan'
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
        path: 'vendor-pricing',
        loadChildren: () => import('./features/vendor-pricing/vendor-pricing.routes').then(m => m.VENDOR_PRICING_ROUTES),
        title: 'Vendor Pricing - Bayan'
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
    loadComponent: () => import('./features/auth/unauthorized/unauthorized.component').then(m => m.UnauthorizedComponent),
    title: 'Unauthorized - Bayan'
  },

  // Catch-all redirect
  {
    path: '**',
    redirectTo: 'home'
  }
];
