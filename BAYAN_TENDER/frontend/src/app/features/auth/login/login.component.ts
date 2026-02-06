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
          <img src="assets/images/logo.png" alt="Bayan" class="logo" />
          <h1>Welcome Back</h1>
          <p>Sign in to your Bayan Tender account</p>
        </div>

        @if (errorMessage()) {
          <p-message severity="error" [text]="errorMessage()!" styleClass="w-full mb-3"></p-message>
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
      background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%);
      padding: 2rem;
    }

    .login-card {
      background: #ffffff;
      border-radius: 16px;
      padding: 2.5rem;
      width: 100%;
      max-width: 420px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
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
      color: #333;
    }

    .login-header p {
      margin: 0.5rem 0 0;
      color: #666;
    }

    .form-field {
      margin-bottom: 1.5rem;
    }

    .form-field label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 500;
      color: #333;
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
      color: #666;
    }

    .forgot-link {
      color: #1976D2;
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
      border-top: 1px solid #e0e0e0;
    }

    .login-footer p {
      margin: 0;
      color: #666;
    }

    .login-footer a {
      color: #1976D2;
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
      }

      .p-password {
        width: 100%;
      }

      .p-button {
        height: 48px;
        font-size: 1rem;
      }

      .p-message {
        width: 100%;
        margin-bottom: 1rem;
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
