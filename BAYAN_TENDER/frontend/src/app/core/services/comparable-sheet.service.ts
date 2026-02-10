import { Injectable, inject, signal } from '@angular/core';
import { Observable, map, tap, catchError, throwError } from 'rxjs';
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
   * Get comparable sheet data for a tender.
   * Calls GET /api/tenders/{tenderId}/evaluation/comparable-sheet
   */
  getComparableSheet(tenderId: number): Observable<ComparableSheet> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<any>(`/tenders/${tenderId}/evaluation/comparable-sheet`).pipe(
      map(dto => this.transformComparableSheetDto(dto, tenderId)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load comparable sheet');
        return throwError(() => error);
      })
    );
  }

  /**
   * Export comparable sheet to Excel.
   * Calls GET /api/tenders/{tenderId}/evaluation/comparable-sheet/export-excel
   * Returns a Blob (file download).
   */
  exportToExcel(tenderId: number, options: ComparableSheetExportOptions): Observable<Blob> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.download(`/tenders/${tenderId}/evaluation/comparable-sheet/export-excel`).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to export');
        return throwError(() => error);
      })
    );
  }

  /**
   * Calculate evaluation scores.
   * Calls POST /api/tenders/{tenderId}/evaluation/calculate-combined
   * The backend calculates technical + commercial combined scores.
   */
  calculateScores(
    tenderId: number,
    criteria: EvaluationCriteria[],
    bidderScores: Record<number, Record<number, number>>
  ): Observable<EvaluationSummary> {
    this._isLoading.set(true);
    this._error.set(null);

    // Derive tech/comm weights from criteria if possible
    const techCriteria = criteria.filter(c => c.type === 'technical');
    const priceCriteria = criteria.filter(c => c.type === 'price');
    const techWeight = techCriteria.reduce((sum, c) => sum + c.weight, 0);
    const commWeight = priceCriteria.reduce((sum, c) => sum + c.weight, 0);

    return this.api.post<any>(`/tenders/${tenderId}/evaluation/calculate-combined`, {
      technicalWeight: techWeight || null,
      commercialWeight: commWeight || null
    }).pipe(
      map(dto => {
        // Transform backend CombinedScorecardDto -> frontend EvaluationSummary
        const bidderEvaluations: BidderEvaluationScore[] = (dto.entries || []).map((entry: any) => ({
          bidderId: entry.bidderId,
          bidderName: entry.companyName || '',
          criteriaScores: {} as Record<number, number>,
          weightedScore: entry.combinedScore || 0,
          rank: entry.finalRank || 0
        }));

        const recommendedEntry = (dto.entries || []).find((e: any) => e.isRecommended);

        return {
          tenderId,
          criteria,
          bidderScores: bidderEvaluations,
          recommendedBidderId: recommendedEntry?.bidderId,
          evaluatedAt: dto.calculatedAt ? new Date(dto.calculatedAt) : new Date(),
          evaluatedBy: undefined
        } as EvaluationSummary;
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

  /** Transform backend ComparableSheetDto -> frontend ComparableSheet */
  private transformComparableSheetDto(dto: any, tenderId: number): ComparableSheet {
    // Build bidder columns from backend bidders list
    const bidders: BidderColumn[] = (dto.bidders || []).map((b: any, index: number) => ({
      bidderId: b.id,
      bidId: b.bidSubmissionId,
      bidderName: b.companyName || `Bidder ${index + 1}`,
      currency: 'SAR', // Backend normalizes to base currency
      fxRate: 1.0,
      totalAmount: b.totalNormalizedAmount || 0,
      normalizedTotal: b.totalNormalizedAmount || 0,
      rank: b.rank || (index + 1),
      isLowestBidder: b.rank === 1,
      submissionDate: new Date()
    }));

    // Determine the lowest total for ranking
    const bidderTotals = bidders.map((b: BidderColumn) => b.normalizedTotal);
    const lowestTotal = bidderTotals.length > 0 ? Math.min(...bidderTotals) : 0;
    const highestTotal = bidderTotals.length > 0 ? Math.max(...bidderTotals) : 0;
    const averageTotal = bidderTotals.length > 0
      ? bidderTotals.reduce((a: number, b: number) => a + b, 0) / bidderTotals.length
      : 0;

    // Build item rows from backend items
    const rows: ComparableSheetRow[] = [];
    const sectionMap = new Map<string, boolean>();
    let totalItems = 0;
    let outlierItems = 0;
    let noBidItems = 0;
    let nonComparableItems = 0;

    (dto.items || []).forEach((item: any) => {
      // Add section header if not already added
      const sectionKey = item.sectionId || item.sectionName;
      if (sectionKey && !sectionMap.has(sectionKey)) {
        sectionMap.set(sectionKey, true);
        rows.push({
          rowId: `section-${sectionKey}`,
          rowType: 'section_header',
          sectionId: sectionKey,
          sectionNumber: '',
          sectionTitle: item.sectionName || '',
          itemNumber: '',
          description: item.sectionName || '',
          quantity: null,
          uom: '',
          bidderData: {},
          averageRate: null,
          medianRate: null,
          lowestRate: null,
          highestRate: null,
          standardDeviation: null,
          isExpanded: true
        });
      }

      // Build bidder data for this item
      const bidderData: Record<number, BidderCellData> = {};
      const validRates: number[] = [];
      let hasOutliers = false;
      let hasNoBid = false;
      let hasNonComparable = false;

      (item.bidderRates || []).forEach((rate: any) => {
        const bidderId = rate.bidderId;
        const rateValue = rate.rate;
        const amount = rate.amount;

        let severity: OutlierSeverity = 'normal';
        let deviationPercent: number | null = rate.deviation || null;

        if (rate.isNoBid) {
          severity = 'no_bid';
          hasNoBid = true;
        } else if (rate.isNonComparable) {
          severity = 'non_comparable';
          hasNonComparable = true;
        } else if (rate.isOutlier && rate.severity != null) {
          // Backend OutlierSeverity enum: 0=Low, 1=Medium, 2=High
          const severityMap: Record<number, OutlierSeverity> = { 0: 'normal', 1: 'minor', 2: 'major' };
          severity = typeof rate.severity === 'number'
            ? (severityMap[rate.severity] || 'normal')
            : (rate.severity as OutlierSeverity || 'normal');
          hasOutliers = true;
        }

        if (rateValue != null && !rate.isNoBid && !rate.isNonComparable) {
          validRates.push(rateValue);
        }

        bidderData[bidderId] = {
          bidderId,
          unitRate: rateValue ?? null,
          amount: amount ?? null,
          normalizedRate: rateValue ?? null,
          normalizedAmount: amount ?? null,
          originalCurrency: 'SAR',
          hasDeviation: deviationPercent != null && Math.abs(deviationPercent) >= 10,
          deviationPercent,
          outlierSeverity: severity,
          isLowest: false,
          isHighest: false
        };
      });

      // Compute stats for item row
      const avgRate = validRates.length > 0
        ? validRates.reduce((a, b) => a + b, 0) / validRates.length
        : null;
      const lowestRate = validRates.length > 0 ? Math.min(...validRates) : null;
      const highestRate = validRates.length > 0 ? Math.max(...validRates) : null;

      // Mark lowest/highest
      Object.values(bidderData).forEach(cell => {
        if (cell.unitRate != null) {
          cell.isLowest = cell.unitRate === lowestRate;
          cell.isHighest = cell.unitRate === highestRate;
        }
      });

      // Standard deviation
      let stdDev: number | null = null;
      if (validRates.length > 1 && avgRate != null) {
        const variance = validRates.reduce((sum, r) => sum + Math.pow(r - avgRate, 2), 0) / validRates.length;
        stdDev = Math.sqrt(variance);
      }

      totalItems++;
      if (hasOutliers) outlierItems++;
      if (hasNoBid) noBidItems++;
      if (hasNonComparable) nonComparableItems++;

      rows.push({
        rowId: `item-${item.boqItemId || item.itemNumber}`,
        rowType: 'item',
        sectionId: sectionKey,
        itemNumber: item.itemNumber || '',
        description: item.description || '',
        quantity: item.quantity,
        uom: item.uom || '',
        bidderData,
        averageRate: item.averageRate ?? avgRate,
        medianRate: this.calculateMedian(validRates),
        lowestRate,
        highestRate,
        standardDeviation: stdDev,
        hasOutliers
      });
    });

    // Build section subtotal rows from backend sectionTotals
    (dto.sectionTotals || []).forEach((st: any) => {
      const bidderData: Record<number, BidderCellData> = {};
      const totals = (st.bidderTotals || []).map((bt: any) => bt.total);
      const stLowest = totals.length > 0 ? Math.min(...totals) : 0;
      const stHighest = totals.length > 0 ? Math.max(...totals) : 0;

      (st.bidderTotals || []).forEach((bt: any) => {
        bidderData[bt.bidderId] = {
          bidderId: bt.bidderId,
          unitRate: null,
          amount: bt.total,
          normalizedRate: null,
          normalizedAmount: bt.total,
          originalCurrency: 'SAR',
          hasDeviation: false,
          deviationPercent: null,
          outlierSeverity: 'normal',
          isLowest: bt.total === stLowest,
          isHighest: bt.total === stHighest
        };
      });

      rows.push({
        rowId: `subtotal-${st.sectionId}`,
        rowType: 'section_subtotal',
        sectionId: st.sectionId,
        sectionTitle: st.sectionName,
        itemNumber: '',
        description: `Subtotal - ${st.sectionName}`,
        quantity: null,
        uom: '',
        bidderData,
        averageRate: null,
        medianRate: null,
        lowestRate: null,
        highestRate: null,
        standardDeviation: null
      });
    });

    // Build grand total row
    const grandTotals: Record<number, number> = {};
    const grandBidderData: Record<number, BidderCellData> = {};
    (dto.grandTotals || []).forEach((gt: any) => {
      grandTotals[gt.bidderId] = gt.grandTotal;
      grandBidderData[gt.bidderId] = {
        bidderId: gt.bidderId,
        unitRate: null,
        amount: gt.grandTotal,
        normalizedRate: null,
        normalizedAmount: gt.grandTotal,
        originalCurrency: 'SAR',
        hasDeviation: false,
        deviationPercent: null,
        outlierSeverity: 'normal',
        isLowest: gt.grandTotal === lowestTotal,
        isHighest: gt.grandTotal === highestTotal
      };
    });

    rows.push({
      rowId: 'grand-total',
      rowType: 'grand_total',
      itemNumber: '',
      description: 'GRAND TOTAL',
      quantity: null,
      uom: '',
      bidderData: grandBidderData,
      averageRate: null,
      medianRate: null,
      lowestRate: null,
      highestRate: null,
      standardDeviation: null
    });

    // Build rank row
    const rankBidderData: Record<number, BidderCellData> = {};
    bidders.forEach((bidder: BidderColumn) => {
      rankBidderData[bidder.bidderId] = {
        bidderId: bidder.bidderId,
        unitRate: bidder.rank,
        amount: null,
        normalizedRate: null,
        normalizedAmount: null,
        originalCurrency: 'SAR',
        hasDeviation: false,
        deviationPercent: null,
        outlierSeverity: bidder.isLowestBidder ? 'normal' : 'minor',
        isLowest: bidder.isLowestBidder,
        isHighest: false
      };
    });

    rows.push({
      rowId: 'rank',
      rowType: 'rank',
      itemNumber: '',
      description: 'RANK',
      quantity: null,
      uom: '',
      bidderData: rankBidderData,
      averageRate: null,
      medianRate: null,
      lowestRate: null,
      highestRate: null,
      standardDeviation: null
    });

    // Build sections summary
    const sections: SectionSummary[] = (dto.sectionTotals || []).map((st: any) => {
      const bidderTotals: Record<number, number> = {};
      (st.bidderTotals || []).forEach((bt: any) => {
        bidderTotals[bt.bidderId] = bt.total;
      });
      return {
        sectionId: st.sectionId,
        sectionNumber: '',
        sectionTitle: st.sectionName || '',
        itemCount: 0,
        bidderTotals
      };
    });

    // Build rankings
    const sortedBidders = [...bidders].sort((a, b) => a.normalizedTotal - b.normalizedTotal);
    const rankings: BidderRanking[] = sortedBidders.map((bidder, index) => ({
      bidderId: bidder.bidderId,
      bidderName: bidder.bidderName,
      rank: index + 1,
      totalAmount: bidder.totalAmount,
      normalizedAmount: bidder.normalizedTotal,
      currency: 'SAR',
      deviationFromLowest: bidder.normalizedTotal - lowestTotal,
      deviationPercent: lowestTotal > 0
        ? Math.round(((bidder.normalizedTotal - lowestTotal) / lowestTotal) * 10000) / 100
        : 0
    }));

    // Build statistics
    const comparableItems = totalItems - nonComparableItems;
    const statistics: ComparableSheetStats = {
      totalItems,
      comparableItems,
      nonComparableItems,
      noBidItems,
      outlierItems,
      bidderCount: bidders.length,
      lowestBidderId: sortedBidders[0]?.bidderId || 0,
      lowestTotal,
      highestTotal,
      averageTotal: Math.round(averageTotal * 100) / 100,
      medianTotal: this.calculateMedian(bidderTotals) || 0
    };

    return {
      tenderId,
      tenderTitle: dto.tenderName || '',
      tenderReference: '',
      baseCurrency: 'SAR',
      generatedAt: dto.generatedAt ? new Date(dto.generatedAt) : new Date(),
      bidders,
      rows,
      sections,
      grandTotals,
      rankings,
      statistics,
      minimumBiddersWarning: dto.minimumBiddersWarning || undefined
    };
  }

  private calculateMedian(values: number[]): number | null {
    if (values.length === 0) return null;
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
  }
}
