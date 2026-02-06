import { Component, inject, OnInit, OnDestroy, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, ActivatedRoute, Router } from '@angular/router';
import { interval, Subscription } from 'rxjs';
import { ButtonModule } from 'primeng/button';
import { TabMenuModule } from 'primeng/tabmenu';
import { MenuItem } from 'primeng/api';
import { TooltipModule } from 'primeng/tooltip';
import { TagModule } from 'primeng/tag';
import { PortalService } from '../../../core/services/portal.service';
import { PortalTenderInfo } from '../../../core/models/portal.model';

@Component({
  selector: 'app-portal-layout',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    ButtonModule,
    TabMenuModule,
    TooltipModule,
    TagModule
  ],
  template: `
    <div class="portal-layout">
      <!-- Header -->
      <header class="portal-header">
        <div class="header-content">
          <div class="header-left">
            <img src="assets/images/logo-white.png" alt="Bayan" class="portal-logo" />
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
                  <span class="countdown-value">{{ countdown().hours | number:'2.0-0' }}</span>
                  <span class="countdown-text">Hours</span>
                </div>
                <span class="countdown-separator">:</span>
                <div class="countdown-unit">
                  <span class="countdown-value">{{ countdown().minutes | number:'2.0-0' }}</span>
                  <span class="countdown-text">Min</span>
                </div>
                <span class="countdown-separator">:</span>
                <div class="countdown-unit">
                  <span class="countdown-value">{{ countdown().seconds | number:'2.0-0' }}</span>
                  <span class="countdown-text">Sec</span>
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

        <!-- Navigation Tabs -->
        <div class="portal-nav" *ngIf="tender()">
          <p-tabMenu [model]="menuItems" [activeItem]="activeItem()"></p-tabMenu>
        </div>
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
      background-color: #f8f9fa;
    }

    /* Header Styles */
    .portal-header {
      background: linear-gradient(135deg, #1565C0 0%, #0D47A1 100%);
      color: white;
      position: sticky;
      top: 0;
      z-index: 1000;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
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

    .portal-logo {
      height: 40px;
    }

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

    .tender-reference {
      font-size: 0.875rem;
      opacity: 0.8;
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 2rem;
    }

    /* Countdown Styles */
    .deadline-countdown {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
    }

    .countdown-label {
      font-size: 0.75rem;
      opacity: 0.8;
      margin-bottom: 0.25rem;
    }

    .countdown-timer {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      background: rgba(255, 255, 255, 0.1);
      padding: 0.5rem 0.75rem;
      border-radius: 8px;
    }

    .countdown-unit {
      display: flex;
      flex-direction: column;
      align-items: center;
      min-width: 40px;
    }

    .countdown-value {
      font-size: 1.25rem;
      font-weight: 700;
      line-height: 1;
    }

    .countdown-text {
      font-size: 0.625rem;
      text-transform: uppercase;
      opacity: 0.7;
    }

    .countdown-separator {
      font-size: 1.25rem;
      font-weight: 700;
      opacity: 0.5;
    }

    /* User Info */
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

    .logout-btn {
      color: white !important;
    }

    .logout-btn:hover {
      background: rgba(255, 255, 255, 0.1) !important;
    }

    /* Navigation */
    .portal-nav {
      background: rgba(255, 255, 255, 0.05);
      padding: 0 2rem;
      max-width: 1400px;
      margin: 0 auto;
      width: 100%;
    }

    :host ::ng-deep {
      .portal-nav .p-tabmenu {
        background: transparent;
        border: none;
      }

      .portal-nav .p-tabmenu-nav {
        background: transparent;
        border: none;
        gap: 0.5rem;
      }

      .portal-nav .p-tabmenuitem {
        .p-menuitem-link {
          background: transparent;
          color: rgba(255, 255, 255, 0.7);
          border: none;
          padding: 1rem 1.5rem;
          border-radius: 8px 8px 0 0;
          transition: all 0.2s ease;

          .p-menuitem-icon {
            color: rgba(255, 255, 255, 0.7);
          }

          &:hover {
            background: rgba(255, 255, 255, 0.1);
            color: white;

            .p-menuitem-icon {
              color: white;
            }
          }
        }

        &.p-highlight .p-menuitem-link {
          background: white;
          color: #1565C0;

          .p-menuitem-icon {
            color: #1565C0;
          }
        }
      }
    }

    /* Main Content */
    .portal-main {
      flex: 1;
      padding: 2rem;
    }

    .portal-content {
      max-width: 1400px;
      margin: 0 auto;
    }

    /* Footer */
    .portal-footer {
      background: #1e293b;
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

    .copyright {
      opacity: 0.7;
    }

    /* Responsive */
    @media (max-width: 991px) {
      .header-content {
        flex-wrap: wrap;
        gap: 1rem;
        padding: 1rem;
      }

      .tender-info {
        display: none;
      }

      .deadline-countdown {
        flex: 1;
        align-items: center;
      }

      .countdown-timer {
        width: 100%;
        justify-content: center;
      }

      .user-info {
        border-left: none;
        padding-left: 0;
      }

      .footer-content {
        flex-direction: column;
        gap: 0.5rem;
        text-align: center;
      }
    }

    @media (max-width: 576px) {
      .portal-main {
        padding: 1rem;
      }

      .countdown-unit {
        min-width: 30px;
      }

      .countdown-value {
        font-size: 1rem;
      }
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

  countdown = signal({
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
    isExpired: false,
    totalSeconds: 0
  });

  menuItems: MenuItem[] = [];
  activeItem = signal<MenuItem | undefined>(undefined);

  ngOnInit(): void {
    this.setupNavigation();
    this.loadTenderInfo();
    this.startCountdown();
  }

  ngOnDestroy(): void {
    this.countdownSubscription?.unsubscribe();
  }

  private setupNavigation(): void {
    const tenderId = this.getTenderId();

    this.menuItems = [
      {
        label: 'Documents',
        icon: 'pi pi-folder',
        routerLink: `/portal/tenders/${tenderId}/documents`,
        command: () => this.setActiveByLabel('Documents')
      },
      {
        label: 'Clarifications',
        icon: 'pi pi-comments',
        routerLink: `/portal/tenders/${tenderId}/clarifications`,
        command: () => this.setActiveByLabel('Clarifications')
      },
      {
        label: 'Submit Bid',
        icon: 'pi pi-upload',
        routerLink: `/portal/tenders/${tenderId}/submit`,
        command: () => this.setActiveByLabel('Submit Bid')
      }
    ];

    // Set initial active item based on current route
    this.setActiveItemFromRoute();
  }

  private setActiveItemFromRoute(): void {
    const currentUrl = this.router.url;
    if (currentUrl.includes('/documents')) {
      this.setActiveByLabel('Documents');
    } else if (currentUrl.includes('/clarifications')) {
      this.setActiveByLabel('Clarifications');
    } else if (currentUrl.includes('/submit')) {
      this.setActiveByLabel('Submit Bid');
    }
  }

  private setActiveByLabel(label: string): void {
    const item = this.menuItems.find(i => i.label === label);
    if (item) {
      this.activeItem.set(item);
    }
  }

  private getTenderId(): number {
    // Try to get from route params first, then from stored tender
    const routeTenderId = this.route.firstChild?.snapshot.params['tenderId'];
    if (routeTenderId) {
      return parseInt(routeTenderId, 10);
    }
    return this.tender()?.id || 0;
  }

  private loadTenderInfo(): void {
    const tenderId = this.getTenderId();
    if (tenderId && !this.tender()) {
      this.portalService.getTenderInfo(tenderId).subscribe();
    }
  }

  private startCountdown(): void {
    // Update countdown every second
    this.countdownSubscription = interval(1000).subscribe(() => {
      const tender = this.tender();
      if (tender?.submissionDeadline) {
        this.countdown.set(
          this.portalService.getDeadlineCountdown(tender.submissionDeadline)
        );
      }
    });

    // Initial calculation
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
