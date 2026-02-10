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
          <img src="assets/images/logo.svg" alt="Bayan" class="logo" />
          <h1>Welcome Back</h1>
          <p>Sign in to your Bayan Tender account</p>
        </div>

        @if (errorMessage()) {
          <p-message severity="error" [text]="errorMessage()!" styleClass="w-full mb-3" data-testid="login-error"></p-message>
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
              <small class="p-error">
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
      background: var(--bayan-muted, #f4f4f5);
      padding: 2rem;
    }

    .login-card {
      background: var(--bayan-card, #ffffff);
      border-radius: var(--bayan-radius-xl, 1rem);
      padding: 2.5rem;
      width: 100%;
      max-width: 420px;
      border: 1px solid var(--bayan-border, #e4e4e7);
      box-shadow: var(--bayan-shadow, 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1));
    }

    .login-header {
      text-align: center;
      margin-bottom: 2rem;
    }

    .logo {
      height: 60px;
      margin-bottom: 1rem;
    }

    .login-header h1 {
      margin: 0;
      font-size: 1.75rem;
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
    }

    .login-header p {
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
      color: var(--bayan-muted-foreground, #71717a);
    }

    .forgot-link {
      color: var(--bayan-primary, #18181b);
      text-decoration: none;
      font-size: 0.875rem;
    }

    .forgot-link:hover {
      text-decoration: underline;
    }

    .login-footer {
      text-align: center;
      margin-top: 1.5rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--bayan-border, #e4e4e7);
    }

    .login-footer p {
      margin: 0;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .login-footer a {
      color: var(--bayan-primary, #18181b);
      text-decoration: none;
      font-weight: 500;
    }

    .login-footer a:hover {
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
        border-radius: var(--bayan-radius, 0.5rem);
        justify-content: center;
      }

      .p-message {
        width: 100%;
        margin-bottom: 1rem;
      }

      .p-checkbox .p-checkbox-box {
        width: 1rem;
        height: 1rem;
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

  private returnUrl = '/dashboard';

  ngOnInit(): void {
    this.initForm();
    this.returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/dashboard';
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
