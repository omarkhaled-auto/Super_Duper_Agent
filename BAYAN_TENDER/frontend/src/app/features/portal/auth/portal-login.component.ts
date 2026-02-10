import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule, ActivatedRoute } from '@angular/router';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { ButtonModule } from 'primeng/button';
import { MessageModule } from 'primeng/message';
import { RippleModule } from 'primeng/ripple';
import { CardModule } from 'primeng/card';
import { DividerModule } from 'primeng/divider';
import { PortalService } from '../../../core/services/portal.service';

@Component({
  selector: 'app-portal-login',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    ReactiveFormsModule,
    InputTextModule,
    PasswordModule,
    ButtonModule,
    MessageModule,
    RippleModule,
    CardModule,
    DividerModule
  ],
  template: `
    <div class="portal-login-container">
      <div class="login-wrapper">
        <!-- Left Panel - Branding -->
        <div class="branding-panel">
          <div class="branding-content">
            <i class="pi pi-briefcase" style="font-size: 2.5rem; margin-bottom: 1rem;"></i>
            <h1 class="brand-title">Bidder Portal</h1>
            <p class="brand-subtitle">
              Access tender documents, submit clarifications, and submit your bid through our secure portal.
            </p>
            <div class="brand-features">
              <div class="feature-item">
                <i class="pi pi-folder"></i>
                <span>Access Tender Documents</span>
              </div>
              <div class="feature-item">
                <i class="pi pi-comments"></i>
                <span>Submit Clarifications</span>
              </div>
              <div class="feature-item">
                <i class="pi pi-upload"></i>
                <span>Submit Your Bid</span>
              </div>
              <div class="feature-item">
                <i class="pi pi-lock"></i>
                <span>Secure & Confidential</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Panel - Login Form -->
        <div class="form-panel">
          <div class="form-content">
            <div class="form-header">
              <h2>Welcome Back</h2>
              <p>Sign in to access the tender portal</p>
            </div>

            @if (errorMessage()) {
              <p-message severity="error" [text]="errorMessage()!" styleClass="w-full mb-4" data-testid="portal-login-error"></p-message>
            }

            <form [formGroup]="loginForm" (ngSubmit)="onSubmit()">
              <!-- Tender Code (Optional) -->
              <div class="form-field">
                <label for="tenderCode">Tender Code (Optional)</label>
                <span class="p-input-icon-left w-full">
                  <i class="pi pi-hashtag"></i>
                  <input
                    pInputText
                    id="tenderCode"
                    type="text"
                    formControlName="tenderCode"
                    placeholder="Enter tender reference code"
                    class="w-full"
                    data-testid="portal-tender-code"
                  />
                </span>
                <small class="field-hint">If you have a tender code, enter it to go directly to that tender</small>
              </div>

              <p-divider></p-divider>

              <!-- Email -->
              <div class="form-field">
                <label for="email">Email Address *</label>
                <span class="p-input-icon-left w-full">
                  <i class="pi pi-envelope"></i>
                  <input
                    pInputText
                    id="email"
                    type="email"
                    formControlName="email"
                    placeholder="Enter your email"
                    class="w-full"
                    data-testid="portal-login-email"
                    [class.ng-invalid]="isFieldInvalid('email')"
                  />
                </span>
                @if (isFieldInvalid('email')) {
                  <small class="p-error">
                    @if (loginForm.get('email')?.errors?.['required']) {
                      Email is required
                    }
                    @if (loginForm.get('email')?.errors?.['email']) {
                      Please enter a valid email address
                    }
                  </small>
                }
              </div>

              <!-- Password -->
              <div class="form-field">
                <label for="password">Password *</label>
                <p-password
                  id="password"
                  formControlName="password"
                  placeholder="Enter your password"
                  [feedback]="false"
                  [toggleMask]="true"
                  styleClass="w-full"
                  inputStyleClass="w-full"
                  data-testid="portal-login-password"
                  [class.ng-invalid]="isFieldInvalid('password')"
                ></p-password>
                @if (isFieldInvalid('password')) {
                  <small class="p-error">
                    @if (loginForm.get('password')?.errors?.['required']) {
                      Password is required
                    }
                    @if (loginForm.get('password')?.errors?.['minlength']) {
                      Password must be at least 6 characters
                    }
                  </small>
                }
              </div>

              <!-- Submit Button -->
              <button
                pButton
                pRipple
                type="submit"
                label="Sign In to Portal"
                icon="pi pi-sign-in"
                class="w-full submit-btn"
                data-testid="portal-login-submit"
                [loading]="isLoading()"
                [disabled]="loginForm.invalid || isLoading()"
              ></button>
            </form>

            <div class="form-footer">
              <p class="help-text">
                <i class="pi pi-info-circle"></i>
                Your login credentials were sent to you via email invitation.
              </p>
              <p class="contact-text">
                Need help? Contact <a href="mailto:support@bayan.ae">support&#64;bayan.ae</a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .portal-login-container {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--bayan-muted, #f4f4f5);
      padding: 1rem;
    }

    .login-wrapper {
      display: flex;
      max-width: 1000px;
      width: 100%;
      background: var(--bayan-card, #ffffff);
      border-radius: var(--bayan-radius-xl, 1rem);
      overflow: hidden;
      border: 1px solid var(--bayan-border, #e4e4e7);
      box-shadow: var(--bayan-shadow, 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1));
    }

    /* Branding Panel */
    .branding-panel {
      flex: 1;
      background: var(--bayan-primary, #18181b);
      color: white;
      padding: 3rem;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .branding-content {
      max-width: 360px;
    }

    .brand-logo {
      height: 50px;
      margin-bottom: 2rem;
    }

    .brand-title {
      font-size: 2rem;
      font-weight: 700;
      margin: 0 0 0.5rem 0;
    }

    .brand-subtitle {
      font-size: 1rem;
      opacity: 0.9;
      line-height: 1.6;
      margin-bottom: 2rem;
    }

    .brand-features {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .feature-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      font-size: 0.9375rem;
      opacity: 0.9;
    }

    .feature-item i {
      font-size: 1.25rem;
      width: 24px;
    }

    /* Form Panel */
    .form-panel {
      flex: 1;
      padding: 3rem;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .form-content {
      width: 100%;
      max-width: 380px;
    }

    .form-header {
      margin-bottom: 2rem;
    }

    .form-header h2 {
      font-size: 1.75rem;
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
      margin: 0 0 0.5rem 0;
    }

    .form-header p {
      color: var(--bayan-muted-foreground, #71717a);
      margin: 0;
    }

    .form-field {
      margin-bottom: 1.25rem;
    }

    .form-field label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
    }

    .field-hint {
      display: block;
      margin-top: 0.25rem;
      color: var(--bayan-muted-foreground, #71717a);
      font-size: 0.8rem;
    }

    .submit-btn {
      height: 46px;
      font-size: 0.9375rem;
      font-weight: 600;
      margin-top: 0.5rem;
    }

    .form-footer {
      margin-top: 2rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--bayan-border, #e4e4e7);
    }

    .help-text {
      display: flex;
      align-items: flex-start;
      gap: 0.5rem;
      color: var(--bayan-muted-foreground, #71717a);
      font-size: 0.875rem;
      margin: 0 0 1rem 0;
      line-height: 1.5;
    }

    .help-text i {
      margin-top: 2px;
      color: var(--bayan-primary, #18181b);
    }

    .contact-text {
      color: var(--bayan-muted-foreground, #71717a);
      font-size: 0.875rem;
      margin: 0;
      text-align: center;
    }

    .contact-text a {
      color: var(--bayan-primary, #18181b);
      text-decoration: none;
      font-weight: 500;
    }

    .contact-text a:hover {
      text-decoration: underline;
    }

    .p-error {
      display: block;
      margin-top: 0.25rem;
    }

    :host ::ng-deep {
      .p-inputtext {
        width: 100%;
        height: 44px;
        padding-left: 2.5rem;
      }

      .p-input-icon-left > i {
        left: 0.875rem;
        color: var(--bayan-muted-foreground, #71717a);
      }

      .p-password {
        width: 100%;

        .p-inputtext {
          height: 44px;
        }
      }

      .p-password-input {
        width: 100%;
      }

      .p-button {
        border-radius: var(--bayan-radius, 0.5rem);
        justify-content: center;
      }

      .p-divider {
        margin: 1.5rem 0;
      }

      .p-message {
        width: 100%;
      }
    }

    /* Responsive */
    @media (max-width: 768px) {
      .login-wrapper {
        flex-direction: column;
      }

      .branding-panel {
        padding: 2rem;
      }

      .branding-content {
        text-align: center;
      }

      .brand-title {
        font-size: 1.5rem;
      }

      .brand-subtitle {
        font-size: 0.9375rem;
      }

      .brand-features {
        display: none;
      }

      .form-panel {
        padding: 2rem;
      }
    }
  `]
})
export class PortalLoginComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly portalService = inject(PortalService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  loginForm!: FormGroup;
  isLoading = this.portalService.isLoading;
  errorMessage = signal<string | null>(null);

  private returnUrl = '';

  ngOnInit(): void {
    this.initForm();
    this.returnUrl = this.route.snapshot.queryParams['returnUrl'] || '';

    // Pre-fill tender code from query params
    const tenderCode = this.route.snapshot.queryParams['tenderCode'];
    if (tenderCode) {
      this.loginForm.patchValue({ tenderCode });
    }
  }

  private initForm(): void {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      tenderCode: ['']
    });
  }

  isFieldInvalid(field: string): boolean {
    const control = this.loginForm.get(field);
    return !!(control && control.invalid && (control.dirty || control.touched));
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.errorMessage.set(null);

    const credentials = {
      email: this.loginForm.value.email,
      password: this.loginForm.value.password,
      tenderCode: this.loginForm.value.tenderCode || undefined
    };

    this.portalService.login(credentials).subscribe({
      next: (response) => {
        // Navigate to tender-specific route if tender ID is provided
        if (response.tenderId) {
          this.router.navigate(['/portal/tenders', response.tenderId, 'documents']);
        } else if (this.returnUrl) {
          this.router.navigateByUrl(this.returnUrl);
        } else {
          // Default: could navigate to a tender selection page
          this.router.navigate(['/portal/tenders']);
        }
      },
      error: (error) => {
        this.errorMessage.set(
          error.error?.message || 'Login failed. Please check your credentials and try again.'
        );
      }
    });
  }
}
