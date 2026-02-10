import { Page, Locator } from '@playwright/test';

/**
 * Check if a locator is visible, with a hard Node.js timeout that ALWAYS fires.
 * This prevents hanging when Angular's dev server blocks JS execution.
 */
export async function safeIsVisible(locator: Locator, timeoutMs = 8000): Promise<boolean> {
  return Promise.race([
    locator.isVisible({ timeout: timeoutMs }).catch(() => false),
    new Promise<boolean>(resolve => setTimeout(() => resolve(false), timeoutMs + 2000)),
  ]);
}

/**
 * Navigate to a URL with bounded timeout. Never throws.
 */
export async function safeGoto(page: Page, url: string, timeoutMs = 15000): Promise<boolean> {
  try {
    await Promise.race([
      page.goto(url, { timeout: timeoutMs, waitUntil: 'domcontentloaded' }),
      new Promise<null>(resolve => setTimeout(() => resolve(null), timeoutMs + 2000)),
    ]);
    return true;
  } catch {
    return false;
  }
}

/**
 * Navigate to a URL and check if specific content rendered.
 * Returns true if page loaded and content is visible.
 */
export async function safeGotoAndCheck(
  page: Page,
  url: string,
  contentSelector: string,
  gotoTimeout = 15000,
  visibleTimeout = 8000,
): Promise<boolean> {
  const navigated = await safeGoto(page, url, gotoTimeout);
  if (!navigated) return false;
  return safeIsVisible(page.locator(contentSelector).first(), visibleTimeout);
}

/**
 * Safely click a tab on the tender details page.
 * Wraps the click + wait in a bounded timeout.
 */
export async function safeClickTab(
  page: Page,
  tabName: string,
  timeoutMs = 10000,
): Promise<boolean> {
  try {
    const tab = page.locator(`.p-tabview-nav li`).filter({ hasText: tabName }).first();
    const isVisible = await safeIsVisible(tab, 5000);
    if (!isVisible) return false;
    await Promise.race([
      tab.click(),
      new Promise<void>(resolve => setTimeout(resolve, timeoutMs)),
    ]);
    // Brief settle time
    await page.waitForTimeout(500);
    return true;
  } catch {
    return false;
  }
}

/**
 * Safely execute page.evaluate with a Node.js timeout.
 * Returns null if evaluation hangs or fails.
 */
export async function safeEvaluate<T>(
  page: Page,
  fn: () => T,
  timeoutMs = 5000,
): Promise<T | null> {
  try {
    return await Promise.race([
      page.evaluate(fn),
      new Promise<null>(resolve => setTimeout(() => resolve(null), timeoutMs)),
    ]);
  } catch {
    return null;
  }
}

/**
 * Safely wait for a URL pattern with bounded timeout. Never throws.
 */
export async function safeWaitForURL(
  page: Page,
  urlPattern: RegExp,
  timeoutMs = 15000,
): Promise<boolean> {
  try {
    await Promise.race([
      page.waitForURL(urlPattern, { timeout: timeoutMs }),
      new Promise<null>(resolve => setTimeout(() => resolve(null), timeoutMs + 2000)),
    ]);
    return urlPattern.test(page.url());
  } catch {
    return urlPattern.test(page.url());
  }
}
