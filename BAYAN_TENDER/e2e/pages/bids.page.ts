import { Page, Locator, expect } from '@playwright/test';

export class BidsPage {
  readonly page: Page;
  private readonly table: Locator;
  private readonly openBidsButton: Locator;
  private readonly downloadAllButton: Locator;
  private readonly emptyState: Locator;

  constructor(page: Page) {
    this.page = page;
    this.table = page.locator('[data-testid="bids-table"], p-table');
    this.openBidsButton = page.locator('[data-testid="open-bids-btn"], button:has-text("Open Bids"), button:has-text("Open All")');
    this.downloadAllButton = page.locator('[data-testid="download-all-bids"], button:has-text("Download All")');
    this.emptyState = page.locator('[data-testid="bids-empty"], .empty-state');
  }

  async expectLoaded() {
    await this.page.waitForTimeout(1000);
  }

  async getBidCount(): Promise<number> {
    return await this.table.locator('.p-datatable-tbody > tr').count();
  }

  async getBidByBidder(bidderName: string): Promise<Locator> {
    return this.table.locator(`tr:has-text("${bidderName}")`);
  }

  async openAllBids() {
    await this.openBidsButton.click();
    // Confirm irreversible action
    const confirmDialog = this.page.locator('p-confirmDialog, .p-dialog:visible');
    if (await confirmDialog.isVisible()) {
      await confirmDialog.locator('button:has-text("Yes"), .p-confirm-dialog-accept').click();
    }
  }

  async disqualifyBid(bidderName: string, reason: string) {
    const row = this.table.locator(`tr:has-text("${bidderName}")`);
    await row.locator('button:has(.pi-ban), button:has-text("Disqualify")').click();
    const dialog = this.page.locator('p-dialog:visible');
    await dialog.waitFor({ state: 'visible' });
    await dialog.locator('textarea').first().fill(reason);
    await dialog.locator('button:has-text("Confirm"), button:has-text("Disqualify")').click();
  }

  async downloadAllBids() {
    await this.downloadAllButton.click();
  }

  async isEmptyStateVisible(): Promise<boolean> {
    return await this.emptyState.isVisible();
  }
}
