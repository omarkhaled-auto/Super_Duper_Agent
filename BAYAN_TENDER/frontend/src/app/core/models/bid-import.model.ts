/**
 * Bid Import Wizard Models
 * Defines interfaces for the 5-step bid import process
 */

/**
 * Column mapping options for Excel parsing
 */
export type BidImportColumnType =
  | 'item_number'
  | 'description'
  | 'quantity'
  | 'uom'
  | 'unit_rate'
  | 'amount'
  | 'currency'
  | 'ignore';

export const BID_IMPORT_COLUMN_OPTIONS: { label: string; value: BidImportColumnType; required: boolean }[] = [
  { label: 'Item Number', value: 'item_number', required: true },
  { label: 'Description', value: 'description', required: false },
  { label: 'Quantity', value: 'quantity', required: false },
  { label: 'UOM', value: 'uom', required: false },
  { label: 'Unit Rate', value: 'unit_rate', required: true },
  { label: 'Amount', value: 'amount', required: false },
  { label: 'Currency', value: 'currency', required: false },
  { label: 'Ignore', value: 'ignore', required: false }
];

/**
 * Step 1: Parse Result
 */
export interface ParsedExcelRow {
  rowIndex: number;
  cells: Record<string, string | number | null>;
  rawData: any[];
}

export interface ParseResult {
  success: boolean;
  filename: string;
  totalRows: number;
  previewRows: ParsedExcelRow[];
  detectedColumns: string[];
  errors?: string[];
}

/**
 * Step 2: Column Mapping
 */
export interface ColumnMapping {
  excelColumn: string;
  targetField: BidImportColumnType | null;
}

export interface MappingValidation {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  missingRequired: BidImportColumnType[];
}

/**
 * Step 3: Match Result
 */
export type MatchType = 'exact' | 'fuzzy' | 'unmatched' | 'extra';

export interface MatchedItem {
  bidderItemId: string;
  bidderItemNumber: string;
  bidderDescription: string;
  bidderQuantity: number;
  bidderUom: string;
  bidderUnitRate: number;
  bidderAmount: number;
  bidderCurrency?: string;

  // BOQ match info
  matchType: MatchType;
  boqItemId?: number;
  boqItemNumber?: string;
  boqDescription?: string;
  boqQuantity?: number;
  boqUom?: string;

  // Fuzzy match info
  confidenceScore?: number;
  matchReason?: string;

  // User decision
  isIncluded: boolean;
  manuallyMatched?: boolean;
}

export interface MatchResult {
  exactMatches: number;
  fuzzyMatches: number;
  unmatchedItems: number;
  extraItems: number;
  items: MatchedItem[];
}

/**
 * Step 4: Normalization
 */
export interface CurrencyNormalization {
  detectedCurrency: string;
  baseCurrency: string;
  fxRate: number;
  canConvert: boolean;
}

export interface UomMismatch {
  itemId: string;
  itemNumber: string;
  bidderUom: string;
  masterUom: string;
  conversionFactor: number | null;
  canConvert: boolean;
  autoConvert: boolean;
  markAsNonComparable: boolean;
}

export interface NormalizationResult {
  currency: CurrencyNormalization;
  uomMismatches: UomMismatch[];
  normalizedItems: NormalizedBidItem[];
}

export interface NormalizedBidItem {
  bidderItemId: string;
  boqItemId: number | null;
  itemNumber: string;
  description: string;
  quantity: number;
  uom: string;
  unitRate: number;
  amount: number;
  originalCurrency: string;
  normalizedUnitRate: number;
  normalizedAmount: number;
  isComparable: boolean;
  isExtra: boolean;
  matchType: MatchType;
}

/**
 * Step 5: Validation
 */
export type ValidationSeverity = 'error' | 'warning' | 'info';

export interface ValidationIssue {
  itemId: string;
  itemNumber: string;
  field: string;
  severity: ValidationSeverity;
  message: string;
  canProceed: boolean;
}

export interface ValidationResult {
  isValid: boolean;
  validItemCount: number;
  warningCount: number;
  errorCount: number;
  issues: ValidationIssue[];
}

/**
 * Final Import
 */
export interface BidImportRequest {
  bidId: number;
  tenderId: number;
  items: NormalizedBidItem[];
  currency: CurrencyNormalization;
  includeExtras: boolean;
}

export interface BidImportResponse {
  success: boolean;
  importedCount: number;
  skippedCount: number;
  errorCount: number;
  totalAmount: number;
  currency: string;
  errors?: string[];
}

/**
 * Wizard State
 */
export interface BidImportWizardState {
  currentStep: number;
  bidId: number;
  tenderId: number;
  filename: string;

  // Step 1 data
  parseResult: ParseResult | null;

  // Step 2 data
  columnMappings: ColumnMapping[];
  mappingValidation: MappingValidation | null;

  // Step 3 data
  matchResult: MatchResult | null;

  // Step 4 data
  normalizationResult: NormalizationResult | null;

  // Step 5 data
  validationResult: ValidationResult | null;

  // Processing states
  isProcessing: boolean;
  error: string | null;
}

/**
 * Currency options commonly used
 */
export const CURRENCY_OPTIONS: { label: string; value: string; symbol: string }[] = [
  { label: 'Saudi Riyal', value: 'SAR', symbol: 'ر.س' },
  { label: 'UAE Dirham', value: 'AED', symbol: 'د.إ' },
  { label: 'US Dollar', value: 'USD', symbol: '$' },
  { label: 'Euro', value: 'EUR', symbol: '€' },
  { label: 'British Pound', value: 'GBP', symbol: '£' },
  { label: 'Kuwaiti Dinar', value: 'KWD', symbol: 'د.ك' },
  { label: 'Bahraini Dinar', value: 'BHD', symbol: 'د.ب' },
  { label: 'Omani Rial', value: 'OMR', symbol: 'ر.ع' },
  { label: 'Qatari Riyal', value: 'QAR', symbol: 'ر.ق' },
  { label: 'Egyptian Pound', value: 'EGP', symbol: 'ج.م' }
];

/**
 * Default FX rates (for demo purposes)
 */
export const DEFAULT_FX_RATES: Record<string, number> = {
  'SAR': 1.0,
  'AED': 0.98,
  'USD': 3.75,
  'EUR': 4.05,
  'GBP': 4.72,
  'KWD': 12.22,
  'BHD': 9.95,
  'OMR': 9.74,
  'QAR': 1.03,
  'EGP': 0.08
};
