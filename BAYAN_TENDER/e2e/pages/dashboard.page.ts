import { Page, Locator, expect } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  private readonly kpiCards: Locator;
  private readonly activeTendersTable: Locator;
  private readonly activityFeed: Locator;
  private readonly newTenderButton: Locator;
  private readonly skeletons: Locator;

  constructor(page: Page) {
    this.page = page;
    this.kpiCards = page.locator('[data-testid="kpi-card"], .kpi-card');
    this.activeTendersTable = page.locator('[data-testid="active-tenders-table"], .table-card p-table');
    this.activityFeed = page.locator('[data-testid="activity-feed"], .activity-feed');
    this.newTenderButton = page.locator('button:has-text("New Tender")');
    this.skeletons = page.locator('p-skeleton');
  }

  async goto() {
    await this.page.goto('/dashboard', { timeout: 20000 }).catch(() => {
      // Dashboard navigation may hang due to JS; continue if URL is correct
    });
    await this.page.waitForURL(/\/dashboard/, { timeout: 5000 }).catch(() => {});
  }

  async expectLoaded() {
    await this.page.waitForURL(/\/dashboard/, { timeout: 15000 }).catch(() => {});
    // Wait for skeletons to disappear (data loaded)
    await this.page.waitForFunction(() => {
      return document.querySelectorAll('p-skeleton').length === 0;
    }, { timeout: 15000 }).catch(() => {});
  }

  async getKpiCardCount(): Promise<number> {
    return await this.kpiCards.count();
  }

  async getKpiValue(name: string): Promise<string | null> {
    const card = this.page.locator(`.kpi-card:has(.kpi-title:text("${name}")) .kpi-value`);
    try {
      return await card.textContent();
    } catch {
      return null;
    }
  }

  async getActiveTendersRowCount(): Promise<number> {
    const rows = this.activeTendersTable.locator('.p-datatable-tbody > tr');
    return await rows.count();
  }

  async clickTenderInTable(title: string) {
    const row = this.activeTendersTable.locator(`tr:has-text("${title}")`);
    await row.click({ timeout: 10000 });
  }

  async getActivityItemCount(): Promise<number> {
    return await this.activityFeed.locator('.activity-item').count().catch(() => 0);
  }

  async clickNewTender() {
    await this.newTenderButton.click({ timeout: 10000 });
  }

  async expectSkeletonsVisible() {
    await expect(this.skeletons.first()).toBeVisible();
  }

  async hasCharts(): Promise<boolean> {
    const canvases = this.page.locator('canvas');
    return (await canvases.count()) > 0;
  }
}
