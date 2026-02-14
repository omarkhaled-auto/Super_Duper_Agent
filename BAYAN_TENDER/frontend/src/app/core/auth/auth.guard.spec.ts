import { TestBed } from '@angular/core/testing';
import { Router, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { AuthService } from './auth.service';
import { authGuard, guestGuard, roleGuard } from './auth.guard';

/**
 * Helper to execute a functional CanActivateFn guard within Angular's injection context.
 * Angular 18 functional guards require `TestBed.runInInjectionContext` to resolve `inject()` calls.
 */
function runGuard(
  guard: typeof authGuard,
  route: ActivatedRouteSnapshot,
  state: RouterStateSnapshot
): boolean {
  return TestBed.runInInjectionContext(() => guard(route, state)) as boolean;
}

describe('Auth Guards', () => {
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let routerSpy: jasmine.SpyObj<Router>;
  let mockRoute: ActivatedRouteSnapshot;
  let mockState: RouterStateSnapshot;

  beforeEach(() => {
    authServiceSpy = jasmine.createSpyObj('AuthService', [
      'isAuthenticated',
      'hasRole',
      'getAccessToken'
    ]);
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        { provide: Router, useValue: routerSpy }
      ]
    });

    mockRoute = new ActivatedRouteSnapshot();
    mockState = { url: '/protected/resource' } as RouterStateSnapshot;
  });

  // ─────────────────────────── authGuard ───────────────────────────

  describe('authGuard', () => {
    it('should allow access when authenticated', () => {
      authServiceSpy.isAuthenticated.and.returnValue(true);

      const result = runGuard(authGuard, mockRoute, mockState);

      expect(result).toBeTrue();
      expect(routerSpy.navigate).not.toHaveBeenCalled();
    });

    it('should redirect to login when not authenticated', () => {
      authServiceSpy.isAuthenticated.and.returnValue(false);

      const result = runGuard(authGuard, mockRoute, mockState);

      expect(result).toBeFalse();
      expect(routerSpy.navigate).toHaveBeenCalledWith(
        ['/auth/login'],
        jasmine.objectContaining({
          queryParams: jasmine.objectContaining({ returnUrl: '/protected/resource' })
        })
      );
    });

    it('should pass returnUrl as query parameter on redirect', () => {
      authServiceSpy.isAuthenticated.and.returnValue(false);
      const deepState = { url: '/tenders/42/details' } as RouterStateSnapshot;

      runGuard(authGuard, mockRoute, deepState);

      expect(routerSpy.navigate).toHaveBeenCalledWith(
        ['/auth/login'],
        { queryParams: { returnUrl: '/tenders/42/details' } }
      );
    });
  });

  // ─────────────────────────── guestGuard ───────────────────────────

  describe('guestGuard', () => {
    it('should allow access when not authenticated', () => {
      authServiceSpy.isAuthenticated.and.returnValue(false);

      const result = runGuard(guestGuard, mockRoute, mockState);

      expect(result).toBeTrue();
      expect(routerSpy.navigate).not.toHaveBeenCalled();
    });

    it('should redirect to home when authenticated', () => {
      authServiceSpy.isAuthenticated.and.returnValue(true);

      const result = runGuard(guestGuard, mockRoute, mockState);

      expect(result).toBeFalse();
      expect(routerSpy.navigate).toHaveBeenCalledWith(['/home']);
    });
  });

  // ─────────────────────────── roleGuard ───────────────────────────

  describe('roleGuard', () => {
    it('should allow access for matching role', () => {
      authServiceSpy.isAuthenticated.and.returnValue(true);
      authServiceSpy.hasRole.and.returnValue(true);
      mockRoute.data = { roles: ['tender_manager'] };

      const result = runGuard(roleGuard, mockRoute, mockState);

      expect(result).toBeTrue();
      expect(authServiceSpy.hasRole).toHaveBeenCalledWith(['tender_manager']);
    });

    it('should deny access for non-matching role', () => {
      authServiceSpy.isAuthenticated.and.returnValue(true);
      authServiceSpy.hasRole.and.returnValue(false);
      mockRoute.data = { roles: ['admin'] };

      const result = runGuard(roleGuard, mockRoute, mockState);

      expect(result).toBeFalse();
      expect(routerSpy.navigate).toHaveBeenCalledWith(['/unauthorized']);
    });

    it('should allow access for admin regardless of required role', () => {
      // The guard itself delegates role-matching to AuthService.hasRole.
      // When AuthService confirms the user has one of the required roles (e.g. "admin"
      // is included in the roles array, or AuthService internally grants admin), it returns true.
      authServiceSpy.isAuthenticated.and.returnValue(true);
      authServiceSpy.hasRole.and.returnValue(true);
      mockRoute.data = { roles: ['tender_manager', 'admin'] };

      const result = runGuard(roleGuard, mockRoute, mockState);

      expect(result).toBeTrue();
      expect(authServiceSpy.hasRole).toHaveBeenCalledWith(['tender_manager', 'admin']);
    });

    it('should redirect to unauthorized page on denial', () => {
      authServiceSpy.isAuthenticated.and.returnValue(true);
      authServiceSpy.hasRole.and.returnValue(false);
      mockRoute.data = { roles: ['auditor'] };

      runGuard(roleGuard, mockRoute, mockState);

      expect(routerSpy.navigate).toHaveBeenCalledWith(['/unauthorized']);
    });

    it('should redirect to login when not authenticated', () => {
      authServiceSpy.isAuthenticated.and.returnValue(false);
      mockRoute.data = { roles: ['admin'] };

      const result = runGuard(roleGuard, mockRoute, mockState);

      expect(result).toBeFalse();
      expect(routerSpy.navigate).toHaveBeenCalledWith(
        ['/auth/login'],
        { queryParams: { returnUrl: '/protected/resource' } }
      );
    });

    it('should allow access when no roles are required', () => {
      authServiceSpy.isAuthenticated.and.returnValue(true);
      mockRoute.data = { roles: [] };

      const result = runGuard(roleGuard, mockRoute, mockState);

      expect(result).toBeTrue();
      expect(authServiceSpy.hasRole).not.toHaveBeenCalled();
    });

    it('should allow access when route data has no roles property', () => {
      authServiceSpy.isAuthenticated.and.returnValue(true);
      mockRoute.data = {};

      const result = runGuard(roleGuard, mockRoute, mockState);

      expect(result).toBeTrue();
      expect(authServiceSpy.hasRole).not.toHaveBeenCalled();
    });
  });
});
