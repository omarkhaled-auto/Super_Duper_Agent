/**
 * Clarification Model Interfaces
 * Defines the data structures for clarifications, RFIs, and Q&A bulletins
 */

export type ClarificationStatus =
  | 'draft'
  | 'submitted'
  | 'under_review'
  | 'answered'
  | 'published'
  | 'rejected';

export type ClarificationPriority = 'low' | 'medium' | 'high' | 'urgent';

export type ClarificationSource = 'bidder' | 'internal' | 'addendum';

export interface Clarification {
  id: number;
  tenderId: number;
  referenceNumber: string;
  subject: string;
  question: string;
  answer?: string;
  status: ClarificationStatus;
  priority: ClarificationPriority;
  source: ClarificationSource;

  // Relationships
  bidderId?: number;
  bidderName?: string;
  relatedBoqSectionId?: number | null;
  relatedBoqSectionTitle?: string;
  bulletinId?: number;
  bulletinNumber?: string;

  // Attachments
  attachments?: ClarificationAttachment[];

  // Dates
  submittedAt?: Date | string;
  answeredAt?: Date | string;
  publishedAt?: Date | string;
  dueDate?: Date | string | null;
  createdAt: Date | string;
  updatedAt: Date | string;

  // Users
  submittedById?: number;
  submittedByName?: string;
  answeredById?: number;
  answeredByName?: string;
}

export interface ClarificationAttachment {
  id: number;
  clarificationId: number;
  fileName: string;
  fileSize: number;
  mimeType: string;
  url: string;
  uploadedAt: Date | string;
  uploadedById: number;
  uploadedByName?: string;
}

export interface ClarificationBulletin {
  id: number;
  tenderId: number;
  bulletinNumber: string;
  issueDate: Date | string;
  title?: string;
  introduction?: string;
  closingNotes?: string;
  clarificationIds: number[];
  clarifications?: Clarification[];
  status: 'draft' | 'published';
  publishedAt?: Date | string;
  publishedById?: number;
  publishedByName?: string;
  pdfUrl?: string;
  createdAt: Date | string;
  updatedAt: Date | string;
}

export interface CreateClarificationDto {
  tenderId: number;
  subject: string;
  question: string;
  priority?: ClarificationPriority;
  source: ClarificationSource;
  relatedBoqSectionId?: number;
  dueDate?: Date | string;
  attachmentIds?: number[];
}

export interface UpdateClarificationDto {
  subject?: string;
  question?: string;
  answer?: string;
  priority?: ClarificationPriority;
  relatedBoqSectionId?: number | null;
  dueDate?: Date | string | null;
}

export interface AnswerClarificationDto {
  answer: string;
  attachmentIds?: number[];
}

export interface CreateBulletinDto {
  tenderId: number;
  bulletinNumber: string;
  issueDate: Date | string;
  title?: string;
  introduction?: string;
  closingNotes?: string;
  clarificationIds: number[];
}

export interface UpdateBulletinDto extends Partial<Omit<CreateBulletinDto, 'tenderId'>> {}

export interface ClarificationFilterParams {
  search?: string;
  status?: ClarificationStatus | ClarificationStatus[];
  source?: ClarificationSource | ClarificationSource[];
  priority?: ClarificationPriority | ClarificationPriority[];
  boqSectionId?: number;
  bidderId?: number;
  dateFrom?: string;
  dateTo?: string;
}

export interface ClarificationSummary {
  total: number;
  byStatus: Record<ClarificationStatus, number>;
  byPriority: Record<ClarificationPriority, number>;
  bySource: Record<ClarificationSource, number>;
  pendingAnswers: number;
  averageResponseTime?: number; // in hours
}

// Status configuration for UI display
export const CLARIFICATION_STATUS_CONFIG: Record<ClarificationStatus, {
  label: string;
  severity: 'secondary' | 'success' | 'info' | 'warn' | 'danger' | 'contrast';
  icon: string;
  description: string;
}> = {
  draft: {
    label: 'Draft',
    severity: 'secondary',
    icon: 'pi-file-edit',
    description: 'Internal RFI not yet submitted'
  },
  submitted: {
    label: 'Submitted',
    severity: 'info',
    icon: 'pi-send',
    description: 'Question submitted, awaiting review'
  },
  under_review: {
    label: 'Under Review',
    severity: 'warn',
    icon: 'pi-clock',
    description: 'Being reviewed by tender team'
  },
  answered: {
    label: 'Answered',
    severity: 'success',
    icon: 'pi-check-circle',
    description: 'Answer provided, pending publication'
  },
  published: {
    label: 'Published',
    severity: 'contrast',
    icon: 'pi-globe',
    description: 'Published in Q&A bulletin'
  },
  rejected: {
    label: 'Rejected',
    severity: 'danger',
    icon: 'pi-times-circle',
    description: 'Question rejected or not applicable'
  }
};

export const CLARIFICATION_PRIORITY_CONFIG: Record<ClarificationPriority, {
  label: string;
  severity: 'secondary' | 'success' | 'info' | 'warn' | 'danger';
  icon: string;
}> = {
  low: { label: 'Low', severity: 'secondary', icon: 'pi-minus' },
  medium: { label: 'Medium', severity: 'info', icon: 'pi-equals' },
  high: { label: 'High', severity: 'warn', icon: 'pi-arrow-up' },
  urgent: { label: 'Urgent', severity: 'danger', icon: 'pi-exclamation-triangle' }
};

export const CLARIFICATION_SOURCE_CONFIG: Record<ClarificationSource, {
  label: string;
  icon: string;
}> = {
  bidder: { label: 'Bidder Question', icon: 'pi-user' },
  internal: { label: 'Internal RFI', icon: 'pi-building' },
  addendum: { label: 'Addendum', icon: 'pi-file-plus' }
};

export const CLARIFICATION_PRIORITY_OPTIONS: { label: string; value: ClarificationPriority }[] = [
  { label: 'Low', value: 'low' },
  { label: 'Medium', value: 'medium' },
  { label: 'High', value: 'high' },
  { label: 'Urgent', value: 'urgent' }
];

export const CLARIFICATION_STATUS_OPTIONS: { label: string; value: ClarificationStatus }[] = [
  { label: 'Draft', value: 'draft' },
  { label: 'Submitted', value: 'submitted' },
  { label: 'Under Review', value: 'under_review' },
  { label: 'Answered', value: 'answered' },
  { label: 'Published', value: 'published' },
  { label: 'Rejected', value: 'rejected' }
];
