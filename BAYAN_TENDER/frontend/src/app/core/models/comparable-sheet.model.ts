/**
 * Comparable Sheet Models
 * Defines interfaces for bid comparison/evaluation grid
 */

/**
 * Outlier severity levels
 */
export type OutlierSeverity = 'normal' | 'minor' | 'major' | 'extreme' | 'no_bid' | 'non_comparable';

export const OUTLIER_CONFIG: Record<OutlierSeverity, {
  label: string;
  color: string;
  bgColor: string;
  deviationRange?: string;
}> = {
  normal: {
    label: 'Normal',
    color: '#155724',
    bgColor: '#d4edda',
    deviationRange: '< 10%'
  },
  minor: {
    label: 'Minor Outlier',
    color: '#856404',
    bgColor: '#fff3cd',
    deviationRange: '10-20%'
  },
  major: {
    label: 'Major Outlier',
    color: '#721c24',
    bgColor: '#ffcccc',
    deviationRange: '> 20%'
  },
  extreme: {
    // Merged into major per PRD 3-tier model; kept for backward compatibility
    label: 'Major Outlier',
    color: '#721c24',
    bgColor: '#ffcccc',
    deviationRange: '> 20%'
  },
  no_bid: {
    label: 'No Bid',
    color: '#6c757d',
    bgColor: '#f4f4f5'
  },
  non_comparable: {
    label: 'Non-Comparable',
    color: '#9333ea',
    bgColor: '#faf5ff'
  }
};

/**
 * Bidder column in the comparable sheet
 */
export interface BidderColumn {
  bidderId: number;
  bidId: number;
  bidderName: string;
  bidderNameAr?: string;
  currency: string;
  fxRate: number;
  totalAmount: number;
  normalizedTotal: number;
  rank: number;
  isLowestBidder: boolean;
  submissionDate: Date | string;
}

/**
 * Cell data for a bidder's rate on an item
 */
export interface BidderCellData {
  bidderId: number;
  unitRate: number | null;
  amount: number | null;
  normalizedRate: number | null;
  normalizedAmount: number | null;
  originalCurrency: string;
  hasDeviation: boolean;
  deviationPercent: number | null;
  outlierSeverity: OutlierSeverity;
  isLowest: boolean;
  isHighest: boolean;
  notes?: string;
}

/**
 * Row types in the comparable sheet
 */
export type RowType = 'section_header' | 'item' | 'section_subtotal' | 'grand_total' | 'rank'
  | 'bill_header' | 'item_group_header' | 'item_subtotal' | 'bill_subtotal';

/**
 * Item row in the comparable sheet
 */
export interface ComparableSheetRow {
  rowId: string;
  rowType: RowType;
  sectionId?: number;
  sectionNumber?: string;
  sectionTitle?: string;

  // For items
  itemId?: number;
  itemNumber: string;
  description: string;
  quantity: number | null;
  uom: string;
  itemType?: string;

  // Bidder data (dynamic columns)
  bidderData: Record<number, BidderCellData>;

  // Computed values
  averageRate: number | null;
  medianRate: number | null;
  lowestRate: number | null;
  highestRate: number | null;
  standardDeviation: number | null;

  // Display flags
  isExpanded?: boolean;
  isHighlighted?: boolean;
  hasOutliers?: boolean;
}

/**
 * Section summary
 */
export interface SectionSummary {
  sectionId: number;
  sectionNumber: string;
  sectionTitle: string;
  itemCount: number;
  bidderTotals: Record<number, number>;
}

/**
 * Complete comparable sheet data
 */
export interface ComparableSheet {
  tenderId: number;
  tenderTitle: string;
  tenderReference: string;
  baseCurrency: string;
  generatedAt: Date | string;
  pricingLevel?: 'Bill' | 'Item' | 'SubItem';

  // Bidders (columns)
  bidders: BidderColumn[];

  // Rows
  rows: ComparableSheetRow[];

  // Section summaries
  sections: SectionSummary[];

  // Grand totals per bidder
  grandTotals: Record<number, number>;

