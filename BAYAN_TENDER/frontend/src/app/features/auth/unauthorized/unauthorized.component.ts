import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { AuthService } from '../../../core/auth/auth.service';

@Component({
  selector: 'app-unauthorized',
  standalone: true,
  imports: [CommonModule, RouterModule, ButtonModule],
  template: `
    <div class="unauthorized-container" data-testid="unauthorized-page">
      <div class="unauthorized-content">
        <div class="lock-icon">
          <i class="pi pi-lock"></i>
        </div>
        <h1>Access Denied</h1>
        <p>You don't have permission to access this page.</p>

        <div class="actions">
          <button
            pButton
            label="Go Back"
            icon="pi pi-arrow-left"
            class="p-button-outlined go-back-btn"
            routerLink="/home"
            data-testid="unauthorized-go-home"
          ></button>
          <a routerLink="/home" class="contact-link">
            <i class="pi pi-envelope"></i>
            Contact Administrator
          </a>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .unauthorized-container {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, var(--bayan-slate-50, #F8FAFC) 0%, var(--bayan-slate-100, #F1F5F9) 100%);
      padding: 2rem;
    }

    .unauthorized-content {
      text-align: center;
      max-width: 420px;
      width: 100%;
    }

    .lock-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 1.5rem;
    }

    .lock-icon i {
      font-size: 4rem;
      color: var(--bayan-slate-300, #CBD5E1);
    }

    h1 {
      margin: 0 0 0.5rem;
      font-size: 1.5rem;
      font-weight: 600;
      color: var(--bayan-slate-900, #0F172A);
    }

    p {
      margin: 0;
      color: var(--bayan-slate-500, #64748B);
      font-size: 0.9375rem;
    }

    .actions {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      margin-top: 2rem;
    }

    .contact-link {
      display: inline-flex;
      align-items: center;
      gap: 0.375rem;
      color: var(--bayan-primary, #4F46E5);
      text-decoration: none;
      font-size: 0.875rem;
      font-weight: 500;
      transition: color var(--bayan-transition-fast, 150ms ease);
    }

    .contact-link:hover {
      color: var(--bayan-primary-hover, #4338CA);
      text-decoration: underline;
    }

    :host ::ng-deep {
      .go-back-btn.p-button.p-button-outlined {
        border-color: var(--bayan-slate-300, #CBD5E1);
        color: var(--bayan-slate-700, #334155);
        border-radius: var(--bayan-radius-lg, 0.75rem);
        padding: 0.625rem 1.5rem;
        font-weight: 500;
        transition: background-color var(--bayan-transition-fast, 150ms ease),
                    border-color var(--bayan-transition-fast, 150ms ease);
      }

      .go-back-btn.p-button.p-button-outlined:hover {
        background: var(--bayan-slate-100, #F1F5F9);
        border-color: var(--bayan-slate-400, #94A3B8);
        color: var(--bayan-slate-700, #334155);
      }
    }
  `]
})
export class UnauthorizedComponent {
  private readonly authService = inject(AuthService);

  logout(): void {
    this.authService.logout();
  }
}

