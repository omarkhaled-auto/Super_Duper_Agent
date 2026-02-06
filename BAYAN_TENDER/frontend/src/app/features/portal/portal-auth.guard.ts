import { inject } from '@angular/core';
import { CanActivateFn, Router, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { PortalService } from '../../core/services/portal.service';

/**
 * Guard to protect portal routes - ensures bidder is authenticated
 */
export const portalAuthGuard: CanActivateFn = (
  route: ActivatedRouteSnapshot,
  state: RouterStateSnapshot
) => {
  const portalService = inject(PortalService);
  const router = inject(Router);

  if (portalService.isAuthenticated()) {
    return true;
  }

  // Store the attempted URL for redirecting after login
  const returnUrl = state.url;

  // Redirect to portal login with return URL
  router.navigate(['/portal/login'], {
    queryParams: { returnUrl }
  });

  return false;
};

/**
 * Guard to prevent authenticated users from accessing login page
 */
export const portalLoginGuard: CanActivateFn = () => {
  const portalService = inject(PortalService);
  const router = inject(Router);

  if (!portalService.isAuthenticated()) {
    return true;
  }

  // If already authenticated, redirect to portal home
  router.navigate(['/portal/tenders']);
  return false;
};
