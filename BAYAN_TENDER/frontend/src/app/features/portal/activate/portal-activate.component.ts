import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule, ActivatedRoute } from '@angular/router';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, AbstractControl, ValidationErrors } from '@angular/forms';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { ButtonModule } from 'primeng/button';
import { MessageModule } from 'primeng/message';
import { RippleModule } from 'primeng/ripple';
import { CardModule } from 'primeng/card';
import { PortalService } from '../../../core/services/portal.service';

@Component({
  selector: 'app-portal-activate',
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
    CardModule
  ],
  template: `
    <div class="portal-login-container">
      <div class="login-wrapper">
        <!-- Left Panel - Branding -->
        <div class="branding-panel">
          <div class="branding-content">
            <i class="pi pi-shield" style="font-size: 2.5rem; margin-bottom: 1rem;"></i>
            <h1 class="brand-title">Activate Account</h1>
            <p class="brand-subtitle">
              Set your password to access the Bayan Tender Bidder Portal. Your account was created when you were invited to a tender.
            </p>
            <div class="brand-features">
              <div class="feature-item">
                <i class="pi pi-check-circle"></i>
                <span>Set a secure password</span>
              </div>
              <div class="feature-item">
                <i class="pi pi-sign-in"></i>
                <span>Access your portal</span>
              </div>
              <div class="feature-item">
                <i class="pi pi-folder"></i>
                <span>View tender documents</span>
              </div>
              <div class="feature-item">
                <i class="pi pi-upload"></i>
                <span>Submit your bid</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Panel - Activation Form -->
        <div class="form-panel">
          <div class="form-content">
            <div class="form-header">
              <h2>Set Your Password</h2>
              <p>Create a password to activate your bidder account</p>
            </div>

            @if (successMessage()) {
              <p-message severity="success" [text]="successMessage()!" styleClass="w-full mb-4"></p-message>
            }

            @if (errorMessage()) {
              <p-message severity="error" [text]="errorMessage()!" styleClass="w-full mb-4"></p-message>
            }

            @if (tokenMissing()) {
              <p-message severity="warn" text="Invalid activation link. Please use the link from your invitation email." styleClass="w-full mb-4"></p-message>
            }

            @if (!tokenMissing() && !successMessage()) {
              <form [formGroup]="activateForm" (ngSubmit)="onSubmit()">
                <!-- Email (read-only) -->
                <div class="form-field">
                  <label for="email">Email Address</label>
                  <span class="p-input-icon-left w-full">
                    <i class="pi pi-envelope"></i>
                    <input
                      pInputText
                      id="email"
                      type="email"
                      formControlName="email"
                      class="w-full"
                      [readonly]="true"
                    />
                  </span>
                </div>

                <!-- Password -->
                <div class="form-field">
                  <label for="password">New Password *</label>
                  <p-password
                    id="password"
                    formControlName="password"
                    placeholder="Enter your new password"
                    [feedback]="true"
                    [toggleMask]="true"
                    styleClass="w-full"
                    inputStyleClass="w-full"
                  ></p-password>
                  @if (isFieldInvalid('password')) {
                    <small class="p-error">
                      @if (activateForm.get('password')?.errors?.['required']) {
                        Password is required
                      }
                      @if (activateForm.get('password')?.errors?.['minlength']) {
                        Password must be at least 8 characters
                      }
                    </small>
                  }
                </div>

                <!-- Confirm Password -->
                <div class="form-field">
                  <label for="confirmPassword">Confirm Password *</label>
                  <p-password
                    id="confirmPassword"
                    formControlName="confirmPassword"
                    placeholder="Confirm your new password"
                    [feedback]="false"
                    [toggleMask]="true"
                    styleClass="w-full"
                    inputStyleClass="w-full"
                  ></p-password>
                  @if (isFieldInvalid('confirmPassword')) {
                    <small class="p-error">
                      @if (activateForm.get('confirmPassword')?.errors?.['required']) {
                        Please confirm your password
                      }
                      @if (activateForm.get('confirmPassword')?.errors?.['passwordMismatch']) {
                        Passwords do not match
                      }
                    </small>
                  }
                </div>

                <!-- Submit Button -->
                <button
                  pButton
                  pRipple
                  type="submit"
                  label="Activate Account"
                  icon="pi pi-check"
                  class="w-full submit-btn"
                  [loading]="isLoading()"
                  [disabled]="activateForm.invalid || isLoading()"
                ></button>
              </form>
            }

            <div class="form-footer">
              <p class="help-text">
                <i class="pi pi-info-circle"></i>
                Already activated your account?
                <a routerLink="/portal/login">Sign in here</a>
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
      margin: 0;
      line-height: 1.5;
    }

    .help-text i {
      margin-top: 2px;
      color: var(--bayan-primary, #18181b);
    }

    .help-text a {
      color: var(--bayan-primary, #18181b);
      text-decoration: none;
      font-weight: 500;
    }

    .help-text a:hover {
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

      .p-message {
        width: 100%;
      }
    }

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
export class PortalActivateComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly portalService = inject(PortalService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  activateForm!: FormGroup;
  isLoading = this.portalService.isLoading;
  errorMessage = signal<string | null>(null);
  successMessage = signal<string | null>(null);
  tokenMissing = signal<boolean>(false);

  private token = '';
  private email = '';

  ngOnInit(): void {
    this.token = this.route.snapshot.queryParams['token'] || '';
    this.email = this.route.snapshot.queryParams['email'] || '';

    if (!this.token || !this.email) {
      this.tokenMissing.set(true);
    }

    this.initForm();
  }

  private initForm(): void {
    this.activateForm = this.fb.group({
      email: [{ value: this.email, disabled: true }],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', [Validators.required]]
    });

    // Add cross-field validator for password match
    this.activateForm.get('confirmPassword')?.addValidators(
      this.passwordMatchValidator.bind(this)
    );
  }

  private passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
    if (!this.activateForm) return null;
    const password = this.activateForm.get('password')?.value;
    const confirmPassword = control.value;
    return password === confirmPassword ? null : { passwordMismatch: true };
  }

  isFieldInvalid(field: string): boolean {
    const control = this.activateForm.get(field);
    return !!(control && control.invalid && (control.dirty || control.touched));
  }

  onSubmit(): void {
    // Re-validate confirmPassword since password might have changed
    this.activateForm.get('confirmPassword')?.updateValueAndValidity();

    if (this.activateForm.invalid) {
      this.activateForm.markAllAsTouched();
      return;
    }

    this.errorMessage.set(null);
    this.successMessage.set(null);

    const data = {
      email: this.email,
      activationToken: this.token,
      password: this.activateForm.get('password')?.value,
      confirmPassword: this.activateForm.get('confirmPassword')?.value
    };

    this.portalService.activateAccount(data).subscribe({
      next: () => {
        this.successMessage.set('Your account has been activated successfully! Redirecting to login...');
        setTimeout(() => {
          this.router.navigate(['/portal/login']);
        }, 2000);
      },
      error: (error) => {
        this.errorMessage.set(
          error.error?.message || 'Activation failed. The link may have expired. Please contact the tender administrator.'
        );
      }
    });
  }
}
