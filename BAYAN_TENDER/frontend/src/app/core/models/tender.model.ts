export type TenderStatus = 'draft' | 'active' | 'evaluation' | 'awarded' | 'closed' | 'cancelled';
export type TenderType = 'open' | 'selective' | 'negotiated';
export type Currency = 'AED' | 'USD' | 'EUR' | 'GBP' | 'SAR';

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
