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
      background: linear-gradient(180deg, #0F172A 0%, #0C1322 100%);
      color: var(--bayan-sidebar-foreground, #F8FAFC);
      border-right: 1px solid rgba(148, 163, 184, 0.08);
      box-shadow: 4px 0 24px rgba(0, 0, 0, 0.12);
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
      padding: 0.75rem 0;
    }

    /* Dark-themed scrollbar for sidebar */
    .sidebar-content::-webkit-scrollbar {
      width: 4px;
    }

    .sidebar-content::-webkit-scrollbar-track {
      background: transparent;
    }

    .sidebar-content::-webkit-scrollbar-thumb {
      background: rgba(148, 163, 184, 0.2);
      border-radius: 4px;
    }

    .sidebar-content::-webkit-scrollbar-thumb:hover {
      background: rgba(148, 163, 184, 0.35);
    }

    .sidebar-footer {
      padding: 0.75rem 1rem;
      border-top: 1px solid rgba(148, 163, 184, 0.08);
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .version {
      font-size: 0.6875rem;
      color: rgba(148, 163, 184, 0.4);
      letter-spacing: 0.04em;
      font-weight: 500;
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
          border-radius: var(--bayan-radius-md, 0.5rem);
          margin: 0 0.625rem;
          padding: 0 !important;
          transition: background-color 200ms ease, box-shadow 200ms ease;
        }

        .p-panelmenu-header-content:hover {
          background-color: rgba(148, 163, 184, 0.08) !important;
        }

        .p-panelmenu-header-link {
          display: flex;
          align-items: center;
          gap: 0.875rem;
          padding: 0.6875rem 0.875rem;
          color: var(--bayan-sidebar-foreground, #F8FAFC) !important;
          font-size: 0.875rem;
          font-weight: 500;
          text-decoration: none;
          cursor: pointer;
          letter-spacing: 0.01em;
        }

        .p-panelmenu-header-label {
          color: var(--bayan-sidebar-foreground, #F8FAFC) !important;
          font-size: 0.875rem;
          font-weight: 500;
        }

        /* ── Item icon (pi-home, pi-file, etc. — PrimeNG names it "submenu-icon") ── */
        .p-panelmenu-submenu-icon {
          color: rgba(148, 163, 184, 0.7);
          font-size: 1.125rem !important;
          width: 22px;
          text-align: center;
          transition: color 200ms ease;
          order: 0;
        }

        .p-panelmenu-header-content:hover .p-panelmenu-submenu-icon {
          color: rgba(165, 180, 252, 0.8);
        }

        /* ── Expand/collapse chevron (PrimeNG renders this FIRST in DOM — move to end) ── */
        .p-panelmenu-header-link > .p-iconwrapper,
        .p-panelmenu-header-link > chevronrighticon,
        .p-panelmenu-header-link > chevrondownicon {
          order: 99;
          margin-left: auto;
          color: rgba(148, 163, 184, 0.35);
          font-size: 0.75rem;
          transition: color 200ms ease, transform 200ms ease;
        }

        .p-panelmenu-header-content:hover > .p-panelmenu-header-link > .p-iconwrapper,
        .p-panelmenu-header-content:hover > .p-panelmenu-header-link > chevronrighticon,
        .p-panelmenu-header-content:hover > .p-panelmenu-header-link > chevrondownicon {
          color: rgba(148, 163, 184, 0.6);
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
          padding: 0.25rem 0 0.375rem 0;
          list-style: none;
          margin: 0;
          position: relative;
        }

        /* Subtle vertical line connector for submenu */
        .p-panelmenu-submenu::before {
          content: '';
          position: absolute;
          left: 2.125rem;
          top: 0.25rem;
          bottom: 0.375rem;
          width: 1px;
          background: rgba(148, 163, 184, 0.1);
          border-radius: 1px;
        }

        /* ── Sub-items (All Tenders, Users, etc.) ── */
        .p-panelmenu-item {
          margin: 0.0625rem 0;
        }

        .p-panelmenu-item-content {
          border: none !important;
          background: transparent !important;
          border-radius: var(--bayan-radius-md, 0.5rem);
          margin: 0 0.625rem;
          transition: background-color 200ms ease;
        }

        .p-panelmenu-item-content:hover {
          background-color: rgba(148, 163, 184, 0.08) !important;
        }

        .p-panelmenu-item-link {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.5rem 0.875rem 0.5rem 2.875rem;
          color: rgba(148, 163, 184, 0.65) !important;
          font-size: 0.8125rem;
          font-weight: 450;
          text-decoration: none;
          cursor: pointer;
          transition: color 200ms ease;
          letter-spacing: 0.01em;
        }

        .p-panelmenu-item-link:hover {
          color: var(--bayan-sidebar-foreground, #F8FAFC) !important;
        }

        .p-panelmenu-item-label {
          color: inherit !important;
          font-size: 0.8125rem;
        }

        .p-panelmenu-item-link .pi {
          color: inherit;
          font-size: 0.9375rem;
          width: 18px;
          text-align: center;
        }

        /* ── Active/Highlight state for sub-items ── */
        .p-panelmenu-item.p-focus > .p-panelmenu-item-content,
        .p-panelmenu-item.p-highlight > .p-panelmenu-item-content {
          background-color: rgba(79, 70, 229, 0.15) !important;
          border-left: 2px solid var(--bayan-sidebar-active-border, #818CF8);
        }

        .p-panelmenu-item.p-focus > .p-panelmenu-item-content .p-panelmenu-item-link,
        .p-panelmenu-item.p-highlight > .p-panelmenu-item-content .p-panelmenu-item-link {
          color: #E0E7FF !important;
          font-weight: 500;
        }

        .p-panelmenu-item.p-focus > .p-panelmenu-item-content .p-panelmenu-item-link .pi,
        .p-panelmenu-item.p-highlight > .p-panelmenu-item-content .p-panelmenu-item-link .pi {
          color: #A5B4FC;
        }

        /* ── Active/Highlight state for header items ── */
        .p-panelmenu-header.p-highlight .p-panelmenu-header-content,
        .p-panelmenu-header.p-panelmenu-header-active .p-panelmenu-header-content {
          background-color: rgba(79, 70, 229, 0.15) !important;
          border-left: 2px solid #818CF8;
        }

        .p-panelmenu-header.p-highlight .p-panelmenu-header-link,
        .p-panelmenu-header.p-panelmenu-header-active .p-panelmenu-header-link {
          color: #E0E7FF !important;
        }

        .p-panelmenu-header.p-highlight .p-panelmenu-header-link .pi,
        .p-panelmenu-header.p-panelmenu-header-active .p-panelmenu-header-link .pi {
          color: #A5B4FC;
        }

        .p-panelmenu-header.p-highlight .p-panelmenu-header-label,
        .p-panelmenu-header.p-panelmenu-header-active .p-panelmenu-header-label {
          color: #E0E7FF !important;
          font-weight: 600;
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
