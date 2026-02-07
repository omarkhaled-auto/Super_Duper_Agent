import { Page, Locator, expect } from '@playwright/test';

export class AdminUsersPage {
  readonly page: Page;
  private readonly table: Locator;
  private readonly searchInput: Locator;
  private readonly createButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.table = page.locator('[data-testid="users-table"], p-table');
    this.searchInput = page.locator('[data-testid="users-search"], input[placeholder*="Search"], p-iconField input');
    this.createButton = page.locator('[data-testid="create-user-btn"], button:has-text("Add User"), button:has-text("Create")');
  }

  async goto() {
    await this.page.goto('/admin/users');
  }

  async expectLoaded() {
    await expect(this.page).toHaveURL(/\/admin\/users/);
    await this.table.waitFor({ state: 'visible', timeout: 10000 });
  }

  async getUserCount(): Promise<number> {
    return await this.table.locator('.p-datatable-tbody > tr').count();
  }

  async searchUser(query: string) {
    await this.searchInput.fill(query);
    await this.page.waitForTimeout(500);
  }

  async expectUserInList(email: string) {
    await expect(this.table.locator(`tr:has-text("${email}")`).first()).toBeVisible();
  }

  async expectUserNotInList(email: string) {
    await expect(this.table.locator(`tr:has-text("${email}")`)).toHaveCount(0);
  }

  async clickCreateUser() {
    await this.createButton.click();
  }
}
