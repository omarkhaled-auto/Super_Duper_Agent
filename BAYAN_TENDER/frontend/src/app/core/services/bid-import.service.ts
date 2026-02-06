import { Injectable, inject, signal } from '@angular/core';
import { Observable, of, delay, map, tap, catchError, throwError } from 'rxjs';
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
  BidImportResponse,
  DEFAULT_FX_RATES
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

  // Mock BOQ items for matching
  private mockBoqItems = [
    { id: 1, itemNumber: '1.1.1', description: 'Site establishment including temporary office', quantity: 1, uom: 'LS' },
    { id: 2, itemNumber: '1.1.2', description: 'Site security and hoarding', quantity: 500, uom: 'LM' },
    { id: 3, itemNumber: '1.1.3', description: 'Equipment mobilization and demobilization', quantity: 1, uom: 'LS' },
    { id: 4, itemNumber: '1.2.1', description: 'Portable toilets - monthly rental', quantity: 12, uom: 'MTH' },
    { id: 5, itemNumber: '1.2.2', description: 'Temporary power supply installation', quantity: 1, uom: 'LS' },
    { id: 6, itemNumber: '2.1.1', description: 'Excavation in ordinary soil including disposal', quantity: 2500, uom: 'M3' },
    { id: 7, itemNumber: '2.1.2', description: 'Excavation in rock including disposal', quantity: 500, uom: 'M3' },
    { id: 8, itemNumber: '2.1.3', description: 'Backfilling with approved material', quantity: 1800, uom: 'M3' },
    { id: 9, itemNumber: '2.1.4', description: 'Dewatering - daywork rate', quantity: 100, uom: 'HR' },
    { id: 10, itemNumber: '2.2.1', description: 'Grade 40 concrete for foundations', quantity: 350, uom: 'M3' },
    { id: 11, itemNumber: '2.2.2', description: 'Grade 40 concrete for columns', quantity: 200, uom: 'M3' },
    { id: 12, itemNumber: '2.2.3', description: 'Steel reinforcement including cutting, bending', quantity: 75000, uom: 'KG' },
    { id: 13, itemNumber: '2.2.4', description: 'Formwork to concrete surfaces', quantity: 1200, uom: 'M2' }
  ];

  /**
   * Parse uploaded Excel file
   */
  parseFile(bidId: number, file: File): Observable<ParseResult> {
    this._isLoading.set(true);
    this._error.set(null);

    // Mock implementation - in production, this would send file to backend
    return of(null).pipe(
      delay(1500),
      map(() => {
        // Simulate parsed Excel data
        const mockRows: ParsedExcelRow[] = [
          { rowIndex: 1, cells: { A: '1.1.1', B: 'Site establishment', C: 1, D: 'LS', E: 45000, F: 45000, G: 'SAR' }, rawData: ['1.1.1', 'Site establishment', 1, 'LS', 45000, 45000, 'SAR'] },
          { rowIndex: 2, cells: { A: '1.1.2', B: 'Site security hoarding', C: 500, D: 'LM', E: 150, F: 75000, G: 'SAR' }, rawData: ['1.1.2', 'Site security hoarding', 500, 'LM', 150, 75000, 'SAR'] },
          { rowIndex: 3, cells: { A: '1.1.3', B: 'Equipment mobilization', C: 1, D: 'LS', E: 30000, F: 30000, G: 'SAR' }, rawData: ['1.1.3', 'Equipment mobilization', 1, 'LS', 30000, 30000, 'SAR'] },
          { rowIndex: 4, cells: { A: '1.2.1', B: 'Portable toilets monthly', C: 12, D: 'MTH', E: 2500, F: 30000, G: 'SAR' }, rawData: ['1.2.1', 'Portable toilets monthly', 12, 'MTH', 2500, 30000, 'SAR'] },
          { rowIndex: 5, cells: { A: '1.2.2', B: 'Temporary power supply', C: 1, D: 'LS', E: 15000, F: 15000, G: 'SAR' }, rawData: ['1.2.2', 'Temporary power supply', 1, 'LS', 15000, 15000, 'SAR'] },
          { rowIndex: 6, cells: { A: '2.1.1', B: 'Excavation ordinary soil', C: 2500, D: 'M3', E: 45, F: 112500, G: 'SAR' }, rawData: ['2.1.1', 'Excavation ordinary soil', 2500, 'M3', 45, 112500, 'SAR'] },
          { rowIndex: 7, cells: { A: '2.1.2', B: 'Excavation rock', C: 500, D: 'M3', E: 120, F: 60000, G: 'SAR' }, rawData: ['2.1.2', 'Excavation rock', 500, 'M3', 120, 60000, 'SAR'] },
          { rowIndex: 8, cells: { A: '2.1.3', B: 'Backfilling approved material', C: 1800, D: 'M3', E: 35, F: 63000, G: 'SAR' }, rawData: ['2.1.3', 'Backfilling approved material', 1800, 'M3', 35, 63000, 'SAR'] },
          { rowIndex: 9, cells: { A: '2.1.4', B: 'Dewatering daywork', C: 100, D: 'HR', E: 350, F: 35000, G: 'SAR' }, rawData: ['2.1.4', 'Dewatering daywork', 100, 'HR', 350, 35000, 'SAR'] },
          { rowIndex: 10, cells: { A: '2.2.1', B: 'Concrete Grade 40 foundations', C: 350, D: 'M3', E: 850, F: 297500, G: 'SAR' }, rawData: ['2.2.1', 'Concrete Grade 40 foundations', 350, 'M3', 850, 297500, 'SAR'] },
          { rowIndex: 11, cells: { A: 'EXT-001', B: 'Additional equipment rental', C: 1, D: 'LS', E: 25000, F: 25000, G: 'SAR' }, rawData: ['EXT-001', 'Additional equipment rental', 1, 'LS', 25000, 25000, 'SAR'] },
        ];

        const result: ParseResult = {
          success: true,
          filename: file.name,
          totalRows: mockRows.length,
          previewRows: mockRows.slice(0, 10),
          detectedColumns: ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        };

        return result;
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
   * Match bidder items to BOQ items
   */
  matchToBoq(
    tenderId: number,
    bidId: number,
    parsedRows: ParsedExcelRow[],
    mappings: ColumnMapping[]
  ): Observable<MatchResult> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(2000),
      map(() => {
        const items: MatchedItem[] = [];
        let exactMatches = 0;
        let fuzzyMatches = 0;
        let unmatchedItems = 0;
        let extraItems = 0;

        // Get field mappings
        const fieldMap: Record<string, string> = {};
        mappings.forEach(m => {
          if (m.targetField && m.targetField !== 'ignore') {
            fieldMap[m.targetField] = m.excelColumn;
          }
        });

        parsedRows.forEach((row, index) => {
          const itemNumber = String(row.cells[fieldMap['item_number']] || '');
          const description = String(row.cells[fieldMap['description']] || '');
          const quantity = Number(row.cells[fieldMap['quantity']] || 0);
          const uom = String(row.cells[fieldMap['uom']] || '');
          const unitRate = Number(row.cells[fieldMap['unit_rate']] || 0);
          const amount = Number(row.cells[fieldMap['amount']] || quantity * unitRate);
          const currency = String(row.cells[fieldMap['currency']] || 'SAR');

          // Try to match with BOQ
          let matchType: MatchType = 'unmatched';
          let boqItem = null;
          let confidenceScore = 0;

          // Exact match by item number
          boqItem = this.mockBoqItems.find(b => b.itemNumber === itemNumber);
          if (boqItem) {
            matchType = 'exact';
            confidenceScore = 100;
            exactMatches++;
          } else {
            // Fuzzy match by description
            const fuzzyMatch = this.findFuzzyMatch(description, itemNumber);
            if (fuzzyMatch) {
              boqItem = fuzzyMatch.item;
              matchType = 'fuzzy';
              confidenceScore = fuzzyMatch.score;
              fuzzyMatches++;
            } else if (itemNumber.startsWith('EXT') || itemNumber.startsWith('ADD')) {
              // Extra item
              matchType = 'extra';
              extraItems++;
            } else {
              unmatchedItems++;
            }
          }

          items.push({
            bidderItemId: `bid-${index}`,
            bidderItemNumber: itemNumber,
            bidderDescription: description,
            bidderQuantity: quantity,
            bidderUom: uom,
            bidderUnitRate: unitRate,
            bidderAmount: amount,
            bidderCurrency: currency,
            matchType,
            boqItemId: boqItem?.id,
            boqItemNumber: boqItem?.itemNumber,
            boqDescription: boqItem?.description,
            boqQuantity: boqItem?.quantity,
            boqUom: boqItem?.uom,
            confidenceScore: matchType !== 'exact' ? confidenceScore : undefined,
            matchReason: matchType === 'fuzzy' ? 'Matched by description similarity' : undefined,
            isIncluded: matchType !== 'extra',
            manuallyMatched: false
          });
        });

        return {
          exactMatches,
          fuzzyMatches,
          unmatchedItems,
          extraItems,
          items
        };
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to match items');
        return throwError(() => error);
      })
    );
  }

  private findFuzzyMatch(description: string, itemNumber: string): { item: any; score: number } | null {
    if (!description) return null;

    const descLower = description.toLowerCase();
    let bestMatch: { item: any; score: number } | null = null;

    for (const boqItem of this.mockBoqItems) {
      const boqDescLower = boqItem.description.toLowerCase();

      // Simple word overlap scoring
      const descWords = descLower.split(/\s+/).filter(w => w.length > 3);
      const boqWords = boqDescLower.split(/\s+/).filter(w => w.length > 3);

      let matchCount = 0;
      descWords.forEach(word => {
        if (boqWords.some(bw => bw.includes(word) || word.includes(bw))) {
          matchCount++;
        }
      });

      const score = Math.round((matchCount / Math.max(descWords.length, boqWords.length)) * 100);

      if (score >= 60 && (!bestMatch || score > bestMatch.score)) {
        bestMatch = { item: boqItem, score };
      }
    }

    return bestMatch;
  }

  /**
   * Get available BOQ items for manual matching
   */
  getBoqItemsForMatching(tenderId: number): Observable<any[]> {
    return of(this.mockBoqItems).pipe(delay(300));
  }

  /**
   * Normalize currency and UOM
   */
  normalize(
    tenderId: number,
    matchedItems: MatchedItem[],
    baseCurrency: string = 'SAR'
  ): Observable<NormalizationResult> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(1000),
      map(() => {
        // Detect currency from items
        const currencies = [...new Set(matchedItems.map(i => i.bidderCurrency).filter(Boolean))];
        const detectedCurrency = currencies[0] || 'SAR';

        const fxRate = detectedCurrency === baseCurrency
          ? 1.0
          : (DEFAULT_FX_RATES[baseCurrency] || 1) / (DEFAULT_FX_RATES[detectedCurrency] || 1);

        const currency: CurrencyNormalization = {
          detectedCurrency,
          baseCurrency,
          fxRate: Math.round(fxRate * 10000) / 10000,
          canConvert: true
        };

        // Check UOM mismatches
        const uomMismatches: UomMismatch[] = [];
        matchedItems.forEach(item => {
          if (item.boqUom && item.bidderUom && item.boqUom !== item.bidderUom) {
            const factor = this.getUomConversionFactor(item.bidderUom, item.boqUom);
            uomMismatches.push({
              itemId: item.bidderItemId,
              itemNumber: item.bidderItemNumber,
              bidderUom: item.bidderUom,
              masterUom: item.boqUom,
              conversionFactor: factor,
              canConvert: factor !== null,
              autoConvert: factor !== null,
              markAsNonComparable: factor === null
            });
          }
        });

        // Create normalized items
        const normalizedItems: NormalizedBidItem[] = matchedItems.map(item => {
          const mismatch = uomMismatches.find(m => m.itemId === item.bidderItemId);
          const isComparable = !mismatch || (mismatch.canConvert && mismatch.autoConvert);

          let normalizedRate = item.bidderUnitRate * fxRate;
          if (mismatch?.conversionFactor) {
            normalizedRate *= mismatch.conversionFactor;
          }

          return {
            bidderItemId: item.bidderItemId,
            boqItemId: item.boqItemId || null,
            itemNumber: item.bidderItemNumber,
            description: item.bidderDescription,
            quantity: item.bidderQuantity,
            uom: item.bidderUom,
            unitRate: item.bidderUnitRate,
            amount: item.bidderAmount,
            originalCurrency: item.bidderCurrency || detectedCurrency,
            normalizedUnitRate: normalizedRate,
            normalizedAmount: normalizedRate * item.bidderQuantity,
            isComparable,
            isExtra: item.matchType === 'extra',
            matchType: item.matchType
          };
        });

        return {
          currency,
          uomMismatches,
          normalizedItems
        };
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to normalize data');
        return throwError(() => error);
      })
    );
  }

  private getUomConversionFactor(fromUom: string, toUom: string): number | null {
    // Common conversions
    const conversions: Record<string, Record<string, number>> = {
      'M': { 'LM': 1, 'CM': 0.01 },
      'LM': { 'M': 1 },
      'M2': { 'SF': 0.0929 },
      'M3': { 'CF': 0.0283 },
      'KG': { 'MT': 0.001, 'LB': 2.205 },
      'MT': { 'KG': 1000 }
    };

    if (fromUom === toUom) return 1;
    return conversions[fromUom]?.[toUom] || null;
  }

  /**
   * Validate items before import
   */
  validate(normalizedItems: NormalizedBidItem[]): Observable<ValidationResult> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(800),
      map(() => {
        const issues: ValidationIssue[] = [];
        let validCount = 0;
        let warningCount = 0;
        let errorCount = 0;

        normalizedItems.forEach(item => {
          // Check for errors
          if (item.unitRate <= 0) {
            issues.push({
              itemId: item.bidderItemId,
              itemNumber: item.itemNumber,
              field: 'unitRate',
              severity: 'error',
              message: 'Unit rate must be greater than zero',
              canProceed: false
            });
            errorCount++;
          } else if (!item.boqItemId && !item.isExtra) {
            issues.push({
              itemId: item.bidderItemId,
              itemNumber: item.itemNumber,
              field: 'match',
              severity: 'warning',
              message: 'Item not matched to BOQ - will be marked as non-comparable',
              canProceed: true
            });
            warningCount++;
          } else if (!item.isComparable) {
            issues.push({
              itemId: item.bidderItemId,
              itemNumber: item.itemNumber,
              field: 'uom',
              severity: 'warning',
              message: 'UOM mismatch - item marked as non-comparable',
              canProceed: true
            });
            warningCount++;
          } else {
            validCount++;
          }

          // Check for warnings
          if (item.quantity === 0) {
            issues.push({
              itemId: item.bidderItemId,
              itemNumber: item.itemNumber,
              field: 'quantity',
              severity: 'warning',
              message: 'Quantity is zero',
              canProceed: true
            });
          }
        });

        return {
          isValid: errorCount === 0,
          validItemCount: validCount,
          warningCount,
          errorCount,
          issues
        };
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
   * Execute the import
   */
  executeImport(request: BidImportRequest): Observable<BidImportResponse> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(2000),
      map(() => {
        const validItems = request.items.filter(i =>
          i.unitRate > 0 && (i.boqItemId || i.isExtra)
        );
        const skippedItems = request.items.length - validItems.length;

        const totalAmount = validItems.reduce((sum, item) =>
          sum + item.normalizedAmount, 0
        );

        return {
          success: true,
          importedCount: validItems.length,
          skippedCount: skippedItems,
          errorCount: 0,
          totalAmount: Math.round(totalAmount * 100) / 100,
          currency: request.currency.baseCurrency
        };
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
