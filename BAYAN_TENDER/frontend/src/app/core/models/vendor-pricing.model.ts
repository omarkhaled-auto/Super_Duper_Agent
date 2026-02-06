/**
 * Vendor pricing dashboard data.
 */
export interface VendorPricingDashboard {
  summary: VendorDashboardSummary;
  topVendors: TopVendor[];
  recentSnapshots: RecentSnapshot[];
  rateTrends: RateTrendDataPoint[];
  tradeBreakdown: TradeBreakdown[];
}

/**
 * Summary statistics for vendor pricing dashboard.
 */
export interface VendorDashboardSummary {
  totalVendors: number;
  totalSnapshots: number;
  totalUniqueItems: number;
  totalBidValue: number;
  averageBidAmount: number;
  snapshotsThisMonth: number;
  newVendorsThisMonth: number;
  defaultCurrency: string;
}

/**
 * Top vendor by pricing volume.
 */
export interface TopVendor {
  bidderId: string;
  bidderName: string;
  tradeSpecialization?: string;
  snapshotCount: number;
  totalBidValue: number;
  averageRateTrend: number;
  trendDirection: 'up' | 'down' | 'stable';
}

/**
 * Recent pricing snapshot.
 */
export interface RecentSnapshot {
  id: string;
  bidderId: string;
  bidderName: string;
  tenderId: string;
  tenderReference: string;
  tenderTitle: string;
  snapshotDate: Date;
  totalBidAmount: number;
  itemCount: number;
  currency: string;
}

/**
 * Data point for rate trend chart.
 */
export interface RateTrendDataPoint {
  date: Date;
  averageRate: number;
  dataPointCount: number;
}

/**
 * Trade breakdown for pie chart.
 */
export interface TradeBreakdown {
  trade: string;
  vendorCount: number;
  totalValue: number;
  percentage: number;
}

/**
 * Vendor rate trends over time.
 */
export interface VendorTrends {
  bidderId: string;
  bidderName: string;
  tradeSpecialization?: string;
  fromDate?: Date;
  toDate?: Date;
  summary: TrendSummary;
  trendPoints: VendorTrendPoint[];
  itemTrends: ItemTrend[];
  tenderParticipation: TenderParticipation[];
}

/**
 * Summary statistics for vendor trends.
 */
export interface TrendSummary {
  totalTenders: number;
  totalItems: number;
  overallAverageRate: number;
  overallPercentageChange: number;
  overallTrendDirection: 'up' | 'down' | 'stable';
  averageVolatility: number;
  totalBidValue: number;
}

/**
 * Single data point in the trend chart.
 */
export interface VendorTrendPoint {
  date: Date;
  tenderReference: string;
  averageRate: number;
  minRate: number;
  maxRate: number;
  totalBidAmount: number;
  itemCount: number;
  currency: string;
  percentageChangeFromPrevious: number;
}

/**
 * Trend data for a specific item.
 */
export interface ItemTrend {
  itemDescription: string;
  uom: string;
  dataPointCount: number;
  averageRate: number;
  minRate: number;
  maxRate: number;
  latestRate: number;
  percentageChange: number;
  trendDirection: 'up' | 'down' | 'stable';
  rateHistory: ItemRatePoint[];
}

/**
 * Single rate data point for an item.
 */
export interface ItemRatePoint {
  date: Date;
  rate: number;
  tenderReference: string;
}

/**
 * Tender participation record.
 */
export interface TenderParticipation {
  tenderId: string;
  tenderReference: string;
  tenderTitle: string;
  submissionDate: Date;
  totalBidAmount: number;
  itemCount: number;
  currency: string;
  averageItemRate: number;
}

/**
 * Vendor list item with pricing data summary.
 */
export interface VendorListItem {
  bidderId: string;
  companyName: string;
  email: string;
  tradeSpecialization?: string;
  isActive: boolean;
  snapshotCount: number;
  latestSnapshotDate?: Date;
  totalBidValue: number;
}

/**
 * Vendor rate item.
 */
export interface VendorItemRate {
  id: string;
  itemDescription: string;
  uom: string;
  rate: number;
  currency: string;
  quantity?: number;
  totalAmount?: number;
  tenderReference: string;
  snapshotDate: Date;
  boqItemId?: string;
}

/**
 * Vendor comparison result.
 */
export interface VendorComparison {
  items: VendorComparisonItem[];
  vendors: VendorComparisonVendor[];
}

/**
 * Vendor in comparison.
 */
export interface VendorComparisonVendor {
  bidderId: string;
  bidderName: string;
}

/**
 * Item in vendor comparison.
 */
export interface VendorComparisonItem {
  itemDescription: string;
  uom: string;
  rates: VendorComparisonRate[];
}

/**
 * Rate for comparison.
 */
export interface VendorComparisonRate {
  bidderId: string;
  rate: number;
  currency: string;
  isLowest: boolean;
  percentageAboveLowest: number;
}
