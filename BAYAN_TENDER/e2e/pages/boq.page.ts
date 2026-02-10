import { Page, Locator, expect } from '@playwright/test';

export class BoqPage {
  readonly page: Page;
  private readonly treeTable: Locator;
  private readonly addSectionButton: Locator;
  private readonly addItemButton: Locator;
  private readonly importButton: Locator;
  private readonly exportButton: Locator;
  private readonly emptyState: Locator;

  constructor(page: Page) {
    this.page = page;
    this.treeTable = page.locator('[data-testid="boq-tree"], p-treeTable, p-table');
    this.addSectionButton = page.locator('[data-testid="add-section-btn"], button:has-text("Add Section")');
    this.addItemButton = page.locator('[data-testid="add-item-btn"], button:has-text("Add Item")');
    this.importButton = page.locator('[data-testid="import-boq-btn"], button:has-text("Import")');
    this.exportButton = page.locator('[data-testid="export-boq-btn"], button:has-text("Export")');
    this.emptyState = page.locator('[data-testid="boq-empty"], .empty-state');
  }

  async expectLoaded() {
    await this.page.waitForTimeout(1000);
  }

  async addSection(number: string, title: string) {
    await this.addSectionButton.click();
    const dialog = this.page.locator('p-dialog:visible');
    await dialog.waitFor({ state: 'visible' });
    await dialog.locator('input[formControlName="number"], input').first().fill(number);
    await dialog.locator('input[formControlName="title"], input').nth(1).fill(title);
    await dialog.locator('button:has-text("Save"), button:has-text("Add")').click();
  }

  async addItem(data: { number: string; description: string; uom: string; quantity: number }) {
    await this.addItemButton.click();
    const dialog = this.page.locator('p-dialog:visible');
    await dialog.waitFor({ state: 'visible' });
    await dialog.locator('input[formControlName="itemNumber"], input').first().fill(data.number);
    await dialog.locator('input[formControlName="description"], textarea, input').nth(1).fill(data.description);
    // UOM dropdown
    const uomDropdown = dialog.locator('p-dropdown').first();
    await uomDropdown.click();
    await this.page.locator(`.p-dropdown-panel .p-dropdown-item:has-text("${data.uom}")`).click();
    await dialog.locator('input[formControlName="quantity"], input[type="number"]').first().fill(data.quantity.toString());
    await dialog.locator('button:has-text("Save"), button:has-text("Add")').click();
  }

  async deleteItem(itemNumber: string) {
    const row = this.treeTable.locator(`tr:has-text("${itemNumber}")`);
    await row.locator('button[icon="pi pi-trash"], button:has(.pi-trash)').click();
    // Confirm deletion
    await this.page.locator('.p-confirm-dialog-accept, button:has-text("Yes")').click();
  }

  async importFromExcel(filePath: string) {
    await this.importButton.click();
    const dialog = this.page.locator('p-dialog:visible');
    await dialog.waitFor({ state: 'visible' });
    const fileInput = dialog.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
  }

  async exportTemplate() {
    await this.exportButton.click();
  }

  async getItemCount(): Promise<number> {
    return await this.treeTable.locator('.p-datatable-tbody > tr, .p-treetable-tbody > tr').count();
  }

  async getSectionCount(): Promise<number> {
    return await this.treeTable.locator('tr.section-row, tr:has(.p-treetable-toggler)').count();
  }

  async expandSection(title: string) {
    const row = this.treeTable.locator(`tr:has-text("${title}")`);
    const toggler = row.locator('.p-treetable-toggler, button[icon="pi pi-chevron-right"]');
    await toggler.click();
  }

  async isEmptyStateVisible(): Promise<boolean> {
    return await this.emptyState.isVisible();
  }
}
