import { Injectable, inject, signal } from '@angular/core';
import { Observable, map, tap, catchError, throwError, switchMap } from 'rxjs';
import { ApiService } from './api.service';
import {
  ParseResult,
  ParsedExcelRow,
  ColumnMapping,
  MappingValidation,
  BidImportColumnType,
  MatchResult,
  MatchedItem,
  MatchType,
  NormalizationResult,
  NormalizedBidItem,
  CurrencyNormalization,
  UomMismatch,
  ValidationResult,
  ValidationIssue,
  BidImportRequest,
  BidImportResponse
} from '../models/bid-import.model';

@Injectable({
  providedIn: 'root'
})
export class BidImportService {
  private readonly api = inject(ApiService);

  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  /** Base URL builder for bid import endpoints */
  private importUrl(tenderId: number, bidId: number): string {
    return `/tenders/${tenderId}/bids/${bidId}/import`;
  }

  /**
   * Parse uploaded Excel file.
   * Calls POST /api/tenders/{tenderId}/bids/{bidId}/import/parse
   * Backend parses the already-uploaded bid document and returns columns + preview rows.
   */
  parseFile(tenderId: number, bidId: number, file: File): Observable<ParseResult> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<any>(`${this.importUrl(tenderId, bidId)}/parse`, {
      previewRowCount: 10
    }).pipe(
      map(dto => {
        // Transform backend ParseBidResultDto -> frontend ParseResult
        const previewRows: ParsedExcelRow[] = (dto.previewRows || []).map((row: Record<string, any>, index: number) => ({
          rowIndex: index + 1,
          cells: row,
          rawData: Object.values(row)
        }));

        const detectedColumns: string[] = (dto.columns || []).map((c: any) => c.header || c.letter || `Col${c.index}`);

        return {
          success: dto.success,
          filename: file.name,
          totalRows: dto.itemCount,
          previewRows,
          detectedColumns,
          errors: dto.errorMessage ? [dto.errorMessage] : undefined
        } as ParseResult;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to parse file');
        return throwError(() => error);
      })
    );
  }

  /**
   * Validate column mappings
   */
  validateMappings(mappings: ColumnMapping[]): MappingValidation {
    const errors: string[] = [];
    const warnings: string[] = [];
    const missingRequired: BidImportColumnType[] = [];

    const requiredFields: BidImportColumnType[] = ['item_number', 'unit_rate'];
    const mappedFields = mappings.filter(m => m.targetField && m.targetField !== 'ignore').map(m => m.targetField);

    // Check required fields
    requiredFields.forEach(field => {
      if (!mappedFields.includes(field)) {
        missingRequired.push(field);
        errors.push(`Required field "${field.replace('_', ' ')}" is not mapped`);
      }
    });

    // Check for duplicate mappings
    const fieldCounts: Record<string, number> = {};
    mappedFields.forEach(field => {
      if (field && field !== 'ignore') {
        fieldCounts[field] = (fieldCounts[field] || 0) + 1;
      }
    });

    Object.entries(fieldCounts).forEach(([field, count]) => {
      if (count > 1) {
        errors.push(`Field "${field.replace('_', ' ')}" is mapped multiple times`);
      }
    });

    // Warnings for recommended fields
    if (!mappedFields.includes('description')) {
      warnings.push('Description is not mapped - items may be harder to match');
    }

    if (!mappedFields.includes('quantity')) {
      warnings.push('Quantity is not mapped - will use BOQ quantities');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      missingRequired
    };
  }

  /**
   * Auto-map columns based on common patterns
   */
  autoMapColumns(columns: string[], previewRows: ParsedExcelRow[]): ColumnMapping[] {
    const mappings: ColumnMapping[] = [];

    // Analyze first row to detect patterns
    const firstRow = previewRows[0];
    if (!firstRow) {
      return columns.map(col => ({ excelColumn: col, targetField: null }));
    }

    columns.forEach(col => {
      const value = firstRow.cells[col];
      let detectedField: BidImportColumnType | null = null;

      if (typeof value === 'string') {
        const lowerValue = value.toLowerCase();

        // Detect item number patterns
        if (/^\d+\.\d+\.\d+$/.test(value) || /^[a-z]{2,3}-\d+$/i.test(value)) {
          detectedField = 'item_number';
        }
        // Detect currency
        else if (['sar', 'aed', 'usd', 'eur', 'gbp'].includes(lowerValue)) {
          detectedField = 'currency';
        }
        // Detect UOM
        else if (['ls', 'ea', 'm2', 'm3', 'lm', 'kg', 'mt', 'hr', 'mth'].includes(lowerValue)) {
          detectedField = 'uom';
        }
        // Long text = description
        else if (value.length > 20) {
          detectedField = 'description';
        }
      } else if (typeof value === 'number') {
        // Heuristic: larger numbers in later columns tend to be amounts
        // Smaller numbers earlier tend to be quantities
        const colIndex = columns.indexOf(col);
        if (colIndex <= 2) {
          detectedField = 'quantity';
        } else if (colIndex === columns.length - 2) {
          detectedField = 'unit_rate';
        } else if (colIndex === columns.length - 1) {
          detectedField = 'amount';
        }
      }

      mappings.push({ excelColumn: col, targetField: detectedField });
    });

    // Apply default mappings for common column positions
    const defaultMappings: Record<number, BidImportColumnType> = {
      0: 'item_number',
      1: 'description',
      2: 'quantity',
      3: 'uom',
      4: 'unit_rate',
      5: 'amount',
      6: 'currency'
    };

    mappings.forEach((mapping, index) => {
      if (!mapping.targetField && defaultMappings[index]) {
        const defaultField = defaultMappings[index];
        // Only apply if not already mapped
        if (!mappings.some(m => m.targetField === defaultField)) {
          mapping.targetField = defaultField;
        }
      }
    });

    return mappings;
  }

  /**
   * Match bidder items to BOQ items.
   * First calls POST /api/tenders/{tenderId}/bids/{bidId}/import/map-columns to extract items,
   * then calls POST /api/tenders/{tenderId}/bids/{bidId}/import/match to match against BOQ.
   */
  matchToBoq(
    tenderId: number,
    bidId: number,
    parsedRows: ParsedExcelRow[],
    mappings: ColumnMapping[]
  ): Observable<MatchResult> {
    this._isLoading.set(true);
    this._error.set(null);

    // Build column mappings DTO for the backend
    const columnMappings: Record<string, string | null> = {};
    mappings.forEach(m => {
      if (m.targetField && m.targetField !== 'ignore') {
        // Map frontend field names to backend ColumnMappingsDto property names
        const fieldToProperty: Record<string, string> = {
          'item_number': 'itemNumberColumn',
          'description': 'descriptionColumn',
          'quantity': 'quantityColumn',
          'uom': 'uomColumn',
          'unit_rate': 'unitRateColumn',
          'amount': 'amountColumn',
          'currency': 'currencyColumn'
        };
        const prop = fieldToProperty[m.targetField];
        if (prop) {
          columnMappings[prop] = m.excelColumn;
        }
      }
    });

    // Build items from parsed rows using the mappings
    const fieldMap: Record<string, string> = {};
    mappings.forEach(m => {
      if (m.targetField && m.targetField !== 'ignore') {
        fieldMap[m.targetField] = m.excelColumn;
      }
    });

    const items = parsedRows.map((row, index) => ({
      rowIndex: index,
      itemNumber: fieldMap['item_number'] ? String(row.cells[fieldMap['item_number']] || '') : null,
      description: fieldMap['description'] ? String(row.cells[fieldMap['description']] || '') : null,
      quantity: fieldMap['quantity'] ? Number(row.cells[fieldMap['quantity']] || 0) : null,
      uom: fieldMap['uom'] ? String(row.cells[fieldMap['uom']] || '') : null,
      unitRate: fieldMap['unit_rate'] ? Number(row.cells[fieldMap['unit_rate']] || 0) : null,
      amount: fieldMap['amount'] ? Number(row.cells[fieldMap['amount']] || 0) : null,
      currency: fieldMap['currency'] ? String(row.cells[fieldMap['currency']] || 'SAR') : null
    }));

    // First call map-columns to extract all items from the full file, then match using those items
    return this.api.post<any>(`${this.importUrl(tenderId, bidId)}/map-columns`, {
      columnMappings: columnMappings
    }).pipe(
      switchMap((mapResult) => this.api.post<any>(`${this.importUrl(tenderId, bidId)}/match`, {
        items: mapResult.items || items,
        fuzzyMatchThreshold: 80.0,
        alternativeMatchCount: 3
      })),
      map(dto => this.mapMatchResultDto(dto)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to match items');
        return throwError(() => error);
      })
    );
  }

  /** Transform backend MatchResultDto -> frontend MatchResult */
  private mapMatchResultDto(dto: any): MatchResult {
    const mapMatchItems = (items: any[], matchType: MatchType): MatchedItem[] =>
      (items || []).map((m: any) => ({
        bidderItemId: String(m.rowIndex),
        bidderItemNumber: m.bidItemNumber || '',
        bidderDescription: m.bidDescription || '',
        bidderQuantity: m.bidQuantity || 0,
        bidderUom: m.bidUom || '',
        bidderUnitRate: m.bidUnitRate || 0,
        bidderAmount: m.bidAmount || 0,
        bidderCurrency: m.currency || 'SAR',
        matchType,
        boqItemId: m.matchedBoqItemId || undefined,
        boqItemNumber: m.matchedBoqItemNumber || undefined,
        boqDescription: m.matchedBoqDescription || undefined,
        boqQuantity: m.matchedBoqQuantity || undefined,
        boqUom: m.matchedBoqUom || undefined,
        confidenceScore: matchType === 'fuzzy' ? m.confidence : undefined,
        matchReason: m.reviewReason || undefined,
        isIncluded: matchType !== 'extra',
        manuallyMatched: false
      }));

    const exactItems = mapMatchItems(dto.exactMatches, 'exact');
    const fuzzyItems = mapMatchItems(dto.fuzzyMatches, 'fuzzy');
    const unmatchedItems = mapMatchItems(dto.unmatched, 'unmatched');
    const extraItems = mapMatchItems(dto.extraItems, 'extra');

    return {
      exactMatches: dto.summary?.exactMatchCount ?? exactItems.length,
      fuzzyMatches: dto.summary?.fuzzyMatchCount ?? fuzzyItems.length,
      unmatchedItems: dto.summary?.unmatchedCount ?? unmatchedItems.length,
      extraItems: dto.summary?.extraItemCount ?? extraItems.length,
      items: [...exactItems, ...fuzzyItems, ...unmatchedItems, ...extraItems]
    };
  }

  /**
   * Get available BOQ items for manual matching.
   * Calls GET /api/tenders/{tenderId}/boq and extracts items from sections.
   */
  getBoqItemsForMatching(tenderId: number): Observable<any[]> {
    return this.api.get<any>(`/tenders/${tenderId}/boq`).pipe(
      map(boqData => {
        // Backend returns BOQ with sections containing items
        const items: any[] = [];
        const sections = boqData.sections || boqData.items || [];
        sections.forEach((section: any) => {
          const sectionItems = section.items || [];
          sectionItems.forEach((item: any) => {
            items.push({
              id: item.id,
              itemNumber: item.itemNumber,
              description: item.description,
              quantity: item.quantity,
              uom: item.uom
            });
          });
        });
        // If the API returns a flat list of items directly
        if (items.length === 0 && Array.isArray(boqData)) {
          return boqData.map((item: any) => ({
            id: item.id,
            itemNumber: item.itemNumber,
            description: item.description,
            quantity: item.quantity,
            uom: item.uom
          }));
        }
        return items;
      })
    );
  }

  /**
   * Normalize currency and UOM.
   * Calls POST /api/tenders/{tenderId}/bids/{bidId}/import/normalize
   * The bidId is extracted from the first matched item's context; caller must also provide it.
   */
  normalize(
    tenderId: number,
    bidId: number,
    matchedItems: MatchedItem[],
    baseCurrency: string = 'SAR'
  ): Observable<NormalizationResult> {
    this._isLoading.set(true);
    this._error.set(null);

    // Detect currency from items for the request
    const currencies = [...new Set(matchedItems.map(i => i.bidderCurrency).filter(Boolean))];
    const detectedCurrency = currencies[0] || baseCurrency;

    return this.api.post<any>(`${this.importUrl(tenderId, bidId)}/normalize`, {
      fxRate: null, // Let backend use stored rate or default
      fxRateSource: 'System',
      persistResults: false // Preview mode
    }).pipe(
      map(dto => {
        // Transform backend NormalizationResultDto -> frontend NormalizationResult
        const currency: CurrencyNormalization = {
          detectedCurrency: dto.nativeCurrency || detectedCurrency,
          baseCurrency: dto.baseCurrency || baseCurrency,
          fxRate: dto.fxRate || 1.0,
          canConvert: true
        };

        const uomMismatches: UomMismatch[] = (dto.uomMismatches || []).map((m: any) => ({
          itemId: String(m.itemId),
          itemNumber: m.itemNumber || '',
          bidderUom: m.bidderUom || '',
          masterUom: m.masterUom || '',
          conversionFactor: m.conversionFactor,
          canConvert: m.canConvert,
          autoConvert: m.canConvert,
          markAsNonComparable: !m.canConvert
        }));

        const normalizedItems: NormalizedBidItem[] = (dto.normalizedItems || []).map((item: any) => ({
          bidderItemId: String(item.bidPricingId || item.boqItemId || ''),
          boqItemId: item.boqItemId || null,
          itemNumber: item.itemNumber || '',
          description: item.description || '',
          quantity: item.originalQuantity || 0,
          uom: item.originalUom || '',
          unitRate: item.originalUnitRate || 0,
          amount: item.originalAmount || 0,
          originalCurrency: item.nativeCurrency || detectedCurrency,
          normalizedUnitRate: item.normalizedUnitRate || 0,
          normalizedAmount: item.normalizedAmount || 0,
          isComparable: !item.isNonComparable,
          isExtra: !item.boqItemId,
          matchType: item.boqItemId ? 'exact' : 'extra' as MatchType
        }));

        return { currency, uomMismatches, normalizedItems };
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to normalize data');
        return throwError(() => error);
      })
    );
  }

  /**
   * Validate items before import.
   * Calls POST /api/tenders/{tenderId}/bids/{bidId}/import/validate
   */
  validate(tenderId: number, bidId: number, normalizedItems: NormalizedBidItem[]): Observable<ValidationResult> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<any>(`${this.importUrl(tenderId, bidId)}/validate`, {
      formulaTolerancePercent: 1.0,
      detectOutliers: true,
      outlierThresholdPercent: 30.0
    }).pipe(
      map(dto => {
        // Transform backend ValidationResultDto -> frontend ValidationResult
        const severityMap: Record<number, 'info' | 'warning' | 'error'> = {
          0: 'info',
          1: 'warning',
          2: 'error'
        };

        const issues: ValidationIssue[] = (dto.issues || []).map((issue: any) => ({
          itemId: String(issue.itemId || ''),
          itemNumber: issue.itemNumber || '',
          field: issue.field || '',
          severity: typeof issue.severity === 'number'
            ? (severityMap[issue.severity] || 'warning')
            : (issue.severity || 'warning'),
          message: issue.message || '',
          canProceed: typeof issue.severity === 'number'
            ? issue.severity < 2
            : issue.severity !== 'error'
        }));

        return {
          isValid: dto.errorCount === 0,
          validItemCount: dto.validCount || 0,
          warningCount: dto.warningCount || 0,
          errorCount: dto.errorCount || 0,
          issues
        } as ValidationResult;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Validation failed');
        return throwError(() => error);
      })
    );
  }

  /**
   * Execute the import.
   * Calls POST /api/tenders/{tenderId}/bids/{bidId}/import/execute
   */
  executeImport(request: BidImportRequest): Observable<BidImportResponse> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<any>(
      `${this.importUrl(request.tenderId, request.bidId)}/execute`,
      {
        forceImport: request.forceImport ?? false,
        createVendorSnapshot: true,
        fxRate: request.currency.fxRate !== 1.0 ? request.currency.fxRate : null
      }
    ).pipe(
      map(dto => {
        // Transform backend ImportResultDto -> frontend BidImportResponse
        const statusStr = typeof dto.status === 'string' ? dto.status.toLowerCase() : '';
        const isSuccess = dto.isSuccess || dto.status === 0 || dto.status === 1 || statusStr === 'imported' || statusStr === 'importedwithwarnings';
        const isFailed = dto.status === 3 || statusStr === 'failed';
        return {
          success: isSuccess,
          importedCount: dto.itemsImported || 0,
          skippedCount: dto.itemsSkipped || 0,
          errorCount: isFailed ? 1 : 0,
          totalAmount: dto.normalizedTotal || dto.totalAmount || 0,
          currency: dto.baseCurrency || dto.nativeCurrency || request.currency.baseCurrency,
          errors: dto.warnings || []
        } as BidImportResponse;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Import failed');
        return throwError(() => error);
      })
    );
  }

  clearError(): void {
    this._error.set(null);
  }
}
