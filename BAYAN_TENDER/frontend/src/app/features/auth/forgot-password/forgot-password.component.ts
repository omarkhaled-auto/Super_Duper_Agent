import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { InputTextModule } from 'primeng/inputtext';
import { ButtonModule } from 'primeng/button';
import { MessageModule } from 'primeng/message';
import { RippleModule } from 'primeng/ripple';
import { AuthService } from '../../../core/auth/auth.service';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    ReactiveFormsModule,
    InputTextModule,
    ButtonModule,
    MessageModule,
    RippleModule
  ],
  template: `
    <div class="forgot-container">
      <div class="forgot-card">
        <a routerLink="/auth/login" class="back-link">
          <i class="pi pi-arrow-left"></i>
          Back to login
        </a>

        <div class="forgot-header">
          <div class="logo-icon">
            <i class="pi pi-lock"></i>
          </div>
          <h1>Reset Password</h1>
          <p>Enter your email to receive a reset link</p>
        </div>

        @if (successMessage()) {
          <div class="success-alert">
            <i class="pi pi-check-circle"></i>
            <span>{{ successMessage() }}</span>
          </div>
        }

        @if (errorMessage()) {
          <div class="error-alert">
            <i class="pi pi-exclamation-circle"></i>
            <span>{{ errorMessage() }}</span>
          </div>
        }

        <form [formGroup]="forgotForm" (ngSubmit)="onSubmit()">
          <div class="form-field">
            <label for="email">Email</label>
            <input
              pInputText
              id="email"
              type="email"
              formControlName="email"
              placeholder="Enter your email"
              class="w-full"
              [class.ng-invalid]="isFieldInvalid('email')"
            />
            @if (isFieldInvalid('email')) {
              <small class="field-error">
                <i class="pi pi-exclamation-circle"></i>
                @if (forgotForm.get('email')?.errors?.['required']) {
                  Email is required
                }
                @if (forgotForm.get('email')?.errors?.['email']) {
                  Please enter a valid email
                }
              </small>
            }
          </div>

          <button
            pButton
            pRipple
            type="submit"
            label="Send Reset Link"
            class="w-full"
            [loading]="isLoading()"
            [disabled]="forgotForm.invalid || isLoading()"
          ></button>
        </form>
      </div>
    </div>
  `,
  styles: [`
    .forgot-container {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, var(--bayan-slate-50, #F8FAFC) 0%, var(--bayan-slate-100, #F1F5F9) 100%);
      padding: 2rem;
    }

    .forgot-card {
      background: var(--bayan-card, #ffffff);
      border-radius: var(--bayan-radius-xl, 1rem);
      padding: 2.5rem;
      width: 100%;
      max-width: 420px;
      box-shadow: var(--bayan-shadow-lg, 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1));
    }

    .back-link {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      color: var(--bayan-primary, #4F46E5);
      text-decoration: none;
      font-size: 0.875rem;
      font-weight: 500;
      margin-bottom: 1.5rem;
      transition: color var(--bayan-transition-fast, 150ms ease);
    }

    .back-link:hover {
      color: var(--bayan-primary-hover, #4338CA);
      text-decoration: underline;
    }

    .forgot-header {
      text-align: center;
      margin-bottom: 2rem;
    }

    .logo-icon {
      width: 56px;
      height: 56px;
      border-radius: var(--bayan-radius-lg, 0.75rem);
      background: var(--bayan-primary-light, #EEF2FF);
      color: var(--bayan-primary, #4F46E5);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 1rem;
      font-size: 1.5rem;
    }

    .forgot-header h1 {
      margin: 0;
      font-size: 1.5rem;
      font-weight: 600;
      color: var(--bayan-slate-900, #0F172A);
    }

    .forgot-header p {
      margin: 0.5rem 0 0;
      color: var(--bayan-slate-500, #64748B);
      font-size: 0.875rem;
    }

    .form-field {
      margin-bottom: 1.25rem;
    }

    .form-field label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 600;
      font-size: 0.875rem;
      color: var(--bayan-slate-700, #334155);
    }

    .success-alert {
      display: flex;
      align-items: flex-start;
      gap: 0.5rem;
      padding: 0.75rem 1rem;
      margin-bottom: 1.25rem;
      background: var(--bayan-success-bg, #F0FDF4);
      border-left: 4px solid var(--bayan-success, #16A34A);
      border-radius: var(--bayan-radius-sm, 0.375rem);
      color: var(--bayan-success, #16A34A);
      font-size: 0.875rem;
      line-height: 1.5;
    }

    .success-alert i {
      margin-top: 2px;
      font-size: 0.875rem;
    }

    .error-alert {
      display: flex;
      align-items: flex-start;
      gap: 0.5rem;
      padding: 0.75rem 1rem;
      margin-bottom: 1.25rem;
      background: var(--bayan-danger-bg, #FEF2F2);
      border-left: 4px solid var(--bayan-danger, #DC2626);
      border-radius: var(--bayan-radius-sm, 0.375rem);
      color: var(--bayan-danger, #DC2626);
      font-size: 0.875rem;
      line-height: 1.5;
    }

    .error-alert i {
      margin-top: 2px;
      font-size: 0.875rem;
    }

    .field-error {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      margin-top: 0.25rem;
      color: var(--bayan-danger, #DC2626);
      font-size: 0.8rem;
    }

    .field-error i {
      font-size: 0.7rem;
    }

    :host ::ng-deep {
      .p-inputtext {
        width: 100%;
        height: 44px;
        border: 1px solid var(--bayan-input, #E2E8F0);
        border-radius: var(--bayan-radius-sm, 0.375rem);
        transition: border-color var(--bayan-transition-fast, 150ms ease),
                    box-shadow var(--bayan-transition-fast, 150ms ease);
      }

      .p-inputtext:focus {
        border-color: var(--bayan-primary, #4F46E5);
        box-shadow: 0 0 0 3px var(--bayan-primary-ring, rgba(79, 70, 229, 0.15));
      }

      .p-button {
        width: 100%;
        height: 46px;
        font-size: 0.9375rem;
        font-weight: 600;
        background: var(--bayan-primary, #4F46E5);
        border-color: var(--bayan-primary, #4F46E5);
        border-radius: var(--bayan-radius-lg, 0.75rem);
        justify-content: center;
        transition: background-color var(--bayan-transition, 200ms ease),
                    border-color var(--bayan-transition, 200ms ease);
      }

      .p-button:hover:not(:disabled) {
        background: var(--bayan-primary-hover, #4338CA);
        border-color: var(--bayan-primary-hover, #4338CA);
      }

      .p-button:active:not(:disabled) {
        background: var(--bayan-primary-active, #3730A3);
        border-color: var(--bayan-primary-active, #3730A3);
      }
    }
  `]
})
export class ForgotPasswordComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);

  forgotForm: FormGroup;
  isLoading = this.authService.isLoading;
  successMessage = signal<string | null>(null);
  errorMessage = signal<string | null>(null);

  constructor() {
    this.forgotForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]]
    });
  }

  isFieldInvalid(field: string): boolean {
    const control = this.forgotForm.get(field);
    return !!(control && control.invalid && (control.dirty || control.touched));
  }

  onSubmit(): void {
    if (this.forgotForm.invalid) {
      this.forgotForm.markAllAsTouched();
      return;
    }

    this.successMessage.set(null);
    this.errorMessage.set(null);

    this.authService.forgotPassword(this.forgotForm.value).subscribe({
      next: () => {
        this.successMessage.set('If an account exists with this email, you will receive a password reset link.');
        this.forgotForm.reset();
      },
      error: (error) => {
        this.errorMessage.set(error.error?.message || 'Failed to send reset email. Please try again.');
      }
    });
  }
}
