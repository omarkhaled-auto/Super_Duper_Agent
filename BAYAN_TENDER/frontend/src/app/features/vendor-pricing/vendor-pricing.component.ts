import { Component, OnInit, inject, signal, computed, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { MultiSelectModule } from 'primeng/multiselect';
import { DatePickerModule } from 'primeng/datepicker';
import { ChartModule } from 'primeng/chart';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { TabViewModule } from 'primeng/tabview';
import { ToastModule } from 'primeng/toast';
import { DialogModule } from 'primeng/dialog';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { MessageService } from 'primeng/api';
import { VendorPricingService } from '../../core/services/vendor-pricing.service';
import {
  VendorPricingDashboard,
  VendorTrends,
  VendorListItem,
  VendorItemRate,
  TopVendor
} from '../../core/models/vendor-pricing.model';
import { PaginatedResponse } from '../../core/models';

interface TradeOption {
  label: string;
  value: string;
}

@Component({
  selector: 'app-vendor-pricing',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    CardModule,
    ButtonModule,
    InputTextModule,
    DropdownModule,
    MultiSelectModule,
    DatePickerModule,
    ChartModule,
    TagModule,
    TooltipModule,
    ProgressSpinnerModule,
    TabViewModule,
    ToastModule,
    DialogModule,
    IconFieldModule,
    InputIconModule
  ],
  providers: [MessageService],
  template: `
    <p-toast></p-toast>
    <div class="vendor-pricing-container">
      <div class="page-header">
        <div>
          <h1>Vendor Pricing Dashboard</h1>
          <p>Analyze vendor rates, trends, and compare pricing across tenders</p>
        </div>
        <div class="header-actions">
          <button
            pButton
            icon="pi pi-download"
            label="Export to Excel"
            class="p-button-outlined"
            (click)="exportToExcel()"
            [disabled]="isLoading()"
          ></button>
          <button
            pButton
            icon="pi pi-refresh"
            label="Refresh"
            (click)="loadDashboard()"
            [disabled]="isLoading()"
          ></button>
        </div>
      </div>

      <!-- Filters -->
      <p-card styleClass="filter-card">
        <div class="filters">
          <p-dropdown
            [options]="tradeOptions"
            [(ngModel)]="selectedTrade"
            placeholder="Filter by Trade"
            [showClear]="true"
            (onChange)="onFilterChange()"
          ></p-dropdown>

          <p-datepicker
            [(ngModel)]="dateRange"
            selectionMode="range"
            [showIcon]="true"
            placeholder="Date Range"
            dateFormat="yy-mm-dd"
            (onSelect)="onFilterChange()"
            (onClear)="onFilterChange()"
          ></p-datepicker>

          <button
            pButton
            icon="pi pi-filter-slash"
            label="Clear Filters"
            class="p-button-outlined p-button-secondary"
            (click)="clearFilters()"
          ></button>
        </div>
      </p-card>

      @if (isLoading()) {
        <div class="loading-container">
          <p-progressSpinner></p-progressSpinner>
          <p>Loading dashboard data...</p>
        </div>
      } @else if (dashboard()) {
        <!-- Summary Cards -->
        <div class="summary-cards">
          <p-card styleClass="summary-card">
            <div class="summary-content">
              <i class="pi pi-building summary-icon"></i>
              <div class="summary-text">
                <span class="summary-value">{{ dashboard()!.summary.totalVendors }}</span>
                <span class="summary-label">Total Vendors</span>
              </div>
            </div>
          </p-card>

          <p-card styleClass="summary-card">
            <div class="summary-content">
              <i class="pi pi-camera summary-icon"></i>
              <div class="summary-text">
                <span class="summary-value">{{ dashboard()!.summary.totalSnapshots }}</span>
                <span class="summary-label">Total Snapshots</span>
              </div>
            </div>
          </p-card>

          <p-card styleClass="summary-card">
            <div class="summary-content">
              <i class="pi pi-list summary-icon"></i>
              <div class="summary-text">
                <span class="summary-value">{{ dashboard()!.summary.totalUniqueItems }}</span>
                <span class="summary-label">Unique Items</span>
              </div>
            </div>
          </p-card>

          <p-card styleClass="summary-card">
            <div class="summary-content">
              <i class="pi pi-dollar summary-icon"></i>
              <div class="summary-text">
                <span class="summary-value">{{ formatCurrency(dashboard()!.summary.totalBidValue) }}</span>
                <span class="summary-label">Total Bid Value</span>
              </div>
            </div>
          </p-card>
        </div>

        <p-tabView>
          <!-- Overview Tab -->
          <p-tabPanel header="Overview">
            <div class="dashboard-grid">
              <!-- Rate Trends Chart -->
              <p-card header="Rate Trends Over Time" styleClass="chart-card">
                @if (rateTrendChartData()) {
                  <p-chart type="line" [data]="rateTrendChartData()" [options]="lineChartOptions"></p-chart>
                } @else {
                  <div class="no-data">No trend data available</div>
                }
              </p-card>

              <!-- Trade Breakdown Chart -->
              <p-card header="Value by Trade" styleClass="chart-card">
                @if (tradeBreakdownChartData()) {
                  <p-chart type="doughnut" [data]="tradeBreakdownChartData()" [options]="doughnutChartOptions"></p-chart>
                } @else {
                  <div class="no-data">No trade data available</div>
                }
              </p-card>

              <!-- Top Vendors Table -->
              <p-card header="Top Vendors by Value" styleClass="table-card full-width">
                <p-table [value]="dashboard()!.topVendors" [rows]="5" styleClass="p-datatable-sm">
                  <ng-template pTemplate="header">
                    <tr>
                      <th>Vendor</th>
                      <th>Trade</th>
                      <th>Snapshots</th>
                      <th>Total Value</th>
                      <th>Trend</th>
                      <th>Actions</th>
                    </tr>
                  </ng-template>
                  <ng-template pTemplate="body" let-vendor>
                    <tr>
                      <td>
                        <div class="vendor-name">{{ vendor.bidderName }}</div>
                      </td>
                      <td>
                        <p-tag [value]="vendor.tradeSpecialization || 'Unspecified'" severity="info"></p-tag>
                      </td>
                      <td>{{ vendor.snapshotCount }}</td>
                      <td>{{ formatCurrency(vendor.totalBidValue) }}</td>
                      <td>
                        <div class="trend-cell">
                          <i
                            [class]="getTrendIcon(vendor.trendDirection)"
                            [style.color]="getTrendColor(vendor.trendDirection)"
                          ></i>
                          <span [style.color]="getTrendColor(vendor.trendDirection)">
                            {{ vendor.averageRateTrend | number:'1.1-1' }}%
                          </span>
                        </div>
                      </td>
                      <td>
                        <button
                          pButton
                          icon="pi pi-chart-line"
                          class="p-button-text p-button-sm"
                          pTooltip="View Trends"
                          (click)="viewVendorTrends(vendor)"
                        ></button>
                        <button
                          pButton
                          icon="pi pi-list"
                          class="p-button-text p-button-sm"
                          pTooltip="View Rates"
                          (click)="viewVendorRates(vendor)"
                        ></button>
                      </td>
                    </tr>
                  </ng-template>
                  <ng-template pTemplate="emptymessage">
                    <tr>
                      <td colspan="6" class="text-center">No vendors found</td>
                    </tr>
                  </ng-template>
                </p-table>
              </p-card>

              <!-- Recent Snapshots -->
              <p-card header="Recent Pricing Snapshots" styleClass="table-card full-width">
                <p-table [value]="dashboard()!.recentSnapshots" [rows]="5" styleClass="p-datatable-sm">
                  <ng-template pTemplate="header">
                    <tr>
                      <th>Date</th>
                      <th>Vendor</th>
                      <th>Tender</th>
                      <th>Items</th>
                      <th>Amount</th>
                    </tr>
                  </ng-template>
                  <ng-template pTemplate="body" let-snapshot>
                    <tr>
                      <td>{{ snapshot.snapshotDate | date:'mediumDate' }}</td>
                      <td>{{ snapshot.bidderName }}</td>
                      <td>
                        <div>
                          <span class="tender-ref">{{ snapshot.tenderReference }}</span>
                          <span class="tender-title">{{ snapshot.tenderTitle }}</span>
                        </div>
                      </td>
                      <td>{{ snapshot.itemCount }}</td>
                      <td>{{ formatCurrency(snapshot.totalBidAmount, snapshot.currency) }}</td>
                    </tr>
                  </ng-template>
                  <ng-template pTemplate="emptymessage">
                    <tr>
                      <td colspan="5" class="text-center">No recent snapshots</td>
                    </tr>
                  </ng-template>
                </p-table>
              </p-card>
            </div>
          </p-tabPanel>

          <!-- Vendor Search Tab -->
          <p-tabPanel header="Vendor Search">
            <div class="vendor-search-section">
              <p-card>
                <div class="search-controls">
                  <p-iconField iconPosition="left" class="search-field">
                    <p-inputIcon styleClass="pi pi-search"></p-inputIcon>
                    <input
                      pInputText
                      type="text"
                      [(ngModel)]="vendorSearchTerm"
                      placeholder="Search vendors by name..."
                      (input)="onVendorSearch()"
                    />
                  </p-iconField>

                  <p-dropdown
                    [options]="tradeOptions"
                    [(ngModel)]="vendorTradeFilter"
                    placeholder="Filter by Trade"
                    [showClear]="true"
                    (onChange)="onVendorSearch()"
                  ></p-dropdown>
                </div>

                <p-table
                  [value]="vendors()"
                  [paginator]="true"
                  [rows]="10"
                  [loading]="vendorsLoading()"
                  [showCurrentPageReport]="true"
                  currentPageReportTemplate="Showing {first} to {last} of {totalRecords} vendors"
                  styleClass="p-datatable-striped"
                >
                  <ng-template pTemplate="header">
                    <tr>
                      <th pSortableColumn="companyName">Company Name <p-sortIcon field="companyName"></p-sortIcon></th>
                      <th>Trade</th>
                      <th pSortableColumn="snapshotCount">Snapshots <p-sortIcon field="snapshotCount"></p-sortIcon></th>
                      <th pSortableColumn="totalBidValue">Total Value <p-sortIcon field="totalBidValue"></p-sortIcon></th>
                      <th>Last Activity</th>
                      <th>Actions</th>
                    </tr>
                  </ng-template>
                  <ng-template pTemplate="body" let-vendor>
                    <tr>
                      <td>
                        <div class="vendor-info">
                          <span class="company-name">{{ vendor.companyName }}</span>
                          <span class="email">{{ vendor.email }}</span>
                        </div>
                      </td>
                      <td>
                        <p-tag [value]="vendor.tradeSpecialization || 'Unspecified'" severity="info"></p-tag>
                      </td>
                      <td>{{ vendor.snapshotCount }}</td>
                      <td>{{ formatCurrency(vendor.totalBidValue) }}</td>
                      <td>{{ vendor.latestSnapshotDate | date:'mediumDate' }}</td>
                      <td>
                        <button
                          pButton
                          icon="pi pi-chart-line"
                          class="p-button-text p-button-sm"
                          pTooltip="View Trends"
                          (click)="viewVendorTrendsById(vendor.bidderId)"
                        ></button>
                        <button
                          pButton
                          icon="pi pi-list"
                          class="p-button-text p-button-sm"
                          pTooltip="View Rates"
                          (click)="viewVendorRatesById(vendor.bidderId)"
                        ></button>
                        <button
                          pButton
                          icon="pi pi-plus"
                          class="p-button-text p-button-sm"
                          pTooltip="Add to Comparison"
                          (click)="addToComparison(vendor)"
                        ></button>
                      </td>
                    </tr>
                  </ng-template>
                  <ng-template pTemplate="emptymessage">
                    <tr>
                      <td colspan="6" class="text-center">No vendors found</td>
                    </tr>
                  </ng-template>
                </p-table>
              </p-card>
            </div>
          </p-tabPanel>

          <!-- Comparison Tab -->
          <p-tabPanel header="Vendor Comparison">
            <p-card>
              <div class="comparison-header">
                <h3>Selected Vendors for Comparison</h3>
                <div class="selected-vendors">
                  @for (vendor of selectedVendorsForComparison(); track vendor.bidderId) {
                    <p-tag [value]="vendor.companyName">
                      <ng-template pTemplate="content">
                        {{ vendor.companyName }}
                        <i class="pi pi-times ml-2 cursor-pointer" (click)="removeFromComparison(vendor)"></i>
                      </ng-template>
                    </p-tag>
                  }
                  @if (selectedVendorsForComparison().length === 0) {
                    <span class="no-selection">Select 2-5 vendors from the Vendor Search tab</span>
                  }
                </div>
                <button
                  pButton
                  label="Compare"
                  icon="pi pi-chart-bar"
                  [disabled]="selectedVendorsForComparison().length < 2 || selectedVendorsForComparison().length > 5"
                  (click)="runComparison()"
                ></button>
              </div>

              @if (comparisonResult()) {
                <div class="comparison-results">
                  <p-table [value]="comparisonResult()!.items" styleClass="p-datatable-sm">
                    <ng-template pTemplate="header">
                      <tr>
                        <th>Item Description</th>
                        <th>UOM</th>
                        @for (vendor of comparisonResult()!.vendors; track vendor.bidderId) {
                          <th>{{ vendor.bidderName }}</th>
                        }
                      </tr>
                    </ng-template>
                    <ng-template pTemplate="body" let-item>
                      <tr>
                        <td>{{ item.itemDescription }}</td>
                        <td>{{ item.uom }}</td>
                        @for (rate of item.rates; track rate.bidderId) {
                          <td [class.lowest-rate]="rate.isLowest">
                            <div class="rate-cell">
                              <span class="rate-value">{{ formatCurrency(rate.rate, rate.currency) }}</span>
                              @if (!rate.isLowest && rate.percentageAboveLowest > 0) {
                                <span class="rate-diff">+{{ rate.percentageAboveLowest | number:'1.1-1' }}%</span>
                              }
                            </div>
                          </td>
                        }
                      </tr>
                    </ng-template>
                  </p-table>
                </div>
              }
            </p-card>
          </p-tabPanel>
        </p-tabView>
      }

      <!-- Vendor Trends Dialog -->
      <p-dialog
        [(visible)]="showTrendsDialog"
        [header]="selectedVendorForTrends()?.bidderName + ' - Rate Trends'"
        [modal]="true"
        [style]="{ width: '90vw', maxWidth: '1200px' }"
        [dismissableMask]="true"
      >
        @if (vendorTrends()) {
          <div class="trends-dialog-content">
            <!-- Summary -->
            <div class="trends-summary">
              <div class="summary-item">
                <span class="label">Total Tenders:</span>
                <span class="value">{{ vendorTrends()!.summary.totalTenders }}</span>
              </div>
              <div class="summary-item">
                <span class="label">Total Items:</span>
                <span class="value">{{ vendorTrends()!.summary.totalItems }}</span>
              </div>
              <div class="summary-item">
                <span class="label">Avg Rate:</span>
                <span class="value">{{ formatCurrency(vendorTrends()!.summary.overallAverageRate) }}</span>
              </div>
              <div class="summary-item">
                <span class="label">Trend:</span>
                <span class="value" [style.color]="getTrendColor(vendorTrends()!.summary.overallTrendDirection)">
                  <i [class]="getTrendIcon(vendorTrends()!.summary.overallTrendDirection)"></i>
                  {{ vendorTrends()!.summary.overallPercentageChange | number:'1.1-1' }}%
                </span>
              </div>
            </div>

            <!-- Trend Chart -->
            @if (vendorTrendChartData()) {
              <div class="trends-chart">
                <p-chart type="line" [data]="vendorTrendChartData()" [options]="vendorTrendChartOptions"></p-chart>
              </div>
            }

            <!-- Item Trends Table -->
            <h4>Item Rate Trends</h4>
            <p-table [value]="vendorTrends()!.itemTrends" [rows]="10" [paginator]="true" styleClass="p-datatable-sm">
              <ng-template pTemplate="header">
                <tr>
                  <th>Item Description</th>
                  <th>UOM</th>
                  <th>Data Points</th>
                  <th>Avg Rate</th>
                  <th>Min</th>
                  <th>Max</th>
                  <th>Latest</th>
                  <th>Trend</th>
                </tr>
              </ng-template>
              <ng-template pTemplate="body" let-item>
                <tr>
                  <td>{{ item.itemDescription }}</td>
                  <td>{{ item.uom }}</td>
                  <td>{{ item.dataPointCount }}</td>
                  <td>{{ item.averageRate | number:'1.2-2' }}</td>
                  <td>{{ item.minRate | number:'1.2-2' }}</td>
                  <td>{{ item.maxRate | number:'1.2-2' }}</td>
                  <td>{{ item.latestRate | number:'1.2-2' }}</td>
                  <td>
                    <div class="trend-cell">
                      <i
                        [class]="getTrendIcon(item.trendDirection)"
                        [style.color]="getTrendColor(item.trendDirection)"
                      ></i>
                      <span [style.color]="getTrendColor(item.trendDirection)">
                        {{ item.percentageChange | number:'1.1-1' }}%
                      </span>
                    </div>
                  </td>
                </tr>
              </ng-template>
            </p-table>
          </div>
        }
      </p-dialog>

      <!-- Vendor Rates Dialog -->
      <p-dialog
        [(visible)]="showRatesDialog"
        [header]="selectedVendorForRates()?.bidderName + ' - Rate History'"
        [modal]="true"
        [style]="{ width: '90vw', maxWidth: '1000px' }"
        [dismissableMask]="true"
      >
        <p-table
          [value]="vendorRates()"
          [paginator]="true"
          [rows]="20"
          [loading]="ratesLoading()"
          styleClass="p-datatable-sm p-datatable-striped"
        >
          <ng-template pTemplate="header">
            <tr>
              <th>Tender</th>
              <th>Date</th>
              <th>Item Description</th>
              <th>UOM</th>
              <th>Rate</th>
              <th>Currency</th>
            </tr>
          </ng-template>
          <ng-template pTemplate="body" let-rate>
            <tr>
              <td>{{ rate.tenderReference }}</td>
              <td>{{ rate.snapshotDate | date:'mediumDate' }}</td>
              <td>{{ rate.itemDescription }}</td>
              <td>{{ rate.uom }}</td>
              <td>{{ rate.rate | number:'1.2-2' }}</td>
              <td>{{ rate.currency }}</td>
            </tr>
          </ng-template>
          <ng-template pTemplate="emptymessage">
            <tr>
              <td colspan="6" class="text-center">No rates found</td>
            </tr>
          </ng-template>
        </p-table>
      </p-dialog>
    </div>
  `,
  styles: [`
    .vendor-pricing-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .page-header h1 {
      margin: 0;
      font-size: 1.75rem;
      color: var(--bayan-slate-900, #0F172A);
    }

    .page-header p {
      margin: 0.25rem 0 0;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .header-actions {
      display: flex;
      gap: 0.5rem;
    }

    :host ::ng-deep .filter-card .p-card-body {
      padding: 1rem;
    }

    .filters {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      align-items: center;
    }

    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem;
      gap: 1rem;
    }

    .summary-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
    }

    :host ::ng-deep .summary-card .p-card-body {
      padding: 1rem;
    }

    .summary-content {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .summary-icon {
      font-size: 2rem;
      color: var(--bayan-primary, #4F46E5);
    }

    .summary-text {
      display: flex;
      flex-direction: column;
    }

    .summary-value {
      font-size: 1.5rem;
      font-weight: 600;
      color: var(--bayan-slate-900, #0F172A);
    }

    .summary-label {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .dashboard-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 1.5rem;
    }

    .full-width {
      grid-column: 1 / -1;
    }

    :host ::ng-deep .chart-card .p-card-content {
      min-height: 300px;
    }

    .no-data {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 200px;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .trend-cell {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .vendor-name {
      font-weight: 500;
    }

    .tender-ref {
      font-weight: 500;
      display: block;
    }

    .tender-title {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #64748B);
      display: block;
    }

    .search-controls {
      display: flex;
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .search-field {
      flex: 1;
      min-width: 300px;
    }

    .search-field input {
      width: 100%;
    }

    .vendor-info {
      display: flex;
      flex-direction: column;
    }

    .company-name {
      font-weight: 500;
    }

    .email {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .comparison-header {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1.5rem;
    }

    .comparison-header h3 {
      margin: 0;
      margin-right: auto;
    }

    .selected-vendors {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      flex: 1;
    }

    .no-selection {
      color: var(--bayan-muted-foreground, #64748B);
      font-style: italic;
    }

    .rate-cell {
      display: flex;
      flex-direction: column;
    }

    .rate-value {
      font-weight: 500;
    }

    .rate-diff {
      font-size: 0.75rem;
      color: var(--bayan-danger, #DC2626);
    }

    .lowest-rate {
      background-color: var(--bayan-success-bg, #f0fdf4) !important;
    }

    .lowest-rate .rate-value {
      color: var(--bayan-success, #16A34A);
    }

    .trends-dialog-content {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .trends-summary {
      display: flex;
      flex-wrap: wrap;
      gap: 2rem;
      padding: 1rem;
      background: var(--bayan-accent, #EEF2FF);
      border-radius: var(--bayan-radius-lg, 0.75rem);
    }

    .summary-item {
      display: flex;
      flex-direction: column;
    }

    .summary-item .label {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .summary-item .value {
      font-size: 1.25rem;
      font-weight: 600;
    }

    .trends-chart {
      min-height: 300px;
    }

    @media (max-width: 768px) {
      .dashboard-grid {
        grid-template-columns: 1fr;
      }

      .search-controls {
        flex-direction: column;
      }

      .search-field {
        width: 100%;
        min-width: unset;
      }
    }
  `]
})
export class VendorPricingComponent implements OnInit {
  private readonly vendorPricingService = inject(VendorPricingService);
  private readonly messageService = inject(MessageService);

