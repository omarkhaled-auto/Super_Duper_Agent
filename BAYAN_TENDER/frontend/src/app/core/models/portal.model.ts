/**
 * Portal Model Interfaces
 * Defines the data structures for bidder portal authentication, documents, and bid submission
 * Note: Types are prefixed with "Portal" to avoid conflicts with admin bid.model.ts
 */

// ============================================
// Portal Authentication
// ============================================

export interface PortalLoginCredentials {
  email: string;
  password: string;
  tenderCode?: string;
}

export interface PortalUser {
  id: string | number;
  bidderId: string | number;
  companyName: string;
  companyNameAr?: string;
  email: string;
  contactPersonName?: string;
  phone?: string;
  crNumber?: string;
}

export interface PortalAuthResponse {
  accessToken: string;
  refreshToken: string;
  user?: PortalUser;
  bidder?: {
    id: string;
    companyName: string;
    contactPerson: string;
    email: string;
    phone?: string;
    tradeSpecialization?: string;
    tenderAccess: Array<{ tenderId: string; tenderTitle: string; tenderReference: string; qualificationStatus: string }>;
  };
  accessTokenExpiresAt?: string;
  refreshTokenExpiresAt?: string;
  tokenType?: string;
  tenderId?: number;
}

export interface PortalTenderInfo {
  id: string | number;
  title: string;
  reference: string;
  clientName: string;
  description?: string;
  submissionDeadline: Date | string;
  clarificationDeadline?: Date | string;
  currency: string;
  estimatedValue?: number;
  bidValidityPeriod: number;
  status: string;
}

// ============================================
// Tender Documents
// ============================================

export type DocumentCategory =
  | 'tender_documents'
  | 'drawings'
  | 'specifications'
  | 'boq'
  | 'contract_documents'
  | 'addenda'
  | 'other';

export interface TenderDocument {
  id: string;
  folderPath: string;
  fileName: string;
  fileSizeBytes: number;
  fileSizeDisplay: string;
  contentType: string;
  version: number;
  createdAt: Date | string;
  isLatest: boolean;
  // Computed on frontend
  category?: DocumentCategory;
}

export interface TenderAddendum {
  id: number;
  tenderId: number;
  addendumNumber: number;
  title: string;
  description?: string;
  issueDate: Date | string;
  documents: TenderDocument[];
  acknowledged: boolean;
  acknowledgedAt?: Date | string;
}

export interface DocumentFolder {
  category: DocumentCategory;
  displayName: string;
  icon: string;
  documents: TenderDocument[];
  totalSize: number;
}

export const DOCUMENT_CATEGORY_CONFIG: Record<DocumentCategory, { label: string; icon: string }> = {
  tender_documents: { label: 'Tender Documents', icon: 'pi-file' },
  drawings: { label: 'Drawings', icon: 'pi-image' },
  specifications: { label: 'Specifications', icon: 'pi-list' },
  boq: { label: 'Bill of Quantities', icon: 'pi-table' },
  contract_documents: { label: 'Contract Documents', icon: 'pi-book' },
  addenda: { label: 'Addenda', icon: 'pi-file-plus' },
  other: { label: 'Other Documents', icon: 'pi-folder' }
};

// ============================================
// Portal Clarifications
// ============================================

export interface PortalClarification {
  id: number | string;
  referenceNumber: string;
  subject: string;
  question: string;
  answer?: string;
  status: string;
  statusDisplay?: string;
  submittedAt: Date | string;
  answeredAt?: Date | string;
  relatedBoqSection?: string;
  relatedBoqSectionTitle?: string;
  isAnonymous?: boolean;
}

export interface PortalBulletin {
  id: number;
  bulletinNumber: string;
  title?: string;
  introduction?: string;
  issueDate: Date | string;
  clarifications: PortalClarification[];
  pdfUrl?: string;
}

export interface SubmitQuestionDto {
  tenderId: string | number;
  subject: string;
  question: string;
  relatedBoqSectionId?: number;
  isAnonymous: boolean;
  attachmentIds?: number[];
}

// ============================================
// Bid Submission (Portal-specific types)
// ============================================

/**
 * Portal-specific bid document type (for bidder upload)
 * Distinct from admin BidDocumentType to avoid conflicts
 */
