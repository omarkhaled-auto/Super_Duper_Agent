import {
  Component,
  Input,
  OnInit,
  OnDestroy,
  inject,
  signal,
  computed,
  ViewChild,
  ElementRef
} from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';

// AG Grid type stubs (ag-grid not installed)
type ColDef = any;
type GridApi = any;
type GridReadyEvent = any;
type CellClassParams = any;
type ValueFormatterParams = any;
type ITooltipParams = any;
type RowClassParams = any;
type GetRowIdParams = any;

// PrimeNG
import { ButtonModule } from 'primeng/button';
import { DropdownModule } from 'primeng/dropdown';
import { InputTextModule } from 'primeng/inputtext';
import { TooltipModule } from 'primeng/tooltip';
import { DialogModule } from 'primeng/dialog';
import { ToastModule } from 'primeng/toast';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';
import { DividerModule } from 'primeng/divider';
import { SelectButtonModule } from 'primeng/selectbutton';
import { CheckboxModule } from 'primeng/checkbox';
import { InputNumberModule } from 'primeng/inputnumber';
import { MessageService } from 'primeng/api';

// Services and Models
import { ComparableSheetService } from '../../../../core/services/comparable-sheet.service';
import {
  ComparableSheet,
  ComparableSheetRow,
  BidderColumn,
  BidderCellData,
  SectionSummary,
  ComparableSheetStats,
  ComparableSheetFilters,
  ComparableSheetExportOptions,
  ComparableSheetSettings,
  OutlierSeverity,
  OUTLIER_CONFIG,
  DEFAULT_COMPARABLE_SHEET_SETTINGS,
  RowType
} from '../../../../core/models/comparable-sheet.model';

/**
 * Filter option for outlier display
 */
interface OutlierFilterOption {
  label: string;
  value: 'all' | 'outliers_only' | 'hide_outliers';
}

/**
 * Section filter option
 */
interface SectionOption {
  label: string;
  value: number | null;
}

/**
 * Grid row data structure for AG Grid
 */
interface GridRowData {
  rowId: string;
  rowType: RowType;
  itemNumber: string;
  description: string;
  quantity: number | null;
  uom: string;
  sectionId?: number;
  sectionNumber?: string;
  sectionTitle?: string;
  averageRate: number | null;
  hasOutliers?: boolean;
  isExpanded?: boolean;
  [key: string]: any; // Dynamic bidder columns
}

