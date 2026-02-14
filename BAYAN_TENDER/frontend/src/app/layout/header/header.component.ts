import { Component, inject, Output, EventEmitter, Input, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MenubarModule } from 'primeng/menubar';
import { ButtonModule } from 'primeng/button';
import { AvatarModule } from 'primeng/avatar';
import { MenuModule } from 'primeng/menu';
import { BadgeModule } from 'primeng/badge';
import { RippleModule } from 'primeng/ripple';
import { MenuItem } from 'primeng/api';
import { AuthService } from '../../core/auth/auth.service';
import { UserRole } from '../../core/models/user.model';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [
    CommonModule,
    MenubarModule,
    ButtonModule,
    AvatarModule,
    MenuModule,
    BadgeModule,
    RippleModule
  ],
  template: `
    <div class="header-container">
      <div class="header-left">
        <button
          pButton
          pRipple
          type="button"
          icon="pi pi-bars"
          class="p-button-text p-button-rounded"
          data-testid="sidebar-toggle"
          (click)="toggleSidebar.emit()"
        ></button>
        <div class="logo">
          <i class="pi pi-briefcase logo-icon" *ngIf="!collapsed"></i>
          <span class="logo-text" *ngIf="!collapsed">Bayan Tender</span>
        </div>
      </div>

      <div class="header-right">
        <button
          pButton
          pRipple
          type="button"
          icon="pi pi-bell"
          class="p-button-text p-button-rounded notification-btn"
          data-testid="notification-btn"
          pBadge
          value="3"
          severity="danger"
        ></button>

        <div class="user-menu" data-testid="user-menu">
          <p-avatar
            [label]="userInitials"
            shape="circle"
            [style]="{ 'background-color': 'var(--bayan-primary, #4F46E5)', color: 'var(--bayan-primary-foreground, #ffffff)', cursor: 'pointer' }"
            (click)="userMenu.toggle($event)"
          ></p-avatar>
          <span class="user-name" (click)="userMenu.toggle($event)">
            {{ currentUser()?.firstName }} {{ currentUser()?.lastName }}
          </span>
          <i class="pi pi-angle-down" (click)="userMenu.toggle($event)"></i>
          <p-menu #userMenu [model]="userMenuItems()" [popup]="true" appendTo="body"></p-menu>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .header-container {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0 1rem;
      height: 64px;
      background: var(--bayan-card, #ffffff);
      border-bottom: 1px solid var(--bayan-border, #E2E8F0);
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 1000;
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .logo {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .logo-icon {
      font-size: 1.5rem;
      color: var(--bayan-primary, #4F46E5);
    }

    .logo-text {
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--bayan-foreground, #020617);
      letter-spacing: -0.025em;
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .notification-btn {
      position: relative;
    }

    .user-menu {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      cursor: pointer;
      padding: 0.5rem;
      border-radius: var(--bayan-radius-sm, 0.375rem);
      transition: background-color 150ms ease;
    }

    .user-menu:hover {
      background-color: var(--bayan-slate-100, #F1F5F9);
    }

    .user-name {
      font-weight: 500;
      color: var(--bayan-foreground, #020617);
      font-size: 0.875rem;
    }

    :host ::ng-deep .p-badge {
      font-size: 0.6rem;
      min-width: 1rem;
      height: 1rem;
      line-height: 1rem;
    }

    :host ::ng-deep .p-button-text:hover {
      background-color: var(--bayan-slate-100, #F1F5F9) !important;
    }
  `]
})
export class HeaderComponent {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  @Input() collapsed = false;
  @Output() toggleSidebar = new EventEmitter<void>();

  currentUser = this.authService.currentUser;

  userMenuItems = computed<MenuItem[]>(() => {
    const user = this.currentUser();
    const role = user?.role;

    const items: MenuItem[] = [];

    if (role) {
      items.push({
        label: `Role: ${this.getRoleLabel(role)}`,
        icon: 'pi pi-id-card',
        disabled: true
      });
      items.push({ separator: true });
    }

    items.push(
      {
        label: 'Home',
        icon: 'pi pi-home',
        command: () => this.router.navigate(['/home'])
      },
      {
        label: 'Notification Settings',
        icon: 'pi pi-bell',
        command: () => this.router.navigate(['/settings/notifications'])
      }
    );

    if (role === UserRole.ADMIN) {
      items.push(
        { separator: true },
        {
          label: 'User Management',
          icon: 'pi pi-users',
          command: () => this.router.navigate(['/admin/users'])
        },
        {
          label: 'System Settings',
          icon: 'pi pi-sliders-h',
          command: () => this.router.navigate(['/admin/settings'])
        }
      );
    }

    if (role === UserRole.AUDITOR || role === UserRole.ADMIN) {
      items.push(
        { separator: true },
        {
          label: 'Audit Logs',
          icon: 'pi pi-history',
          command: () => this.router.navigate(['/admin/audit-logs'])
        }
      );
    }

    items.push(
      { separator: true },
      {
        label: 'Logout',
        icon: 'pi pi-sign-out',
        command: () => this.authService.logout()
      }
    );

    return items;
  });

  get userInitials(): string {
    const user = this.currentUser();
    if (!user) return 'U';
    return `${user.firstName?.charAt(0) || ''}${user.lastName?.charAt(0) || ''}`.toUpperCase();
  }

  private getRoleLabel(role: UserRole): string {
    switch (role) {
      case UserRole.ADMIN:
        return 'Admin';
      case UserRole.TENDER_MANAGER:
        return 'Tender Manager';
      case UserRole.COMMERCIAL_ANALYST:
        return 'Commercial Analyst';
      case UserRole.TECHNICAL_PANELIST:
        return 'Technical Panelist';
      case UserRole.APPROVER:
        return 'Approver';
      case UserRole.AUDITOR:
        return 'Auditor';
      default:
        return role;
    }
  }
}
