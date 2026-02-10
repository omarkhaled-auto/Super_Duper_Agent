import { Page, Locator, expect } from '@playwright/test';

export class EvaluationPage {
  readonly page: Page;
  private readonly comparableSheet: Locator;
  private readonly scorecard: Locator;
  private readonly calculateButton: Locator;
  private readonly awardPackButton: Locator;
  private readonly sensitivityButton: Locator;
  private readonly exportButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.comparableSheet = page.locator('[data-testid="comparable-sheet"], .comparable-sheet, app-comparable-sheet');
    this.scorecard = page.locator('[data-testid="scorecard"], app-combined-scorecard');
    this.calculateButton = page.locator('[data-testid="calculate-scores-btn"], button:has-text("Calculate"), button:has-text("Recalculate")');
    this.awardPackButton = page.locator('[data-testid="award-pack-btn"], button:has-text("Award Pack"), button:has-text("Generate")');
    this.sensitivityButton = page.locator('[data-testid="sensitivity-btn"], button:has-text("Sensitivity")');
    this.exportButton = page.locator('[data-testid="export-comparable-btn"], button:has-text("Export")');
  }

  async expectLoaded() {
    await this.page.waitForTimeout(1000);
  }

  async viewComparableSheet() {
    const tab = this.page.locator('[role="tab"]:has-text("Comparable"), button:has-text("Comparable Sheet")').first();
    if (await tab.isVisible()) {
      await tab.click();
    }
  }

  async expectComparableSheetHasRows(minCount: number) {
    const rows = this.comparableSheet.locator('.p-datatable-tbody > tr, table tbody tr');
    await expect(rows).toHaveCount(minCount, { timeout: 10000 });
  }

  async calculateCommercialScores() {
    await this.calculateButton.click();
  }

  async viewCombinedScorecard() {
    const tab = this.page.locator('[role="tab"]:has-text("Scorecard"), button:has-text("Combined Scorecard")').first();
    if (await tab.isVisible()) {
      await tab.click();
    }
  }

  async runSensitivityAnalysis() {
    await this.sensitivityButton.click();
    const dialog = this.page.locator('p-dialog:visible');
    if (await dialog.isVisible()) {
      await dialog.locator('button:has-text("Run"), button:has-text("Analyze")').click();
    }
  }

  async generateAwardPack() {
    await this.awardPackButton.click();
    const dialog = this.page.locator('p-dialog:visible');
    if (await dialog.isVisible()) {
      await dialog.locator('button:has-text("Generate"), button:has-text("Create")').click();
    }
  }

  async exportComparableSheet() {
    await this.exportButton.click();
  }

  async getBidderCount(): Promise<number> {
    // Count columns representing bidders in comparable sheet
    const headers = this.comparableSheet.locator('th');
    return Math.max(0, (await headers.count()) - 2); // Subtract item/description columns
  }

  async getExceptionsCount(): Promise<number> {
    const panel = this.page.locator('app-exceptions-panel, [data-testid="exceptions-panel"]');
    return await panel.locator('.exception-item, tr').count();
  }
}
