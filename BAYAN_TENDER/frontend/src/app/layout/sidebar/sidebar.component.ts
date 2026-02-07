import { Component, inject, Input, Output, EventEmitter, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { PanelMenuModule } from 'primeng/panelmenu';
import { MenuItem } from 'primeng/api';
import { AuthService } from '../../core/auth/auth.service';
import { UserRole } from '../../core/models/user.model';

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
      background: #ffffff;
      border-right: 1px solid #e0e0e0;
      position: fixed;
      left: 0;
      top: 64px;
      display: flex;
      flex-direction: column;
      transition: width 0.3s ease;
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

    .sidebar-footer {
      padding: 1rem;
      border-top: 1px solid #e0e0e0;
      text-align: center;
    }

    .version {
      font-size: 0.75rem;
      color: #999;
    }

    :host ::ng-deep {
      .sidebar-menu {
        border: none;

        .p-panelmenu-panel {
          margin-bottom: 0.25rem;
        }

        .p-panelmenu-header {
          border-radius: 0;
        }

        .p-panelmenu-header-content {
          border: none;
          background: transparent;
          border-radius: 8px;
          margin: 0 0.5rem;
          transition: background-color 0.2s;
        }

        .p-panelmenu-header-content:hover {
          background-color: #f5f5f5;
        }

        .p-panelmenu-header-link {
          padding: 0.75rem 1rem;
          color: #333;
        }

        .p-panelmenu-content {
          border: none;
          background: transparent;
        }

        .p-menuitem-link {
          padding: 0.5rem 1rem 0.5rem 2.5rem;
          border-radius: 8px;
          margin: 0 0.5rem;
        }

        .p-menuitem-link:hover {
          background-color: #f5f5f5;
        }

        .p-menuitem-icon {
          margin-right: 0.75rem;
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
    const user = this.currentUser();

    const baseItems: MenuItem[] = [
      {
        label: 'Dashboard',
        icon: 'pi pi-home',
        routerLink: ['/dashboard'],
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
      },
      {
        label: 'Reports',
        icon: 'pi pi-chart-bar',
        items: [
          {
            label: 'Analytics',
            icon: 'pi pi-chart-line',
            routerLink: ['/reports/analytics'],
            command: () => this.menuItemClick.emit()
          },
          {
            label: 'Export',
            icon: 'pi pi-download',
            routerLink: ['/reports/export'],
            command: () => this.menuItemClick.emit()
          }
        ]
      }
    ];

    // Add admin menu items if user has admin role
    if (this.authService.hasRole([UserRole.ADMIN, UserRole.TENDER_MANAGER])) {
      baseItems.push({
        label: 'Administration',
        icon: 'pi pi-cog',
        items: [
          {
            label: 'Users',
            icon: 'pi pi-users',
            routerLink: ['/admin/users'],
            command: () => this.menuItemClick.emit()
          },
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
          },
          {
            label: 'Settings',
            icon: 'pi pi-sliders-h',
            routerLink: ['/admin/settings'],
            command: () => this.menuItemClick.emit()
          },
          {
            label: 'Audit Logs',
            icon: 'pi pi-history',
            routerLink: ['/admin/audit-logs'],
            command: () => this.menuItemClick.emit()
          }
        ]
      });
    }

    return baseItems;
  });
}