@Component({
  selector: 'app-comparable-sheet',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    DropdownModule,
    InputTextModule,
    TooltipModule,
    DialogModule,
    ToastModule,
    ProgressSpinnerModule,
    MessageModule,
    DividerModule,
    SelectButtonModule,
    CheckboxModule,
    InputNumberModule
  ],
  providers: [MessageService, DecimalPipe],
  template: `
    <p-toast></p-toast>

    <div class="comparable-sheet-container" data-testid="comparable-sheet">
      <!-- Toolbar -->
      <div class="toolbar">
        <div class="toolbar-left">
          <!-- Section Filter -->
          <p-dropdown
            [options]="sectionOptions()"
            [(ngModel)]="selectedSection"
            placeholder="All Sections"
            [style]="{ width: '200px' }"
            (onChange)="onFilterChange()"
          ></p-dropdown>

          <!-- Outlier Filter -->
          <p-dropdown
            [options]="outlierFilterOptions"
            [(ngModel)]="selectedOutlierFilter"
            placeholder="Outlier Filter"
            [style]="{ width: '180px' }"
            (onChange)="onFilterChange()"
          ></p-dropdown>

          <!-- Search -->
          <span class="p-input-icon-left">
            <i class="pi pi-search"></i>
            <input
              type="text"
              pInputText
              [(ngModel)]="searchTerm"
              placeholder="Search items..."
              [style]="{ width: '200px' }"
              (input)="onSearchChange()"
            />
          </span>
        </div>

        <div class="toolbar-right">
          <button
            pButton
            icon="pi pi-file-excel"
            label="Export to Excel"
            class="p-button-success"
            [loading]="isExporting()"
            (click)="exportToExcel()"
          ></button>

          <button
            pButton
            icon="pi pi-filter"
            [label]="showOutliersHighlight() ? 'Hide Outliers' : 'Show Outliers'"
            [class]="showOutliersHighlight() ? 'p-button-warning' : 'p-button-outlined'"
            (click)="toggleOutlierHighlight()"
          ></button>

          <button
            pButton
            icon="pi pi-cog"
            class="p-button-outlined p-button-secondary"
            pTooltip="Settings"
            (click)="showSettingsDialog = true"
          ></button>
        </div>
      </div>

      <!-- Statistics Bar -->
      @if (statistics()) {
        <div class="statistics-bar">
          <div class="stat-item">
            <span class="stat-label">Total Items</span>
            <span class="stat-value">{{ statistics()!.totalItems }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-label">Bidders</span>
            <span class="stat-value">{{ statistics()!.bidderCount }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-label">Outliers</span>
            <span class="stat-value outlier-high">{{ getHighOutlierCount() }}</span>
            <span class="stat-sublabel">High</span>
            <span class="stat-value outlier-medium">{{ getMediumOutlierCount() }}</span>
            <span class="stat-sublabel">Medium</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-label">Max Deviation</span>
            <span class="stat-value deviation">{{ getMaxDeviation() | number:'1.1-1' }}%</span>
          </div>
        </div>
      }

      <!-- Minimum Bidders Warning -->
      @if (comparableSheet()?.minimumBiddersWarning) {
        <p-message
          severity="warn"
          [text]="comparableSheet()!.minimumBiddersWarning!"
          styleClass="w-full mb-3"
        ></p-message>
      }

      <!-- Error Message -->
      @if (comparableSheetService.error()) {
        <p-message
          severity="error"
          [text]="comparableSheetService.error()!"
          styleClass="w-full mb-3"
        ></p-message>
      }

      <!-- Loading State -->
      @if (comparableSheetService.isLoading() && !gridData().length) {
        <div class="loading-container">
          <p-progressSpinner
            [style]="{ width: '50px', height: '50px' }"
            strokeWidth="4"
          ></p-progressSpinner>
          <p>Loading comparable sheet...</p>
        </div>
      } @else if (!gridData().length) {
        <!-- Empty State -->
        <div class="empty-state">
          <i class="pi pi-table" style="font-size: 3rem; color: var(--bayan-border, #e4e4e7);"></i>
          <h3>No Data Available</h3>
          <p>The comparable sheet will be available after bids are opened and BOQ data is imported.</p>
        </div>
      } @else {
        <!-- AG Grid -->
        <div class="grid-container">
          <!-- AG Grid placeholder - install ag-grid-angular and ag-grid-community to enable -->
          <div class="ag-grid-placeholder" data-testid="comparable-sheet-table" style="width: 100%; min-height: 200px; display: flex; align-items: center; justify-content: center; border: 1px dashed var(--bayan-border, #e4e4e7); border-radius: var(--bayan-radius, 0.5rem); color: var(--bayan-muted-foreground, #71717a);">
            <span>Comparable Sheet Grid (requires ag-grid installation)</span>
          </div>
        </div>

        <!-- Legend -->
        <div class="legend">
          <div class="legend-title">Color Legend:</div>
          <div class="legend-items">
            <div class="legend-item">
              <span class="legend-color" [style.background-color]="'#d4edda'"></span>
              <span class="legend-text">Normal (&lt;10% deviation)</span>
            </div>
            <div class="legend-item">
              <span class="legend-color" [style.background-color]="'#fff3cd'"></span>
              <span class="legend-text">Minor Outlier (10-20%)</span>
            </div>
            <div class="legend-item">
              <span class="legend-color" [style.background-color]="'#ffcccc'"></span>
              <span class="legend-text">Major Outlier (&gt;20%)</span>
            </div>
            <div class="legend-item">
              <span class="legend-color" [style.background-color]="'#f4f4f5'"></span>
              <span class="legend-text">No Bid (NB)</span>
            </div>
            <div class="legend-item">
              <span class="legend-color" [style.background-color]="'#faf5ff'"></span>
              <span class="legend-text">Non-Comparable</span>
            </div>
          </div>
        </div>
      }
    </div>

    <!-- Settings Dialog -->
    <p-dialog
      header="Comparable Sheet Settings"
      [(visible)]="showSettingsDialog"
      [modal]="true"
      [style]="{ width: '500px' }"
      [closable]="true"
      [draggable]="false"
    >
      <div class="settings-content">
        <h4>Display Options</h4>
        <div class="settings-group">
          <div class="setting-item">
            <p-checkbox
              [(ngModel)]="settings.showQuantityColumn"
              [binary]="true"
              inputId="showQty"
            ></p-checkbox>
            <label for="showQty">Show Quantity Column</label>
          </div>
          <div class="setting-item">
            <p-checkbox
              [(ngModel)]="settings.showUomColumn"
              [binary]="true"
              inputId="showUom"
            ></p-checkbox>
            <label for="showUom">Show UOM Column</label>
          </div>
          <div class="setting-item">
            <p-checkbox
              [(ngModel)]="settings.showAverageColumn"
              [binary]="true"
              inputId="showAvg"
            ></p-checkbox>
            <label for="showAvg">Show Average Column</label>
          </div>
          <div class="setting-item">
            <p-checkbox
              [(ngModel)]="settings.highlightLowestBidder"
              [binary]="true"
              inputId="highlightLowest"
            ></p-checkbox>
            <label for="highlightLowest">Highlight Lowest Bidder</label>
          </div>
          <div class="setting-item">
            <p-checkbox
              [(ngModel)]="settings.highlightOutliers"
              [binary]="true"
              inputId="highlightOutliers"
            ></p-checkbox>
            <label for="highlightOutliers">Highlight Outliers</label>
          </div>
        </div>

        <p-divider></p-divider>

        <h4>Outlier Thresholds (%)</h4>
        <div class="threshold-settings">
          <div class="threshold-item">
            <label>Minor (Yellow):</label>
            <p-inputNumber
              [(ngModel)]="settings.outlierThresholds.minor"
              [min]="1"
              [max]="100"
              [showButtons]="true"
              suffix="%"
            ></p-inputNumber>
          </div>
          <div class="threshold-item">
            <label>Major (Red):</label>
            <p-inputNumber
              [(ngModel)]="settings.outlierThresholds.major"
              [min]="1"
              [max]="100"
              [showButtons]="true"
              suffix="%"
            ></p-inputNumber>
          </div>
        </div>

        <p-divider></p-divider>

        <div class="setting-item">
          <label>Decimal Places:</label>
          <p-inputNumber
            [(ngModel)]="settings.decimalPlaces"
            [min]="0"
            [max]="4"
            [showButtons]="true"
          ></p-inputNumber>
        </div>
      </div>

      <ng-template pTemplate="footer">
        <button
          pButton
          label="Reset to Defaults"
          class="p-button-text"
          (click)="resetSettings()"
        ></button>
        <button
          pButton
          label="Apply"
          (click)="applySettings()"
        ></button>
      </ng-template>
    </p-dialog>
  `,
  styles: [`
    .comparable-sheet-container {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      height: 100%;
    }

    /* Toolbar */
    .toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem;
      background-color: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius, 0.5rem);
      flex-wrap: wrap;
      gap: 1rem;
    }

    .toolbar-left,
    .toolbar-right {
      display: flex;
      gap: 0.5rem;
      align-items: center;
      flex-wrap: wrap;
    }

    .p-input-icon-left {
      display: flex;
      align-items: center;
    }

    .p-input-icon-left i {
      position: absolute;
      left: 0.75rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .p-input-icon-left input {
      padding-left: 2.5rem;
    }

    /* Statistics Bar */
    .statistics-bar {
      display: flex;
      align-items: center;
      gap: 1.5rem;
      padding: 1rem 1.5rem;
      background: var(--bayan-primary, #18181b);
      border-radius: var(--bayan-radius, 0.5rem);
      color: white;
      flex-wrap: wrap;
    }

    .stat-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .stat-label {
      font-size: 0.875rem;
      opacity: 0.9;
    }

    .stat-value {
      font-size: 1.25rem;
      font-weight: 700;
    }

    .stat-sublabel {
      font-size: 0.75rem;
      opacity: 0.8;
      margin-left: 0.25rem;
    }

    .stat-value.outlier-high {
      color: #ffcccc;
    }

    .stat-value.outlier-medium {
      color: #fff3cd;
    }

    .stat-value.deviation {
      color: #ffd54f;
    }

    .stat-divider {
      width: 1px;
      height: 30px;
      background-color: rgba(255, 255, 255, 0.3);
    }

    /* Loading & Empty States */
    .loading-container,
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem;
      gap: 1rem;
      text-align: center;
    }

    .loading-container p,
    .empty-state p {
      color: var(--bayan-muted-foreground, #71717a);
      margin: 0;
    }

    .empty-state h3 {
      margin: 0;
      color: var(--bayan-foreground, #09090b);
    }

    /* Grid Container */
    .grid-container {
      flex: 1;
      min-height: 400px;
      border-radius: var(--bayan-radius, 0.5rem);
      overflow: hidden;
      border: 1px solid var(--bayan-border, #e4e4e7);
    }

    /* AG Grid Custom Styles */
    :host ::ng-deep .ag-theme-alpine {
      --ag-header-background-color: var(--bayan-accent, #f4f4f5);
      --ag-header-foreground-color: var(--bayan-foreground, #09090b);
      --ag-row-hover-color: var(--bayan-muted, #f4f4f5);
      --ag-selected-row-background-color: var(--bayan-accent, #f4f4f5);
      font-family: inherit;
    }

    :host ::ng-deep .ag-header-cell-text {
      font-weight: 600;
    }

    :host ::ng-deep .frozen-column {
      background-color: var(--bayan-muted, #f4f4f5);
    }

    :host ::ng-deep .section-header-row {
      background-color: var(--bayan-accent, #f4f4f5) !important;
      font-weight: 600;
    }

    :host ::ng-deep .section-subtotal-row {
      background-color: var(--bayan-accent, #f4f4f5) !important;
      font-weight: 600;
    }

    :host ::ng-deep .grand-total-row {
      background-color: var(--bayan-success-bg, #f0fdf4) !important;
      font-weight: 700;
      font-size: 1.05em;
    }

    :host ::ng-deep .rank-row {
      background-color: #fff8e1 !important;
      font-weight: 600;
    }

    :host ::ng-deep .cell-normal {
      background-color: #d4edda;
      color: #155724;
    }

    :host ::ng-deep .cell-minor {
      background-color: #fff3cd;
      color: #856404;
    }

    :host ::ng-deep .cell-major {
      background-color: #ffcccc;
      color: #721c24;
    }

    :host ::ng-deep .cell-extreme {
      background-color: #dc3545;
      color: #ffffff;
    }

    :host ::ng-deep .cell-no-bid {
      background-color: var(--bayan-accent, #f4f4f5);
      color: #6c757d;
      font-style: italic;
    }

    :host ::ng-deep .cell-non-comparable {
      background-color: #faf5ff;
      color: #9333ea;
    }

    :host ::ng-deep .cell-lowest {
      border: 2px solid #28a745;
      font-weight: 700;
    }

    :host ::ng-deep .bidder-header {
      text-align: center;
      white-space: normal;
      line-height: 1.3;
    }

    :host ::ng-deep .bidder-header .bidder-name {
      font-weight: 600;
      display: block;
    }

    :host ::ng-deep .bidder-header .bidder-total {
      font-size: 0.85em;
      color: var(--bayan-muted-foreground, #71717a);
      display: block;
    }

    /* Legend */
    .legend {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1rem;
      background-color: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius, 0.5rem);
      flex-wrap: wrap;
    }

    .legend-title {
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
    }

    .legend-items {
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
    }

    .legend-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .legend-color {
      width: 20px;
      height: 20px;
      border-radius: var(--bayan-radius-sm, 0.375rem);
      border: 1px solid #ddd;
    }

    .legend-text {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    /* Settings Dialog */
    .settings-content {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .settings-content h4 {
      margin: 0;
      color: var(--bayan-foreground, #09090b);
    }

    .settings-group {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .setting-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .setting-item label {
      color: var(--bayan-foreground, #09090b);
    }

    .threshold-settings {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .threshold-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .threshold-item label {
      min-width: 120px;
      color: var(--bayan-foreground, #09090b);
    }

    /* Responsive */
    @media (max-width: 992px) {
      .toolbar {
        flex-direction: column;
        align-items: stretch;
      }

      .toolbar-left,
      .toolbar-right {
        justify-content: center;
      }

      .statistics-bar {
        justify-content: center;
      }

      .stat-divider {
        display: none;
      }

      .legend {
        flex-direction: column;
        align-items: flex-start;
      }
    }

    @media (max-width: 768px) {
      .toolbar-left,
      .toolbar-right {
        flex-direction: column;
        width: 100%;
      }

      .toolbar-left > *,
      .toolbar-right > * {
        width: 100%;
      }

      :host ::ng-deep .p-dropdown {
        width: 100% !important;
      }

      :host ::ng-deep .p-inputtext {
        width: 100% !important;
      }
    }
  `]
})
export class ComparableSheetComponent implements OnInit, OnDestroy {
  @Input() tenderId!: number;

