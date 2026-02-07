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
    <div class="portal-tenders-container">
      <div class="portal-header">
        <div class="header-left">
          <i class="pi pi-briefcase header-icon"></i>
          <div>
            <h1>Bidder Portal</h1>
            <p>Welcome, {{ companyName() }}</p>
          </div>
        </div>
        <button pButton label="Logout" icon="pi pi-sign-out" class="p-button-outlined" (click)="logout()"></button>
      </div>

      @if (tenders().length > 0) {
        <h2 class="section-title">Your Tenders</h2>
        <div class="tenders-grid">
          @for (tender of tenders(); track tender.tenderId) {
            <p-card styleClass="tender-card">
              <div class="tender-info">
                <h3>{{ tender.tenderTitle }}</h3>
                <p class="tender-ref">{{ tender.tenderReference }}</p>
                <p-tag [value]="tender.qualificationStatus" severity="success"></p-tag>
              </div>
              <div class="tender-actions">
                <a pButton label="Open" icon="pi pi-folder-open"
                   [routerLink]="['/portal/tenders', tender.tenderId, 'documents']"></a>
              </div>
            </p-card>
          }
        </div>
      } @else {
        <div class="empty-state">
          <i class="pi pi-inbox empty-icon"></i>
          <h2>No Tenders Assigned</h2>
          <p>You haven't been invited to any tenders yet. When a tender manager adds you to a tender, it will appear here.</p>
          <p class="contact-info">
            <i class="pi pi-envelope"></i>
            Contact <strong>support&#64;bayan.ae</strong> if you believe this is an error.
          </p>
        </div>
      }
    </div>
  `,
  styles: [`
    .portal-tenders-container {
      min-height: 100vh;
      background: #f0f2f5;
      padding: 2rem;
    }

    .portal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: white;
      padding: 1.5rem 2rem;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
      margin-bottom: 2rem;
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .header-icon {
      font-size: 2rem;
      color: #1565C0;
    }

    .portal-header h1 {
      margin: 0;
      font-size: 1.5rem;
      color: #1e293b;
    }

    .portal-header p {
      margin: 0.25rem 0 0;
      color: #64748b;
    }

    .section-title {
      color: #334155;
      margin-bottom: 1rem;
    }

    .tenders-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 1rem;
    }

    .tender-info h3 {
      margin: 0 0 0.5rem;
      color: #1e293b;
    }

    .tender-ref {
      color: #64748b;
      margin: 0 0 0.75rem;
      font-family: monospace;
    }

    .tender-actions {
      margin-top: 1rem;
      display: flex;
      justify-content: flex-end;
    }

    .empty-state {
      text-align: center;
      padding: 4rem 2rem;
      background: white;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
      margin-top: 2rem;
    }

    .empty-icon {
      font-size: 4rem;
      color: #cbd5e1;
      margin-bottom: 1rem;
    }

    .empty-state h2 {
      color: #334155;
      margin: 0 0 0.75rem;
    }

    .empty-state p {
      color: #64748b;
      max-width: 480px;
      margin: 0 auto 1rem;
      line-height: 1.6;
    }

    .contact-info {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
    }

    .contact-info i {
      color: #3b82f6;
    }
  `]
})
export class PortalTendersComponent implements OnInit {
  private readonly portalService = inject(PortalService);

  companyName = signal('');
  tenders = signal<Array<{ tenderId: string; tenderTitle: string; tenderReference: string; qualificationStatus: string }>>([]);

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
