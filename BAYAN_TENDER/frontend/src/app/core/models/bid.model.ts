/**
 * Bid Status Types
 */
export type BidStatus =
  | 'submitted'    // Bid received, amounts hidden
  | 'opened'       // Bid opened, amounts visible
  | 'late'         // Submitted after deadline
  | 'imported'     // BOQ imported into system
  | 'disqualified' // Bid disqualified
  | 'accepted'     // Late bid accepted
  | 'rejected';    // Late bid rejected

/**
 * Bid Document Types
 */
export type BidDocumentCategory =
  | 'commercial'   // Priced BOQ
  | 'technical'    // Methodology, CVs, Program, HSE
  | 'supporting';  // Other files

export type BidDocumentType =
  | 'priced_boq'
  | 'methodology'
  | 'team_cvs'
  | 'work_program'
  | 'hse_plan'
  | 'organization_chart'
  | 'equipment_list'
  | 'similar_projects'
  | 'financial_statement'
  | 'bid_bond'
  | 'power_of_attorney'
  | 'other';

/**
 * Bid Document Interface
 */
export interface BidDocument {
  id: number;
  bidId: number;
  filename: string;
  originalFilename: string;
  fileSize: number;
  mimeType: string;
  documentType: BidDocumentType;
  category: BidDocumentCategory;
  uploadedAt: Date | string;
  downloadUrl?: string;
  previewUrl?: string;
  isPreviewable: boolean;
}

/**
 * Bid Summary (after import)
 */
export interface BidSummary {
  totalAmount: number;
  currency: string;
  validityDays: number;
  validUntil: Date | string;
  exceptions?: string[];
  alternativeOffers?: string[];
  discounts?: string;
  paymentTerms?: string;
}

/**
 * Bid Submission Interface
 */
export interface BidSubmission {
  id: number;
  tenderId: number;
  bidderId: number;
  bidderName: string;
  bidderNameAr?: string;
  bidderEmail: string;
  submissionTime: Date | string;
  status: BidStatus;

  // Amount is hidden until opened
  bidAmount?: number;
  currency?: string;

  // Late bid info
  isLate: boolean;
  lateReason?: string;
  lateAcceptedAt?: Date | string;
  lateAcceptedBy?: number;
  lateAcceptedByName?: string;
  lateRejectedAt?: Date | string;
  lateRejectedBy?: number;
  lateRejectedByName?: string;
  lateRejectionReason?: string;

  // Opening info
  openedAt?: Date | string;
  openedBy?: number;
  openedByName?: string;

  // Disqualification info
  disqualifiedAt?: Date | string;
  disqualifiedBy?: number;
  disqualifiedByName?: string;
  disqualificationReason?: string;

  // Import info
  importedAt?: Date | string;
  importedBy?: number;
  importedByName?: string;
  bidSummary?: BidSummary;

  // Documents
  documents: BidDocument[];
  filesCount: number;

  // Metadata
  createdAt: Date | string;
  updatedAt: Date | string;
}

/**
 * Bid List Item (for table display)
 */
export interface BidListItem {
  id: number;
  tenderId: number;
  bidderId: number;
  bidderName: string;
  submissionTime: Date | string;
  status: BidStatus;
  bidAmount?: number;
  currency?: string;
  filesCount: number;
  isLate: boolean;
}

/**
 * Bid Filter Parameters
 */
export interface BidFilterParams {
  status?: BidStatus | BidStatus[];
  isLate?: boolean;
  search?: string;
}

/**
 * Open Bids Response
 */
export interface OpenBidsResponse {
  success: boolean;
  openedCount: number;
  openedAt: Date | string;
  openedBy: string;
}

/**
 * Accept/Reject Late Bid DTO
 */
export interface RejectLateBidDto {
  reason: string;
}

/**
 * Disqualify Bid DTO
 */
export interface DisqualifyBidDto {
  reason: string;
}

/**
 * Bid Statistics
 */
export interface BidStatistics {
  totalBids: number;
  lateBids: number;
  openedBids: number;
  importedBids: number;
  disqualifiedBids: number;
  pendingLateBids: number;
  bidsOpened: boolean;
}

/**
 * Status configuration for display
 */
export const BID_STATUS_CONFIG: Record<BidStatus, {
  label: string;
  severity: 'secondary' | 'success' | 'info' | 'warn' | 'danger' | 'contrast';
  icon: string;
}> = {
  submitted: { label: 'Submitted', severity: 'secondary', icon: 'pi-inbox' },
  opened: { label: 'Opened', severity: 'info', icon: 'pi-eye' },
  late: { label: 'Late', severity: 'warn', icon: 'pi-clock' },
  imported: { label: 'Imported', severity: 'success', icon: 'pi-check-circle' },
  disqualified: { label: 'Disqualified', severity: 'danger', icon: 'pi-times-circle' },
  accepted: { label: 'Accepted', severity: 'success', icon: 'pi-check' },
  rejected: { label: 'Rejected', severity: 'danger', icon: 'pi-ban' }
};

/**
 * Document type labels
 */
export const BID_DOCUMENT_TYPE_LABELS: Record<BidDocumentType, string> = {
  priced_boq: 'Priced BOQ',
  methodology: 'Technical Methodology',
  team_cvs: 'Team CVs',
  work_program: 'Work Program',
  hse_plan: 'HSE Plan',
  organization_chart: 'Organization Chart',
  equipment_list: 'Equipment List',
  similar_projects: 'Similar Projects',
  financial_statement: 'Financial Statement',
  bid_bond: 'Bid Bond',
  power_of_attorney: 'Power of Attorney',
  other: 'Other'
};

/**
 * Document category labels
 */
export const BID_DOCUMENT_CATEGORY_LABELS: Record<BidDocumentCategory, string> = {
  commercial: 'Commercial Documents',
  technical: 'Technical Documents',
  supporting: 'Supporting Documents'
};