  readonly comparableSheetService = inject(ComparableSheetService);
  private readonly messageService = inject(MessageService);
  private readonly decimalPipe = inject(DecimalPipe);
  private readonly destroy$ = new Subject<void>();

  private gridApi: GridApi | null = null;

  // Data signals
  comparableSheet = signal<ComparableSheet | null>(null);
  gridData = signal<GridRowData[]>([]);
  statistics = signal<ComparableSheetStats | null>(null);
  bidders = signal<BidderColumn[]>([]);

  // UI state signals
  isExporting = signal<boolean>(false);
  showOutliersHighlight = signal<boolean>(true);

  // Filter state
  selectedSection: number | null = null;
  selectedOutlierFilter: 'all' | 'outliers_only' | 'hide_outliers' = 'all';
  searchTerm = '';

  // Dialog state
  showSettingsDialog = false;

  // Settings
  settings: ComparableSheetSettings = { ...DEFAULT_COMPARABLE_SHEET_SETTINGS };

  // Outlier filter options
  outlierFilterOptions: OutlierFilterOption[] = [
    { label: 'All Items', value: 'all' },
    { label: 'Only Outliers', value: 'outliers_only' },
    { label: 'Hide Outliers', value: 'hide_outliers' }
  ];

  // Computed: Section dropdown options
  sectionOptions = computed((): SectionOption[] => {
    const sheet = this.comparableSheet();
    if (!sheet) return [{ label: 'All Sections', value: null }];

    const options: SectionOption[] = [{ label: 'All Sections', value: null }];
    sheet.sections.forEach(section => {
      options.push({
        label: `${section.sectionNumber} - ${section.sectionTitle}`,
        value: section.sectionId
      });
    });
    return options;
  });