  // Loading states
  isLoading = this.vendorPricingService.isLoading;
  vendorsLoading = signal(false);
  ratesLoading = signal(false);

  // Data
  dashboard = this.vendorPricingService.dashboard;
  vendors = signal<VendorListItem[]>([]);
  vendorTrends = signal<VendorTrends | null>(null);
  vendorRates = signal<VendorItemRate[]>([]);
  comparisonResult = signal<any>(null);

  // Filters
  selectedTrade: string | null = null;
  dateRange: Date[] | null = null;
  vendorSearchTerm = '';
  vendorTradeFilter: string | null = null;

  // Dialog states
  showTrendsDialog = false;
  showRatesDialog = false;
  selectedVendorForTrends = signal<TopVendor | null>(null);
  selectedVendorForRates = signal<TopVendor | null>(null);

  // Comparison
  selectedVendorsForComparison = signal<VendorListItem[]>([]);

  // Trade options
  tradeOptions: TradeOption[] = [
    { label: 'IT Services', value: 'IT_SERVICES' },
    { label: 'Construction', value: 'CONSTRUCTION' },
    { label: 'Consulting', value: 'CONSULTING' },
    { label: 'Supplies', value: 'SUPPLIES' },
    { label: 'Maintenance', value: 'MAINTENANCE' },
    { label: 'Security', value: 'SECURITY' },
    { label: 'Logistics', value: 'LOGISTICS' },
    { label: 'Healthcare', value: 'HEALTHCARE' },
    { label: 'Education', value: 'EDUCATION' },
    { label: 'Financial', value: 'FINANCIAL' },
    { label: 'Engineering', value: 'ENGINEERING' },
    { label: 'Telecommunications', value: 'TELECOMMUNICATIONS' },
    { label: 'Other', value: 'OTHER' }
  ];

