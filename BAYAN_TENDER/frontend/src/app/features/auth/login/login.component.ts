import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule, ActivatedRoute } from '@angular/router';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { ButtonModule } from 'primeng/button';
import { CheckboxModule } from 'primeng/checkbox';
import { MessagesModule } from 'primeng/messages';
import { MessageModule } from 'primeng/message';
import { RippleModule } from 'primeng/ripple';
import { AuthService } from '../../../core/auth/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    ReactiveFormsModule,
    InputTextModule,
    PasswordModule,
    ButtonModule,
    CheckboxModule,
    MessagesModule,
    MessageModule,
    RippleModule
  ],
  template: `
    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <div class="logo-icon">
            <i class="pi pi-building"></i>
          </div>
          <h1>Bayan Tender</h1>
          <p>Sign in to your account</p>
        </div>

        @if (errorMessage()) {
          <div class="error-alert" data-testid="login-error">
            <i class="pi pi-exclamation-circle"></i>
            <span>{{ errorMessage() }}</span>
          </div>
        }

        <form [formGroup]="loginForm" (ngSubmit)="onSubmit()">
          <div class="form-field">
            <label for="email">Email</label>
            <input
              pInputText
              id="email"
              type="email"
              formControlName="email"
              placeholder="Enter your email"
              class="w-full"
              data-testid="login-email"
              [class.ng-invalid]="isFieldInvalid('email')"
            />
            @if (isFieldInvalid('email')) {
              <small class="field-error">
                <i class="pi pi-exclamation-circle"></i>
                @if (loginForm.get('email')?.errors?.['required']) {
                  Email is required
                }
                @if (loginForm.get('email')?.errors?.['email']) {
                  Please enter a valid email
                }
              </small>
            }
          </div>

          <div class="form-field">
            <label for="password">Password</label>
            <p-password
              id="password"
              formControlName="password"
              placeholder="Enter your password"
              [feedback]="false"
              [toggleMask]="true"
              styleClass="w-full"
              inputStyleClass="w-full"
              data-testid="login-password"
              [class.ng-invalid]="isFieldInvalid('password')"
            ></p-password>
            @if (isFieldInvalid('password')) {
              <small class="field-error">
                <i class="pi pi-exclamation-circle"></i>
                @if (loginForm.get('password')?.errors?.['required']) {
                  Password is required
                }
                @if (loginForm.get('password')?.errors?.['minlength']) {
                  Password must be at least 6 characters
                }
              </small>
            }
          </div>

          <div class="form-options">
            <div class="remember-me">
              <p-checkbox
                formControlName="rememberMe"
                [binary]="true"
                inputId="rememberMe"
                data-testid="login-remember"
              ></p-checkbox>
              <label for="rememberMe">Remember me</label>
            </div>
            <a routerLink="/auth/forgot-password" class="forgot-link">
              Forgot password?
            </a>
          </div>

          <button
            pButton
            pRipple
            type="submit"
            label="Sign In"
            class="w-full"
            data-testid="login-submit"
            [loading]="isLoading()"
            [disabled]="loginForm.invalid || isLoading()"
          ></button>
        </form>

        <div class="login-footer">
          <p>
            Don't have an account?
            <a routerLink="/auth/register">Create one</a>
          </p>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .login-container {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, var(--bayan-slate-50, #F8FAFC) 0%, var(--bayan-slate-100, #F1F5F9) 100%);
      padding: 2rem;
    }

    .login-card {
      background: var(--bayan-card, #ffffff);
      border-radius: var(--bayan-radius-xl, 1rem);
      padding: 2.5rem;
      width: 100%;
      max-width: 420px;
      box-shadow: var(--bayan-shadow-lg, 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1));
    }

    .login-header {
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

    .login-header h1 {
      margin: 0;
      font-size: 1.5rem;
      font-weight: 600;
      color: var(--bayan-slate-900, #0F172A);
    }

    .login-header p {
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

    .form-options {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
    }

    .remember-me {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .remember-me label {
      cursor: pointer;
      color: var(--bayan-slate-500, #64748B);
      font-size: 0.875rem;
    }

    .forgot-link {
      color: var(--bayan-primary, #4F46E5);
      text-decoration: none;
      font-size: 0.875rem;
      font-weight: 500;
    }

    .forgot-link:hover {
      text-decoration: underline;
      color: var(--bayan-primary-hover, #4338CA);
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

    .login-footer {
      text-align: center;
      margin-top: 1.5rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--bayan-border, #E2E8F0);
    }

    .login-footer p {
      margin: 0;
      color: var(--bayan-slate-500, #64748B);
      font-size: 0.875rem;
    }

    .login-footer a {
      color: var(--bayan-primary, #4F46E5);
      text-decoration: none;
      font-weight: 500;
    }

    .login-footer a:hover {
      text-decoration: underline;
      color: var(--bayan-primary-hover, #4338CA);
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

      .p-password {
        width: 100%;

        .p-inputtext {
          height: 44px;
        }
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

      .p-checkbox .p-checkbox-box {
        width: 1rem;
        height: 1rem;
      }

      .p-checkbox .p-checkbox-box.p-highlight,
      .p-checkbox.p-highlight .p-checkbox-box,
      .p-checkbox.p-checkbox-checked .p-checkbox-box {
        background: var(--bayan-primary, #4F46E5);
        border-color: var(--bayan-primary, #4F46E5);
      }
    }
  `]
})
export class LoginComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  loginForm!: FormGroup;
  isLoading = this.authService.isLoading;
  errorMessage = signal<string | null>(null);

  private returnUrl = '/home';

  ngOnInit(): void {
    this.initForm();
    this.returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/home';
  }

  private initForm(): void {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      rememberMe: [false]
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

    this.authService.login(this.loginForm.value).subscribe({
      next: () => {
        this.router.navigateByUrl(this.returnUrl);
      },
      error: (error) => {
        this.errorMessage.set(error.error?.message || 'Login failed. Please try again.');
      }
    });
  }
}