  // Computed: Column definitions for AG Grid
  columnDefs = computed((): ColDef[] => {
    const sheet = this.comparableSheet();
    if (!sheet) return [];

    const cols: ColDef[] = [
      // Frozen columns
      {
        field: 'itemNumber',
        headerName: 'Item #',
        width: 100,
        pinned: 'left',
        cellClass: 'frozen-column',
        suppressMovable: true
      },
      {
        field: 'description',
        headerName: 'Description',
        width: 250,
        pinned: 'left',
        cellClass: 'frozen-column',
        suppressMovable: true,
        tooltipField: 'description'
      }
    ];

    // Optional Quantity column
    if (this.settings.showQuantityColumn) {
      cols.push({
        field: 'quantity',
        headerName: 'Qty',
        width: 80,
        pinned: 'left',
        cellClass: 'frozen-column',
        type: 'numericColumn',
        valueFormatter: (params: ValueFormatterParams) => {
          if (params.value === null || params.value === undefined) return '';
          return this.decimalPipe.transform(params.value, '1.0-2') || '';
        }
      });
    }

    // Optional UOM column
    if (this.settings.showUomColumn) {
      cols.push({
        field: 'uom',
        headerName: 'UOM',
        width: 70,
        pinned: 'left',
        cellClass: 'frozen-column'
      });
    }

    // Dynamic bidder columns
    sheet.bidders.forEach(bidder => {
      cols.push({
        field: `bidder_${bidder.bidderId}`,
        headerName: bidder.bidderName,
        headerComponent: undefined,
        headerTooltip: `${bidder.bidderName}\nTotal: ${this.decimalPipe.transform(bidder.totalAmount, '1.0-0')} ${bidder.currency}`,
        width: 130,
        type: 'numericColumn',
        cellClass: (params: CellClassParams) => this.getBidderCellClass(params, bidder.bidderId),
        valueFormatter: (params: ValueFormatterParams) => this.formatBidderCellValue(params, bidder.bidderId),
        tooltipValueGetter: (params: ITooltipParams) => this.getBidderCellTooltip(params, bidder.bidderId)
      });
    });

    // Optional Average column
    if (this.settings.showAverageColumn) {
      cols.push({
        field: 'averageRate',
        headerName: 'Average',
        width: 100,
        type: 'numericColumn',
        valueFormatter: (params: ValueFormatterParams) => {
          if (params.value === null || params.value === undefined) return '';
          return this.decimalPipe.transform(params.value, `1.${this.settings.decimalPlaces}-${this.settings.decimalPlaces}`) || '';
        }
      });
    }

    return cols;
  });

