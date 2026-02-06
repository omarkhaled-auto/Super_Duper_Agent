import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HeaderComponent } from './header/header.component';
import { SidebarComponent } from './sidebar/sidebar.component';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [CommonModule, RouterModule, HeaderComponent, SidebarComponent],
  template: `
    <div class="layout-wrapper" [class.sidebar-collapsed]="sidebarCollapsed()">
      <app-header
        [collapsed]="sidebarCollapsed()"
        (toggleSidebar)="toggleSidebar()"
      ></app-header>

      <app-sidebar
        [collapsed]="sidebarCollapsed()"
        (menuItemClick)="onMenuItemClick()"
      ></app-sidebar>

      <main class="main-content">
        <div class="content-wrapper">
          <router-outlet></router-outlet>
        </div>
      </main>
    </div>

    <!-- Mobile overlay -->
    @if (!sidebarCollapsed() && isMobile()) {
      <div class="sidebar-overlay" (click)="toggleSidebar()"></div>
    }
  `,
  styles: [`
    .layout-wrapper {
      min-height: 100vh;
      background-color: #f5f7fa;
    }

    .main-content {
      margin-left: 280px;
      margin-top: 64px;
      min-height: calc(100vh - 64px);
      transition: margin-left 0.3s ease;
    }

    .layout-wrapper.sidebar-collapsed .main-content {
      margin-left: 64px;
    }

    .content-wrapper {
      padding: 1.5rem;
      max-width: 1400px;
      margin: 0 auto;
    }

    .sidebar-overlay {
      position: fixed;
      top: 64px;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: rgba(0, 0, 0, 0.5);
      z-index: 998;
    }

    @media (max-width: 991px) {
      .main-content {
        margin-left: 0;
      }

      .layout-wrapper.sidebar-collapsed .main-content {
        margin-left: 0;
      }

      :host ::ng-deep .sidebar-container {
        transform: translateX(-100%);
      }

      :host ::ng-deep .layout-wrapper:not(.sidebar-collapsed) .sidebar-container {
        transform: translateX(0);
        width: 280px !important;
      }
    }
  `]
})
export class LayoutComponent {
  sidebarCollapsed = signal(false);
  isMobile = signal(false);

  constructor() {
    this.checkMobile();
    if (typeof window !== 'undefined') {
      window.addEventListener('resize', () => this.checkMobile());
    }
  }

  private checkMobile(): void {
    if (typeof window !== 'undefined') {
      this.isMobile.set(window.innerWidth < 992);
      if (this.isMobile()) {
        this.sidebarCollapsed.set(true);
      }
    }
  }

  toggleSidebar(): void {
    this.sidebarCollapsed.update(collapsed => !collapsed);
  }

  onMenuItemClick(): void {
    if (this.isMobile()) {
      this.sidebarCollapsed.set(true);
    }
  }
}
