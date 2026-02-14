import { Routes } from '@angular/router';
import { roleGuard } from '../../core/auth/auth.guard';
import { UserRole } from '../../core/models/user.model';
import { VendorPricingComponent } from './vendor-pricing.component';

export const VENDOR_PRICING_ROUTES: Routes = [
  {
    path: '',
    component: VendorPricingComponent,
    canActivate: [roleGuard],
    data: { roles: [UserRole.ADMIN, UserRole.TENDER_MANAGER, UserRole.COMMERCIAL_ANALYST, UserRole.AUDITOR] },
    title: 'Vendor Pricing - Bayan'
  }
];
