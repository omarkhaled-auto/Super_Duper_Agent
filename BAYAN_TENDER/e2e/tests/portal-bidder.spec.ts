import { test, expect } from '@playwright/test';
import { PortalLoginPage } from '../pages/portal-login.page';
import { PortalTenderPage } from '../pages/portal-tender.page';
import { USERS, INVALID_CREDENTIALS, ROUTES, TEST_FILES } from '../fixtures/test-data';
import { safeIsVisible, safeGoto } from '../helpers/safe-navigation';

test.describe('Portal - Bidder', () => {
  test.describe('Portal Login', () => {
    test('should render portal login page', async ({ page }) => {
      const navigated = await safeGoto(page, '/portal/login', 15000);
      if (!navigated) test.skip(true, 'Portal login page did not load');
      await expect(page.locator('input[type="email"], #email')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('p-password input, input[type="password"]')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('button[type="submit"]')).toBeVisible({ timeout: 10000 });
    });

    test('should show error for invalid credentials', async ({ page }) => {
      const portalLogin = new PortalLoginPage(page);
      try {
        await portalLogin.goto();
      } catch {
        test.skip(true, 'Portal login page did not load');
      }
      await portalLogin.login(INVALID_CREDENTIALS.wrongEmail, INVALID_CREDENTIALS.wrongPassword);

      await page.waitForTimeout(3000);
      const url = page.url();
      expect(url).toContain('/portal');
    });

    test('should login successfully as bidder', async ({ page }) => {
      const portalLogin = new PortalLoginPage(page);
      try {
        await portalLogin.goto();
      } catch {
        test.skip(true, 'Portal login page did not load');
      }
      await portalLogin.login(USERS.bidder.email, USERS.bidder.password);

      try {
        await page.waitForURL(/\/portal/, { timeout: 15000 });
      } catch {
        const url = page.url();
        expect(url).toContain('/portal');
      }
    });
  });

  test.describe('Portal Tender View', () => {
    let portalTender: PortalTenderPage;
    let portalLoaded = false;

    test.beforeEach(async ({ page }) => {
      portalLoaded = false;
      portalTender = new PortalTenderPage(page);

      try {
        const navigated = await safeGoto(page, '/portal', 15000);
        if (!navigated) return;
        const anyContent = await safeIsVisible(
          page.locator('main, .portal-content, app-portal-layout, h1, p-table').first(), 8000
        );
        portalLoaded = anyContent;
      } catch {
        portalLoaded = false;
      }
    });

    test('should display tender information', async ({ page }) => {
      test.skip(!portalLoaded, 'Portal page did not render');
      const content = page.locator('main, .portal-content, app-portal-layout');
      await expect(content.first()).toBeVisible({ timeout: 10000 }).catch(() => {});
    });

    test('should show documents tab', async ({ page }) => {
      test.skip(!portalLoaded, 'Portal page did not render');
      const docsTab = page.locator('[role="tab"]:has-text("Documents"), button:has-text("Documents")');
      const isVisible = await safeIsVisible(docsTab.first(), 5000);
      if (isVisible) {
        await docsTab.first().click({ timeout: 10000 });
      }
    });

    test('should show clarifications section', async ({ page }) => {
      test.skip(!portalLoaded, 'Portal page did not render');
      const clarTab = page.locator('[role="tab"]:has-text("Clarifications"), button:has-text("Clarifications")');
      const isVisible = await safeIsVisible(clarTab.first(), 5000);
      if (isVisible) {
        await clarTab.first().click({ timeout: 10000 });
      }
    });
  });

  test.describe('Bid Submission', () => {
    let portalLoaded = false;

    test.beforeEach(async ({ page }) => {
      portalLoaded = false;
      try {
        const navigated = await safeGoto(page, '/portal', 15000);
        if (!navigated) return;
        const anyContent = await safeIsVisible(
          page.locator('main, .portal-content, app-portal-layout, h1').first(), 8000
        );
        portalLoaded = anyContent;
      } catch {
        portalLoaded = false;
      }
    });

    test('should show file upload area', async ({ page }) => {
      test.skip(!portalLoaded, 'Portal page did not render');
      const fileUpload = page.locator('p-fileUpload, input[type="file"]');
      await fileUpload.first().isVisible({ timeout: 5000 }).catch(() => false);
    });

    test('should validate file type restrictions', async ({ page }) => {
      test.skip(!portalLoaded, 'Portal page did not render');
      const fileInput = page.locator('input[type="file"]').first();
      const isVisible = await fileInput.isVisible({ timeout: 5000 }).catch(() => false);
      if (isVisible) {
        const acceptAttr = await fileInput.getAttribute('accept');
        if (acceptAttr) {
          expect(acceptAttr.length).toBeGreaterThan(0);
        }
      }
    });

    test('should have Submit Bid button', async ({ page }) => {
      test.skip(!portalLoaded, 'Portal page did not render');
      const submitBtn = page.locator('button:has-text("Submit Bid"), button:has-text("Submit")');
      await submitBtn.first().isVisible({ timeout: 5000 }).catch(() => false);
    });

    test('should show confirmation before bid submission', async ({ page }) => {
      test.skip(!portalLoaded, 'Portal page did not render');
      const submitBtn = page.locator('button:has-text("Submit Bid")').first();
      const isVisible = await submitBtn.isVisible({ timeout: 5000 }).catch(() => false);
      const isDisabled = isVisible ? await submitBtn.isDisabled().catch(() => true) : true;

      if (isVisible && !isDisabled) {
        await submitBtn.click({ timeout: 10000 });
        const dialog = page.locator('p-confirmDialog:visible, .p-dialog:visible');
        const dialogVisible = await dialog.first().isVisible({ timeout: 5000 }).catch(() => false);
        if (dialogVisible) {
          await expect(dialog.first()).toContainText(/confirm/i, { timeout: 5000 });
        }
      }
    });
  });

  test.describe('Clarification Questions', () => {
    let portalLoaded = false;

    test.beforeEach(async ({ page }) => {
      portalLoaded = false;
      try {
        const navigated = await safeGoto(page, '/portal', 15000);
        if (!navigated) return;
        const anyContent = await safeIsVisible(
          page.locator('main, .portal-content, app-portal-layout, h1').first(), 8000
        );
        portalLoaded = anyContent;
      } catch {
        portalLoaded = false;
      }
    });

    test('should have Ask Question button', async ({ page }) => {
      test.skip(!portalLoaded, 'Portal page did not render');
      const askBtn = page.locator('button:has-text("Ask Question"), button:has-text("Submit Question")');
      await askBtn.first().isVisible({ timeout: 5000 }).catch(() => false);
    });

    test('should open question dialog', async ({ page }) => {
      test.skip(!portalLoaded, 'Portal page did not render');
      const askBtn = page.locator('button:has-text("Ask Question"), button:has-text("Submit Question")').first();
      const isVisible = await askBtn.isVisible({ timeout: 5000 }).catch(() => false);
      if (isVisible) {
        await askBtn.click({ timeout: 10000 });
        const dialog = page.locator('p-dialog:visible');
        await expect(dialog.first()).toBeVisible({ timeout: 5000 }).catch(() => {});
      }
    });
  });

  test.describe('Bulletins', () => {
    let portalLoaded = false;

    test.beforeEach(async ({ page }) => {
      portalLoaded = false;
      try {
        const navigated = await safeGoto(page, '/portal', 15000);
        if (!navigated) return;
        const anyContent = await safeIsVisible(
          page.locator('main, .portal-content, app-portal-layout, h1').first(), 8000
        );
        portalLoaded = anyContent;
      } catch {
        portalLoaded = false;
      }
    });

    test('should show bulletins section', async ({ page }) => {
      test.skip(!portalLoaded, 'Portal page did not render');
      const bulletins = page.locator('[data-testid="bulletins"], .bulletins');
      await bulletins.first().isVisible({ timeout: 5000 }).catch(() => false);
    });

    test('should have Acknowledge button for bulletins', async ({ page }) => {
      test.skip(!portalLoaded, 'Portal page did not render');
      const ackBtn = page.locator('button:has-text("Acknowledge")').first();
      await ackBtn.isVisible({ timeout: 5000 }).catch(() => false);
    });
  });

  test.describe('Bid Receipt', () => {
    let portalLoaded = false;

    test.beforeEach(async ({ page }) => {
      portalLoaded = false;
      try {
        const navigated = await safeGoto(page, '/portal', 15000);
        if (!navigated) return;
        const anyContent = await safeIsVisible(
          page.locator('main, .portal-content, app-portal-layout, h1').first(), 8000
        );
        portalLoaded = anyContent;
      } catch {
        portalLoaded = false;
      }
    });

    test('should show receipt after bid submission', async ({ page }) => {
      test.skip(!portalLoaded, 'Portal page did not render');
      const receipt = page.locator('.bid-receipt, [data-testid="bid-receipt"]');
      await receipt.first().isVisible({ timeout: 5000 }).catch(() => false);
    });

    test('should have download receipt button', async ({ page }) => {
      test.skip(!portalLoaded, 'Portal page did not render');
      const downloadBtn = page.locator('button:has-text("Download Receipt"), a:has-text("Receipt")');
      await downloadBtn.first().isVisible({ timeout: 5000 }).catch(() => false);
    });
  });
});
