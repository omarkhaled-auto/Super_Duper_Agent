/**
 * BOQ (Bill of Quantities) Model Interfaces
 * Defines the data structures for BOQ sections, items, and tree nodes
 */

export type BoqItemType = 'base' | 'alternate' | 'provisional_sum' | 'daywork';

export interface BoqSection {
  id: number;
  tenderId: number;
  parentSectionId?: number | null;
  sectionNumber: string;
  title: string;
  description?: string;
  sortOrder: number;
  createdAt: Date | string;
  updatedAt: Date | string;
  // Computed fields
  itemCount?: number;
  totalValue?: number;
}

export interface BoqItem {
  id: number;
  tenderId: number;
  sectionId: number;
  itemNumber: string;
  description: string;
  quantity: number;
  uom: string; // Unit of Measure
  type: BoqItemType;
  notes?: string;
  unitRate?: number;
  totalAmount?: number;
  sortOrder: number;
  createdAt: Date | string;
  updatedAt: Date | string;
}

export interface BoqTreeNode {
  key: string;
  data: BoqSection | BoqItem;
  type: 'section' | 'item';
  children?: BoqTreeNode[];
  expanded?: boolean;
  // For display
  itemNumber?: string;
  description?: string;
  quantity?: number | null;
  uom?: string;
  itemType?: BoqItemType | null;
}

export interface CreateBoqSectionDto {
  tenderId: number;
  parentSectionId?: number | null;
  sectionNumber: string;
  title: string;
  description?: string;
}

export interface UpdateBoqSectionDto extends Partial<Omit<CreateBoqSectionDto, 'tenderId'>> {}

export interface CreateBoqItemDto {
  tenderId: number;
  sectionId: number;
  itemNumber: string;
  description: string;
  quantity: number;
  uom: string;
  type: BoqItemType;
  notes?: string;
}

export interface UpdateBoqItemDto extends Partial<Omit<CreateBoqItemDto, 'tenderId'>> {}

export interface BoqImportMapping {
  itemNumber?: string;
  description?: string;
  quantity?: string;
  uom?: string;
  type?: string;
  notes?: string;
  sectionNumber?: string;
  sectionTitle?: string;
}

export interface BoqImportRow {
  rowNumber: number;
  data: Record<string, any>;
  mappedData?: Partial<BoqItem & BoqSection>;
  status: 'valid' | 'warning' | 'error';
  errors?: string[];
  warnings?: string[];
}

export interface BoqImportResult {
  totalRows: number;
  validRows: number;
  warningRows: number;
  errorRows: number;
  rows: BoqImportRow[];
  detectedSections: string[];
}

export interface BoqExportOptions {
  columns: {
    section: boolean;
    itemNumber: boolean;
    description: boolean;
    quantity: boolean;
    uom: boolean;
    notes: boolean;
    unitRate: boolean;
    totalAmount: boolean;
  };
  lockColumns: boolean;
  includeInstructions: boolean;
  language: 'en' | 'ar' | 'both';
}

export interface BoqSummary {
  totalSections: number;
  totalSubsections: number;
  totalItems: number;
  itemsByType: Record<BoqItemType, number>;
}

// Dropdown options
export const UOM_OPTIONS: { label: string; value: string }[] = [
  { label: 'Numbers (nos)', value: 'nos' },
  { label: 'Lump Sum (LS)', value: 'LS' },
  { label: 'Square Meter (m2)', value: 'm2' },
  { label: 'Cubic Meter (m3)', value: 'm3' },
  { label: 'Linear Meter (lm)', value: 'lm' },
  { label: 'Kilogram (kg)', value: 'kg' },
  { label: 'Metric Ton (ton)', value: 'ton' },
  { label: 'Meter (m)', value: 'm' },
  { label: 'Day (day)', value: 'day' },
  { label: 'Week (week)', value: 'week' },
  { label: 'Month (month)', value: 'month' },
  { label: 'Set (set)', value: 'set' },
  { label: 'Lot (lot)', value: 'lot' },
  { label: 'Liter (ltr)', value: 'ltr' },
  { label: 'Square Foot (sqft)', value: 'sqft' },
  { label: 'Percentage (%)', value: '%' }
];

export const BOQ_ITEM_TYPE_OPTIONS: { label: string; value: BoqItemType; description: string }[] = [
  { label: 'Base', value: 'base', description: 'Standard line item included in base bid' },
  { label: 'Alternate', value: 'alternate', description: 'Optional item for consideration' },
  { label: 'Provisional Sum', value: 'provisional_sum', description: 'Estimated allowance for undefined work' },
  { label: 'Daywork', value: 'daywork', description: 'Work charged on time and materials basis' }
];

export const BOQ_ITEM_TYPE_CONFIG: Record<BoqItemType, { label: string; severity: 'success' | 'info' | 'warn' | 'secondary' }> = {
  base: { label: 'Base', severity: 'success' },
  alternate: { label: 'Alternate', severity: 'info' },
  provisional_sum: { label: 'Provisional Sum', severity: 'warn' },
  daywork: { label: 'Daywork', severity: 'secondary' }
};