  // Computed: Filtered grid data
  filteredGridData = computed((): GridRowData[] => {
    let data = this.gridData();

    // Section filter
    if (this.selectedSection !== null) {
      data = data.filter(row =>
        row.sectionId === this.selectedSection ||
        row.rowType === 'grand_total' ||
        row.rowType === 'rank'
      );
    }

    // Outlier filter
    if (this.selectedOutlierFilter === 'outliers_only') {
      data = data.filter(row =>
        row.hasOutliers ||
        row.rowType === 'section_header' ||
        row.rowType === 'section_subtotal' ||
        row.rowType === 'grand_total' ||
        row.rowType === 'rank'
      );
    } else if (this.selectedOutlierFilter === 'hide_outliers') {
      data = data.filter(row =>
        !row.hasOutliers ||
        row.rowType !== 'item'
      );
    }

    // Search filter
    if (this.searchTerm.trim()) {
      const term = this.searchTerm.toLowerCase().trim();
      data = data.filter(row =>
        row.itemNumber.toLowerCase().includes(term) ||
        row.description.toLowerCase().includes(term) ||
        row.rowType !== 'item'
      );
    }

    return data;
  });

  // Default column definition
  defaultColDef: ColDef = {
    sortable: true,
    resizable: true,
    filter: false
  };

