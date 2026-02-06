import { Injectable, inject, signal } from '@angular/core';
import { Observable, of, delay, map, tap, catchError, throwError } from 'rxjs';
import { ApiService } from './api.service';
import {
  ComparableSheet,
  ComparableSheetRow,
  BidderColumn,
  BidderCellData,
  SectionSummary,
  BidderRanking,
  ComparableSheetStats,
  ComparableSheetFilters,
  ComparableSheetExportOptions,
  OutlierSeverity,
  OUTLIER_CONFIG,
  EvaluationSummary,
  EvaluationCriteria,
  BidderEvaluationScore,
  DEFAULT_COMPARABLE_SHEET_SETTINGS,
  ComparableSheetSettings
} from '../models/comparable-sheet.model';

@Injectable({
  providedIn: 'root'
})
export class ComparableSheetService {
  private readonly api = inject(ApiService);

  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  /**
   * Get comparable sheet data for a tender
   */
  getComparableSheet(tenderId: number): Observable<ComparableSheet> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(1500),
      map(() => this.generateMockComparableSheet(tenderId)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load comparable sheet');
        return throwError(() => error);
      })
    );
  }

  /**
   * Export comparable sheet to Excel
   */
  exportToExcel(tenderId: number, options: ComparableSheetExportOptions): Observable<Blob> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(2000),
      map(() => {
        // Mock implementation - in production this would generate actual Excel
        return new Blob([''], {
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        });
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to export');
        return throwError(() => error);
      })
    );
  }

  /**
   * Calculate evaluation scores
   */
  calculateScores(
    tenderId: number,
    criteria: EvaluationCriteria[],
    bidderScores: Record<number, Record<number, number>>
  ): Observable<EvaluationSummary> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(1000),
      map(() => {
        const bidderEvaluations: BidderEvaluationScore[] = Object.entries(bidderScores).map(([bidderId, scores]) => {
          let weightedScore = 0;
          criteria.forEach(c => {
            const score = scores[c.id] || 0;
            weightedScore += (score / c.maxScore) * c.weight;
          });

          return {
            bidderId: parseInt(bidderId),
            bidderName: this.getBidderName(parseInt(bidderId)),
            criteriaScores: scores,
            weightedScore: Math.round(weightedScore * 100) / 100,
            rank: 0
          };
        });

        // Calculate ranks
        bidderEvaluations.sort((a, b) => b.weightedScore - a.weightedScore);
        bidderEvaluations.forEach((b, i) => b.rank = i + 1);

        return {
          tenderId,
          criteria,
          bidderScores: bidderEvaluations,
          recommendedBidderId: bidderEvaluations[0]?.bidderId,
          evaluatedAt: new Date(),
          evaluatedBy: 'Admin User'
        };
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to calculate scores');
        return throwError(() => error);
      })
    );
  }

  /**
   * Calculate outlier severity based on deviation from average
   */
  calculateOutlierSeverity(
    value: number,
    average: number,
    settings: ComparableSheetSettings = DEFAULT_COMPARABLE_SHEET_SETTINGS
  ): OutlierSeverity {
    if (value === null || value === 0) return 'no_bid';

    const deviation = Math.abs((value - average) / average) * 100;

    if (deviation >= settings.outlierThresholds.major) return 'major';
    if (deviation >= settings.outlierThresholds.minor) return 'minor';
    return 'normal';
  }

  /**
   * Get cell style class based on outlier severity
   */
  getCellStyleClass(severity: OutlierSeverity): string {
    const config = OUTLIER_CONFIG[severity];
    return `bg-[${config.bgColor}] text-[${config.color}]`;
  }

  /**
   * Filter rows based on criteria
   */
  filterRows(rows: ComparableSheetRow[], filters: ComparableSheetFilters): ComparableSheetRow[] {
    return rows.filter(row => {
      // Section filter
      if (filters.sectionId && row.sectionId !== filters.sectionId) {
        return false;
      }

      // Search filter
      if (filters.searchTerm) {
        const term = filters.searchTerm.toLowerCase();
        const matchesSearch =
          row.itemNumber.toLowerCase().includes(term) ||
          row.description.toLowerCase().includes(term);
        if (!matchesSearch) return false;
      }

      // Outlier filter
      if (filters.showOutliersOnly && !row.hasOutliers) {
        return false;
      }

      // Non-comparable filter
      if (filters.showNonComparableOnly) {
        const hasNonComparable = Object.values(row.bidderData).some(
          cell => cell.outlierSeverity === 'non_comparable'
        );
        if (!hasNonComparable) return false;
      }

      // No bid filter
      if (filters.showNoBidOnly) {
        const hasNoBid = Object.values(row.bidderData).some(
          cell => cell.outlierSeverity === 'no_bid'
        );
        if (!hasNoBid) return false;
      }

      return true;
    });
  }

  clearError(): void {
    this._error.set(null);
  }

  private getBidderName(bidderId: number): string {
    const names: Record<number, string> = {
      1: 'Tech Solutions Ltd',
      2: 'SecureTech Solutions',
      3: 'Global IT Partners',
      4: 'Network Systems LLC',
      5: 'Digital Infrastructure Co'
    };
    return names[bidderId] || `Bidder ${bidderId}`;
  }

  private generateMockComparableSheet(tenderId: number): ComparableSheet {
    // Mock bidders
    const bidders: BidderColumn[] = [
      {
        bidderId: 1,
        bidId: 1,
        bidderName: 'Tech Solutions Ltd',
        bidderNameAr: 'حلول تقنية المحدودة',
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

    // Mock rows
    const rows: ComparableSheetRow[] = [
      // Section 1 Header
      this.createSectionHeader(1, '1', 'General Requirements'),

      // Section 1.1 Header
      this.createSectionHeader(2, '1.1', 'Site Mobilization', 1),

      // Items
      this.createItemRow('1.1.1', 'Site establishment', 1, 'LS', bidders, {
        1: { rate: 45000, amount: 45000 },
        2: { rate: 52000, amount: 52000 },
        3: { rate: 48000, amount: 48000 }
      }),
      this.createItemRow('1.1.2', 'Site security and hoarding', 500, 'LM', bidders, {
        1: { rate: 150, amount: 75000 },
        2: { rate: 165, amount: 82500 },
        3: { rate: 155, amount: 77500 }
      }),
      this.createItemRow('1.1.3', 'Equipment mobilization', 1, 'LS', bidders, {
        1: { rate: 30000, amount: 30000 },
        2: { rate: 28000, amount: 28000 },
        3: { rate: 32000, amount: 32000 }
      }),

      // Section 1.1 Subtotal
      this.createSubtotalRow(2, '1.1', 'Site Mobilization', bidders, {
        1: 150000,
        2: 162500,
        3: 157500
      }),

      // Section 1.2 Header
      this.createSectionHeader(3, '1.2', 'Temporary Facilities', 1),

      this.createItemRow('1.2.1', 'Portable toilets - monthly rental', 12, 'MTH', bidders, {
        1: { rate: 2500, amount: 30000 },
        2: { rate: 2800, amount: 33600 },
        3: { rate: 2600, amount: 31200 }
      }),
      this.createItemRow('1.2.2', 'Temporary power supply', 1, 'LS', bidders, {
        1: { rate: 15000, amount: 15000 },
        2: { rate: 18000, amount: 18000 },
        3: { rate: 16000, amount: 16000 }
      }),

      // Section 1.2 Subtotal
      this.createSubtotalRow(3, '1.2', 'Temporary Facilities', bidders, {
        1: 45000,
        2: 51600,
        3: 47200
      }),

      // Section 1 Subtotal
      this.createSubtotalRow(1, '1', 'General Requirements', bidders, {
        1: 195000,
        2: 214100,
        3: 204700
      }),

      // Section 2 Header
      this.createSectionHeader(4, '2', 'Civil Works'),

      // Section 2.1 Header
      this.createSectionHeader(5, '2.1', 'Earthworks', 4),

      this.createItemRow('2.1.1', 'Excavation in ordinary soil', 2500, 'M3', bidders, {
        1: { rate: 45, amount: 112500 },
        2: { rate: 48, amount: 120000 },
        3: { rate: 46, amount: 115000 }
      }),
      this.createItemRow('2.1.2', 'Excavation in rock', 500, 'M3', bidders, {
        1: { rate: 120, amount: 60000 },
        2: { rate: 180, amount: 90000 }, // Major outlier
        3: { rate: 125, amount: 62500 }
      }),
      this.createItemRow('2.1.3', 'Backfilling with approved material', 1800, 'M3', bidders, {
        1: { rate: 35, amount: 63000 },
        2: { rate: 38, amount: 68400 },
        3: { rate: 36, amount: 64800 }
      }),
      this.createItemRow('2.1.4', 'Dewatering - daywork rate', 100, 'HR', bidders, {
        1: { rate: 350, amount: 35000 },
        2: { rate: null, amount: null }, // No bid
        3: { rate: 380, amount: 38000 }
      }),

      // Section 2.1 Subtotal
      this.createSubtotalRow(5, '2.1', 'Earthworks', bidders, {
        1: 270500,
        2: 278400,
        3: 280300
      }),

      // Grand Total
      this.createGrandTotalRow(bidders, {
        1: 485000,
        2: 512000,
        3: 498500
      }),

      // Rank Row
      this.createRankRow(bidders)
    ];

    // Sections
    const sections: SectionSummary[] = [
      { sectionId: 1, sectionNumber: '1', sectionTitle: 'General Requirements', itemCount: 5, bidderTotals: { 1: 195000, 2: 214100, 3: 204700 } },
      { sectionId: 2, sectionNumber: '1.1', sectionTitle: 'Site Mobilization', itemCount: 3, bidderTotals: { 1: 150000, 2: 162500, 3: 157500 } },
      { sectionId: 3, sectionNumber: '1.2', sectionTitle: 'Temporary Facilities', itemCount: 2, bidderTotals: { 1: 45000, 2: 51600, 3: 47200 } },
      { sectionId: 4, sectionNumber: '2', sectionTitle: 'Civil Works', itemCount: 4, bidderTotals: { 1: 270500, 2: 278400, 3: 280300 } },
      { sectionId: 5, sectionNumber: '2.1', sectionTitle: 'Earthworks', itemCount: 4, bidderTotals: { 1: 270500, 2: 278400, 3: 280300 } }
    ];

    // Rankings
    const rankings: BidderRanking[] = [
      {
        bidderId: 1,
        bidderName: 'Tech Solutions Ltd',
        rank: 1,
        totalAmount: 485000,
        normalizedAmount: 485000,
        currency: 'SAR',
        deviationFromLowest: 0,
        deviationPercent: 0
      },
      {
        bidderId: 3,
        bidderName: 'Global IT Partners',
        rank: 2,
        totalAmount: 498500,
        normalizedAmount: 498500,
        currency: 'SAR',
        deviationFromLowest: 13500,
        deviationPercent: 2.78
      },
      {
        bidderId: 2,
        bidderName: 'SecureTech Solutions',
        rank: 3,
        totalAmount: 512000,
        normalizedAmount: 512000,
        currency: 'SAR',
        deviationFromLowest: 27000,
        deviationPercent: 5.57
      }
    ];

    // Statistics
    const statistics: ComparableSheetStats = {
      totalItems: 9,
      comparableItems: 8,
      nonComparableItems: 0,
      noBidItems: 1,
      outlierItems: 1,
      bidderCount: 3,
      lowestBidderId: 1,
      lowestTotal: 485000,
      highestTotal: 512000,
      averageTotal: 498500,
      medianTotal: 498500
    };

    return {
      tenderId,
      tenderTitle: 'IT Infrastructure Upgrade Project',
      tenderReference: 'TND-2026-001',
      baseCurrency: 'SAR',
      generatedAt: new Date(),
      bidders,
      rows,
      sections,
      grandTotals: { 1: 485000, 2: 512000, 3: 498500 },
      rankings,
      statistics
    };
  }

  private createSectionHeader(sectionId: number, sectionNumber: string, title: string, parentId?: number): ComparableSheetRow {
    return {
      rowId: `section-${sectionId}`,
      rowType: 'section_header',
      sectionId,
      sectionNumber,
      sectionTitle: title,
      itemNumber: sectionNumber,
      description: title,
      quantity: null,
      uom: '',
      bidderData: {},
      averageRate: null,
      medianRate: null,
      lowestRate: null,
      highestRate: null,
      standardDeviation: null,
      isExpanded: true
    };
  }

  private createItemRow(
    itemNumber: string,
    description: string,
    quantity: number,
    uom: string,
    bidders: BidderColumn[],
    rates: Record<number, { rate: number | null; amount: number | null }>
  ): ComparableSheetRow {
    const bidderData: Record<number, BidderCellData> = {};
    const validRates = Object.values(rates).filter(r => r.rate !== null).map(r => r.rate as number);
    const average = validRates.length > 0 ? validRates.reduce((a, b) => a + b, 0) / validRates.length : 0;
    const lowest = validRates.length > 0 ? Math.min(...validRates) : 0;
    const highest = validRates.length > 0 ? Math.max(...validRates) : 0;

    let hasOutliers = false;

    bidders.forEach(bidder => {
      const rateData = rates[bidder.bidderId];
      const rate = rateData?.rate;
      const amount = rateData?.amount;

      let severity: OutlierSeverity = 'normal';
      let deviationPercent: number | null = null;

      if (rate === null) {
        severity = 'no_bid';
      } else if (average > 0) {
        deviationPercent = ((rate - average) / average) * 100;
        if (Math.abs(deviationPercent) >= 50) {
          severity = 'extreme';
          hasOutliers = true;
        } else if (Math.abs(deviationPercent) >= 20) {
          severity = 'major';
          hasOutliers = true;
        } else if (Math.abs(deviationPercent) >= 10) {
          severity = 'minor';
          hasOutliers = true;
        }
      }

      bidderData[bidder.bidderId] = {
        bidderId: bidder.bidderId,
        unitRate: rate,
        amount: amount,
        normalizedRate: rate,
        normalizedAmount: amount,
        originalCurrency: bidder.currency,
        hasDeviation: deviationPercent !== null && Math.abs(deviationPercent) >= 10,
        deviationPercent,
        outlierSeverity: severity,
        isLowest: rate === lowest && rate !== null,
        isHighest: rate === highest && rate !== null
      };
    });

    // Calculate standard deviation
    let stdDev: number | null = null;
    if (validRates.length > 1) {
      const variance = validRates.reduce((sum, rate) => sum + Math.pow(rate - average, 2), 0) / validRates.length;
      stdDev = Math.sqrt(variance);
    }

    return {
      rowId: `item-${itemNumber}`,
      rowType: 'item',
      itemNumber,
      description,
      quantity,
      uom,
      bidderData,
      averageRate: average || null,
      medianRate: this.calculateMedian(validRates),
      lowestRate: lowest || null,
      highestRate: highest || null,
      standardDeviation: stdDev,
      hasOutliers
    };
  }

  private createSubtotalRow(
    sectionId: number,
    sectionNumber: string,
    title: string,
    bidders: BidderColumn[],
    totals: Record<number, number>
  ): ComparableSheetRow {
    const bidderData: Record<number, BidderCellData> = {};
    const values = Object.values(totals);
    const lowest = Math.min(...values);

    bidders.forEach(bidder => {
      const total = totals[bidder.bidderId] || 0;
      bidderData[bidder.bidderId] = {
        bidderId: bidder.bidderId,
        unitRate: null,
        amount: total,
        normalizedRate: null,
        normalizedAmount: total,
        originalCurrency: bidder.currency,
        hasDeviation: false,
        deviationPercent: null,
        outlierSeverity: 'normal',
        isLowest: total === lowest,
        isHighest: total === Math.max(...values)
      };
    });

    return {
      rowId: `subtotal-${sectionId}`,
      rowType: 'section_subtotal',
      sectionId,
      sectionNumber,
      sectionTitle: title,
      itemNumber: '',
      description: `Subtotal - ${title}`,
      quantity: null,
      uom: '',
      bidderData,
      averageRate: null,
      medianRate: null,
      lowestRate: null,
      highestRate: null,
      standardDeviation: null
    };
  }

  private createGrandTotalRow(
    bidders: BidderColumn[],
    totals: Record<number, number>
  ): ComparableSheetRow {
    const bidderData: Record<number, BidderCellData> = {};
    const values = Object.values(totals);
    const lowest = Math.min(...values);

    bidders.forEach(bidder => {
      const total = totals[bidder.bidderId] || 0;
      bidderData[bidder.bidderId] = {
        bidderId: bidder.bidderId,
        unitRate: null,
        amount: total,
        normalizedRate: null,
        normalizedAmount: total,
        originalCurrency: bidder.currency,
        hasDeviation: false,
        deviationPercent: null,
        outlierSeverity: 'normal',
        isLowest: total === lowest,
        isHighest: total === Math.max(...values)
      };
    });

    return {
      rowId: 'grand-total',
      rowType: 'grand_total',
      itemNumber: '',
      description: 'GRAND TOTAL',
      quantity: null,
      uom: '',
      bidderData,
      averageRate: null,
      medianRate: null,
      lowestRate: null,
      highestRate: null,
      standardDeviation: null
    };
  }

  private createRankRow(bidders: BidderColumn[]): ComparableSheetRow {
    const bidderData: Record<number, BidderCellData> = {};

    bidders.forEach(bidder => {
      bidderData[bidder.bidderId] = {
        bidderId: bidder.bidderId,
        unitRate: bidder.rank,
        amount: null,
        normalizedRate: null,
        normalizedAmount: null,
        originalCurrency: bidder.currency,
        hasDeviation: false,
        deviationPercent: null,
        outlierSeverity: bidder.isLowestBidder ? 'normal' : 'minor',
        isLowest: bidder.isLowestBidder,
        isHighest: false
      };
    });

    return {
      rowId: 'rank',
      rowType: 'rank',
      itemNumber: '',
      description: 'RANK',
      quantity: null,
      uom: '',
      bidderData,
      averageRate: null,
      medianRate: null,
      lowestRate: null,
      highestRate: null,
      standardDeviation: null
    };
  }

  private calculateMedian(values: number[]): number | null {
    if (values.length === 0) return null;
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
  }
}
