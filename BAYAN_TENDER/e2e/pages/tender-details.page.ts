import { Page, Locator, expect } from '@playwright/test';

export class TenderDetailsPage {
  readonly page: Page;
  private readonly title: Locator;
  private readonly statusTag: Locator;
  private readonly reference: Locator;
  private readonly editButton: Locator;
  private readonly publishButton: Locator;
  private readonly tabView: Locator;
  private readonly breadcrumb: Locator;

  constructor(page: Page) {
    this.page = page;
    this.title = page.locator('[data-testid="tender-title"], .tender-title-section h1');
    this.statusTag = page.locator('[data-testid="tender-status"], .tender-meta p-tag');
    this.reference = page.locator('[data-testid="tender-reference"], .reference');
    this.editButton = page.locator('[data-testid="edit-tender-btn"], button:has-text("Edit")');
    this.publishButton = page.locator('[data-testid="publish-tender-btn"], button:has-text("Publish")');
    this.tabView = page.locator('p-tabView');
    this.breadcrumb = page.locator('p-breadcrumb');
  }

  async goto(tenderId: string | number) {
    await this.page.goto(`/tenders/${tenderId}`, { timeout: 15000, waitUntil: 'domcontentloaded' });
  }

  async expectLoaded(expectedTitle?: string) {
    await expect(this.title).toBeVisible({ timeout: 15000 });
    if (expectedTitle) {
      await expect(this.title).toContainText(expectedTitle, { timeout: 10000 });
    }
  }

  async getStatus(): Promise<string | null> {
    return await this.statusTag.textContent();
  }

  async getReference(): Promise<string | null> {
    return await this.reference.textContent();
  }

  async clickTab(tabName: string) {
    const tab = this.tabView.locator(`[role="tab"]:has-text("${tabName}"), .p-tabview-nav li:has-text("${tabName}")`).first();
    await tab.click();
  }

  async clickEdit() {
    await this.editButton.click();
  }

  async clickPublish() {
    await this.publishButton.click();
  }

  async expectStatus(expected: string) {
    await expect(this.statusTag).toContainText(expected);
  }

  async isEditVisible(): Promise<boolean> {
    return await this.editButton.isVisible();
  }

  async isPublishVisible(): Promise<boolean> {
    return await this.publishButton.isVisible();
  }

  async getTabNames(): Promise<string[]> {
    const tabs = this.tabView.locator('.p-tabview-nav li');
    const count = await tabs.count();
    const names: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await tabs.nth(i).textContent();
      if (text) names.push(text.trim());
    }
    return names;
  }

  async expectTabVisible(tabName: string) {
    await expect(this.tabView.locator(`.p-tabview-nav li:has-text("${tabName}")`).first()).toBeVisible();
  }

  async getActivityLogCount(): Promise<number> {
    return await this.page.locator('.activity-item').count();
  }

  async getBidderCount(): Promise<number> {
    return await this.page.locator('.bidders-preview-card .p-datatable-tbody > tr').count();
  }
}
