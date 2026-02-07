import { Page, Locator, expect } from '@playwright/test';

export class ClarificationsPage {
  readonly page: Page;
  private readonly table: Locator;
  private readonly createButton: Locator;
  private readonly filterDropdown: Locator;
  private readonly emptyState: Locator;

  constructor(page: Page) {
    this.page = page;
    this.table = page.locator('[data-testid="clarifications-table"], p-table');
    this.createButton = page.locator('[data-testid="create-clarification-btn"], button:has-text("New"), button:has-text("Create")');
    this.filterDropdown = page.locator('[data-testid="clarification-filter"], p-dropdown');
    this.emptyState = page.locator('[data-testid="clarifications-empty"], .empty-state');
  }

  async expectLoaded() {
    await this.page.waitForTimeout(1000);
  }

  async createQuestion(subject: string, question: string) {
    await this.createButton.click();
    const dialog = this.page.locator('p-dialog:visible');
    await dialog.waitFor({ state: 'visible' });
    await dialog.locator('input[formControlName="subject"], input').first().fill(subject);
    await dialog.locator('textarea[formControlName="question"], textarea').first().fill(question);
    await dialog.locator('button:has-text("Submit"), button:has-text("Save")').click();
  }

  async answerClarification(subject: string, answer: string) {
    const row = this.table.locator(`tr:has-text("${subject}")`);
    await row.locator('button:has(.pi-reply), button:has-text("Answer")').click();
    const dialog = this.page.locator('p-dialog:visible');
    await dialog.waitFor({ state: 'visible' });
    await dialog.locator('textarea').first().fill(answer);
    await dialog.locator('button:has-text("Submit"), button:has-text("Save")').click();
  }

  async approveClarification(subject: string) {
    const row = this.table.locator(`tr:has-text("${subject}")`);
    await row.locator('button:has(.pi-check), button:has-text("Approve")').click();
  }

  async createBulletin() {
    await this.page.locator('button:has-text("Generate Bulletin"), button:has-text("Publish")').click();
    const dialog = this.page.locator('p-dialog:visible');
    if (await dialog.isVisible()) {
      await dialog.locator('button:has-text("Generate"), button:has-text("Publish")').click();
    }
  }

  async filterByStatus(status: string) {
    await this.filterDropdown.click();
    await this.page.locator(`.p-dropdown-panel .p-dropdown-item:has-text("${status}")`).click();
  }

  async getCount(): Promise<number> {
    return await this.table.locator('.p-datatable-tbody > tr').count();
  }

  async isEmptyStateVisible(): Promise<boolean> {
    return await this.emptyState.isVisible();
  }
}
