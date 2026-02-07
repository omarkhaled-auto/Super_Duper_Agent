// ============================================================================
// BAYAN Tender E2E Test Data
// Comprehensive test fixtures for all roles, entities, and scenarios
// ============================================================================

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface UserCredentials {
  email: string;
  password: string;
  role: string;
}

export interface EvaluationCriterion {
  name: string;
  weight: number;
  description: string;
}

export interface TenderPayload {
  title: string;
  description: string;
  tenderType: string;
  baseCurrency: string;
  bidValidityDays: number;
  technicalWeight: number;
  commercialWeight: number;
  evaluationCriteria: EvaluationCriterion[];
}

export interface BoqSection {
  number: string;
  title: string;
  description: string;
}

export interface BoqItem {
  sectionNumber: string;
  number: string;
  description: string;
  uom: string;
  quantity: number;
}

// ---------------------------------------------------------------------------
// User credentials for all 7 roles
// ---------------------------------------------------------------------------

export const USERS: Record<string, UserCredentials> = {
  admin: { email: 'admin@bayan.ae', password: 'Bayan@2024', role: 'Admin' },
  tenderManager: { email: 'tendermgr@bayan.ae', password: 'Bayan@2024', role: 'TenderManager' },
  analyst: { email: 'analyst@bayan.ae', password: 'Bayan@2024', role: 'CommercialAnalyst' },
  panelist: { email: 'panelist1@bayan.ae', password: 'Bayan@2024', role: 'Panelist' },
  approver: { email: 'approver@bayan.ae', password: 'Bayan@2024', role: 'Approver' },
  auditor: { email: 'auditor@bayan.ae', password: 'Bayan@2024', role: 'Auditor' },
  bidder: { email: 'bidder@vendor.ae', password: 'Bayan@2024', role: 'Bidder' },
};

// ---------------------------------------------------------------------------
// Sample tender creation payload
// ---------------------------------------------------------------------------

export const SAMPLE_TENDER: TenderPayload = {
  title: 'E2E Test Tender - IT Infrastructure Upgrade',
  description: 'Automated test tender for comprehensive E2E testing',
  tenderType: 'Open',
  baseCurrency: 'AED',
  bidValidityDays: 90,
  technicalWeight: 70,
  commercialWeight: 30,
  evaluationCriteria: [
    { name: 'Technical Approach', weight: 40, description: 'Quality of proposed technical solution' },
    { name: 'Experience', weight: 35, description: 'Relevant project experience' },
    { name: 'Team Composition', weight: 25, description: 'Qualification of proposed team' },
  ],
};

// ---------------------------------------------------------------------------
// Function to generate dates relative to now
// ---------------------------------------------------------------------------

export function generateTenderDates() {
  const now = new Date();
  return {
    issueDate: new Date(now.getTime() + 1 * 24 * 60 * 60 * 1000).toISOString(),
    clarificationDeadline: new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000).toISOString(),
    submissionDeadline: new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    openingDate: new Date(now.getTime() + 31 * 24 * 60 * 60 * 1000).toISOString(),
  };
}

// ---------------------------------------------------------------------------
// Sample BOQ data
// ---------------------------------------------------------------------------

export const SAMPLE_BOQ_SECTIONS: BoqSection[] = [
  { number: '1', title: 'General Requirements', description: 'General project requirements' },
  { number: '2', title: 'Hardware Supply', description: 'Server and networking equipment' },
];

export const SAMPLE_BOQ_ITEMS: BoqItem[] = [
  { sectionNumber: '1', number: '1.1', description: 'Project Management', uom: 'LS', quantity: 1 },
  { sectionNumber: '1', number: '1.2', description: 'Site Survey', uom: 'No', quantity: 5 },
  { sectionNumber: '2', number: '2.1', description: 'Server Rack 42U', uom: 'No', quantity: 3 },
  { sectionNumber: '2', number: '2.2', description: 'Network Switch 48-port', uom: 'No', quantity: 10 },
];

// ---------------------------------------------------------------------------
// Sample clarification data
// ---------------------------------------------------------------------------

export const SAMPLE_CLARIFICATION = {
  subject: 'Server Specifications Clarification',
  question: 'Please clarify the minimum server specifications for the proposed solution.',
  answer: 'The minimum specifications are: 2x Intel Xeon Gold, 256GB RAM, 4TB NVMe SSD.',
};

// ---------------------------------------------------------------------------
// Sample client data
// ---------------------------------------------------------------------------

export const SAMPLE_CLIENT = {
  name: 'E2E Test Ministry',
  nameAr: '\u0648\u0632\u0627\u0631\u0629 \u0627\u0644\u0627\u062e\u062a\u0628\u0627\u0631',
  contactPerson: 'Test Contact',
  email: 'contact@testministry.ae',
  phone: '+971-50-123-4567',
};

// ---------------------------------------------------------------------------
// Sample bidder data
// ---------------------------------------------------------------------------

export const SAMPLE_BIDDER = {
  companyNameEn: 'E2E Test Vendor Corp',
  companyNameAr: '\u0634\u0631\u0643\u0629 \u0628\u0627\u0626\u0639 \u0627\u0644\u0627\u062e\u062a\u0628\u0627\u0631',
  email: 'test@vendor.ae',
  phone: '+971-50-987-6543',
  crNumber: 'CR-2024-E2E-001',
};

// ---------------------------------------------------------------------------
// Invalid credentials for negative tests
// ---------------------------------------------------------------------------

export const INVALID_CREDENTIALS = {
  wrongEmail: 'nonexistent@bayan.ae',
  wrongPassword: 'WrongPassword123!',
  invalidEmail: 'not-an-email',
  shortPassword: '123',
};

// ---------------------------------------------------------------------------
// File paths for uploads (relative to e2e directory)
// ---------------------------------------------------------------------------

export const TEST_FILES = {
  sampleBoq: 'fixtures/files/sample-boq.xlsx',
  sampleBidDocument: 'fixtures/files/sample-bid-document.pdf',
  sampleMethodology: 'fixtures/files/sample-methodology.pdf',
};

// ---------------------------------------------------------------------------
// Route constants
// ---------------------------------------------------------------------------

export const ROUTES = {
  login: '/auth/login',
  forgotPassword: '/auth/forgot-password',
  dashboard: '/dashboard',
  approverDashboard: '/dashboard/approver',
  tenders: '/tenders',
  newTender: '/tenders/new',
  adminUsers: '/admin/users',
  adminClients: '/admin/clients',
  adminBidders: '/admin/bidders',
  adminSettings: '/admin/settings',
  adminAuditLogs: '/admin/audit-logs',
  portalLogin: '/portal/login',
  unauthorized: '/unauthorized',
};
