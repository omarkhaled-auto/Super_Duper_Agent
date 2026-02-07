import { Page, Locator, expect } from '@playwright/test';

export class TenderWizardPage {
  readonly page: Page;
  private readonly steps: Locator;
  private readonly nextButton: Locator;
  private readonly prevButton: Locator;
  private readonly saveAsDraftButton: Locator;
  private readonly createTenderButton: Locator;
  private readonly cancelButton: Locator;
  private readonly titleInput: Locator;
  private readonly descriptionInput: Locator;
  private readonly clientDropdown: Locator;
  private readonly typeDropdown: Locator;
  private readonly currencyDropdown: Locator;
  private readonly technicalWeightInput: Locator;
  private readonly commercialWeightInput: Locator;
  private readonly toast: Locator;

  constructor(page: Page) {
    this.page = page;
    this.steps = page.locator('p-steps');
    this.nextButton = page.locator('[data-testid="wizard-next"], button:has-text("Next")');
    this.prevButton = page.locator('[data-testid="wizard-prev"], button:has-text("Previous")');
    this.saveAsDraftButton = page.locator('[data-testid="wizard-save-draft"], button:has-text("Save as Draft")');
    this.createTenderButton = page.locator('[data-testid="wizard-create"], button:has-text("Create Tender")');
    this.cancelButton = page.locator('button:has-text("Cancel")');
    this.titleInput = page.locator('[data-testid="tender-title"] input, [formControlName="title"], input[formControlName="title"]');
    this.descriptionInput = page.locator('[data-testid="tender-description"] textarea, textarea[formControlName="description"]');
    this.clientDropdown = page.locator('[data-testid="tender-client"], [formControlName="clientId"] p-dropdown, p-autoComplete');
    this.typeDropdown = page.locator('[data-testid="tender-type"], p-dropdown:has([formControlName="type"])');
    this.currencyDropdown = page.locator('[data-testid="tender-currency"], p-dropdown:has([formControlName="currency"])');
    this.technicalWeightInput = page.locator('[data-testid="technical-weight"] input, input[formControlName="technicalWeight"]');
    this.commercialWeightInput = page.locator('[data-testid="commercial-weight"] input, input[formControlName="commercialWeight"]');
    this.toast = page.locator('p-toast');
  }

  async goto() {
    await this.page.goto('/tenders/new', { timeout: 15000, waitUntil: 'domcontentloaded' });
  }

  async expectOnStep(stepNumber: number) {
    const activeStep = this.steps.locator('.p-highlight');
    await expect(activeStep).toBeVisible();
  }

  // Step 1 - Basic Info
  async fillTitle(title: string) {
    await this.titleInput.fill(title);
  }

  async fillDescription(desc: string) {
    await this.descriptionInput.fill(desc);
  }

  async selectClient(name: string) {
    await this.clientDropdown.click();
    await this.page.locator(`.p-dropdown-panel .p-dropdown-item:has-text("${name}"), .p-autocomplete-panel .p-autocomplete-item:has-text("${name}")`).first().click();
  }

  async selectTenderType(type: string) {
    await this.typeDropdown.click();
    await this.page.locator(`.p-dropdown-panel .p-dropdown-item:has-text("${type}")`).click();
  }

  async selectCurrency(code: string) {
    await this.currencyDropdown.click();
    await this.page.locator(`.p-dropdown-panel .p-dropdown-item:has-text("${code}")`).click();
  }

  // Step 2 - Dates
  async setIssueDate(date: Date) {
    const dateInput = this.page.locator('[formControlName="issueDate"] input, p-calendar:first-of-type input').first();
    await dateInput.fill(this.formatDate(date));
  }

  async setSubmissionDeadline(date: Date) {
    const dateInput = this.page.locator('[formControlName="submissionDeadline"] input').first();
    await dateInput.fill(this.formatDate(date));
  }

  async setClarificationDeadline(date: Date) {
    const dateInput = this.page.locator('[formControlName="clarificationDeadline"] input').first();
    await dateInput.fill(this.formatDate(date));
  }

  async setOpeningDate(date: Date) {
    const dateInput = this.page.locator('[formControlName="openingDate"] input').first();
    await dateInput.fill(this.formatDate(date));
  }

  // Step 3 - Criteria
  async setTechnicalWeight(weight: number) {
    await this.technicalWeightInput.fill(weight.toString());
  }

  async setCommercialWeight(weight: number) {
    await this.commercialWeightInput.fill(weight.toString());
  }

  async addCriterion(name: string, weight: number) {
    const addButton = this.page.locator('button:has-text("Add Criterion"), button:has-text("Add")').first();
    await addButton.click();
    const lastCriterion = this.page.locator('[formArrayName="evaluationCriteria"] > :last-child');
    await lastCriterion.locator('input[formControlName="name"]').fill(name);
    await lastCriterion.locator('input[formControlName="weight"]').fill(weight.toString());
  }

  // Step 4 - Review
  async expectSummaryContains(text: string) {
    await expect(this.page.locator('app-review-step')).toContainText(text);
  }

  // Navigation
  async nextStep() {
    await this.nextButton.click();
  }

  async previousStep() {
    await this.prevButton.click();
  }

  async saveDraft() {
    await this.saveAsDraftButton.click();
  }

  async createTender() {
    await this.createTenderButton.click();
  }

  async clickCancel() {
    await this.cancelButton.click();
  }

  async isNextDisabled(): Promise<boolean> {
    return await this.nextButton.isDisabled();
  }

  private formatDate(date: Date): string {
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  }
}
