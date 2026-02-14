import { Component, inject, Input, Output, EventEmitter, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { PanelMenuModule } from 'primeng/panelmenu';
import { MenuItem } from 'primeng/api';
import { AuthService } from '../../core/auth/auth.service';
import { UserRole } from '../../core/models/user.model';
import { RoleGroups } from '../../core/auth/role-groups';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule, PanelMenuModule],
  template: `
    <div class="sidebar-container" [class.collapsed]="collapsed" data-testid="sidebar">
      <div class="sidebar-content">
        <p-panelMenu [model]="menuItems()" [multiple]="false" styleClass="sidebar-menu" data-testid="sidebar-menu"></p-panelMenu>
      </div>
      <div class="sidebar-footer">
        <span class="version" *ngIf="!collapsed">v1.0.0</span>
      </div>
    </div>
  `,
  styles: [`
    .sidebar-container {
      width: 280px;
      height: calc(100vh - 64px);
      background: var(--bayan-sidebar-bg, #0F172A);
      color: var(--bayan-sidebar-foreground, #F8FAFC);
      border-right: 1px solid var(--bayan-sidebar-border, #1E293B);
      position: fixed;
      left: 0;
      top: 64px;
      display: flex;
      flex-direction: column;
      transition: width 0.2s ease;
      overflow: hidden;
      z-index: 999;
    }

    .sidebar-container.collapsed {
      width: 64px;
    }

    .sidebar-content {
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
      padding: 1rem 0;
    }

    /* Dark-themed scrollbar for sidebar */
    .sidebar-content::-webkit-scrollbar {
      width: 6px;
    }

    .sidebar-content::-webkit-scrollbar-track {
      background: transparent;
    }

    .sidebar-content::-webkit-scrollbar-thumb {
      background: rgba(248, 250, 252, 0.15);
      border-radius: 3px;
    }

    .sidebar-content::-webkit-scrollbar-thumb:hover {
      background: rgba(248, 250, 252, 0.25);
    }

    .sidebar-footer {
      padding: 1rem;
      border-top: 1px solid var(--bayan-sidebar-border, #1E293B);
      text-align: center;
    }

    .version {
      font-size: 0.75rem;
      color: var(--bayan-slate-500, #64748B);
    }

    :host ::ng-deep {
      .sidebar-menu {
        border: none;
        background: transparent;

        .p-panelmenu-panel {
          background: transparent !important;
          border: none !important;
          border-radius: 0 !important;
          margin-bottom: 0.125rem;
        }

        /* ── Header items (Dashboard, Tenders, etc.) ── */
        .p-panelmenu-header {
          border-radius: 0;
          color: var(--bayan-sidebar-foreground, #F8FAFC) !important;
        }

        .p-panelmenu-header-content {
          border: none !important;
          background: transparent !important;
          border-radius: var(--bayan-radius-sm, 0.375rem);
          margin: 0 0.5rem;
          padding: 0 !important;
          transition: background-color 150ms ease;
        }

        .p-panelmenu-header-content:hover {
          background-color: rgba(248, 250, 252, 0.08) !important;
        }

        .p-panelmenu-header-link {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.625rem 0.75rem;
          color: var(--bayan-sidebar-foreground, #F8FAFC) !important;
          font-size: 0.875rem;
          font-weight: 500;
          text-decoration: none;
          cursor: pointer;
        }

        .p-panelmenu-header-label {
          color: var(--bayan-sidebar-foreground, #F8FAFC) !important;
          font-size: 0.875rem;
          font-weight: 500;
        }

        .p-panelmenu-header-link .pi {
          color: var(--bayan-sidebar-muted, #94A3B8);
          font-size: 1.125rem;
        }

        /* ── Submenu chevron icon ── */
        .p-panelmenu-submenu-icon {
          color: var(--bayan-sidebar-muted, #94A3B8) !important;
          font-size: 0.75rem !important;
          margin-left: auto;
        }

        /* ── Expanded submenu content ── */
        .p-panelmenu-content {
          border: none !important;
          background: transparent !important;
          padding: 0;
        }

        .p-panelmenu-content-container {
          overflow: visible !important;
        }

        .p-panelmenu-submenu {
          padding: 0.25rem 0;
          list-style: none;
          margin: 0;
        }

        /* ── Sub-items (All Tenders, Users, etc.) ── */
        .p-panelmenu-item {
          margin: 0.0625rem 0;
        }

        .p-panelmenu-item-content {
          border: none !important;
          background: transparent !important;
          border-radius: var(--bayan-radius-sm, 0.375rem);
          margin: 0 0.5rem;
          transition: background-color 150ms ease;
        }

        .p-panelmenu-item-content:hover {
          background-color: rgba(248, 250, 252, 0.08) !important;
        }

        .p-panelmenu-item-link {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.5rem 0.75rem 0.5rem 2.75rem;
          color: var(--bayan-sidebar-muted, #94A3B8) !important;
          font-size: 0.875rem;
          text-decoration: none;
          cursor: pointer;
          transition: color 150ms ease;
        }

        .p-panelmenu-item-link:hover {
          color: var(--bayan-sidebar-foreground, #F8FAFC) !important;
        }

        .p-panelmenu-item-label {
          color: inherit !important;
          font-size: 0.875rem;
        }

        .p-panelmenu-item-link .pi {
          color: inherit;
          font-size: 1rem;
        }

        /* ── Active/Highlight state for sub-items ── */
        .p-panelmenu-item.p-focus > .p-panelmenu-item-content,
        .p-panelmenu-item.p-highlight > .p-panelmenu-item-content {
          background-color: rgba(79, 70, 229, 0.12) !important;
          border-left: 3px solid var(--bayan-sidebar-active-border, #4F46E5);
        }

        .p-panelmenu-item.p-focus > .p-panelmenu-item-content .p-panelmenu-item-link,
        .p-panelmenu-item.p-highlight > .p-panelmenu-item-content .p-panelmenu-item-link {
          color: #ffffff !important;
        }

        .p-panelmenu-item.p-focus > .p-panelmenu-item-content .p-panelmenu-item-link .pi,
        .p-panelmenu-item.p-highlight > .p-panelmenu-item-content .p-panelmenu-item-link .pi {
          color: #A5B4FC;
        }

        /* ── Active/Highlight state for header items ── */
        .p-panelmenu-header.p-highlight .p-panelmenu-header-content,
        .p-panelmenu-header.p-panelmenu-header-active .p-panelmenu-header-content {
          background-color: rgba(79, 70, 229, 0.12) !important;
        }

        .p-panelmenu-header.p-highlight .p-panelmenu-header-link .pi,
        .p-panelmenu-header.p-panelmenu-header-active .p-panelmenu-header-link .pi {
          color: #A5B4FC;
        }
      }
    }
  `]
})
export class SidebarComponent {
  private readonly authService = inject(AuthService);

