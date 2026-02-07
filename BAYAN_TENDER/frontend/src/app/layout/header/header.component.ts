import { Component, inject, Output, EventEmitter, Input } from '@angular/core';
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
            [style]="{ 'background-color': '#2196F3', color: '#ffffff', cursor: 'pointer' }"
            (click)="userMenu.toggle($event)"
          ></p-avatar>
          <span class="user-name" (click)="userMenu.toggle($event)">
            {{ currentUser()?.firstName }} {{ currentUser()?.lastName }}
          </span>
          <i class="pi pi-angle-down" (click)="userMenu.toggle($event)"></i>
          <p-menu #userMenu [model]="userMenuItems" [popup]="true" appendTo="body"></p-menu>
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
      background: #ffffff;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
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
      color: #1976D2;
    }

    .logo-text {
      font-size: 1.25rem;
      font-weight: 600;
      color: #1976D2;
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
      border-radius: 8px;
      transition: background-color 0.2s;
    }

    .user-menu:hover {
      background-color: #f5f5f5;
    }

    .user-name {
      font-weight: 500;
      color: #333;
    }

    :host ::ng-deep .p-badge {
      font-size: 0.6rem;
      min-width: 1rem;
      height: 1rem;
      line-height: 1rem;
    }
  `]
})
export class HeaderComponent {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  @Input() collapsed = false;
  @Output() toggleSidebar = new EventEmitter<void>();

  currentUser = this.authService.currentUser;

  userMenuItems: MenuItem[] = [
    {
      label: 'Profile',
      icon: 'pi pi-user',
      command: () => this.router.navigate(['/profile'])
    },
    {
      label: 'Settings',
      icon: 'pi pi-cog',
      command: () => this.router.navigate(['/settings'])
    },
    { separator: true },
    {
      label: 'Logout',
      icon: 'pi pi-sign-out',
      command: () => this.authService.logout()
    }
  ];

  get userInitials(): string {
    const user = this.currentUser();
    if (!user) return 'U';
    return `${user.firstName?.charAt(0) || ''}${user.lastName?.charAt(0) || ''}`.toUpperCase();
  }
}
