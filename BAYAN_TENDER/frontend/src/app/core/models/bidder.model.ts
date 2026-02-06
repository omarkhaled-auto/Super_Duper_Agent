/**
 * Prequalification status for bidders
 */
export enum PrequalificationStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected'
}

/**
 * NDA (Non-Disclosure Agreement) status
 */
export enum NdaStatus {
  NOT_SENT = 'not_sent',
  SENT = 'sent',
  SIGNED = 'signed',
  EXPIRED = 'expired'
}

/**
 * Trade specialization categories
 */
export enum TradeSpecialization {
  IT_SERVICES = 'it_services',
  CONSTRUCTION = 'construction',
  CONSULTING = 'consulting',
  SUPPLIES = 'supplies',
  MAINTENANCE = 'maintenance',
  SECURITY = 'security',
  LOGISTICS = 'logistics',
  HEALTHCARE = 'healthcare',
  EDUCATION = 'education',
  FINANCIAL = 'financial',
  ENGINEERING = 'engineering',
  TELECOMMUNICATIONS = 'telecommunications',
  OTHER = 'other'
}

/**
 * Main Bidder interface representing a registered bidder/vendor
 */
export interface Bidder {
  id: number;
  companyNameEn: string;
  companyNameAr?: string;
  email: string;
  phone?: string;
  crNumber?: string; // Commercial Registration Number (unique)
  address?: string;
  tradeSpecializations: TradeSpecialization[];
  prequalificationStatus: PrequalificationStatus;
  ndaStatus: NdaStatus;
  contactPersonName?: string;
  contactPersonEmail?: string;
  contactPersonPhone?: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
  tendersCount?: number; // Number of tenders participated in
  activeTendersCount?: number;
  lastActivityDate?: Date;
}

/**
 * DTO for creating a new bidder
 */
export interface CreateBidderDto {
  companyNameEn: string;
  companyNameAr?: string;
  email: string;
  phone?: string;
  crNumber?: string;
  address?: string;
  tradeSpecializations: TradeSpecialization[];
  prequalificationStatus?: PrequalificationStatus;
  ndaStatus?: NdaStatus;
  contactPersonName?: string;
  contactPersonEmail?: string;
  contactPersonPhone?: string;
}

/**
 * DTO for updating an existing bidder
 */
export interface UpdateBidderDto extends Partial<CreateBidderDto> {
  isActive?: boolean;
}

/**
 * Represents a bidder invited to a specific tender
 */
export interface TenderBidder {
  id: number;
  tenderId: number;
  bidderId: number;
  bidder: Bidder;
  invitedAt: Date;
  invitedBy: number;
  invitationStatus: InvitationStatus;
  invitationSentAt?: Date;
  invitationViewedAt?: Date;
  responseDate?: Date;
  declineReason?: string;
  bidSubmittedAt?: Date;
  bidStatus?: BidStatus;
}

/**
 * Status of invitation sent to bidder
 */
export enum InvitationStatus {
  PENDING = 'pending',
  SENT = 'sent',
  VIEWED = 'viewed',
  ACCEPTED = 'accepted',
  DECLINED = 'declined',
  EXPIRED = 'expired'
}

/**
 * Status of bid submitted by bidder
 */
export enum BidStatus {
  NOT_SUBMITTED = 'not_submitted',
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  UNDER_REVIEW = 'under_review',
  QUALIFIED = 'qualified',
  DISQUALIFIED = 'disqualified',
  AWARDED = 'awarded',
  REJECTED = 'rejected'
}

/**
 * Query parameters for filtering bidders
 */
export interface BidderQueryParams {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  search?: string;
  trade?: TradeSpecialization;
  prequalificationStatus?: PrequalificationStatus;
  isActive?: boolean;
  [key: string]: string | number | boolean | undefined;
}

/**
 * DTO for inviting bidders to a tender
 */
export interface InviteBiddersDto {
  bidderIds: number[];
  customMessage?: string;
}

/**
 * Email template merge fields for bidder invitations
 */
export interface InvitationEmailMergeFields {
  bidderName: string;
  tenderTitle: string;
  deadlineDate: string;
  portalLink: string;
}