  // Chart options
  lineChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' as const }
    },
    scales: {
      y: { beginAtZero: true }
    }
  };

  doughnutChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'right' as const }
    }
  };

  vendorTrendChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' as const }
    },
    scales: {
      y: { beginAtZero: true }
    }
  };

  // Computed chart data
  rateTrendChartData = computed(() => {
    const dash = this.dashboard();
    if (!dash?.rateTrends?.length) return null;

    return {
      labels: dash.rateTrends.map(t => new Date(t.date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })),
      datasets: [{
        label: 'Average Rate',
        data: dash.rateTrends.map(t => t.averageRate),
        fill: false,
        borderColor: '#4F46E5',
        tension: 0.4
      }]
    };
  });

  tradeBreakdownChartData = computed(() => {
    const dash = this.dashboard();
    if (!dash?.tradeBreakdown?.length) return null;

    const colors = ['#4F46E5', '#6366F1', '#818CF8', '#A5B4FC', '#C7D2FE', '#E0E7FF', '#334155', '#64748B'];

    return {
      labels: dash.tradeBreakdown.map(t => t.trade),
      datasets: [{
        data: dash.tradeBreakdown.map(t => t.totalValue),
        backgroundColor: colors.slice(0, dash.tradeBreakdown.length)
      }]
    };
  });

  vendorTrendChartData = computed(() => {
    const trends = this.vendorTrends();
    if (!trends?.trendPoints?.length) return null;

    return {
      labels: trends.trendPoints.map(t => new Date(t.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' })),
      datasets: [
        {
          label: 'Average Rate',
          data: trends.trendPoints.map(t => t.averageRate),
          fill: false,
          borderColor: '#4F46E5',
          tension: 0.4
        },
        {
          label: 'Min Rate',
          data: trends.trendPoints.map(t => t.minRate),
          fill: false,
          borderColor: '#388E3C',
          borderDash: [5, 5],
          tension: 0.4
        },
        {
          label: 'Max Rate',
          data: trends.trendPoints.map(t => t.maxRate),
          fill: false,
          borderColor: '#F57C00',
          borderDash: [5, 5],
          tension: 0.4
        }
      ]
    };
  });

  ngOnInit(): void {
    this.loadDashboard();
    this.loadVendors();
  }

  loadDashboard(): void {
    const params: any = {};
    if (this.selectedTrade) params.tradeSpecialization = this.selectedTrade;
    if (this.dateRange?.[0]) params.fromDate = this.dateRange[0];
    if (this.dateRange?.[1]) params.toDate = this.dateRange[1];

    this.vendorPricingService.getDashboard(params).subscribe({
      error: (err) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load dashboard data'
        });
      }
    });
  }

  loadVendors(): void {
    this.vendorsLoading.set(true);
    this.vendorPricingService.getVendors({
      search: this.vendorSearchTerm || undefined,
      tradeSpecialization: this.vendorTradeFilter || undefined,
      onlyWithPricingData: true
    }).subscribe({
      next: (response) => {
        this.vendors.set(response.items);
        this.vendorsLoading.set(false);
      },
      error: () => {
        this.vendorsLoading.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load vendors'
        });
      }
    });
  }

  onFilterChange(): void {
    this.loadDashboard();
  }

  clearFilters(): void {
    this.selectedTrade = null;
    this.dateRange = null;
    this.loadDashboard();
  }

  onVendorSearch(): void {
    this.loadVendors();
  }

  viewVendorTrends(vendor: TopVendor): void {
    this.selectedVendorForTrends.set(vendor);
    this.showTrendsDialog = true;
    this.loadVendorTrends(vendor.bidderId);
  }

  viewVendorTrendsById(bidderId: string): void {
    const vendor = this.vendors().find(v => v.bidderId === bidderId);
    if (vendor) {
      this.selectedVendorForTrends.set({
        bidderId: vendor.bidderId,
        bidderName: vendor.companyName,
        tradeSpecialization: vendor.tradeSpecialization,
        snapshotCount: vendor.snapshotCount,
        totalBidValue: vendor.totalBidValue,
        averageRateTrend: 0,
        trendDirection: 'stable'
      });
    }
    this.showTrendsDialog = true;
    this.loadVendorTrends(bidderId);
  }

  loadVendorTrends(bidderId: string): void {
    this.vendorPricingService.getVendorTrends(bidderId).subscribe({
      next: (trends) => this.vendorTrends.set(trends),
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load vendor trends'
        });
      }
    });
  }

  viewVendorRates(vendor: TopVendor): void {
    this.selectedVendorForRates.set(vendor);
    this.showRatesDialog = true;
    this.loadVendorRates(vendor.bidderId);
  }

  viewVendorRatesById(bidderId: string): void {
    const vendor = this.vendors().find(v => v.bidderId === bidderId);
    if (vendor) {
      this.selectedVendorForRates.set({
        bidderId: vendor.bidderId,
        bidderName: vendor.companyName,
        tradeSpecialization: vendor.tradeSpecialization,
        snapshotCount: vendor.snapshotCount,
        totalBidValue: vendor.totalBidValue,
        averageRateTrend: 0,
        trendDirection: 'stable'
      });
    }
    this.showRatesDialog = true;
    this.loadVendorRates(bidderId);
  }

  loadVendorRates(bidderId: string): void {
    this.ratesLoading.set(true);
    this.vendorPricingService.getVendorRates(bidderId, { latestOnly: false, pageSize: 100 }).subscribe({
      next: (response) => {
        this.vendorRates.set(response.items);
        this.ratesLoading.set(false);
      },
      error: () => {
        this.ratesLoading.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load vendor rates'
        });
      }
    });
  }

  addToComparison(vendor: VendorListItem): void {
    const current = this.selectedVendorsForComparison();
    if (current.length >= 5) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Limit Reached',
        detail: 'Maximum 5 vendors can be compared at once'
      });
      return;
    }
    if (current.some(v => v.bidderId === vendor.bidderId)) {
      this.messageService.add({
        severity: 'info',
        summary: 'Already Added',
        detail: 'This vendor is already in the comparison list'
      });
      return;
    }
    this.selectedVendorsForComparison.update(vendors => [...vendors, vendor]);
    this.messageService.add({
      severity: 'success',
      summary: 'Added',
      detail: `${vendor.companyName} added to comparison`
    });
  }

  removeFromComparison(vendor: VendorListItem): void {
    this.selectedVendorsForComparison.update(vendors =>
      vendors.filter(v => v.bidderId !== vendor.bidderId)
    );
  }

  runComparison(): void {
    const bidderIds = this.selectedVendorsForComparison().map(v => v.bidderId);
    this.vendorPricingService.compareVendors({ bidderIds }).subscribe({
      next: (result) => this.comparisonResult.set(result),
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to compare vendors'
        });
      }
    });
  }

  exportToExcel(): void {
    this.vendorPricingService.downloadExport({
      fromDate: this.dateRange?.[0],
      toDate: this.dateRange?.[1],
      tradeSpecialization: this.selectedTrade || undefined
    });
    this.messageService.add({
      severity: 'info',
      summary: 'Exporting',
      detail: 'Preparing Excel export...'
    });
  }

  formatCurrency(value: number | undefined | null, currency: string = 'AED'): string {
    if (value == null || isNaN(value)) {
      return `${currency} 0`;
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  }

  getTrendIcon(direction: string): string {
    switch (direction) {
      case 'up': return 'pi pi-arrow-up';
      case 'down': return 'pi pi-arrow-down';
      default: return 'pi pi-minus';
    }
  }

  getTrendColor(direction: string): string {
    switch (direction) {
      case 'up': return '#DC2626';
      case 'down': return '#16A34A';
      default: return '#64748B';
    }
  }
}
