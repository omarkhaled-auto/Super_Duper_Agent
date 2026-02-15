import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { PortalService } from '../../../core/services/portal.service';

@Component({
  selector: 'app-portal-tenders',
  standalone: true,
  imports: [CommonModule, RouterModule, CardModule, ButtonModule, TagModule],
  template: `
    <div class="portal-page">
      <!-- Dark branded header -->
      <header class="portal-header">
        <div class="header-inner">
          <div class="header-left">
            <img src="assets/images/logo-white.png" alt="Bayan" class="header-logo" />
            <div class="header-divider"></div>
            <div>
              <h1>Bidder Portal</h1>
              <p>Welcome, {{ companyName() }}</p>
            </div>
          </div>
          <button pButton label="Logout" icon="pi pi-sign-out" class="p-button-outlined logout-btn" (click)="logout()"></button>
        </div>
      </header>

      <!-- Main content -->
      <main class="portal-main">
        <div class="main-inner">
          @if (tenders().length > 0) {
            <div class="section-header">
              <h2>Your Tenders</h2>
              <span class="tender-count">{{ tenders().length }} {{ tenders().length === 1 ? 'tender' : 'tenders' }}</span>
            </div>
            <div class="tenders-grid">
              @for (tender of tenders(); track tender.tenderId) {
                <a class="tender-card" [routerLink]="['/portal/tenders', tender.tenderId, 'documents']">
                  <div class="card-accent" [class.submitted]="tender.hasSubmittedBid"></div>
                  <div class="card-body">
                    <div class="card-top">
                      <span class="tender-ref">{{ tender.tenderReference }}</span>
                      @if (tender.hasSubmittedBid) {
                        <span class="status-badge submitted"><i class="pi pi-check-circle"></i> Submitted</span>
                      } @else {
                        <span class="status-badge pending"><i class="pi pi-clock"></i> {{ tender.qualificationStatus || 'Pending' }}</span>
                      }
                    </div>
                    <h3 class="tender-title">{{ tender.tenderTitle }}</h3>
                    <div class="card-footer">
                      <span class="open-link">Open tender <i class="pi pi-arrow-right"></i></span>
                    </div>
                  </div>
                </a>
              }
            </div>
          } @else {
            <div class="empty-state">
              <div class="empty-icon-wrap">
                <i class="pi pi-inbox"></i>
              </div>
              <h2>No Tenders Assigned</h2>
              <p>You haven't been invited to any tenders yet. When a tender manager adds you, it will appear here.</p>
              <p class="contact-info">
                <i class="pi pi-envelope"></i>
                Contact <strong>support&#64;bayan.ae</strong> if you believe this is an error.
              </p>
            </div>
          }
        </div>
      </main>

      <!-- Footer -->
      <footer class="portal-footer">
        <span>Powered by Bayan Tender Management System</span>
        <span>Support: support&#64;bayan.ae</span>
      </footer>
    </div>
  `,
  styles: [`
    /* ── Page layout ─────────────────────────────────────── */
    .portal-page {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      background: var(--bayan-slate-50, #F8FAFC);
    }

    /* ── Dark branded header ─────────────────────────────── */
    .portal-header {
      background: var(--bayan-slate-800, #1E293B);
      color: white;
      box-shadow: 0 1px 3px 0 rgba(0,0,0,0.2);
    }

    .header-inner {
      max-width: 1100px;
      margin: 0 auto;
      padding: 1.25rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 1.25rem;
    }

    .header-logo {
      height: 34px;
      width: auto;
      object-fit: contain;
    }

    .header-divider {
      width: 1px;
      height: 32px;
      background: rgba(255,255,255,0.2);
    }

    :host .portal-header h1 {
      margin: 0;
      font-size: 1.25rem;
      font-weight: 600;
      line-height: 1.3;
      color: #ffffff !important;
    }

    .portal-header p {
      margin: 2px 0 0;
      font-size: 0.8125rem;
      color: var(--bayan-slate-400, #94A3B8);
    }

    .logout-btn {
      color: white !important;
      border-color: rgba(255,255,255,0.25) !important;
      font-size: 0.8125rem !important;
    }

    .logout-btn:hover {
      background: rgba(255,255,255,0.1) !important;
      border-color: rgba(255,255,255,0.4) !important;
    }

    /* ── Main content ────────────────────────────────────── */
    .portal-main {
      flex: 1;
      padding: 2rem;
    }

    .main-inner {
      max-width: 1100px;
      margin: 0 auto;
    }

    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 1.5rem;
    }

    .section-header h2 {
      margin: 0;
      font-size: 1.375rem;
      font-weight: 700;
      color: var(--bayan-slate-900, #0F172A);
    }

    .tender-count {
      font-size: 0.8125rem;
      color: var(--bayan-slate-400, #94A3B8);
      font-weight: 500;
    }

    /* ── Tender cards ────────────────────────────────────── */
    .tenders-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 1.25rem;
    }

    .tender-card {
      display: flex;
      text-decoration: none;
      color: inherit;
      background: var(--bayan-card, #ffffff);
      border-radius: var(--bayan-radius-lg, 0.75rem);
      border: 1px solid var(--bayan-border, #E2E8F0);
      overflow: hidden;
      transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
      cursor: pointer;
      box-shadow: 0 1px 3px 0 rgba(0,0,0,0.04);
    }

    .tender-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px -4px rgba(0,0,0,0.1);
      border-color: var(--bayan-primary, #4F46E5);
    }

    .card-accent {
      width: 5px;
      flex-shrink: 0;
      background: var(--bayan-slate-300, #CBD5E1);
    }

    .card-accent.submitted {
      background: #16A34A;
    }

    .card-body {
      flex: 1;
      padding: 1.25rem 1.5rem;
      display: flex;
      flex-direction: column;
      min-height: 140px;
    }

    .card-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.75rem;
    }

    .tender-ref {
      font-family: 'SF Mono', 'Fira Code', monospace;
      font-size: 0.75rem;
      color: var(--bayan-slate-400, #94A3B8);
      letter-spacing: 0.02em;
    }

    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      font-size: 0.6875rem;
      font-weight: 600;
      padding: 0.25rem 0.625rem;
      border-radius: 999px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }

    .status-badge i {
      font-size: 0.625rem;
    }

    .status-badge.submitted {
      background: #DCFCE7;
      color: #15803D;
    }

    .status-badge.pending {
      background: #FEF3C7;
      color: #92400E;
    }

    .tender-title {
      margin: 0;
      font-size: 1.0625rem;
      font-weight: 600;
      color: var(--bayan-slate-900, #0F172A);
      line-height: 1.4;
      flex: 1;
    }

    .card-footer {
      margin-top: 1rem;
      display: flex;
      justify-content: flex-end;
    }

    .open-link {
      font-size: 0.8125rem;
      font-weight: 600;
      color: var(--bayan-primary, #4F46E5);
      display: inline-flex;
      align-items: center;
      gap: 0.375rem;
      transition: gap 180ms ease;
    }

    .open-link i {
      font-size: 0.75rem;
      transition: transform 180ms ease;
    }

    .tender-card:hover .open-link {
      gap: 0.5rem;
    }

    .tender-card:hover .open-link i {
      transform: translateX(2px);
    }

    /* ── Empty state ─────────────────────────────────────── */
    .empty-state {
      text-align: center;
      padding: 5rem 2rem;
      background: var(--bayan-card, #ffffff);
      border-radius: var(--bayan-radius-lg, 0.75rem);
      border: 1px solid var(--bayan-border, #E2E8F0);
    }

    .empty-icon-wrap {
      width: 80px;
      height: 80px;
      margin: 0 auto 1.5rem;
      border-radius: 50%;
      background: var(--bayan-slate-100, #F1F5F9);
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .empty-icon-wrap i {
      font-size: 2.5rem;
      color: var(--bayan-slate-300, #CBD5E1);
    }

    .empty-state h2 {
      color: var(--bayan-foreground, #020617);
      margin: 0 0 0.75rem;
      font-size: 1.25rem;
    }

    .empty-state p {
      color: var(--bayan-muted-foreground, #64748B);
      max-width: 420px;
      margin: 0 auto 1rem;
      line-height: 1.6;
      font-size: 0.9375rem;
    }

    .contact-info {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
    }

    .contact-info i {
      color: var(--bayan-primary, #4F46E5);
    }

    /* ── Footer ──────────────────────────────────────────── */
    .portal-footer {
      background: var(--bayan-slate-700, #334155);
      color: var(--bayan-slate-400, #94A3B8);
      padding: 1rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.8125rem;
    }

    /* ── Responsive ──────────────────────────────────────── */
    @media (max-width: 768px) {
      .header-inner { padding: 1rem; }
      .header-divider { display: none; }
      .portal-main { padding: 1.25rem; }
      .tenders-grid { grid-template-columns: 1fr; }
      .portal-footer { flex-direction: column; gap: 0.5rem; text-align: center; }
    }
  `]
})
export class PortalTendersComponent implements OnInit {
  private readonly portalService = inject(PortalService);

  companyName = signal('');
  tenders = signal<Array<{ tenderId: string; tenderTitle: string; tenderReference: string; qualificationStatus: string; hasSubmittedBid?: boolean }>>([]);

  ngOnInit(): void {
    const user = this.portalService.currentUser();
    this.companyName.set(user?.companyName || 'Bidder');

    // Load tenders from localStorage portal_user data (tenderAccess was stored during login)
    const userStr = localStorage.getItem('portal_user');
    if (userStr) {
      try {
        const userData = JSON.parse(userStr);
        if (userData.tenderAccess) {
          this.tenders.set(userData.tenderAccess);
        }
      } catch {
        // ignore parse errors
      }
    }
  }

  logout(): void {
    this.portalService.logout();
  }
}
