import { APIRequestContext } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:5000/api';

// ---------------------------------------------------------------------------
// Types — aligned with backend DTOs
// ---------------------------------------------------------------------------

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  errors?: string[];
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  user: {
    id: string;
    email: string;
    fullName: string;
    role: string;
  };
}

export interface CreateClientPayload {
  name: string;
  contactPerson?: string;
  email?: string;
  phone?: string;
  address?: string;
}

export interface CreateBidderPayload {
  companyName: string;
  crNumber?: string;
  licenseNumber?: string;
  contactPerson: string;
  email: string;
  phone?: string;
  tradeSpecialization?: string;
}

export interface CreateTenderPayload {
  title: string;
  description?: string;
  clientId: string;
  tenderType: string;
  baseCurrency: string;
  bidValidityDays: number;
  issueDate: string;
  clarificationDeadline: string;
  submissionDeadline: string;
  openingDate: string;
  technicalWeight: number;
  commercialWeight: number;
  evaluationCriteria: EvaluationCriterionPayload[];
}

export interface EvaluationCriterionPayload {
  name: string;
  weightPercentage: number;
  guidanceNotes?: string;
  sortOrder: number;
}

export interface CreateBoqSectionPayload {
  sectionNumber: string;
  title: string;
  sortOrder: number;
  parentSectionId?: string;
}

export interface CreateBoqItemPayload {
  sectionId: string;
  itemNumber: string;
  description: string;
  quantity: number;
  uom: string;
  itemType?: number; // 0 = Base (default)
  notes?: string;
  sortOrder: number;
}

// ---------------------------------------------------------------------------
// Generic helper
// ---------------------------------------------------------------------------

async function apiCall<T>(
  request: APIRequestContext,
  method: 'get' | 'post' | 'put' | 'delete',
  path: string,
  token: string,
  data?: unknown,
): Promise<T> {
  const url = `${API_URL}${path}`;
  const headers = { Authorization: `Bearer ${token}` };

  let res;
  if (method === 'get') {
    res = await request.get(url, { headers });
  } else if (method === 'post') {
    res = await request.post(url, { headers, data });
  } else if (method === 'put') {
    res = await request.put(url, { headers, data });
  } else {
    res = await request.delete(url, { headers });
  }

  if (!res.ok()) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${method.toUpperCase()} ${path} returned ${res.status()}: ${text}`);
  }

  const body: ApiResponse<T> = await res.json();
  if (!body.success) {
    throw new Error(`API ${path} failed: ${body.message ?? 'unknown error'}`);
  }
  return body.data;
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export async function login(
  request: APIRequestContext,
  email: string,
  password: string,
): Promise<AuthTokens> {
  const res = await request.post(`${API_URL}/auth/login`, {
    data: { email, password, rememberMe: true },
  });
  const body: ApiResponse<AuthTokens> = await res.json();
  if (!body.success) {
    throw new Error(`Login failed for ${email}: ${body.message ?? res.status()}`);
  }
  return body.data;
}

// ---------------------------------------------------------------------------
// Clients
// ---------------------------------------------------------------------------

export async function createClient(
  request: APIRequestContext,
  token: string,
  data: CreateClientPayload,
): Promise<Record<string, unknown>> {
  return apiCall(request, 'post', '/clients', token, data);
}

export async function getClients(
  request: APIRequestContext,
  token: string,
): Promise<Record<string, unknown>> {
  return apiCall(request, 'get', '/clients?page=1&pageSize=10', token);
}

// ---------------------------------------------------------------------------
// Bidders
// ---------------------------------------------------------------------------

export async function createBidder(
  request: APIRequestContext,
  token: string,
  data: CreateBidderPayload,
): Promise<Record<string, unknown>> {
  return apiCall(request, 'post', '/bidders', token, data);
}

export async function getBidders(
  request: APIRequestContext,
  token: string,
): Promise<Record<string, unknown>> {
  return apiCall(request, 'get', '/bidders?page=1&pageSize=10', token);
}

// ---------------------------------------------------------------------------
// Tenders
// ---------------------------------------------------------------------------

export async function createTender(
  request: APIRequestContext,
  token: string,
  data: CreateTenderPayload,
): Promise<Record<string, unknown>> {
  return apiCall(request, 'post', '/tenders', token, data);
}

export async function publishTender(
  request: APIRequestContext,
  token: string,
  tenderId: string,
): Promise<Record<string, unknown>> {
  return apiCall(request, 'post', `/tenders/${tenderId}/publish`, token);
}

export async function cancelTender(
  request: APIRequestContext,
  token: string,
  tenderId: string,
  reason?: string,
): Promise<Record<string, unknown>> {
  return apiCall(request, 'post', `/tenders/${tenderId}/cancel`, token, reason ? { reason } : undefined);
}

export async function getNextReference(
  request: APIRequestContext,
  token: string,
): Promise<string> {
  return apiCall(request, 'get', '/tenders/next-reference', token);
}

export async function getTenderById(
  request: APIRequestContext,
  token: string,
  id: string,
): Promise<Record<string, unknown>> {
  return apiCall(request, 'get', `/tenders/${id}`, token);
}

// ---------------------------------------------------------------------------
// BOQ
// ---------------------------------------------------------------------------

export async function createBoqSection(
  request: APIRequestContext,
  token: string,
  tenderId: string,
  data: CreateBoqSectionPayload,
): Promise<Record<string, unknown>> {
  return apiCall(request, 'post', `/tenders/${tenderId}/boq/sections`, token, data);
}

export async function createBoqItem(
  request: APIRequestContext,
  token: string,
  tenderId: string,
  data: CreateBoqItemPayload,
): Promise<Record<string, unknown>> {
  return apiCall(request, 'post', `/tenders/${tenderId}/boq/items`, token, data);
}

// ---------------------------------------------------------------------------
// Bidding
// ---------------------------------------------------------------------------

export async function inviteBidders(
  request: APIRequestContext,
  token: string,
  tenderId: string,
  bidderIds: string[],
): Promise<Record<string, unknown>> {
  // The API expects a direct array of GUIDs, not a wrapper
  return apiCall(request, 'post', `/tenders/${tenderId}/invite`, token, bidderIds);
}

export async function openBids(
  request: APIRequestContext,
  token: string,
  tenderId: string,
): Promise<Record<string, unknown>> {
  return apiCall(request, 'post', `/tenders/${tenderId}/bids/open`, token);
}
