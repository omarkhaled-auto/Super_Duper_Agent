import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { of, throwError } from 'rxjs';
import { AuthService } from './auth.service';
import { authInterceptor, languageInterceptor, errorInterceptor } from './auth.interceptor';

describe('HTTP Interceptors', () => {
  let httpClient: HttpClient;
  let httpTesting: HttpTestingController;
  let authServiceSpy: jasmine.SpyObj<AuthService>;

  // ═══════════════════════════════════════════════════════════════
  //  authInterceptor
  // ═══════════════════════════════════════════════════════════════

  describe('authInterceptor', () => {
    beforeEach(() => {
      authServiceSpy = jasmine.createSpyObj('AuthService', [
        'getAccessToken',
        'refreshToken',
        'logout'
      ]);

      TestBed.configureTestingModule({
        providers: [
          provideHttpClient(withInterceptors([authInterceptor])),
          provideHttpClientTesting(),
          { provide: AuthService, useValue: authServiceSpy }
        ]
      });

      httpClient = TestBed.inject(HttpClient);
      httpTesting = TestBed.inject(HttpTestingController);
    });

    afterEach(() => {
      httpTesting.verify();
    });

    it('should add Authorization header when token exists', () => {
      authServiceSpy.getAccessToken.and.returnValue('test-jwt-token');

      httpClient.get('/api/tenders').subscribe();

      const req = httpTesting.expectOne('/api/tenders');
      expect(req.request.headers.get('Authorization')).toBe('Bearer test-jwt-token');
      req.flush({});
    });

    it('should not add header when no token', () => {
      authServiceSpy.getAccessToken.and.returnValue(null);

      httpClient.get('/api/tenders').subscribe();

      const req = httpTesting.expectOne('/api/tenders');
      expect(req.request.headers.has('Authorization')).toBeFalse();
      req.flush({});
    });

    it('should not add header for login endpoint', () => {
      authServiceSpy.getAccessToken.and.returnValue('test-jwt-token');

      httpClient.post('/api/auth/login', { email: 'a@b.com', password: 'pass' }).subscribe();

      const req = httpTesting.expectOne('/api/auth/login');
      expect(req.request.headers.has('Authorization')).toBeFalse();
      req.flush({});
    });

    it('should not add header for register endpoint', () => {
      authServiceSpy.getAccessToken.and.returnValue('test-jwt-token');

      httpClient.post('/api/auth/register', {}).subscribe();

      const req = httpTesting.expectOne('/api/auth/register');
      expect(req.request.headers.has('Authorization')).toBeFalse();
      req.flush({});
    });

    it('should not add header for refresh endpoint', () => {
      authServiceSpy.getAccessToken.and.returnValue('test-jwt-token');

      httpClient.post('/api/auth/refresh', {}).subscribe();

      const req = httpTesting.expectOne('/api/auth/refresh');
      expect(req.request.headers.has('Authorization')).toBeFalse();
      req.flush({});
    });

    it('should not add header for forgot-password endpoint', () => {
      authServiceSpy.getAccessToken.and.returnValue('test-jwt-token');

      httpClient.post('/api/auth/forgot-password', {}).subscribe();

      const req = httpTesting.expectOne('/api/auth/forgot-password');
      expect(req.request.headers.has('Authorization')).toBeFalse();
      req.flush({});
    });

    it('should use Bearer prefix', () => {
      authServiceSpy.getAccessToken.and.returnValue('abc123');

      httpClient.get('/api/data').subscribe();

      const req = httpTesting.expectOne('/api/data');
      const authHeader = req.request.headers.get('Authorization')!;
      expect(authHeader.startsWith('Bearer ')).toBeTrue();
      expect(authHeader).toBe('Bearer abc123');
      req.flush({});
    });

    it('should attempt token refresh on 401 error', () => {
      authServiceSpy.getAccessToken.and.returnValue('expired-token');
      authServiceSpy.refreshToken.and.returnValue(
        of({ accessToken: 'new-token', refreshToken: 'new-refresh' })
      );

      httpClient.get('/api/tenders').subscribe();

      // First request fails with 401
      const firstReq = httpTesting.expectOne('/api/tenders');
      firstReq.flush(null, { status: 401, statusText: 'Unauthorized' });

      // After refresh, the interceptor retries the request with new token
      const retryReq = httpTesting.expectOne('/api/tenders');
      expect(retryReq.request.headers.get('Authorization')).toBe('Bearer new-token');
      retryReq.flush({ data: 'success' });
    });

    it('should logout when token refresh fails', () => {
      authServiceSpy.getAccessToken.and.returnValue('expired-token');
      authServiceSpy.refreshToken.and.returnValue(
        throwError(() => new Error('Refresh failed'))
      );

      httpClient.get('/api/tenders').subscribe({
        error: () => {
          // Expected error path
        }
      });

      const req = httpTesting.expectOne('/api/tenders');
      req.flush(null, { status: 401, statusText: 'Unauthorized' });

      expect(authServiceSpy.logout).toHaveBeenCalled();
    });

    it('should pass through non-401 errors without attempting refresh', () => {
      authServiceSpy.getAccessToken.and.returnValue('valid-token');
      let errorReceived = false;

      httpClient.get('/api/tenders').subscribe({
        error: (err) => {
          errorReceived = true;
          expect(err.status).toBe(500);
        }
      });

      const req = httpTesting.expectOne('/api/tenders');
      req.flush(null, { status: 500, statusText: 'Internal Server Error' });

      expect(errorReceived).toBeTrue();
      expect(authServiceSpy.refreshToken).not.toHaveBeenCalled();
    });

    it('should not attempt refresh for 401 on auth endpoints', () => {
      authServiceSpy.getAccessToken.and.returnValue(null);

      httpClient.post('/api/auth/login', {}).subscribe({
        error: () => { /* expected */ }
      });

      const req = httpTesting.expectOne('/api/auth/login');
      req.flush(null, { status: 401, statusText: 'Unauthorized' });

      expect(authServiceSpy.refreshToken).not.toHaveBeenCalled();
    });
  });

  // ═══════════════════════════════════════════════════════════════
  //  languageInterceptor
  // ═══════════════════════════════════════════════════════════════

  describe('languageInterceptor', () => {
    beforeEach(() => {
      TestBed.configureTestingModule({
        providers: [
          provideHttpClient(withInterceptors([languageInterceptor])),
          provideHttpClientTesting()
        ]
      });

      httpClient = TestBed.inject(HttpClient);
      httpTesting = TestBed.inject(HttpTestingController);
    });

    afterEach(() => {
      httpTesting.verify();
      localStorage.removeItem('bayan_language');
    });

    it('should add Accept-Language header', () => {
      httpClient.get('/api/tenders').subscribe();

      const req = httpTesting.expectOne('/api/tenders');
      expect(req.request.headers.has('Accept-Language')).toBeTrue();
      req.flush({});
    });

    it('should use current language setting from localStorage', () => {
      localStorage.setItem('bayan_language', 'ar');

      httpClient.get('/api/tenders').subscribe();

      const req = httpTesting.expectOne('/api/tenders');
      expect(req.request.headers.get('Accept-Language')).toBe('ar');
      req.flush({});
    });

    it('should default to "en" when no language is set', () => {
      localStorage.removeItem('bayan_language');

      httpClient.get('/api/tenders').subscribe();

      const req = httpTesting.expectOne('/api/tenders');
      expect(req.request.headers.get('Accept-Language')).toBe('en');
      req.flush({});
    });
  });

  // ═══════════════════════════════════════════════════════════════
  //  errorInterceptor
  // ═══════════════════════════════════════════════════════════════

  describe('errorInterceptor', () => {
    beforeEach(() => {
      TestBed.configureTestingModule({
        providers: [
          provideHttpClient(withInterceptors([errorInterceptor])),
          provideHttpClientTesting()
        ]
      });

      httpClient = TestBed.inject(HttpClient);
      httpTesting = TestBed.inject(HttpTestingController);
    });

    afterEach(() => {
      httpTesting.verify();
    });

    it('should pass through successful responses', () => {
      let responseData: unknown;

      httpClient.get('/api/tenders').subscribe((data) => {
        responseData = data;
      });

      const req = httpTesting.expectOne('/api/tenders');
      req.flush({ items: [] });

      expect(responseData).toEqual({ items: [] });
    });

    it('should handle 401 with "Unauthorized access" message', () => {
      let errorResult: any;

      httpClient.get('/api/protected').subscribe({
        error: (err) => { errorResult = err; }
      });

      const req = httpTesting.expectOne('/api/protected');
      req.flush(null, { status: 401, statusText: 'Unauthorized' });

      expect(errorResult.message).toBe('Unauthorized access');
    });

    it('should handle 403 with "Access forbidden" message', () => {
      let errorResult: any;

      httpClient.get('/api/admin').subscribe({
        error: (err) => { errorResult = err; }
      });

      const req = httpTesting.expectOne('/api/admin');
      req.flush(null, { status: 403, statusText: 'Forbidden' });

      expect(errorResult.message).toBe('Access forbidden');
    });

    it('should handle 404 with "Resource not found" message', () => {
      let errorResult: any;

      httpClient.get('/api/tenders/9999').subscribe({
        error: (err) => { errorResult = err; }
      });

      const req = httpTesting.expectOne('/api/tenders/9999');
      req.flush(null, { status: 404, statusText: 'Not Found' });

      expect(errorResult.message).toBe('Resource not found');
    });

    it('should handle 500 with "Internal server error" message', () => {
      let errorResult: any;

      httpClient.get('/api/tenders').subscribe({
        error: (err) => { errorResult = err; }
      });

      const req = httpTesting.expectOne('/api/tenders');
      req.flush(null, { status: 500, statusText: 'Internal Server Error' });

      expect(errorResult.message).toBe('Internal server error');
    });

    it('should handle 400 with server-provided message', () => {
      let errorResult: any;

      httpClient.post('/api/tenders', {}).subscribe({
        error: (err) => { errorResult = err; }
      });

      const req = httpTesting.expectOne('/api/tenders');
      req.flush({ message: 'Title is required' }, { status: 400, statusText: 'Bad Request' });

      expect(errorResult.message).toBe('Title is required');
    });

    it('should handle 503 with "Service unavailable" message', () => {
      let errorResult: any;

      httpClient.get('/api/tenders').subscribe({
        error: (err) => { errorResult = err; }
      });

      const req = httpTesting.expectOne('/api/tenders');
      req.flush(null, { status: 503, statusText: 'Service Unavailable' });

      expect(errorResult.message).toBe('Service unavailable');
    });

    it('should handle network errors (status 0)', () => {
      let errorResult: any;

      httpClient.get('/api/tenders').subscribe({
        error: (err) => { errorResult = err; }
      });

      const req = httpTesting.expectOne('/api/tenders');
      // Simulate a network error using ProgressEvent which creates a client-side ErrorEvent-like error
      req.error(new ProgressEvent('error'), { status: 0, statusText: 'Unknown Error' });

      // Network errors have status 0, handled by the default case
      expect(errorResult).toBeDefined();
      expect(errorResult.message).toBeDefined();
    });

    it('should log error to console', () => {
      spyOn(console, 'error');

      httpClient.get('/api/tenders').subscribe({
        error: () => { /* expected */ }
      });

      const req = httpTesting.expectOne('/api/tenders');
      req.flush(null, { status: 500, statusText: 'Internal Server Error' });

      expect(console.error).toHaveBeenCalled();
    });
  });
});
