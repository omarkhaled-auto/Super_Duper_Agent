import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CardModule } from 'primeng/card';
import { ChartModule } from 'primeng/chart';
import { MessageModule } from 'primeng/message';
import { SkeletonModule } from 'primeng/skeleton';
import { DashboardService } from '../../core/services/dashboard.service';
import { OverviewDashboard } from '../../core/models/dashboard.model';
import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-overview-dashboard',
  standalone: true,
  imports: [CommonModule, CardModule, ChartModule, MessageModule, SkeletonModule],
  template: `
    <div class="overview-container" data-testid="overview-dashboard">
      <div class="overview-header">
        <div>
          <h1>Overview</h1>
          <p>Welcome back, {{ currentUser()?.firstName }}.</p>
        </div>
      </div>

      @if (dashboardService.error()) {
        <p-message severity="error" [text]="dashboardService.error()!" styleClass="w-full"></p-message>
      }

      <div class="cards-grid">
        @if (dashboardService.isLoading() && !overview()) {
          @for (i of [1,2,3,4,5,6]; track i) {
            <p-card styleClass="stat-card">
              <p-skeleton width="100%" height="64px"></p-skeleton>
            </p-card>
          }
        } @else {
          <p-card styleClass="stat-card">
            <div class="stat">
              <div class="label">Total Tenders</div>
              <div class="value">{{ overview()?.tenderCounts?.total ?? 0 }}</div>
            </div>
          </p-card>
          <p-card styleClass="stat-card">
            <div class="stat">
              <div class="label">Active</div>
              <div class="value">{{ overview()?.tenderCounts?.active ?? 0 }}</div>
            </div>
          </p-card>
          <p-card styleClass="stat-card">
            <div class="stat">
              <div class="label">Evaluation</div>
              <div class="value">{{ overview()?.tenderCounts?.evaluation ?? 0 }}</div>
            </div>
          </p-card>
          <p-card styleClass="stat-card">
            <div class="stat">
              <div class="label">Awarded</div>
              <div class="value">{{ overview()?.tenderCounts?.awarded ?? 0 }}</div>
            </div>
          </p-card>
          <p-card styleClass="stat-card">
            <div class="stat">
              <div class="label">Pending Approvals</div>
              <div class="value">{{ overview()?.pendingApprovals ?? 0 }}</div>
            </div>
          </p-card>
          <p-card styleClass="stat-card">
            <div class="stat">
              <div class="label">Total Contract Value</div>
              <div class="value">
                {{ overview()?.totalContractValue ?? 0 | number:'1.0-0' }} {{ overview()?.currency || 'SAR' }}
              </div>
            </div>
          </p-card>
        }
      </div>

      <div class="charts-grid">
        <p-card header="Activity Trend" styleClass="chart-card">
          @if (dashboardService.isLoading() && !overview()) {
            <p-skeleton width="100%" height="260px"></p-skeleton>
          } @else {
            <div class="chart-wrap">
              <p-chart type="line" [data]="activityTrendData" [options]="activityTrendOptions"></p-chart>
            </div>
          }
        </p-card>

        <p-card header="Award Value Trend" styleClass="chart-card">
          @if (dashboardService.isLoading() && !overview()) {
            <p-skeleton width="100%" height="260px"></p-skeleton>
          } @else {
            <div class="chart-wrap">
              <p-chart type="bar" [data]="valueTrendData" [options]="valueTrendOptions"></p-chart>
            </div>
          }
        </p-card>
      </div>
    </div>
  `,
  styles: [`
    .overview-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .overview-header h1 {
      margin: 0;
      font-size: 1.75rem;
      font-weight: 600;
      color: var(--bayan-slate-900);
    }

    .overview-header p {
      margin: 0.25rem 0 0;
      color: var(--bayan-slate-500);
    }

    .cards-grid {
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 1rem;
    }

    @media (max-width: 1280px) {
      .cards-grid {
        grid-template-columns: repeat(3, 1fr);
      }
    }

    @media (max-width: 640px) {
      .cards-grid {
        grid-template-columns: 1fr;
      }
    }

    :host ::ng-deep .stat-card {
      .p-card {
        background: var(--bayan-card);
        box-shadow: var(--bayan-shadow-sm);
        border-radius: var(--bayan-radius-lg);
        border: 1px solid var(--bayan-border);
        border-left: 4px solid var(--bayan-primary);
      }
      .p-card-body {
        padding: 1.25rem;
      }
    }

    .stat {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .label {
      font-size: 0.8rem;
      color: var(--bayan-slate-500);
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .value {
      font-size: 1.5rem;
      font-weight: 600;
      color: var(--bayan-slate-900);
    }

    .charts-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }

    @media (max-width: 1024px) {
      .charts-grid {
        grid-template-columns: 1fr;
      }
    }

    :host ::ng-deep .chart-card {
      .p-card {
        background: var(--bayan-card);
        box-shadow: var(--bayan-shadow-sm);
        border-radius: var(--bayan-radius-lg);
        border: 1px solid var(--bayan-border);
      }
      .p-card-body {
        padding: 1.5rem;
        padding-top: 0;
      }
      .p-card-title {
        color: var(--bayan-slate-900);
        font-weight: 600;
        font-size: 1rem;
      }
    }

    .chart-wrap {
      height: 280px;
    }
  `]
})
export class OverviewDashboardComponent implements OnInit {
  readonly dashboardService = inject(DashboardService);
  private readonly authService = inject(AuthService);

