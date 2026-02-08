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
        <div class="forgot-header">
          <img src="assets/images/logo.png" alt="Bayan" class="logo" />
          <h1>Forgot Password</h1>
          <p>Enter your email to receive a password reset link</p>
        </div>

        @if (successMessage()) {
          <p-message severity="success" [text]="successMessage()!" styleClass="w-full mb-3"></p-message>
        }

        @if (errorMessage()) {
          <p-message severity="error" [text]="errorMessage()!" styleClass="w-full mb-3"></p-message>
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
              <small class="p-error">
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

        <div class="forgot-footer">
          <a routerLink="/auth/login">
            <i class="pi pi-arrow-left"></i>
            Back to Sign In
          </a>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .forgot-container {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--bayan-muted, #f4f4f5);
      padding: 2rem;
    }

    .forgot-card {
      background: var(--bayan-card, #ffffff);
      border-radius: var(--bayan-radius-xl, 1rem);
      padding: 2.5rem;
      width: 100%;
      max-width: 420px;
      border: 1px solid var(--bayan-border, #e4e4e7);
      box-shadow: var(--bayan-shadow, 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1));
    }

    .forgot-header {
      text-align: center;
      margin-bottom: 2rem;
    }

    .logo {
      height: 60px;
      margin-bottom: 1rem;
    }

    .forgot-header h1 {
      margin: 0;
      font-size: 1.75rem;
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
    }

    .forgot-header p {
      margin: 0.5rem 0 0;
      color: var(--bayan-muted-foreground, #71717a);
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

    .forgot-footer {
      text-align: center;
      margin-top: 1.5rem;
    }

    .forgot-footer a {
      color: var(--bayan-primary, #18181b);
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
    }

    .forgot-footer a:hover {
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
      }

      .p-button {
        width: 100%;
        height: 46px;
        font-size: 0.9375rem;
        font-weight: 600;
        border-radius: var(--bayan-radius, 0.5rem);
        justify-content: center;
      }

      .p-message {
        width: 100%;
        margin-bottom: 1rem;
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