  // Rankings
  rankings: BidderRanking[];

  // Statistics
  statistics: ComparableSheetStats;

  // Warning when fewer than 3 bidders
  minimumBiddersWarning?: string;
}

/**
 * Bidder ranking
 */
export interface BidderRanking {
  bidderId: number;
  bidderName: string;
  rank: number;
  totalAmount: number;
  normalizedAmount: number;
  currency: string;
  deviationFromLowest: number;
  deviationPercent: number;
}

/**
 * Overall statistics
 */
export interface ComparableSheetStats {
  totalItems: number;
  comparableItems: number;
  nonComparableItems: number;
  noBidItems: number;
  outlierItems: number;
  bidderCount: number;
  lowestBidderId: number;
  lowestTotal: number;
  highestTotal: number;
  averageTotal: number;
  medianTotal: number;
}

/**
 * Filter options for comparable sheet
 */
export interface ComparableSheetFilters {
  sectionId?: number;
  showOutliersOnly: boolean;
  showNonComparableOnly: boolean;
  showNoBidOnly: boolean;
  searchTerm: string;
  outlierSeverity?: OutlierSeverity[];
}

/**
 * Export options
 */
export interface ComparableSheetExportOptions {
  format: 'xlsx' | 'pdf' | 'csv';
  includeStatistics: boolean;
  includeRankings: boolean;
  highlightOutliers: boolean;
  includeSectionSubtotals: boolean;
  includeColorCoding: boolean;
  language: 'en' | 'ar' | 'both';
}

/**
 * Evaluation score configuration
 */
export interface EvaluationCriteria {
  id: number;
  name: string;
  weight: number;
  type: 'price' | 'technical' | 'delivery' | 'experience' | 'other';
  maxScore: number;
}

/**
 * Bidder evaluation scores
 */
export interface BidderEvaluationScore {
  bidderId: number;
  bidderName: string;
  criteriaScores: Record<number, number>;
  weightedScore: number;
  rank: number;
}

/**
 * Evaluation summary
 */
export interface EvaluationSummary {
  tenderId: number;
  criteria: EvaluationCriteria[];
  bidderScores: BidderEvaluationScore[];
  recommendedBidderId?: number;
  evaluatedAt?: Date | string;
  evaluatedBy?: string;
}

/**
 * Cell tooltip data
 */
export interface CellTooltipData {
  itemNumber: string;
  description: string;
  bidderName: string;
  quantity: number;
  uom: string;
  unitRate: number;
  amount: number;
  currency: string;
  normalizedRate: number;
  averageRate: number;
  deviationPercent: number;
  outlierSeverity: OutlierSeverity;
}

/**
 * Column definitions for AG Grid
 */
export interface ComparableSheetColumnDef {
  field: string;
  headerName: string;
  width?: number;
  minWidth?: number;
  pinned?: 'left' | 'right';
  cellClass?: string | string[];
  headerClass?: string | string[];
  type?: 'numeric' | 'text';
  bidderId?: number;
  isFrozen?: boolean;
}

/**
 * Settings for comparable sheet display
 */
export interface ComparableSheetSettings {
  showQuantityColumn: boolean;
  showUomColumn: boolean;
  showItemTypeColumn: boolean;
  showAverageColumn: boolean;
  showDeviationColumn: boolean;
  highlightLowestBidder: boolean;
  highlightOutliers: boolean;
  outlierThresholds: {
    minor: number;  // default 10
    major: number;  // default 20
  };
  decimalPlaces: number;
  showNormalizedValues: boolean;
}

export const DEFAULT_COMPARABLE_SHEET_SETTINGS: ComparableSheetSettings = {
  showQuantityColumn: true,
  showUomColumn: true,
  showItemTypeColumn: false,
  showAverageColumn: true,
  showDeviationColumn: true,
  highlightLowestBidder: true,
  highlightOutliers: true,
  outlierThresholds: {
    minor: 10,
    major: 20
  },
  decimalPlaces: 2,
  showNormalizedValues: true
};
