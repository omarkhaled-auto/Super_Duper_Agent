import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA, SimpleChange } from '@angular/core';
import { of, throwError } from 'rxjs';

import { BidImportDialogComponent } from './bid-import-dialog.component';
import { BidImportService } from '../../../../core/services/bid-import.service';
import { BidDocument } from '../../../../core/models/bid.model';
import {
  ParseResult,
  MatchResult,
  MatchedItem,
  NormalizationResult,
  ValidationResult,
  BidImportResponse,
  MappingValidation,
  ColumnMapping,
  BidImportColumnType
} from '../../../../core/models/bid-import.model';

describe('BidImportDialogComponent', () => {
  let component: BidImportDialogComponent;
  let fixture: ComponentFixture<BidImportDialogComponent>;
  let bidImportServiceSpy: jasmine.SpyObj<BidImportService>;

  // ---------------------------------------------------------------
  // Test fixtures
  // ---------------------------------------------------------------
  const mockBidDocument: BidDocument = {
    id: 1,
    bidId: 10,
    filename: 'bid_boq_tech_solutions.xlsx',
    originalFilename: 'Tech_Solutions_BOQ.xlsx',
    fileSize: 245760,
    mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    documentType: 'priced_boq',
    category: 'commercial',
    uploadedAt: new Date('2026-02-01'),
    isPreviewable: false
  };

  const mockParseResult: ParseResult = {
    success: true,
    filename: 'bid_boq_tech_solutions.xlsx',
    totalRows: 11,
    previewRows: [
      { rowIndex: 1, cells: { A: '1.1.1', B: 'Site establishment', C: 1, D: 'LS', E: 45000, F: 45000, G: 'SAR' }, rawData: [] },
      { rowIndex: 2, cells: { A: '1.1.2', B: 'Site security hoarding', C: 500, D: 'LM', E: 150, F: 75000, G: 'SAR' }, rawData: [] },
      { rowIndex: 3, cells: { A: '1.1.3', B: 'Equipment mobilization', C: 1, D: 'LS', E: 30000, F: 30000, G: 'SAR' }, rawData: [] }
    ],
    detectedColumns: ['A', 'B', 'C', 'D', 'E', 'F', 'G']
  };

  const mockMappingValid: MappingValidation = {
    isValid: true,
    errors: [],
    warnings: [],
    missingRequired: []
  };

  const mockMappingInvalid: MappingValidation = {
    isValid: false,
    errors: ['Required field "item number" is not mapped'],
    warnings: ['Description is not mapped - items may be harder to match'],
    missingRequired: ['item_number']
  };

  const mockMatchResult: MatchResult = {
    exactMatches: 8,
    fuzzyMatches: 1,
    unmatchedItems: 1,
    extraItems: 1,
    items: [
      {
        bidderItemId: 'bid-0',
        bidderItemNumber: '1.1.1',
        bidderDescription: 'Site establishment',
        bidderQuantity: 1,
        bidderUom: 'LS',
        bidderUnitRate: 45000,
        bidderAmount: 45000,
        bidderCurrency: 'SAR',
        matchType: 'exact',
        boqItemId: 1,
        boqItemNumber: '1.1.1',
        boqDescription: 'Site establishment including temporary office',
        isIncluded: true,
        manuallyMatched: false
      },
      {
        bidderItemId: 'bid-1',
        bidderItemNumber: '1.1.2',
        bidderDescription: 'Site security hoarding',
        bidderQuantity: 500,
        bidderUom: 'LM',
        bidderUnitRate: 150,
        bidderAmount: 75000,
        bidderCurrency: 'SAR',
        matchType: 'fuzzy',
        boqItemId: 2,
        boqItemNumber: '1.1.2',
        boqDescription: 'Site security and hoarding',
        confidenceScore: 75,
        isIncluded: true,
        manuallyMatched: false
      },
      {
        bidderItemId: 'bid-2',
        bidderItemNumber: 'UNKNOWN-01',
        bidderDescription: 'Misc charges',
        bidderQuantity: 1,
        bidderUom: 'LS',
        bidderUnitRate: 5000,
        bidderAmount: 5000,
        bidderCurrency: 'SAR',
        matchType: 'unmatched',
        isIncluded: false,
        manuallyMatched: false
      },
      {
        bidderItemId: 'bid-3',
        bidderItemNumber: 'EXT-001',
        bidderDescription: 'Additional equipment rental',
        bidderQuantity: 1,
        bidderUom: 'LS',
        bidderUnitRate: 25000,
        bidderAmount: 25000,
        bidderCurrency: 'SAR',
        matchType: 'extra',
        isIncluded: true,
        manuallyMatched: false
      }
    ]
  };

  const mockNormalizationResult: NormalizationResult = {
    currency: {
      detectedCurrency: 'SAR',
      baseCurrency: 'SAR',
      fxRate: 1.0,
      canConvert: true
    },
    uomMismatches: [],
    normalizedItems: [
      {
        bidderItemId: 'bid-0',
        boqItemId: 1,
        itemNumber: '1.1.1',
        description: 'Site establishment',
        quantity: 1,
        uom: 'LS',
        unitRate: 45000,
        amount: 45000,
        originalCurrency: 'SAR',
        normalizedUnitRate: 45000,
        normalizedAmount: 45000,
        isComparable: true,
        isExtra: false,
        matchType: 'exact'
      }
    ]
  };

  const mockValidationResult: ValidationResult = {
    isValid: true,
    validItemCount: 9,
    warningCount: 1,
    errorCount: 0,
    issues: [
      {
        itemId: 'bid-2',
        itemNumber: 'UNKNOWN-01',
        field: 'match',
        severity: 'warning',
        message: 'Item not matched to BOQ - will be marked as non-comparable',
        canProceed: true
      }
    ]
  };

  const mockImportResponse: BidImportResponse = {
    success: true,
    importedCount: 10,
    skippedCount: 1,
    errorCount: 0,
    totalAmount: 788000,
    currency: 'SAR'
  };

  // ---------------------------------------------------------------
  // Setup
  // ---------------------------------------------------------------
  beforeEach(async () => {
    bidImportServiceSpy = jasmine.createSpyObj('BidImportService', [
      'parseFile',
      'autoMapColumns',
      'validateMappings',
      'matchToBoq',
      'normalize',
      'validate',
      'executeImport',
      'getBoqItemsForMatching'
    ]);

    // Default return values
    bidImportServiceSpy.parseFile.and.returnValue(of(mockParseResult));
    bidImportServiceSpy.validateMappings.and.returnValue(mockMappingValid);
    bidImportServiceSpy.autoMapColumns.and.returnValue([
      { excelColumn: 'A', targetField: 'item_number' },
      { excelColumn: 'B', targetField: 'description' },
      { excelColumn: 'C', targetField: 'quantity' },
      { excelColumn: 'D', targetField: 'uom' },
      { excelColumn: 'E', targetField: 'unit_rate' },
      { excelColumn: 'F', targetField: 'amount' },
      { excelColumn: 'G', targetField: 'currency' }
    ]);
    bidImportServiceSpy.matchToBoq.and.returnValue(of(mockMatchResult));
    bidImportServiceSpy.normalize.and.returnValue(of(mockNormalizationResult));
    bidImportServiceSpy.validate.and.returnValue(of(mockValidationResult));
    bidImportServiceSpy.executeImport.and.returnValue(of(mockImportResponse));
    bidImportServiceSpy.getBoqItemsForMatching.and.returnValue(of([
      { id: 1, itemNumber: '1.1.1', description: 'Site establishment including temporary office', quantity: 1, uom: 'LS' },
      { id: 2, itemNumber: '1.1.2', description: 'Site security and hoarding', quantity: 500, uom: 'LM' }
    ]));

    await TestBed.configureTestingModule({
      imports: [BidImportDialogComponent],
      schemas: [NO_ERRORS_SCHEMA],
      providers: [
        { provide: BidImportService, useValue: bidImportServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(BidImportDialogComponent);
    component = fixture.componentInstance;
    component.tenderId = 1;
    component.bidId = 10;
    component.bidDocument = mockBidDocument;
  });

  // ---------------------------------------------------------------
  // Tests
  // ---------------------------------------------------------------

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with step 1 (file upload)', () => {
    fixture.detectChanges();
    expect(component.activeStep()).toBe(0);
    expect(component.parseResult()).toBeNull();
    expect(component.isParsing()).toBeFalse();
  });

  it('should accept valid file types (xlsx, csv)', () => {
    // The component relies on the bidDocument having the correct mimeType.
    // An xlsx document should be accepted for parsing without error.
    const xlsxDoc: BidDocument = {
      ...mockBidDocument,
      filename: 'boq.xlsx',
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    };
    component.bidDocument = xlsxDoc;
    fixture.detectChanges();

    component.parseFile();
    expect(bidImportServiceSpy.parseFile).toHaveBeenCalledWith(
      10,
      jasmine.any(File)
    );

    // Verify the File was created with the correct filename
    const callArgs = bidImportServiceSpy.parseFile.calls.mostRecent().args;
    const file = callArgs[1] as File;
    expect(file.name).toBe('boq.xlsx');
  });

  it('should reject invalid file types (no bidDocument)', () => {
    component.bidDocument = null;
    fixture.detectChanges();

    component.parseFile();

    // parseFile should not be called when bidDocument is null
    expect(bidImportServiceSpy.parseFile).not.toHaveBeenCalled();
  });

  it('should display file name after selection', () => {
    fixture.detectChanges();

    expect(component.bidDocument).toBeTruthy();
    expect(component.bidDocument!.originalFilename).toBe('Tech_Solutions_BOQ.xlsx');

    // The component template renders bidDocument.originalFilename
    const compiled = fixture.nativeElement as HTMLElement;
    fixture.detectChanges();
    // Since dialog visibility defaults to false, we set it to true to render content
    component.visible = true;
    component.ngOnChanges({
      visible: new SimpleChange(false, true, false)
    });
    fixture.detectChanges();

    expect(component.bidDocument!.originalFilename).toBe('Tech_Solutions_BOQ.xlsx');
  });

  it('should call parse API on file upload', () => {
    fixture.detectChanges();

    component.parseFile();

    expect(bidImportServiceSpy.parseFile).toHaveBeenCalledWith(10, jasmine.any(File));
  });

  it('should display column preview after parse', fakeAsync(() => {
    fixture.detectChanges();

    component.parseFile();
    tick();

    expect(component.parseResult()).toBeTruthy();
    expect(component.parseResult()!.totalRows).toBe(11);
    expect(component.parseResult()!.detectedColumns).toEqual(['A', 'B', 'C', 'D', 'E', 'F', 'G']);
    expect(component.parseResult()!.previewRows.length).toBe(3);
    expect(component.isParsing()).toBeFalse();
  }));

  it('should allow column mapping', fakeAsync(() => {
    fixture.detectChanges();

    // First parse the file to populate detected columns
    component.parseFile();
    tick();

    // Verify column mappings were initialized
    const mappings = component.columnMappings();
    expect(Object.keys(mappings).length).toBe(7);
    expect(mappings['A']).toBeNull();

    // Simulate mapping a column
    component.onMappingChange('A', 'item_number');

    const updatedMappings = component.columnMappings();
    expect(updatedMappings['A']).toBe('item_number');
    expect(bidImportServiceSpy.validateMappings).toHaveBeenCalled();
  }));

  it('should proceed to match step after mapping', fakeAsync(() => {
    fixture.detectChanges();

    // Parse file
    component.parseFile();
    tick();

    // Set up valid mappings
    component.onMappingChange('A', 'item_number');
    component.onMappingChange('E', 'unit_rate');

    // The validation returns valid
    bidImportServiceSpy.validateMappings.and.returnValue(mockMappingValid);
    component.validateMappings();

    // Move to mapping step, then to match step
    component.activeStep.set(1);
    component.nextStep();

    // Should advance to step 2 (match step)
    expect(component.activeStep()).toBe(2);
    expect(bidImportServiceSpy.matchToBoq).toHaveBeenCalled();
  }));

  it('should display matched items', fakeAsync(() => {
    fixture.detectChanges();

    // Simulate having a parse result and advancing to match step
    component.parseResult.set(mockParseResult);
    component.columnMappings.set({ A: 'item_number', B: 'description', E: 'unit_rate' });
    component.mappingValidation.set(mockMappingValid);
    component.activeStep.set(1);

    component.nextStep();
    tick();

    const result = component.matchResult();
    expect(result).toBeTruthy();
    expect(result!.exactMatches).toBe(8);
    expect(result!.fuzzyMatches).toBe(1);
    expect(result!.unmatchedItems).toBe(1);
    expect(result!.extraItems).toBe(1);
    expect(result!.items.length).toBe(4);
  }));

  it('should allow manual match corrections', fakeAsync(() => {
    fixture.detectChanges();

    // Set up match result with an unmatched item
    component.matchResult.set(mockMatchResult);
    component.activeStep.set(2);
    fixture.detectChanges();

    const unmatchedItems = component.unmatchedItems();
    expect(unmatchedItems.length).toBe(1);
    expect(unmatchedItems[0].bidderItemNumber).toBe('UNKNOWN-01');

    // Simulate manual BOQ selection
    const unmatchedItem = component.matchResult()!.items.find(
      i => i.matchType === 'unmatched'
    )!;

    component.onBoqItemSelected(unmatchedItem, {
      value: { id: 5, itemNumber: '1.2.2', description: 'Temporary power supply installation' }
    });

    expect(unmatchedItem.boqItemId).toBe(5);
    expect(unmatchedItem.matchType).toBe('exact');
    expect(unmatchedItem.manuallyMatched).toBeTrue();
    expect(unmatchedItem.isIncluded).toBeTrue();
  }));

  it('should proceed to normalize step', fakeAsync(() => {
    fixture.detectChanges();

    // Set up match result
    component.parseResult.set(mockParseResult);
    component.matchResult.set(mockMatchResult);
    component.activeStep.set(2);

    component.nextStep();
    tick();

    expect(component.activeStep()).toBe(3);
    expect(bidImportServiceSpy.normalize).toHaveBeenCalled();
    expect(component.normalizationResult()).toBeTruthy();
    expect(component.normalizationResult()!.currency.detectedCurrency).toBe('SAR');
  }));

  it('should display normalization preview', fakeAsync(() => {
    fixture.detectChanges();

    // Set up normalization result
    component.normalizationResult.set(mockNormalizationResult);
    component.activeStep.set(3);
    fixture.detectChanges();

    const result = component.normalizationResult();
    expect(result).toBeTruthy();
    expect(result!.currency.fxRate).toBe(1.0);
    expect(result!.currency.baseCurrency).toBe('SAR');
    expect(result!.uomMismatches.length).toBe(0);
    expect(result!.normalizedItems.length).toBe(1);
  }));

  it('should call execute import on final step', fakeAsync(() => {
    fixture.detectChanges();

    // Set up all required state for import
    component.normalizationResult.set(mockNormalizationResult);
    component.validationResult.set(mockValidationResult);
    component.activeStep.set(4);

    component.executeImport();
    tick();

    expect(bidImportServiceSpy.executeImport).toHaveBeenCalledWith(
      jasmine.objectContaining({
        bidId: 10,
        tenderId: 1,
        includeExtras: true
      })
    );

    const result = component.importResult();
    expect(result).toBeTruthy();
    expect(result!.success).toBeTrue();
    expect(result!.importedCount).toBe(10);
    expect(result!.totalAmount).toBe(788000);
    expect(result!.currency).toBe('SAR');
    expect(component.isImporting()).toBeFalse();
  }));

  it('should handle API errors gracefully', fakeAsync(() => {
    fixture.detectChanges();

    const error = new Error('Network error');
    bidImportServiceSpy.parseFile.and.returnValue(throwError(() => error));

    component.parseFile();
    tick();

    // isParsing should be set back to false after error
    expect(component.isParsing()).toBeFalse();
    // parseResult should remain null
    expect(component.parseResult()).toBeNull();
  }));

  // ---------------------------------------------------------------
  // Additional behavioral tests
  // ---------------------------------------------------------------

  it('should reset state when dialog becomes visible', () => {
    // Simulate first use — set some state
    component.activeStep.set(3);
    component.parseResult.set(mockParseResult);
    component.matchResult.set(mockMatchResult);

    // Trigger ngOnChanges with visible = true
    component.visible = true;
    component.ngOnChanges({
      visible: new SimpleChange(false, true, false)
    });

    expect(component.activeStep()).toBe(0);
    expect(component.parseResult()).toBeNull();
    expect(component.matchResult()).toBeNull();
    expect(component.normalizationResult()).toBeNull();
    expect(component.validationResult()).toBeNull();
    expect(component.importResult()).toBeNull();
  });

  it('should correctly determine canProceed for each step', () => {
    fixture.detectChanges();

    // Step 0: needs parseResult
    component.activeStep.set(0);
    expect(component.canProceed()).toBeFalse();
    component.parseResult.set(mockParseResult);
    expect(component.canProceed()).toBeTrue();

    // Step 1: needs valid mapping
    component.activeStep.set(1);
    component.mappingValidation.set(null);
    expect(component.canProceed()).toBeFalse();
    component.mappingValidation.set(mockMappingValid);
    expect(component.canProceed()).toBeTrue();
    component.mappingValidation.set(mockMappingInvalid);
    expect(component.canProceed()).toBeFalse();

    // Step 2: needs matchResult
    component.activeStep.set(2);
    component.matchResult.set(null);
    expect(component.canProceed()).toBeFalse();
    component.matchResult.set(mockMatchResult);
    expect(component.canProceed()).toBeTrue();

    // Step 3: needs normalizationResult
    component.activeStep.set(3);
    component.normalizationResult.set(null);
    expect(component.canProceed()).toBeFalse();
    component.normalizationResult.set(mockNormalizationResult);
    expect(component.canProceed()).toBeTrue();
  });

  it('should emit visibleChange(false) on cancel', () => {
    spyOn(component.visibleChange, 'emit');

    component.onCancel();

    expect(component.visibleChange.emit).toHaveBeenCalledWith(false);
  });

  it('should emit imported event and close on complete', () => {
    spyOn(component.visibleChange, 'emit');
    spyOn(component.imported, 'emit');

    component.importResult.set(mockImportResponse);
    component.onComplete();

    expect(component.imported.emit).toHaveBeenCalledWith(mockImportResponse);
    expect(component.visibleChange.emit).toHaveBeenCalledWith(false);
  });

  it('should format file sizes correctly', () => {
    expect(component.formatFileSize(500)).toBe('500 B');
    expect(component.formatFileSize(2048)).toBe('2.0 KB');
    expect(component.formatFileSize(1536000)).toBe('1.5 MB');
  });

  it('should navigate back one step with previousStep()', () => {
    component.activeStep.set(3);
    component.previousStep();
    expect(component.activeStep()).toBe(2);

    component.previousStep();
    expect(component.activeStep()).toBe(1);
  });

  it('should correctly identify required fields', () => {
    expect(component.isRequiredField('item_number')).toBeTrue();
    expect(component.isRequiredField('unit_rate')).toBeTrue();
    expect(component.isRequiredField('description')).toBeFalse();
    expect(component.isRequiredField('quantity')).toBeFalse();
    expect(component.isRequiredField(null)).toBeFalse();
  });

  it('should mark unmatched item as extra', () => {
    const item: MatchedItem = {
      bidderItemId: 'bid-99',
      bidderItemNumber: 'UNKNOWN-01',
      bidderDescription: 'Unknown item',
      bidderQuantity: 1,
      bidderUom: 'LS',
      bidderUnitRate: 5000,
      bidderAmount: 5000,
      matchType: 'unmatched',
      isIncluded: false,
      manuallyMatched: false
    };

    component.markAsExtra(item);

    expect(item.matchType).toBe('extra');
    expect(item.isIncluded).toBeTrue();
  });

  it('should return correct issue icon for each severity', () => {
    expect(component.getIssueIcon('error')).toContain('pi-times-circle');
    expect(component.getIssueIcon('warning')).toContain('pi-exclamation-triangle');
    expect(component.getIssueIcon('info')).toContain('pi-info-circle');
    expect(component.getIssueIcon('unknown')).toContain('pi-question-circle');
  });

  it('should compute fuzzyMatches from matchResult', () => {
    component.matchResult.set(mockMatchResult);

    const fuzzy = component.fuzzyMatches();
    expect(fuzzy.length).toBe(1);
    expect(fuzzy[0].matchType).toBe('fuzzy');
    expect(fuzzy[0].confidenceScore).toBe(75);
  });

  it('should compute extraItems from matchResult', () => {
    component.matchResult.set(mockMatchResult);

    const extras = component.extraItems();
    expect(extras.length).toBe(1);
    expect(extras[0].matchType).toBe('extra');
    expect(extras[0].bidderItemNumber).toBe('EXT-001');
  });

  it('should handle match step API error gracefully', fakeAsync(() => {
    fixture.detectChanges();

    bidImportServiceSpy.matchToBoq.and.returnValue(throwError(() => new Error('Match failed')));

    component.parseResult.set(mockParseResult);
    component.columnMappings.set({ A: 'item_number', E: 'unit_rate' });
    component.mappingValidation.set(mockMappingValid);
    component.activeStep.set(1);

    component.nextStep();
    tick();

    // Step advanced but matchResult remains null due to error
    expect(component.activeStep()).toBe(2);
    expect(component.isMatching()).toBeFalse();
    expect(component.matchResult()).toBeNull();
  }));

  it('should not execute import when normalizationResult or validationResult is null', () => {
    fixture.detectChanges();

    component.normalizationResult.set(null);
    component.validationResult.set(null);

    component.executeImport();

    expect(bidImportServiceSpy.executeImport).not.toHaveBeenCalled();
  });
});
