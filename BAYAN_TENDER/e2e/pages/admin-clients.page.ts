import { Page, Locator, expect } from '@playwright/test';

export class AdminClientsPage {
  readonly page: Page;
  private readonly table: Locator;
  private readonly searchInput: Locator;
  private readonly createButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.table = page.locator('[data-testid="clients-table"], p-table');
    this.searchInput = page.locator('[data-testid="clients-search"], input[placeholder*="Search"], p-iconField input');
    this.createButton = page.locator('[data-testid="create-client-btn"], button:has-text("Add Client"), button:has-text("Create"), button:has-text("New")');
  }

  async goto() {
    await this.page.goto('/admin/clients');
  }

  async expectLoaded() {
    await expect(this.page).toHaveURL(/\/admin\/clients/);
  }

  async getClientCount(): Promise<number> {
    return await this.table.locator('.p-datatable-tbody > tr').count();
  }

  async searchClient(query: string) {
    await this.searchInput.fill(query);
    await this.page.waitForTimeout(500);
  }

  async createClient(data: { name: string; contactPerson?: string; email?: string }) {
    await this.createButton.click();
    const dialog = this.page.locator('p-dialog:visible');
    await dialog.waitFor({ state: 'visible' });
    await dialog.locator('input[formControlName="name"], input').first().fill(data.name);
    if (data.contactPerson) {
      await dialog.locator('input[formControlName="contactPerson"], input').nth(1).fill(data.contactPerson);
    }
    if (data.email) {
      await dialog.locator('input[formControlName="email"], input[type="email"]').fill(data.email);
    }
    await dialog.locator('button:has-text("Save"), button:has-text("Create")').click();
  }

  async editClient(name: string, newData: { name?: string }) {
    const row = this.table.locator(`tr:has-text("${name}")`);
    await row.locator('button:has(.pi-pencil)').click();
    const dialog = this.page.locator('p-dialog:visible');
    await dialog.waitFor({ state: 'visible' });
    if (newData.name) {
      await dialog.locator('input').first().clear();
      await dialog.locator('input').first().fill(newData.name);
    }
    await dialog.locator('button:has-text("Save"), button:has-text("Update")').click();
  }

  async expectClientInList(name: string) {
    await expect(this.table.locator(`tr:has-text("${name}")`).first()).toBeVisible();
  }
}
