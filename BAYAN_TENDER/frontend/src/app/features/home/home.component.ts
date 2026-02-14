import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { AuthService } from '../../core/auth/auth.service';
import { UserRole } from '../../core/models/user.model';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, ProgressSpinnerModule],
  template: `
    <div class="home-redirect" data-testid="home-redirect">
      <p-progressSpinner [style]="{ width: '28px', height: '28px' }" strokeWidth="4"></p-progressSpinner>
      <span>Redirecting...</span>
    </div>
  `,
  styles: [`
    .home-redirect {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.75rem;
      padding: 2rem;
      color: var(--bayan-slate-500);
      font-size: 0.875rem;
    }

    :host ::ng-deep .p-progress-spinner-circle {
      stroke: var(--bayan-primary) !important;
    }
  `]
})
export class HomeComponent implements OnInit {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  ngOnInit(): void {
    const role = this.authService.userRole();

    const target = (() => {
      switch (role) {
        case UserRole.APPROVER:
          return '/dashboard/approver';
        case UserRole.AUDITOR:
        case UserRole.COMMERCIAL_ANALYST:
          return '/dashboard/overview';
        case UserRole.TECHNICAL_PANELIST:
          return '/tenders';
        case UserRole.ADMIN:
        case UserRole.TENDER_MANAGER:
          return '/dashboard';
        default:
          return '/tenders';
      }
    })();

    this.router.navigateByUrl(target, { replaceUrl: true });
  }
}