  @Input() collapsed = false;
  @Output() menuItemClick = new EventEmitter<void>();

  currentUser = this.authService.currentUser;

  /**
   * Cached menu items using computed signal.
   * IMPORTANT: Using a getter here would create new array references on every
   * change detection cycle, causing PrimeNG PanelMenu to re-render infinitely.
   */
  menuItems = computed<MenuItem[]>(() => {
    // Reading currentUser signal makes this recompute only when user changes
    this.currentUser();

    const baseItems: MenuItem[] = [
      {
        label: 'Dashboard',
        icon: 'pi pi-home',
        routerLink: ['/home'],
        command: () => this.menuItemClick.emit()
      },
      {
        label: 'Tenders',
        icon: 'pi pi-file',
        items: [
          {
            label: 'All Tenders',
            icon: 'pi pi-list',
            routerLink: ['/tenders'],
            command: () => this.menuItemClick.emit()
          },
          {
            label: 'My Bids',
            icon: 'pi pi-bookmark',
            routerLink: ['/tenders/my-bids'],
            command: () => this.menuItemClick.emit()
          },
          {
            label: 'Saved Tenders',
            icon: 'pi pi-star',
            routerLink: ['/tenders/saved'],
            command: () => this.menuItemClick.emit()
          }
        ]
      }
    ];

    if (this.authService.hasRole([...RoleGroups.vendorPricingViewers])) {
      baseItems.push({
        label: 'Vendor Pricing',
        icon: 'pi pi-chart-line',
        routerLink: ['/vendor-pricing'],
        command: () => this.menuItemClick.emit()
      });
    }

    const adminItems: MenuItem[] = [];

    if (this.authService.hasRole([UserRole.ADMIN])) {
      adminItems.push({
        label: 'Users',
        icon: 'pi pi-users',
        routerLink: ['/admin/users'],
        command: () => this.menuItemClick.emit()
      });
    }

    if (this.authService.hasRole([UserRole.ADMIN, UserRole.TENDER_MANAGER])) {
      adminItems.push(
        {
          label: 'Clients',
          icon: 'pi pi-briefcase',
          routerLink: ['/admin/clients'],
          command: () => this.menuItemClick.emit()
        },
        {
          label: 'Bidders',
          icon: 'pi pi-building',
          routerLink: ['/admin/bidders'],
          command: () => this.menuItemClick.emit()
        }
      );
    }

    if (this.authService.hasRole([UserRole.ADMIN])) {
      adminItems.push({
        label: 'System Settings',
        icon: 'pi pi-sliders-h',
        routerLink: ['/admin/settings'],
        command: () => this.menuItemClick.emit()
      });
    }

    if (this.authService.hasRole([UserRole.ADMIN, UserRole.AUDITOR])) {
      adminItems.push({
        label: 'Audit Logs',
        icon: 'pi pi-history',
        routerLink: ['/admin/audit-logs'],
        command: () => this.menuItemClick.emit()
      });
    }

    if (adminItems.length > 0) {
      baseItems.push({
        label: 'Administration',
        icon: 'pi pi-cog',
        items: adminItems
      });
    }

    return baseItems;
  });
}
