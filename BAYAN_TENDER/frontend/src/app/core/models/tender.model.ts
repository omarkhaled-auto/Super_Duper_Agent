export type TenderStatus = 'draft' | 'active' | 'evaluation' | 'awarded' | 'closed' | 'cancelled';
export type TenderType = 'open' | 'selective' | 'negotiated';
export type Currency = 'AED' | 'USD' | 'EUR' | 'GBP' | 'SAR';

// PricingLevel is imported from boq.model.ts
import type { PricingLevel } from './boq.model';
export type { PricingLevel };

export const PRICING_LEVEL_OPTIONS = [
  {
    value: 'SubItem' as PricingLevel,
    label: 'Sub-Item Level (Most Detailed)',
    description: 'Bidders price each sub-item (e.g., 1.01.a, 2.02.b). Provides maximum pricing detail.',
    icon: 'pi-sitemap'
  },
  {
    value: 'Item' as PricingLevel,
    label: 'Item/Group Level',
    description: 'Bidders price at item group level (e.g., 1.01, 2.02). Sub-items are for reference only.',
    icon: 'pi-list'
  },
  {
    value: 'Bill' as PricingLevel,
    label: 'Bill Level (Lump Sum)',
    description: 'Bidders provide lump sum per bill/section (e.g., Bill 1, Bill 2). Simplest pricing.',
    icon: 'pi-file'
  }
];

export interface EvaluationCriterion {
  id?: number;
  name: string;
  weight: number;
  description?: string;
  maxScore?: number;
}

export interface TenderDates {
  issueDate: Date | string;
  clarificationDeadline?: Date | string;
  submissionDeadline: Date | string;
  openingDate?: Date | string;
}

export interface Tender {
  id: number;
  title: string;
  reference: string;
  description?: string;
  clientId: number;
  clientName?: string;
  type: TenderType;
  status: TenderStatus;
  currency: Currency;
  estimatedValue?: number;
  bidValidityPeriod?: number; // in days
  dates: TenderDates;
  technicalWeight: number;
  commercialWeight: number;
  evaluationCriteria: EvaluationCriterion[];
  pricingLevel: PricingLevel;
  invitedBiddersCount?: number;
  submittedBidsCount?: number;
  createdAt: Date | string;
  updatedAt: Date | string;
  createdBy?: number;
  createdByName?: string;
}

export interface TenderListItem {
  id: number;
  title: string;
  reference: string;
  clientId: number;
  clientName: string;
  status: TenderStatus;
  submissionDeadline: Date | string;
  estimatedValue?: number;
  currency: Currency;
  invitedBiddersCount: number;
  submittedBidsCount: number;
}

export interface CreateTenderDto {
  title: string;
  reference: string;
  description?: string;
  clientId: number;
  type: TenderType;
  currency: Currency;
  estimatedValue?: number;
  bidValidityPeriod?: number;
  dates: TenderDates;
  technicalWeight: number;
  commercialWeight: number;
  evaluationCriteria: Omit<EvaluationCriterion, 'id'>[];
  pricingLevel?: PricingLevel;
  status?: TenderStatus;
}

export interface UpdateTenderDto extends Partial<CreateTenderDto> {}

export interface TenderFilterParams {
  search?: string;
  status?: TenderStatus | TenderStatus[];
  clientId?: number;
  currency?: Currency;
  dateFrom?: string;
  dateTo?: string;
  type?: TenderType;
}

export interface TenderInvitedBidder {
  id: number;
  tenderId: number;
  bidderId: number;
  bidderName: string;
  bidderEmail: string;
  invitedAt: Date | string;
  status: 'pending' | 'viewed' | 'declined' | 'submitted';
  viewedAt?: Date | string;
  submittedAt?: Date | string;
}

export interface TenderActivity {
  id: number;
  tenderId: number;
  action: string;
  description: string;
  userId: number;
  userName: string;
  timestamp: Date | string;
}

export const DEFAULT_EVALUATION_CRITERIA: Omit<EvaluationCriterion, 'id'>[] = [
  { name: 'Compliance', weight: 20, description: 'Compliance with tender requirements' },
  { name: 'Methodology', weight: 20, description: 'Technical approach and methodology' },
  { name: 'Team CVs', weight: 15, description: 'Qualifications and experience of proposed team' },
  { name: 'Program', weight: 15, description: 'Work program and schedule' },
  { name: 'QA/QC', weight: 15, description: 'Quality assurance and quality control procedures' },
  { name: 'HSE', weight: 15, description: 'Health, safety and environment policies' }
];

export const TENDER_STATUS_CONFIG: Record<TenderStatus, { label: string; severity: 'secondary' | 'success' | 'info' | 'warn' | 'danger' | 'contrast'; icon: string }> = {
  draft: { label: 'Draft', severity: 'secondary', icon: 'pi-file-edit' },
  active: { label: 'Active', severity: 'success', icon: 'pi-check-circle' },
  evaluation: { label: 'Evaluation', severity: 'info', icon: 'pi-chart-bar' },
  awarded: { label: 'Awarded', severity: 'contrast', icon: 'pi-trophy' },
  closed: { label: 'Closed', severity: 'warn', icon: 'pi-lock' },
  cancelled: { label: 'Cancelled', severity: 'danger', icon: 'pi-times-circle' }
};

export const TENDER_TYPE_OPTIONS: { label: string; value: TenderType; description: string }[] = [
  { label: 'Open', value: 'open', description: 'Open to all qualified bidders' },
  { label: 'Selective', value: 'selective', description: 'Invitation-based bidding' },
  { label: 'Negotiated', value: 'negotiated', description: 'Direct negotiation with selected vendors' }
];

export const CURRENCY_OPTIONS: { label: string; value: Currency; symbol: string }[] = [
  { label: 'UAE Dirham (AED)', value: 'AED', symbol: 'AED' },
  { label: 'US Dollar (USD)', value: 'USD', symbol: '$' },
  { label: 'Euro (EUR)', value: 'EUR', symbol: '€' },
  { label: 'British Pound (GBP)', value: 'GBP', symbol: '£' },
  { label: 'Saudi Riyal (SAR)', value: 'SAR', symbol: 'SAR' }
];
