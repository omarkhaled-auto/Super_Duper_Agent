import { Page, Locator, expect } from '@playwright/test';

export class PortalTenderPage {
  readonly page: Page;
  private readonly documentsTab: Locator;
  private readonly clarificationsTab: Locator;
  private readonly submitBidButton: Locator;
  private readonly fileUpload: Locator;
  private readonly bidReceipt: Locator;

  constructor(page: Page) {
    this.page = page;
    this.documentsTab = page.locator('[data-testid="portal-documents-tab"], [role="tab"]:has-text("Documents")');
    this.clarificationsTab = page.locator('[data-testid="portal-clarifications-tab"], [role="tab"]:has-text("Clarifications")');
    this.submitBidButton = page.locator('[data-testid="submit-bid-btn"], button:has-text("Submit Bid"), button:has-text("Submit")');
    this.fileUpload = page.locator('[data-testid="bid-file-upload"], p-fileUpload, input[type="file"]');
    this.bidReceipt = page.locator('[data-testid="bid-receipt"], .bid-receipt');
  }

  async viewDocuments() {
    if (await this.documentsTab.isVisible()) {
      await this.documentsTab.click();
    }
  }

  async downloadDocument(docName: string) {
    const doc = this.page.locator(`[data-testid="document-item"]:has-text("${docName}"), tr:has-text("${docName}")`);
    await doc.locator('button:has(.pi-download), a:has-text("Download")').click();
  }

  async submitClarification(subject: string, question: string) {
    if (await this.clarificationsTab.isVisible()) {
      await this.clarificationsTab.click();
    }
    await this.page.locator('button:has-text("Ask Question"), button:has-text("Submit Question")').click();
    const dialog = this.page.locator('p-dialog:visible');
    await dialog.waitFor({ state: 'visible' });
    await dialog.locator('input').first().fill(subject);
    await dialog.locator('textarea').first().fill(question);
    await dialog.locator('button:has-text("Submit")').click();
  }

  async acknowledgeBulletin(bulletinTitle: string) {
    const bulletin = this.page.locator(`.bulletin-item:has-text("${bulletinTitle}"), tr:has-text("${bulletinTitle}")`);
    await bulletin.locator('button:has-text("Acknowledge")').click();
  }

  async uploadBidDocument(filePath: string) {
    const fileInput = this.page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(filePath);
  }

  async submitBid() {
    await this.submitBidButton.click();
    // Confirm submission
    const confirmDialog = this.page.locator('p-confirmDialog:visible, .p-dialog:visible');
    if (await confirmDialog.isVisible()) {
      await confirmDialog.locator('button:has-text("Yes"), button:has-text("Confirm"), .p-confirm-dialog-accept').click();
    }
  }

  async isSubmitBidEnabled(): Promise<boolean> {
    return !(await this.submitBidButton.isDisabled());
  }

  async viewReceipt(): Promise<string | null> {
    return await this.bidReceipt.textContent();
  }

  async downloadReceipt() {
    await this.page.locator('button:has-text("Download Receipt"), a:has-text("Receipt")').click();
  }
}
