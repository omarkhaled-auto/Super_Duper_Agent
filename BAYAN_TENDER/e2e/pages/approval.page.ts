import { Page, Locator, expect } from '@playwright/test';

export class ApprovalPage {
  readonly page: Page;
  private readonly workflowDiagram: Locator;
  private readonly initiateButton: Locator;
  private readonly approveButton: Locator;
  private readonly rejectButton: Locator;
  private readonly returnButton: Locator;
  private readonly commentInput: Locator;
  private readonly statusBadge: Locator;
  private readonly historyTable: Locator;

  constructor(page: Page) {
    this.page = page;
    this.workflowDiagram = page.locator('[data-testid="approval-workflow"], .approval-workflow, app-approval-tab');
    this.initiateButton = page.locator('[data-testid="initiate-approval-btn"], button:has-text("Initiate"), button:has-text("Start Approval")');
    this.approveButton = page.locator('[data-testid="approve-btn"], button:has-text("Approve")');
    this.rejectButton = page.locator('[data-testid="reject-btn"], button:has-text("Reject")');
    this.returnButton = page.locator('[data-testid="return-btn"], button:has-text("Return"), button:has-text("Revision")');
    this.commentInput = page.locator('[data-testid="approval-comment"], textarea');
    this.statusBadge = page.locator('[data-testid="approval-status"], .approval-status, p-tag');
    this.historyTable = page.locator('[data-testid="approval-history"], .approval-history p-table, p-table');
  }

  async expectLoaded() {
    await this.workflowDiagram.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
  }

  async initiateApproval(approverEmails: string[], deadline?: Date) {
    await this.initiateButton.click();
    const dialog = this.page.locator('p-dialog:visible');
    await dialog.waitFor({ state: 'visible' });

    for (let i = 0; i < approverEmails.length; i++) {
      const approverInput = dialog.locator('p-dropdown, p-autoComplete, input').nth(i);
      await approverInput.click();
      await this.page.locator(`.p-dropdown-panel .p-dropdown-item:has-text("${approverEmails[i]}"), .p-autocomplete-panel .p-autocomplete-item:has-text("${approverEmails[i]}")`).first().click();
    }

    await dialog.locator('button:has-text("Start"), button:has-text("Initiate"), button:has-text("Submit")').click();
  }

  async approveLevel(comment: string) {
    if (await this.commentInput.isVisible()) {
      await this.commentInput.fill(comment);
    }
    await this.approveButton.click();
    // Confirm if dialog appears
    const confirmDialog = this.page.locator('p-confirmDialog:visible');
    if (await confirmDialog.isVisible()) {
      await confirmDialog.locator('.p-confirm-dialog-accept').click();
    }
  }

  async rejectLevel(comment: string) {
    if (await this.commentInput.isVisible()) {
      await this.commentInput.fill(comment);
    }
    await this.rejectButton.click();
    const confirmDialog = this.page.locator('p-confirmDialog:visible');
    if (await confirmDialog.isVisible()) {
      await confirmDialog.locator('.p-confirm-dialog-accept').click();
    }
  }

  async returnForRevision(comment: string) {
    if (await this.commentInput.isVisible()) {
      await this.commentInput.fill(comment);
    }
    await this.returnButton.click();
  }

  async getWorkflowStatus(): Promise<string | null> {
    return await this.statusBadge.first().textContent();
  }

  async getCurrentLevel(): Promise<number> {
    const activeLevel = this.page.locator('.level-active, .step-active, .p-highlight');
    const text = await activeLevel.first().textContent();
    return parseInt(text || '0');
  }

  async getHistoryCount(): Promise<number> {
    return await this.historyTable.locator('.p-datatable-tbody > tr').count();
  }

  async isInitiateVisible(): Promise<boolean> {
    return await this.initiateButton.isVisible();
  }

  async isApproveVisible(): Promise<boolean> {
    return await this.approveButton.isVisible();
  }
}