  currentUser = this.authService.currentUser;
  overview = signal<OverviewDashboard | null>(null);

  activityTrendData: any;
  activityTrendOptions: any;
  valueTrendData: any;
  valueTrendOptions: any;

  ngOnInit(): void {
    this.load();
    this.initChartOptions();
  }

  private load(): void {
    this.dashboardService.getOverviewDashboard({ monthsBack: 6 }).subscribe({
      next: (data) => {
        this.overview.set(data);
        this.buildCharts(data);
      },
      error: (err) => console.error('Failed to load overview dashboard:', err)
    });
  }

  private initChartOptions(): void {
    this.activityTrendOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#475569',
            font: { size: 12 }
          }
        },
      },
      scales: {
        x: {
          ticks: { color: '#64748B', font: { size: 11 } },
          grid: { color: '#E2E8F0' }
        },
        y: {
          beginAtZero: true,
          ticks: { color: '#64748B', font: { size: 11 } },
          grid: { color: '#E2E8F0' }
        }
      }
    };

    this.valueTrendOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          ticks: { color: '#64748B', font: { size: 11 } },
          grid: { color: '#E2E8F0' }
        },
        y: {
          beginAtZero: true,
          ticks: { color: '#64748B', font: { size: 11 } },
          grid: { color: '#E2E8F0' }
        }
      }
    };
  }

  private buildCharts(data: OverviewDashboard): void {
    const labels = (data.monthlyTrend || []).map(x => x.month);
    const tendersCreated = (data.monthlyTrend || []).map(x => x.tendersCreated);
    const bidsReceived = (data.monthlyTrend || []).map(x => x.bidsReceived);
    const contractValues = (data.monthlyTrend || []).map(x => x.contractValue);

    this.activityTrendData = {
      labels,
      datasets: [
        {
          label: 'Tenders Created',
          data: tendersCreated,
          borderColor: '#4F46E5',
          backgroundColor: 'rgba(79, 70, 229, 0.12)',
          tension: 0.3,
          fill: true
        },
        {
          label: 'Bids Received',
          data: bidsReceived,
          borderColor: '#22C55E',
          backgroundColor: 'rgba(34, 197, 94, 0.10)',
          tension: 0.3,
          fill: true
        }
      ]
    };

    this.valueTrendData = {
      labels,
      datasets: [
        {
          label: 'Contract Value',
          data: contractValues,
          backgroundColor: '#4F46E5',
          borderRadius: 6
        }
      ]
    };
  }
}
