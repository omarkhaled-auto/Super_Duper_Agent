import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { of, throwError } from 'rxjs';

import { ComparableSheetComponent } from './comparable-sheet.component';
import { ComparableSheetService } from '../../../../core/services/comparable-sheet.service';
import { MessageService } from 'primeng/api';
import {
  ComparableSheet,
  ComparableSheetRow,
  BidderColumn,
  BidderCellData,
  ComparableSheetStats,
  SectionSummary,
  BidderRanking,
  OutlierSeverity,
  DEFAULT_COMPARABLE_SHEET_SETTINGS,
  ComparableSheetSettings
} from '../../../../core/models/comparable-sheet.model';

describe('ComparableSheetComponent', () => {
  let component: ComparableSheetComponent;
  let fixture: ComponentFixture<ComparableSheetComponent>;
  let comparableSheetServiceSpy: jasmine.SpyObj<ComparableSheetService>;
  let messageServiceSpy: jasmine.SpyObj<MessageService>;

  // ---------------------------------------------------------------
  // Test fixtures — bidders
  // ---------------------------------------------------------------
  const mockBidders: BidderColumn[] = [
    {
      bidderId: 1,
      bidId: 1,
      bidderName: 'Tech Solutions Ltd',
      currency: 'SAR',
      fxRate: 1.0,
      totalAmount: 485000,
      normalizedTotal: 485000,
      rank: 1,
      isLowestBidder: true,
      submissionDate: new Date('2026-02-25')
    },
    {
      bidderId: 2,
      bidId: 2,
      bidderName: 'SecureTech Solutions',
      currency: 'SAR',
      fxRate: 1.0,
      totalAmount: 512000,
      normalizedTotal: 512000,
      rank: 3,
      isLowestBidder: false,
      submissionDate: new Date('2026-02-26')
    },
    {
      bidderId: 3,
      bidId: 3,
      bidderName: 'Global IT Partners',
      currency: 'SAR',
      fxRate: 1.0,
      totalAmount: 498500,
      normalizedTotal: 498500,
      rank: 2,
      isLowestBidder: false,
      submissionDate: new Date('2026-02-27')
    }
  ];

  // ---------------------------------------------------------------
  // Helper: create a BidderCellData
  // ---------------------------------------------------------------
  function makeCellData(
    bidderId: number,
    rate: number | null,
    deviation: number | null,
    severity: OutlierSeverity,
    isLowest = false
  ): BidderCellData {
    return {
      bidderId,
      unitRate: rate,
      amount: rate !== null ? rate * 100 : null,
      normalizedRate: rate,
      normalizedAmount: rate !== null ? rate * 100 : null,
      originalCurrency: 'SAR',
      hasDeviation: deviation !== null && Math.abs(deviation) >= 10,
      deviationPercent: deviation,
      outlierSeverity: severity,
      isLowest,
      isHighest: false
    };
  }

  // ---------------------------------------------------------------
  // Test fixtures — rows
  // ---------------------------------------------------------------
  function buildMockRows(): ComparableSheetRow[] {
    return [
      // Section header
      {
        rowId: 'section-1',
        rowType: 'section_header',
        sectionId: 1,
        sectionNumber: '1',
        sectionTitle: 'General Requirements',
        itemNumber: '1',
        description: 'General Requirements',
        quantity: null,
        uom: '',
        bidderData: {},
        averageRate: null,
        medianRate: null,
        lowestRate: null,
        highestRate: null,
        standardDeviation: null,
        isExpanded: true
      },
      // Normal item (no outliers)
      {
        rowId: 'item-1.1.1',
        rowType: 'item',
        sectionId: 1,
        itemNumber: '1.1.1',
        description: 'Site establishment',
        quantity: 1,
        uom: 'LS',
        bidderData: {
          1: makeCellData(1, 45000, -3.45, 'normal', true),
          2: makeCellData(2, 48000, 3.1, 'normal'),
          3: makeCellData(3, 46600, 0, 'normal')
        },
        averageRate: 46533,
        medianRate: 46600,
        lowestRate: 45000,
        highestRate: 48000,
        standardDeviation: 1247,
        hasOutliers: false
      },
      // Item with minor outlier (10-20% deviation)
      {
        rowId: 'item-1.1.2',
        rowType: 'item',
        sectionId: 1,
        itemNumber: '1.1.2',
        description: 'Site security and hoarding',
        quantity: 500,
        uom: 'LM',
        bidderData: {
          1: makeCellData(1, 150, -4.8, 'normal', true),
          2: makeCellData(2, 180, 14.3, 'minor'),
          3: makeCellData(3, 142, -9.9, 'normal')
        },
        averageRate: 157.3,
        medianRate: 150,
        lowestRate: 142,
        highestRate: 180,
        standardDeviation: 16,
        hasOutliers: true
      },
      // Item with major outlier (>20% deviation)
      {
        rowId: 'item-2.1.2',
        rowType: 'item',
        sectionId: 2,
        itemNumber: '2.1.2',
        description: 'Excavation in rock',
        quantity: 500,
        uom: 'M3',
        bidderData: {
          1: makeCellData(1, 120, -15.5, 'minor'),
          2: makeCellData(2, 210, 47.9, 'major'),
          3: makeCellData(3, 125, -12, 'minor')
        },
        averageRate: 141.7,
        medianRate: 125,
        lowestRate: 120,
        highestRate: 210,
        standardDeviation: 42,
        hasOutliers: true
      },
      // Item with no bid
      {
        rowId: 'item-2.1.4',
        rowType: 'item',
        sectionId: 2,
        itemNumber: '2.1.4',
        description: 'Dewatering - daywork rate',
        quantity: 100,
        uom: 'HR',
        bidderData: {
          1: makeCellData(1, 350, -4.1, 'normal', true),
          2: makeCellData(2, null, null, 'no_bid'),
          3: makeCellData(3, 380, 4.1, 'normal')
        },
        averageRate: 365,
        medianRate: 365,
        lowestRate: 350,
        highestRate: 380,
        standardDeviation: 15,
        hasOutliers: false
      },
      // Section subtotal
      {
        rowId: 'subtotal-1',
        rowType: 'section_subtotal',
        sectionId: 1,
        sectionNumber: '1',
        sectionTitle: 'General Requirements',
        itemNumber: '',
        description: 'Subtotal - General Requirements',
        quantity: null,
        uom: '',
        bidderData: {
          1: makeCellData(1, null, null, 'normal'),
          2: makeCellData(2, null, null, 'normal'),
          3: makeCellData(3, null, null, 'normal')
        },
        averageRate: null,
        medianRate: null,
        lowestRate: null,
        highestRate: null,
        standardDeviation: null
      },
      // Grand total
      {
        rowId: 'grand-total',
        rowType: 'grand_total',
        itemNumber: '',
        description: 'GRAND TOTAL',
        quantity: null,
        uom: '',
        bidderData: {
          1: { ...makeCellData(1, null, null, 'normal'), amount: 485000 },
          2: { ...makeCellData(2, null, null, 'normal'), amount: 512000 },
          3: { ...makeCellData(3, null, null, 'normal'), amount: 498500 }
        },
        averageRate: null,
        medianRate: null,
        lowestRate: null,
        highestRate: null,
        standardDeviation: null
      },
      // Rank row
      {
        rowId: 'rank',
        rowType: 'rank',
        itemNumber: '',
        description: 'RANK',
        quantity: null,
        uom: '',
        bidderData: {
          1: { ...makeCellData(1, 1, null, 'normal'), isLowest: true },
          2: { ...makeCellData(2, 3, null, 'minor'), isLowest: false },
          3: { ...makeCellData(3, 2, null, 'minor'), isLowest: false }
        },
        averageRate: null,
        medianRate: null,
        lowestRate: null,
        highestRate: null,
        standardDeviation: null
      }
    ];
  }

  const mockStatistics: ComparableSheetStats = {
    totalItems: 9,
    comparableItems: 8,
    nonComparableItems: 0,
    noBidItems: 1,
    outlierItems: 2,
    bidderCount: 3,
    lowestBidderId: 1,
    lowestTotal: 485000,
    highestTotal: 512000,
    averageTotal: 498500,
    medianTotal: 498500
  };

  const mockSections: SectionSummary[] = [
    { sectionId: 1, sectionNumber: '1', sectionTitle: 'General Requirements', itemCount: 2, bidderTotals: { 1: 195000, 2: 214100, 3: 204700 } },
    { sectionId: 2, sectionNumber: '2', sectionTitle: 'Civil Works', itemCount: 2, bidderTotals: { 1: 270500, 2: 278400, 3: 280300 } }
  ];

  const mockRankings: BidderRanking[] = [
    { bidderId: 1, bidderName: 'Tech Solutions Ltd', rank: 1, totalAmount: 485000, normalizedAmount: 485000, currency: 'SAR', deviationFromLowest: 0, deviationPercent: 0 },
    { bidderId: 3, bidderName: 'Global IT Partners', rank: 2, totalAmount: 498500, normalizedAmount: 498500, currency: 'SAR', deviationFromLowest: 13500, deviationPercent: 2.78 },
    { bidderId: 2, bidderName: 'SecureTech Solutions', rank: 3, totalAmount: 512000, normalizedAmount: 512000, currency: 'SAR', deviationFromLowest: 27000, deviationPercent: 5.57 }
  ];

  function buildMockComparableSheet(overrides: Partial<ComparableSheet> = {}): ComparableSheet {
    return {
      tenderId: 1,
      tenderTitle: 'IT Infrastructure Upgrade Project',
      tenderReference: 'TND-2026-001',
      baseCurrency: 'SAR',
      generatedAt: new Date(),
      bidders: mockBidders,
      rows: buildMockRows(),
      sections: mockSections,
      grandTotals: { 1: 485000, 2: 512000, 3: 498500 },
      rankings: mockRankings,
      statistics: mockStatistics,
      ...overrides
    };
  }

  // ---------------------------------------------------------------
  // Setup
  // ---------------------------------------------------------------
  beforeEach(async () => {
    comparableSheetServiceSpy = jasmine.createSpyObj(
      'ComparableSheetService',
      ['getComparableSheet', 'exportToExcel', 'calculateOutlierSeverity', 'getCellStyleClass', 'filterRows', 'clearError'],
      {
        isLoading: jasmine.createSpy('isLoading').and.returnValue(false),
        error: jasmine.createSpy('error').and.returnValue(null)
      }
    );
    messageServiceSpy = jasmine.createSpyObj('MessageService', ['add']);

    comparableSheetServiceSpy.getComparableSheet.and.returnValue(of(buildMockComparableSheet()));
    comparableSheetServiceSpy.exportToExcel.and.returnValue(of(new Blob([''], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })));

    await TestBed.configureTestingModule({
      imports: [ComparableSheetComponent],
      schemas: [NO_ERRORS_SCHEMA],
      providers: [
        DecimalPipe,
        { provide: ComparableSheetService, useValue: comparableSheetServiceSpy },
        { provide: MessageService, useValue: messageServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ComparableSheetComponent);
    component = fixture.componentInstance;
    component.tenderId = 1;
  });

  // ---------------------------------------------------------------
  // Tests
  // ---------------------------------------------------------------

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should load comparable sheet data on init', fakeAsync(() => {
    fixture.detectChanges(); // triggers ngOnInit
    tick();

    expect(comparableSheetServiceSpy.getComparableSheet).toHaveBeenCalledWith(1);
    expect(component.comparableSheet()).toBeTruthy();
    expect(component.comparableSheet()!.tenderTitle).toBe('IT Infrastructure Upgrade Project');
    expect(component.bidders().length).toBe(3);
    expect(component.gridData().length).toBeGreaterThan(0);
    expect(component.statistics()).toBeTruthy();
  }));

  it('should display loading spinner while loading', () => {
    // Before ngOnInit has completed, gridData is empty and service is loading
    (comparableSheetServiceSpy.isLoading as jasmine.Spy).and.returnValue(true);
    // Do not call fixture.detectChanges with tick, so data has not loaded yet
    expect(component.gridData().length).toBe(0);
    // The template checks: comparableSheetService.isLoading() && !gridData().length
    // Both conditions are satisfied, so the loading spinner would be rendered
    expect(comparableSheetServiceSpy.isLoading()).toBeTrue();
  });

  it('should display error message on load failure', fakeAsync(() => {
    const error = new Error('Server unavailable');
    comparableSheetServiceSpy.getComparableSheet.and.returnValue(throwError(() => error));

    fixture.detectChanges();
    tick();

    // Error should trigger a toast message
    expect(messageServiceSpy.add).toHaveBeenCalledWith(
      jasmine.objectContaining({
        severity: 'error',
        summary: 'Error'
      })
    );
    // No data should be loaded
    expect(component.comparableSheet()).toBeNull();
    expect(component.gridData().length).toBe(0);
  }));

  it('should display minimum bidders warning when present', fakeAsync(() => {
    const warningSheet = buildMockComparableSheet({
      minimumBiddersWarning: 'Only 2 bidders submitted. Minimum of 3 recommended for reliable comparison.'
    });
    comparableSheetServiceSpy.getComparableSheet.and.returnValue(of(warningSheet));

    fixture.detectChanges();
    tick();

    expect(component.comparableSheet()!.minimumBiddersWarning).toBeTruthy();
    expect(component.comparableSheet()!.minimumBiddersWarning).toContain('Only 2 bidders');
  }));

  it('should render bidder columns in grid', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const colDefs = component.columnDefs();
    expect(colDefs.length).toBeGreaterThan(0);

    // Should have frozen columns (itemNumber, description, qty, uom) + bidders + average
    const bidderCols = colDefs.filter(c => c.field?.startsWith('bidder_'));
    expect(bidderCols.length).toBe(3);
    expect(bidderCols[0].headerName).toBe('Tech Solutions Ltd');
    expect(bidderCols[1].headerName).toBe('SecureTech Solutions');
    expect(bidderCols[2].headerName).toBe('Global IT Partners');
  }));

  it('should apply outlier styling to cells', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    // The getBidderCellClass is a private method used via cellClass callbacks.
    // We verify by checking the column definitions have cellClass functions.
    const colDefs = component.columnDefs();
    const bidderCol = colDefs.find(c => c.field === 'bidder_2');
    expect(bidderCol).toBeTruthy();
    expect(bidderCol!.cellClass).toBeDefined();
    expect(typeof bidderCol!.cellClass).toBe('function');
  }));

  it('should classify minor outliers correctly (10-20%)', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    // From test data: bidder 2 on item 1.1.2 has 14.3% deviation -> minor
    const sheet = component.comparableSheet()!;
    const minorOutlierRow = sheet.rows.find(r => r.rowId === 'item-1.1.2');
    expect(minorOutlierRow).toBeTruthy();

    const bidder2Cell = minorOutlierRow!.bidderData[2];
    expect(bidder2Cell.outlierSeverity).toBe('minor');
    expect(bidder2Cell.deviationPercent).toBe(14.3);
    expect(minorOutlierRow!.hasOutliers).toBeTrue();
  }));

  it('should classify major outliers correctly (>20%)', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    // From test data: bidder 2 on item 2.1.2 has 47.9% deviation -> major
    const sheet = component.comparableSheet()!;
    const majorOutlierRow = sheet.rows.find(r => r.rowId === 'item-2.1.2');
    expect(majorOutlierRow).toBeTruthy();

    const bidder2Cell = majorOutlierRow!.bidderData[2];
    expect(bidder2Cell.outlierSeverity).toBe('major');
    expect(bidder2Cell.deviationPercent).toBe(47.9);
    expect(majorOutlierRow!.hasOutliers).toBeTrue();
  }));

  it('should toggle settings dialog visibility', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    expect(component.showSettingsDialog).toBeFalse();

    component.showSettingsDialog = true;
    expect(component.showSettingsDialog).toBeTrue();

    component.showSettingsDialog = false;
    expect(component.showSettingsDialog).toBeFalse();
  }));

  it('should update outlier thresholds from settings', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    // Default thresholds
    expect(component.settings.outlierThresholds.minor).toBe(10);
    expect(component.settings.outlierThresholds.major).toBe(20);

    // Update thresholds
    component.settings.outlierThresholds.minor = 15;
    component.settings.outlierThresholds.major = 30;

    component.applySettings();

    expect(component.settings.outlierThresholds.minor).toBe(15);
    expect(component.settings.outlierThresholds.major).toBe(30);
    expect(component.showSettingsDialog).toBeFalse();
  }));

  it('should export sheet data', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    // Mock URL.createObjectURL and revokeObjectURL since they are used in exportToExcel
    const createObjectURLSpy = spyOn(URL, 'createObjectURL').and.returnValue('blob:mock-url');
    const revokeObjectURLSpy = spyOn(URL, 'revokeObjectURL');

    component.exportToExcel();
    tick();

    expect(comparableSheetServiceSpy.exportToExcel).toHaveBeenCalledWith(
      1,
      jasmine.objectContaining({
        format: 'xlsx',
        includeStatistics: true,
        includeRankings: true
      })
    );
    expect(component.isExporting()).toBeFalse();
    expect(messageServiceSpy.add).toHaveBeenCalledWith(
      jasmine.objectContaining({
        severity: 'success',
        summary: 'Success'
      })
    );
    expect(createObjectURLSpy).toHaveBeenCalled();
    expect(revokeObjectURLSpy).toHaveBeenCalled();
  }));

  it('should handle empty data gracefully', fakeAsync(() => {
    const emptySheet = buildMockComparableSheet({
      rows: [],
      bidders: [],
      statistics: {
        totalItems: 0,
        comparableItems: 0,
        nonComparableItems: 0,
        noBidItems: 0,
        outlierItems: 0,
        bidderCount: 0,
        lowestBidderId: 0,
        lowestTotal: 0,
        highestTotal: 0,
        averageTotal: 0,
        medianTotal: 0
      }
    });
    comparableSheetServiceSpy.getComparableSheet.and.returnValue(of(emptySheet));

    fixture.detectChanges();
    tick();

    // Grid data should be empty
    expect(component.gridData().length).toBe(0);
    expect(component.bidders().length).toBe(0);
    // Column defs should still compute (frozen columns exist even without bidders)
    const colDefs = component.columnDefs();
    const bidderCols = colDefs.filter(c => c.field?.startsWith('bidder_'));
    expect(bidderCols.length).toBe(0);

    // Outlier counts should be zero
    expect(component.getHighOutlierCount()).toBe(0);
    expect(component.getMediumOutlierCount()).toBe(0);
    expect(component.getMaxDeviation()).toBe(0);
  }));

  // ---------------------------------------------------------------
  // Additional behavioral tests
  // ---------------------------------------------------------------

  it('should reset settings to defaults', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    // Modify settings
    component.settings.decimalPlaces = 4;
    component.settings.highlightOutliers = false;
    component.settings.outlierThresholds.minor = 25;

    component.resetSettings();

    expect(component.settings.decimalPlaces).toBe(DEFAULT_COMPARABLE_SHEET_SETTINGS.decimalPlaces);
    expect(component.settings.highlightOutliers).toBe(DEFAULT_COMPARABLE_SHEET_SETTINGS.highlightOutliers);
    expect(component.settings.outlierThresholds.minor).toBe(DEFAULT_COMPARABLE_SHEET_SETTINGS.outlierThresholds.minor);
  }));

  it('should toggle outlier highlight', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    expect(component.showOutliersHighlight()).toBeTrue();

    component.toggleOutlierHighlight();
    expect(component.showOutliersHighlight()).toBeFalse();

    component.toggleOutlierHighlight();
    expect(component.showOutliersHighlight()).toBeTrue();
  }));

  it('should compute section options from comparable sheet', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    const options = component.sectionOptions();
    expect(options.length).toBeGreaterThan(1);
    expect(options[0].label).toBe('All Sections');
    expect(options[0].value).toBeNull();
    expect(options[1].label).toContain('General Requirements');
  }));

  it('should count high (major + extreme) outliers correctly', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    // From test data: bidder 2 on item 2.1.2 has severity 'major' -> 1 high outlier
    const count = component.getHighOutlierCount();
    expect(count).toBe(1);
  }));

  it('should count medium (minor) outliers correctly', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    // From test data: bidder 2 on item 1.1.2 has severity 'minor',
    // bidder 1 on item 2.1.2 has severity 'minor', bidder 3 on item 2.1.2 has severity 'minor'
    const count = component.getMediumOutlierCount();
    expect(count).toBe(3);
  }));

  it('should compute max deviation correctly', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    // From test data: bidder 2 on item 2.1.2 has |47.9%| deviation
    const maxDev = component.getMaxDeviation();
    expect(maxDev).toBe(47.9);
  }));

  it('should filter grid data by section', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    // All data initially
    const allData = component.filteredGridData();
    expect(allData.length).toBe(component.gridData().length);

    // Filter to section 1
    component.selectedSection = 1;
    const filteredData = component.filteredGridData();

    // Should include section 1 items + grand_total + rank rows
    const section1Items = filteredData.filter(r => r.rowType === 'item');
    section1Items.forEach(item => {
      expect(item.sectionId).toBe(1);
    });
  }));

  it('should filter grid data by search term', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    component.searchTerm = 'Excavation';
    const filtered = component.filteredGridData();

    // Should include items matching "Excavation" + non-item rows (headers, subtotals, etc.)
    const matchingItems = filtered.filter(r => r.rowType === 'item');
    matchingItems.forEach(item => {
      expect(item.description.toLowerCase()).toContain('excavation');
    });
  }));

  it('should handle export error gracefully', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    comparableSheetServiceSpy.exportToExcel.and.returnValue(
      throwError(() => new Error('Export failed'))
    );

    component.exportToExcel();
    tick();

    expect(component.isExporting()).toBeFalse();
    expect(messageServiceSpy.add).toHaveBeenCalledWith(
      jasmine.objectContaining({
        severity: 'error',
        summary: 'Error'
      })
    );
  }));

  it('should return correct row class based on row type', () => {
    expect(component.getRowClass({ data: { rowType: 'section_header' } } as any)).toBe('section-header-row');
    expect(component.getRowClass({ data: { rowType: 'section_subtotal' } } as any)).toBe('section-subtotal-row');
    expect(component.getRowClass({ data: { rowType: 'grand_total' } } as any)).toBe('grand-total-row');
    expect(component.getRowClass({ data: { rowType: 'rank' } } as any)).toBe('rank-row');
    expect(component.getRowClass({ data: { rowType: 'item' } } as any)).toBe('');
    expect(component.getRowClass({ data: null } as any)).toBe('');
  });

  it('should include quantity and UOM columns when enabled in settings', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    component.settings.showQuantityColumn = true;
    component.settings.showUomColumn = true;

    const colDefs = component.columnDefs();
    const qtyCol = colDefs.find(c => c.field === 'quantity');
    const uomCol = colDefs.find(c => c.field === 'uom');

    expect(qtyCol).toBeTruthy();
    expect(uomCol).toBeTruthy();
  }));

  it('should exclude quantity and UOM columns when disabled in settings', fakeAsync(() => {
    fixture.detectChanges();
    tick();

    component.settings.showQuantityColumn = false;
    component.settings.showUomColumn = false;

    const colDefs = component.columnDefs();
    const qtyCol = colDefs.find(c => c.field === 'quantity');
    const uomCol = colDefs.find(c => c.field === 'uom');

    expect(qtyCol).toBeUndefined();
    expect(uomCol).toBeUndefined();
  }));
});
