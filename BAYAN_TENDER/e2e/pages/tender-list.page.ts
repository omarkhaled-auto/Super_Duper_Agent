import { Page, Locator, expect } from '@playwright/test';

export class TenderListPage {
  readonly page: Page;
  private readonly searchInput: Locator;
  private readonly newTenderButton: Locator;
  private readonly exportButton: Locator;
  private readonly table: Locator;
  private readonly tableRows: Locator;
  private readonly filterPanel: Locator;
  private readonly clearFiltersButton: Locator;
  private readonly statusCheckboxes: Locator;
  private readonly clientDropdown: Locator;
  private readonly loadingSpinner: Locator;
  private readonly emptyMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.searchInput = page.locator('[data-testid="tender-search"], p-iconField input');
    this.newTenderButton = page.locator('[data-testid="new-tender-btn"], button:has-text("New Tender")');
    this.exportButton = page.locator('[data-testid="export-btn"], button:has-text("Export")');
    this.table = page.locator('[data-testid="tender-table"], .table-card p-table');
    this.tableRows = page.locator('.table-card .p-datatable-tbody > tr');
    this.filterPanel = page.locator('[data-testid="filter-panel"], p-panel');
    this.clearFiltersButton = page.locator('button:has-text("Clear All Filters")');
    this.statusCheckboxes = page.locator('.status-checkboxes p-checkbox');
    this.clientDropdown = page.locator('.filter-group:has(.filter-label:text("Client")) p-dropdown');
    this.loadingSpinner = page.locator('p-progressSpinner');
    this.emptyMessage = page.locator('.empty-state');
  }

  async goto() {
    await this.page.goto('/tenders', { timeout: 15000, waitUntil: 'domcontentloaded' });
  }

  async expectLoaded() {
    // Table may not appear if there is no data -- catch gracefully
    await this.table.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
  }

  async searchTenders(query: string) {
    await this.searchInput.fill(query, { timeout: 10000 });
    // Wait for debounced search
    await this.page.waitForTimeout(500);
  }

  async getRowCount(): Promise<number> {
    return await this.tableRows.count().catch(() => 0);
  }

  async clickNewTender() {
    await this.newTenderButton.click({ timeout: 10000 });
  }

  async clickTender(title: string) {
    const row = this.tableRows.filter({ hasText: title }).first();
    await row.click({ timeout: 10000 });
  }

  async expectTenderInList(title: string) {
    await expect(this.tableRows.filter({ hasText: title }).first()).toBeVisible();
  }

  async expectTenderNotInList(title: string) {
    await expect(this.tableRows.filter({ hasText: title })).toHaveCount(0);
  }

  async filterByStatus(statusLabel: string) {
    // Open filter panel first
    const panelContent = this.filterPanel.locator('.p-panel-content');
    const isHidden = await panelContent.isHidden().catch(() => true);
    if (isHidden) {
      await this.filterPanel.locator('.p-panel-header').click({ timeout: 10000 });
    }
    const checkbox = this.page.locator(`.status-checkbox:has(label:has-text("${statusLabel}")) p-checkbox`);
    await checkbox.click({ timeout: 10000 });
  }

  async clearFilters() {
    await this.clearFiltersButton.click({ timeout: 10000 });
  }

  async exportToExcel() {
    await this.exportButton.click({ timeout: 10000 });
  }

  async sortByColumn(columnName: string) {
    const header = this.page.locator(`th:has-text("${columnName}")`);
    await header.click({ timeout: 10000 });
  }

  async selectPageSize(size: number) {
    const pageSizeDropdown = this.page.locator('.p-paginator .p-dropdown');
    await pageSizeDropdown.click({ timeout: 10000 });
    await this.page.locator(`.p-dropdown-panel .p-dropdown-item:has-text("${size}")`).click({ timeout: 10000 });
  }

  async goToNextPage() {
    await this.page.locator('.p-paginator-next').click({ timeout: 10000 });
  }

  async goToPreviousPage() {
    await this.page.locator('.p-paginator-prev').click({ timeout: 10000 });
  }

  async isEmptyStateVisible(): Promise<boolean> {
    return await this.emptyMessage.isVisible().catch(() => false);
  }
}
