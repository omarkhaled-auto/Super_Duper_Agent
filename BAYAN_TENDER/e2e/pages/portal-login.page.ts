import { Page, Locator, expect } from '@playwright/test';

export class PortalLoginPage {
  readonly page: Page;
  private readonly emailInput: Locator;
  private readonly passwordInput: Locator;
  private readonly submitButton: Locator;
  private readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.locator('[data-testid="portal-email"], #email, input[type="email"]');
    this.passwordInput = page.locator('[data-testid="portal-password"] input, p-password input, input[type="password"]');
    this.submitButton = page.locator('[data-testid="portal-submit"], button[type="submit"]');
    this.errorMessage = page.locator('[data-testid="portal-error"], p-message[severity="error"]');
  }

  async goto() {
    await this.page.goto('/portal/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectLoggedIn() {
    await expect(this.page).toHaveURL(/\/portal\//);
  }

  async expectError() {
    await expect(this.errorMessage).toBeVisible();
  }

  async expectOnPortalLogin() {
    await expect(this.page).toHaveURL(/\/portal\/login/);
  }
}
