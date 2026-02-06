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
            <img src="assets/images/logo-white.png" alt="Bayan" class="brand-logo" />
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
              <p-message severity="error" [text]="errorMessage()!" styleClass="w-full mb-4"></p-message>
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
      background: #f0f2f5;
      padding: 1rem;
    }

    .login-wrapper {
      display: flex;
      max-width: 1000px;
      width: 100%;
      background: white;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
    }

    /* Branding Panel */
    .branding-panel {
      flex: 1;
      background: linear-gradient(135deg, #1565C0 0%, #0D47A1 100%);
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
      color: #1e293b;
      margin: 0 0 0.5rem 0;
    }

    .form-header p {
      color: #64748b;
      margin: 0;
    }

    .form-field {
      margin-bottom: 1.5rem;
    }

    .form-field label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 500;
      color: #334155;
    }

    .field-hint {
      display: block;
      margin-top: 0.25rem;
      color: #64748b;
      font-size: 0.8125rem;
    }

    .submit-btn {
      height: 48px;
      font-size: 1rem;
      margin-top: 0.5rem;
    }

    .form-footer {
      margin-top: 2rem;
      padding-top: 1.5rem;
      border-top: 1px solid #e2e8f0;
    }

    .help-text {
      display: flex;
      align-items: flex-start;
      gap: 0.5rem;
      color: #64748b;
      font-size: 0.875rem;
      margin: 0 0 1rem 0;
      line-height: 1.5;
    }

    .help-text i {
      margin-top: 2px;
      color: #3b82f6;
    }

    .contact-text {
      color: #64748b;
      font-size: 0.875rem;
      margin: 0;
      text-align: center;
    }

    .contact-text a {
      color: #1565C0;
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
        padding-left: 2.5rem;
      }

      .p-input-icon-left > i {
        left: 0.875rem;
        color: #94a3b8;
      }

      .p-password {
        width: 100%;
      }

      .p-password-input {
        width: 100%;
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