  ngOnInit(): void {
    this.loadData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Load comparable sheet data
   */
  private loadData(): void {
    this.comparableSheetService.getComparableSheet(this.tenderId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (sheet) => {
          this.comparableSheet.set(sheet);
          this.bidders.set(sheet.bidders);
          this.statistics.set(sheet.statistics);
          this.gridData.set(this.transformToGridData(sheet));
        },
        error: (error) => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to load comparable sheet'
          });
        }
      });
  }

  /**
   * Transform ComparableSheet to AG Grid row data
   */
  private transformToGridData(sheet: ComparableSheet): GridRowData[] {
    return sheet.rows.map(row => {
      const gridRow: GridRowData = {
        rowId: row.rowId,
        rowType: row.rowType,
        itemNumber: row.itemNumber,
        description: row.description,
        quantity: row.quantity,
        uom: row.uom,
        sectionId: row.sectionId,
        sectionNumber: row.sectionNumber,
        sectionTitle: row.sectionTitle,
        averageRate: row.averageRate,
        hasOutliers: row.hasOutliers,
        isExpanded: row.isExpanded,
        // Store original bidder data for tooltip access
        _bidderData: row.bidderData
      };

      // Add bidder column values
      sheet.bidders.forEach(bidder => {
        const cellData = row.bidderData[bidder.bidderId];
        if (cellData) {
          if (row.rowType === 'rank') {
            gridRow[`bidder_${bidder.bidderId}`] = cellData.unitRate; // Rank value
          } else if (row.rowType === 'section_subtotal' || row.rowType === 'grand_total') {
            gridRow[`bidder_${bidder.bidderId}`] = cellData.amount; // Subtotal/Total amount
          } else if (row.rowType === 'item') {
            gridRow[`bidder_${bidder.bidderId}`] = cellData.normalizedRate ?? cellData.unitRate;
          } else {
            gridRow[`bidder_${bidder.bidderId}`] = null;
          }
        }
      });

      return gridRow;
    });
  }

  /**
   * Get row ID for AG Grid
   */
  getRowId = (params: GetRowIdParams): string => {
    return params.data.rowId;
  };

  /**
   * Get row class based on row type
   */
  getRowClass = (params: RowClassParams): string => {
    const rowType = params.data?.rowType;
    switch (rowType) {
      case 'section_header':
        return 'section-header-row';
      case 'section_subtotal':
        return 'section-subtotal-row';
      case 'grand_total':
        return 'grand-total-row';
      case 'rank':
        return 'rank-row';
      default:
        return '';
    }
  };

  /**
   * Get cell class for bidder columns based on outlier severity
   */
  private getBidderCellClass(params: CellClassParams, bidderId: number): string | string[] {
    const rowData = params.data;
    if (!rowData || rowData.rowType !== 'item') return '';

    const bidderData = rowData._bidderData?.[bidderId] as BidderCellData | undefined;
    if (!bidderData) return '';

    const classes: string[] = [];

    // Outlier severity styling
    if (this.showOutliersHighlight() && this.settings.highlightOutliers) {
      switch (bidderData.outlierSeverity) {
        case 'normal':
          classes.push('cell-normal');
          break;
        case 'minor':
          classes.push('cell-minor');
          break;
        case 'major':
        case 'extreme':
          classes.push('cell-major');
          break;
        case 'no_bid':
          classes.push('cell-no-bid');
          break;
        case 'non_comparable':
          classes.push('cell-non-comparable');
          break;
      }
    }

    // Highlight lowest bidder
    if (this.settings.highlightLowestBidder && bidderData.isLowest) {
      classes.push('cell-lowest');
    }

    return classes;
  }

  /**
   * Format bidder cell value
   */
  private formatBidderCellValue(params: ValueFormatterParams, bidderId: number): string {
    const rowData = params.data;
    if (!rowData) return '';

    // Rank row shows rank number
    if (rowData.rowType === 'rank') {
      const value = params.value;
      if (value === null || value === undefined) return '';
      return `#${value}`;
    }

    // Section header shows nothing
    if (rowData.rowType === 'section_header') {
      return '';
    }

    // Check for no bid
    const bidderData = rowData._bidderData?.[bidderId] as BidderCellData | undefined;
    if (bidderData?.outlierSeverity === 'no_bid') {
      return 'NB';
    }

    // Check for non-comparable
    if (bidderData?.outlierSeverity === 'non_comparable') {
      return 'N/C';
    }

    // Format numeric value
    const value = params.value;
    if (value === null || value === undefined) return '';

    return this.decimalPipe.transform(
      value,
      `1.${this.settings.decimalPlaces}-${this.settings.decimalPlaces}`
    ) || '';
  }

  /**
   * Get tooltip content for bidder cell
   */
  private getBidderCellTooltip(params: ITooltipParams, bidderId: number): string {
    const rowData = params.data;
    if (!rowData || rowData.rowType !== 'item') return '';

    const bidderData = rowData._bidderData?.[bidderId] as BidderCellData | undefined;
    if (!bidderData) return '';

    if (bidderData.outlierSeverity === 'no_bid') {
      return 'No Bid submitted for this item';
    }

    if (bidderData.outlierSeverity === 'non_comparable') {
      return 'Non-comparable item';
    }

    const lines: string[] = [];
    lines.push(`Rate: ${this.decimalPipe.transform(bidderData.unitRate, '1.2-2')}`);

    if (rowData.averageRate !== null) {
      lines.push(`Average: ${this.decimalPipe.transform(rowData.averageRate, '1.2-2')}`);
    }

    if (bidderData.deviationPercent !== null) {
      const sign = bidderData.deviationPercent >= 0 ? '+' : '';
      lines.push(`Deviation: ${sign}${this.decimalPipe.transform(bidderData.deviationPercent, '1.1-1')}%`);
    }

    lines.push(`Currency: ${bidderData.originalCurrency}`);

    if (rowData.uom) {
      lines.push(`UOM: ${rowData.uom}`);
    }

    return lines.join('\n');
  }

  /**
   * Handle grid ready event
   */
  onGridReady(params: GridReadyEvent): void {
    this.gridApi = params.api;
    this.gridApi.sizeColumnsToFit();
  }

  /**
   * Handle filter changes
   */
  onFilterChange(): void {
    // The computed signal filteredGridData will automatically update
    // Just trigger change detection if needed
    this.gridApi?.redrawRows();
  }

  /**
   * Handle search input changes (debounced)
   */
  onSearchChange(): void {
    // Computed signal handles filtering automatically
  }

  /**
   * Toggle outlier highlight
   */
  toggleOutlierHighlight(): void {
    this.showOutliersHighlight.set(!this.showOutliersHighlight());
    this.gridApi?.redrawRows();
  }

  /**
   * Export to Excel
   */
  exportToExcel(): void {
    this.isExporting.set(true);

    const options: ComparableSheetExportOptions = {
      format: 'xlsx',
      includeStatistics: true,
      includeRankings: true,
      highlightOutliers: this.settings.highlightOutliers,
      includeSectionSubtotals: true,
      includeColorCoding: true,
      language: 'en'
    };

    this.comparableSheetService.exportToExcel(this.tenderId, options)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (blob) => {
          this.isExporting.set(false);

          // Trigger download
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `comparable_sheet_${this.tenderId}_${new Date().toISOString().split('T')[0]}.xlsx`;
          a.click();
          window.URL.revokeObjectURL(url);

          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Comparable sheet exported successfully'
          });
        },
        error: (error) => {
          this.isExporting.set(false);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to export comparable sheet'
          });
        }
      });
  }

  /**
   * Get high outlier count (major + extreme)
   */
  getHighOutlierCount(): number {
    const sheet = this.comparableSheet();
    if (!sheet) return 0;

    let count = 0;
    sheet.rows.forEach(row => {
      if (row.rowType === 'item') {
        Object.values(row.bidderData).forEach(cell => {
          if (cell.outlierSeverity === 'major' || cell.outlierSeverity === 'extreme') {
            count++;
          }
        });
      }
    });
    return count;
  }

  /**
   * Get medium outlier count (minor)
   */
  getMediumOutlierCount(): number {
    const sheet = this.comparableSheet();
    if (!sheet) return 0;

    let count = 0;
    sheet.rows.forEach(row => {
      if (row.rowType === 'item') {
        Object.values(row.bidderData).forEach(cell => {
          if (cell.outlierSeverity === 'minor') {
            count++;
          }
        });
      }
    });
    return count;
  }

  /**
   * Get maximum deviation percentage
   */
  getMaxDeviation(): number {
    const sheet = this.comparableSheet();
    if (!sheet) return 0;

    let maxDeviation = 0;
    sheet.rows.forEach(row => {
      if (row.rowType === 'item') {
        Object.values(row.bidderData).forEach(cell => {
          if (cell.deviationPercent !== null) {
            const absDeviation = Math.abs(cell.deviationPercent);
            if (absDeviation > maxDeviation) {
              maxDeviation = absDeviation;
            }
          }
        });
      }
    });
    return maxDeviation;
  }

  /**
   * Reset settings to defaults
   */
  resetSettings(): void {
    this.settings = { ...DEFAULT_COMPARABLE_SHEET_SETTINGS };
  }

  /**
   * Apply settings and close dialog
   */
  applySettings(): void {
    this.showSettingsDialog = false;
    // Rebuild column definitions by triggering computed
    this.gridApi?.setGridOption('columnDefs', this.columnDefs());
    this.gridApi?.redrawRows();
  }
}
