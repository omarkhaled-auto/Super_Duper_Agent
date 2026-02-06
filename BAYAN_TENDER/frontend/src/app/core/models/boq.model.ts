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
    itemNumber: boolean;
    description: boolean;
    quantity: boolean;
    uom: boolean;
    type: boolean;
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
  { label: 'Each (EA)', value: 'EA' },
  { label: 'Lump Sum (LS)', value: 'LS' },
  { label: 'Square Meter (M2)', value: 'M2' },
  { label: 'Cubic Meter (M3)', value: 'M3' },
  { label: 'Linear Meter (LM)', value: 'LM' },
  { label: 'Kilogram (KG)', value: 'KG' },
  { label: 'Metric Ton (MT)', value: 'MT' },
  { label: 'Hour (HR)', value: 'HR' },
  { label: 'Day (DAY)', value: 'DAY' },
  { label: 'Week (WK)', value: 'WK' },
  { label: 'Month (MTH)', value: 'MTH' },
  { label: 'Set (SET)', value: 'SET' },
  { label: 'Lot (LOT)', value: 'LOT' },
  { label: 'Number (NO)', value: 'NO' },
  { label: 'Pair (PR)', value: 'PR' }
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
