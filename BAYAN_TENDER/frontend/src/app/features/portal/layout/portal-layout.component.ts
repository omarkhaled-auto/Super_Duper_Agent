import { Component, inject, OnInit, OnDestroy, signal, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, ActivatedRoute, Router } from '@angular/router';
import { interval, Subscription } from 'rxjs';
import { ButtonModule } from 'primeng/button';
import { TooltipModule } from 'primeng/tooltip';
import { TagModule } from 'primeng/tag';
import { PortalService } from '../../../core/services/portal.service';

@Component({
  selector: 'app-portal-layout',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    RouterModule,
    ButtonModule,
    TooltipModule,
    TagModule
  ],
  template: `
    <div class="portal-layout">
      <!-- Header -->
      <header class="portal-header">
        <div class="header-content">
          <div class="header-left">
            <a routerLink="/portal/tenders" class="back-link" pTooltip="Back to Your Tenders" tooltipPosition="bottom">
              <i class="pi pi-arrow-left"></i>
            </a>
            <img src="assets/images/logo-white.svg" alt="Bayan" class="portal-logo" />
            <div class="tender-info" *ngIf="tender()">
              <h1 class="tender-title">{{ tender()?.title }}</h1>
              <span class="tender-reference">{{ tender()?.reference }}</span>
            </div>
          </div>

          <div class="header-right">
            <!-- Deadline Countdown -->
            <div class="deadline-countdown" *ngIf="tender() && !countdown().isExpired">
              <span class="countdown-label">Submission Deadline:</span>
              <div class="countdown-timer">
                <div class="countdown-unit">
                  <span class="countdown-value">{{ countdown().days }}</span>
                  <span class="countdown-text">Days</span>
                </div>
                <span class="countdown-separator">:</span>
                <div class="countdown-unit">
                  <span class="countdown-value">{{ padZero(countdown().hours) }}</span>
                  <span class="countdown-text">Hours</span>
                </div>
                <span class="countdown-separator">:</span>
                <div class="countdown-unit">
                  <span class="countdown-value">{{ padZero(countdown().minutes) }}</span>
                  <span class="countdown-text">Min</span>
                </div>
              </div>
            </div>

            <p-tag
              *ngIf="countdown().isExpired"
              severity="danger"
              value="Deadline Passed"
              icon="pi pi-exclamation-triangle"
            ></p-tag>

            <!-- User Menu -->
            <div class="user-info" *ngIf="user()">
              <span class="user-company">{{ user()?.companyName }}</span>
              <button
                pButton
                icon="pi pi-sign-out"
                class="p-button-text p-button-sm logout-btn"
                pTooltip="Logout"
                tooltipPosition="bottom"
                (click)="logout()"
              ></button>
            </div>
          </div>
        </div>

        <!-- Navigation Tabs — plain Angular routerLink -->
        <nav class="portal-nav" *ngIf="tenderId">
          <a
            *ngFor="let tab of tabs"
            [routerLink]="['/portal/tenders', tenderId, tab.path]"
            routerLinkActive="active"
            class="nav-tab"
          >
            <i class="pi {{ tab.icon }}"></i>
            <span>{{ tab.label }}</span>
          </a>
        </nav>
      </header>

      <!-- Main Content -->
      <main class="portal-main">
        <div class="portal-content">
          <router-outlet></router-outlet>
        </div>
      </main>

      <!-- Footer -->
      <footer class="portal-footer">
        <div class="footer-content">
          <div class="footer-left">
            <span class="company-info">{{ tender()?.clientName }}</span>
          </div>
          <div class="footer-center">
            <span class="copyright">Powered by Bayan Tender Management System</span>
          </div>
          <div class="footer-right">
            <span class="support-info">Support: support&#64;bayan.ae</span>
          </div>
        </div>
      </footer>
    </div>
  `,
  styles: [`
    .portal-layout {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      background-color: var(--bayan-muted, #f4f4f5);
    }

    .portal-header {
      background: var(--bayan-primary, #18181b);
      color: white;
      position: sticky;
      top: 0;
      z-index: 1000;
      border-bottom: 1px solid var(--bayan-border, #e4e4e7);
      box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05);
    }

    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 2rem;
      max-width: 1400px;
      margin: 0 auto;
      width: 100%;
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 1.5rem;
    }

    .back-link {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 36px;
      border-radius: 0.375rem;
      color: rgba(255, 255, 255, 0.7);
      text-decoration: none;
      transition: background 0.15s ease, color 0.15s ease;
    }

    .back-link:hover {
      background: rgba(255, 255, 255, 0.1);
      color: white;
    }

    .back-link i { font-size: 1.125rem; }

    .portal-logo { height: 40px; }

    .tender-info {
      border-left: 1px solid rgba(255, 255, 255, 0.3);
      padding-left: 1.5rem;
    }

    .tender-title {
      font-size: 1.125rem;
      font-weight: 600;
      margin: 0;
      line-height: 1.3;
      max-width: 400px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .tender-reference { font-size: 0.875rem; opacity: 0.8; }

    .header-right {
      display: flex;
      align-items: center;
      gap: 2rem;
    }

    .deadline-countdown {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
    }

    .countdown-label { font-size: 0.75rem; opacity: 0.8; margin-bottom: 0.25rem; }

    .countdown-timer {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      background: rgba(255, 255, 255, 0.1);
      padding: 0.5rem 0.75rem;
      border-radius: 0.375rem;
    }

    .countdown-unit {
      display: flex;
      flex-direction: column;
      align-items: center;
      min-width: 40px;
    }

    .countdown-value { font-size: 1.25rem; font-weight: 700; line-height: 1; }
    .countdown-text { font-size: 0.625rem; text-transform: uppercase; opacity: 0.7; }
    .countdown-separator { font-size: 1.25rem; font-weight: 700; opacity: 0.5; }

    .user-info {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      border-left: 1px solid rgba(255, 255, 255, 0.3);
      padding-left: 1.5rem;
    }

    .user-company {
      font-weight: 500;
      max-width: 200px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .logout-btn { color: white !important; }
    .logout-btn:hover { background: rgba(255, 255, 255, 0.1) !important; }

    /* Navigation Tabs */
    .portal-nav {
      display: flex;
      gap: 0.25rem;
      padding: 0 2rem;
      max-width: 1400px;
      margin: 0 auto;
      width: 100%;
      background: rgba(255, 255, 255, 0.05);
    }

    .nav-tab {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.875rem 1.5rem;
      color: rgba(255, 255, 255, 0.7);
      text-decoration: none;
      border-radius: 0.375rem 0.375rem 0 0;
      transition: background 0.15s ease, color 0.15s ease;
      font-weight: 500;
      font-size: 0.9375rem;
      cursor: pointer;
      user-select: none;
    }

    .nav-tab:hover {
      background: rgba(255, 255, 255, 0.1);
      color: white;
    }

    .nav-tab.active {
      background: var(--bayan-card, #ffffff);
      color: var(--bayan-primary, #18181b);
    }

    .nav-tab.active i {
      color: var(--bayan-primary, #18181b);
    }

    /* Main Content */
    .portal-main { flex: 1; padding: 2rem; }
    .portal-content { max-width: 1400px; margin: 0 auto; }

    /* Footer */
    .portal-footer {
      background: var(--bayan-foreground, #09090b);
      color: rgba(255, 255, 255, 0.7);
      padding: 1rem 2rem;
      margin-top: auto;
    }

    .footer-content {
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.875rem;
    }

    .copyright { opacity: 0.7; }

    @media (max-width: 991px) {
      .header-content { flex-wrap: wrap; gap: 1rem; padding: 1rem; }
      .tender-info { display: none; }
      .deadline-countdown { flex: 1; align-items: center; }
      .countdown-timer { width: 100%; justify-content: center; }
      .user-info { border-left: none; padding-left: 0; }
      .footer-content { flex-direction: column; gap: 0.5rem; text-align: center; }
    }

    @media (max-width: 576px) {
      .portal-main { padding: 1rem; }
      .portal-nav { padding: 0 1rem; gap: 0; }
      .nav-tab { padding: 0.75rem 1rem; font-size: 0.8125rem; }
      .countdown-unit { min-width: 30px; }
      .countdown-value { font-size: 1rem; }
    }
  `]
})
export class PortalLayoutComponent implements OnInit, OnDestroy {
  private readonly portalService = inject(PortalService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  private countdownSubscription?: Subscription;

  tender = this.portalService.currentTender;
  user = this.portalService.currentUser;
  tenderId = '';

  countdown = signal({
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
    isExpired: false,
    totalSeconds: 0
  });

  tabs = [
    { label: 'Documents', icon: 'pi-folder', path: 'documents' },
    { label: 'Clarifications', icon: 'pi-comments', path: 'clarifications' },
    { label: 'Submit Bid', icon: 'pi-upload', path: 'submit' }
  ];

  ngOnInit(): void {
    this.tenderId = this.route.snapshot.params['tenderId'] || '';
    this.loadTenderInfo();
    this.startCountdown();
  }

  ngOnDestroy(): void {
    this.countdownSubscription?.unsubscribe();
  }

  padZero(n: number): string {
    return n < 10 ? '0' + n : '' + n;
  }

  private loadTenderInfo(): void {
    if (this.tenderId && !this.tender()) {
      this.portalService.getTenderInfo(this.tenderId).subscribe({
        next: () => this.updateCountdown()
      });
    }
  }

  private startCountdown(): void {
    // Update countdown every 30 seconds (not every second — reduces change detection)
    this.countdownSubscription = interval(30000).subscribe(() => {
      this.updateCountdown();
    });
    this.updateCountdown();
  }

  private updateCountdown(): void {
    const tender = this.tender();
    if (tender?.submissionDeadline) {
      this.countdown.set(
        this.portalService.getDeadlineCountdown(tender.submissionDeadline)
      );
    }
  }

  logout(): void {
    this.portalService.logout();
  }
}
