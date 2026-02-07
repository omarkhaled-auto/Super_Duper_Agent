import { Page, Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  private readonly emailInput: Locator;
  private readonly passwordInput: Locator;
  private readonly submitButton: Locator;
  private readonly rememberMeCheckbox: Locator;
  private readonly errorMessage: Locator;
  private readonly forgotPasswordLink: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.locator('#email');
    this.passwordInput = page.locator('p-password input');
    this.submitButton = page.locator('button[type="submit"]');
    this.rememberMeCheckbox = page.locator('p-checkbox');
    this.errorMessage = page.locator('p-message[severity="error"]');
    this.forgotPasswordLink = page.locator('a[routerLink="/auth/forgot-password"]');
  }

  async goto() {
    await this.page.goto('/auth/login', { waitUntil: 'networkidle' });
    // Ensure Angular has bootstrapped and form is rendered
    await this.emailInput.waitFor({ state: 'visible', timeout: 15000 });
  }

  async fillEmail(email: string) {
    await this.emailInput.fill(email);
  }

  async fillPassword(password: string) {
    await this.passwordInput.fill(password);
  }

  async clickRememberMe() {
    await this.rememberMeCheckbox.click();
  }

  async submit() {
    await this.submitButton.click();
  }

  async login(email: string, password: string) {
    await this.fillEmail(email);
    await this.fillPassword(password);
    await this.submit();
  }

  async getErrorMessage(): Promise<string | null> {
    try {
      await this.errorMessage.waitFor({ state: 'visible', timeout: 5000 });
      return await this.errorMessage.textContent();
    } catch {
      return null;
    }
  }

  async expectOnLoginPage() {
    await expect(this.page).toHaveURL(/\/auth\/login/);
  }

  async expectErrorVisible() {
    await expect(this.errorMessage).toBeVisible();
  }

  async clickForgotPassword() {
    await this.forgotPasswordLink.click();
  }

  async getValidationError(field: string): Promise<string | null> {
    const error = this.page.locator(`.form-field:has(#${field}) .p-error, .form-field:has([formControlName="${field}"]) .p-error`);
    try {
      await error.waitFor({ state: 'visible', timeout: 3000 });
      return await error.textContent();
    } catch {
      return null;
    }
  }

  async isSubmitDisabled(): Promise<boolean> {
    return await this.submitButton.isDisabled();
  }
}
