import { Page, Locator, expect } from '@playwright/test';

export class AdminBiddersPage {
  readonly page: Page;
  private readonly table: Locator;
  private readonly searchInput: Locator;
  private readonly createButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.table = page.locator('[data-testid="bidders-table"], p-table');
    this.searchInput = page.locator('[data-testid="bidders-search"], input[placeholder*="Search"], p-iconField input');
    this.createButton = page.locator('[data-testid="create-bidder-btn"], button:has-text("Add Bidder"), button:has-text("Create"), button:has-text("New")');
  }

  async goto() {
    await this.page.goto('/admin/bidders');
  }

  async expectLoaded() {
    await expect(this.page).toHaveURL(/\/admin\/bidders/);
  }

  async getBidderCount(): Promise<number> {
    return await this.table.locator('.p-datatable-tbody > tr').count();
  }

  async searchBidder(query: string) {
    await this.searchInput.fill(query);
    await this.page.waitForTimeout(500);
  }

  async createBidder(data: { companyNameEn: string; email: string; crNumber?: string }) {
    await this.createButton.click();
    const dialog = this.page.locator('p-dialog:visible');
    await dialog.waitFor({ state: 'visible' });
    await dialog.locator('input[formControlName="companyNameEn"], input').first().fill(data.companyNameEn);
    await dialog.locator('input[formControlName="email"], input[type="email"]').fill(data.email);
    if (data.crNumber) {
      await dialog.locator('input[formControlName="crNumber"]').fill(data.crNumber);
    }
    await dialog.locator('button:has-text("Save"), button:has-text("Create")').click();
  }

  async editBidder(companyName: string, newData: { email?: string }) {
    const row = this.table.locator(`tr:has-text("${companyName}")`);
    await row.locator('button:has(.pi-pencil)').click();
    const dialog = this.page.locator('p-dialog:visible');
    await dialog.waitFor({ state: 'visible' });
    if (newData.email) {
      await dialog.locator('input[type="email"]').clear();
      await dialog.locator('input[type="email"]').fill(newData.email);
    }
    await dialog.locator('button:has-text("Save"), button:has-text("Update")').click();
  }

  async expectBidderInList(companyName: string) {
    await expect(this.table.locator(`tr:has-text("${companyName}")`).first()).toBeVisible();
  }
}