export type PortalBidDocumentType =
  | 'priced_boq'
  | 'methodology'
  | 'team_cvs'
  | 'program'
  | 'hse_plan'
  | 'qa_qc_plan'
  | 'supporting_documents';

/**
 * Portal bid document (bidder's uploaded file)
 */
export interface PortalBidDocument {
  id: number;
  bidId: number;
  documentType: PortalBidDocumentType;
  fileName: string;
  fileSize: number;
  mimeType: string;
  url: string;
  uploadedAt: Date | string;
  isRequired: boolean;
}

export interface PortalBidUploadProgress {
  documentType: PortalBidDocumentType;
  fileName: string;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
}

/**
 * Portal bid submission (bidder's draft/submitted bid)
 */
export interface PortalBidSubmission {
  id: number;
  tenderId: number;
  bidderId: number;
  bidderName: string;
  documents: PortalBidDocument[];
  bidValidityDays: number;
  termsAccepted: boolean;
  termsAcceptedAt?: Date | string;
  status: 'draft' | 'submitted' | 'late_submitted' | 'withdrawn';
  submittedAt?: Date | string;
  receiptNumber?: string;
  isLateSubmission: boolean;
  createdAt: Date | string;
  updatedAt: Date | string;
}

export interface SubmitBidDto {
  tenderId: string | number;
  bidValidityDays: number;
  termsAccepted: boolean;
  documentIds: number[];
}

export interface PortalBidReceipt {
  id: number;
  receiptNumber: string;
  tenderId: number;
  tenderTitle: string;
  tenderReference: string;
  bidderId: number;
  bidderName: string;
  bidderEmail: string;
  submittedAt: Date | string;
  isLateSubmission: boolean;
  documents: {
    type: PortalBidDocumentType;
    fileName: string;
    fileSize: number;
  }[];
  totalFileSize: number;
  pdfUrl?: string;
}

export const PORTAL_BID_DOCUMENT_TYPE_CONFIG: Record<PortalBidDocumentType, {
  label: string;
  icon: string;
  isRequired: boolean;
  acceptedFormats: string[];
  maxSize: number; // in MB
  description: string;
}> = {
  priced_boq: {
    label: 'Priced BOQ',
    icon: 'pi-file-excel',
    isRequired: true,
    acceptedFormats: ['.xlsx', '.xls'],
    maxSize: 50,
    description: 'Complete priced Bill of Quantities in Excel format'
  },
  methodology: {
    label: 'Technical Methodology',
    icon: 'pi-file-pdf',
    isRequired: true,
    acceptedFormats: ['.pdf', '.docx', '.doc'],
    maxSize: 100,
    description: 'Technical approach and methodology document'
  },
  team_cvs: {
    label: 'Team CVs',
    icon: 'pi-users',
    isRequired: true,
    acceptedFormats: ['.pdf', '.docx', '.doc'],
    maxSize: 50,
    description: 'CVs of key personnel proposed for the project'
  },
  program: {
    label: 'Work Program',
    icon: 'pi-calendar',
    isRequired: true,
    acceptedFormats: ['.pdf', '.mpp', '.xlsx', '.xls'],
    maxSize: 50,
    description: 'Project schedule and work program'
  },
  hse_plan: {
    label: 'HSE Plan',
    icon: 'pi-shield',
    isRequired: true,
    acceptedFormats: ['.pdf', '.docx', '.doc'],
    maxSize: 50,
    description: 'Health, Safety and Environment plan'
  },
  qa_qc_plan: {
    label: 'QA/QC Plan',
    icon: 'pi-check-square',
    isRequired: false,
    acceptedFormats: ['.pdf', '.docx', '.doc'],
    maxSize: 50,
    description: 'Quality Assurance and Quality Control plan'
  },
  supporting_documents: {
    label: 'Supporting Documents',
    icon: 'pi-paperclip',
    isRequired: false,
    acceptedFormats: ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.zip'],
    maxSize: 200,
    description: 'Additional supporting documentation'
  }
};

// ============================================
// BOQ Section Options (for clarification dropdown)
// ============================================

export interface BoqSectionOption {
  id: number;
  sectionNumber: string;
  title: string;
}
