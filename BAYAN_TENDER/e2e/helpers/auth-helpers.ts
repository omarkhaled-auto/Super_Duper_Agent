import { Page, expect } from '@playwright/test';

// ---------------------------------------------------------------------------
// UI-based Login / Logout
// ---------------------------------------------------------------------------

/**
 * Log in via the internal staff login page.
 *
 * Navigates to `/auth/login`, fills the email and password fields (PrimeNG
 * p-password wraps the real `<input>`), submits the form, and waits until the
 * browser has redirected to `/dashboard`.
 */
export async function loginViaUI(
  page: Page,
  email: string,
  password: string,
): Promise<void> {
  await page.goto('/auth/login');
  await page.waitForLoadState('networkidle');

  // Email field
  await page.locator('#email').fill(email);

  // PrimeNG p-password wraps the native input — locate it explicitly
  await page.locator('p-password input').fill(password);

  // Submit the form
  await page.locator('button[type="submit"]').click();

  // Wait for navigation to the dashboard
  await page.waitForURL('**/dashboard', { timeout: 15_000 });
}

/**
 * Log in via the external bidder portal login page.
 */
export async function loginPortalViaUI(
  page: Page,
  email: string,
  password: string,
): Promise<void> {
  await page.goto('/portal/login');
  await page.waitForLoadState('networkidle');

  await page.locator('#email').fill(email);
  await page.locator('p-password input').fill(password);
  await page.locator('button[type="submit"]').click();

  // Portal dashboard URL may vary; wait for any /portal route
  await page.waitForURL('**/portal/dashboard**', { timeout: 15_000 });
}

/**
 * Log out by opening the user menu in the header and clicking the logout item.
 * Waits until the browser has been redirected back to `/auth/login`.
 */
export async function logout(page: Page): Promise<void> {
  // Open the user/avatar menu in the top-right of the layout header
  const userMenu = page.locator(
    'header .user-menu, .layout-topbar .p-avatar, [data-testid="user-menu"]',
  );
  await userMenu.click();

  // Click the logout menu entry
  const logoutItem = page.locator(
    'text=Logout, text=Sign out, [data-testid="logout"]',
  ).first();
  await logoutItem.click();

  await page.waitForURL('**/auth/login', { timeout: 10_000 });
}

// ---------------------------------------------------------------------------
// URL Assertions
// ---------------------------------------------------------------------------

/**
 * Assert that the page has been redirected to the staff login page.
 */
export async function expectRedirectToLogin(page: Page): Promise<void> {
  await expect(page).toHaveURL(/\/auth\/login/);
}

/**
 * Assert that the page is currently on the dashboard.
 */
export async function expectOnDashboard(page: Page): Promise<void> {
  await expect(page).toHaveURL(/\/dashboard/);
}

// ---------------------------------------------------------------------------
// Token / Storage Utilities
// ---------------------------------------------------------------------------

/**
 * Retrieve the stored JWT access token from `localStorage`.
 *
 * Checks the BAYAN-specific key names used by StorageService and PortalService.
 */
export async function getStoredToken(page: Page): Promise<string | null> {
  return page.evaluate(() => {
    return (
      localStorage.getItem('bayan_access_token') ??
      localStorage.getItem('portal_access_token') ??
      sessionStorage.getItem('bayan_access_token') ??
      null
    );
  });
}

/**
 * Clear all authentication-related data from both localStorage and sessionStorage.
 *
 * Removes BAYAN-specific keys used by StorageService and PortalService.
 */
export async function clearAuth(page: Page): Promise<void> {
  await page.evaluate(() => {
    // Internal staff auth (StorageService)
    localStorage.removeItem('bayan_access_token');
    localStorage.removeItem('bayan_refresh_token');
    localStorage.removeItem('bayan_user');
    localStorage.removeItem('bayan_remember_me');
    sessionStorage.removeItem('bayan_access_token');
    sessionStorage.removeItem('bayan_refresh_token');
    sessionStorage.removeItem('bayan_user');
    // Portal bidder auth (PortalService)
    localStorage.removeItem('portal_access_token');
    localStorage.removeItem('portal_refresh_token');
    localStorage.removeItem('portal_user');
    localStorage.removeItem('portal_tender');
  });
}
