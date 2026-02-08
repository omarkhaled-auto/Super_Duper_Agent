export interface User {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
  lastLogin?: Date;
  avatar?: string;
  phone?: string;
  company?: string;
}

export enum UserRole {
  ADMIN = 'admin',
  TENDER_MANAGER = 'tender_manager',
  COMMERCIAL_ANALYST = 'commercial_analyst',
  TECHNICAL_PANELIST = 'technical_panelist',
  APPROVER = 'approver',
  AUDITOR = 'auditor',
  BIDDER = 'bidder',
  VIEWER = 'viewer'
}

/**
 * Maps the numeric role value from the backend API to the frontend UserRole enum.
 * Backend: Admin=0, TenderManager=1, CommercialAnalyst=2, TechnicalPanelist=3,
 *          Approver=4, Auditor=5, Bidder=6
 */
const ROLE_MAP: Record<number, UserRole> = {
  0: UserRole.ADMIN,
  1: UserRole.TENDER_MANAGER,
  2: UserRole.COMMERCIAL_ANALYST,
  3: UserRole.TECHNICAL_PANELIST,
  4: UserRole.APPROVER,
  5: UserRole.AUDITOR,
  6: UserRole.BIDDER,
};

const STRING_ROLE_MAP: Record<string, UserRole> = {
  'admin': UserRole.ADMIN,
  'tendermanager': UserRole.TENDER_MANAGER,
  'tender_manager': UserRole.TENDER_MANAGER,
  'commercialanalyst': UserRole.COMMERCIAL_ANALYST,
  'commercial_analyst': UserRole.COMMERCIAL_ANALYST,
  'technicalpanelist': UserRole.TECHNICAL_PANELIST,
  'technical_panelist': UserRole.TECHNICAL_PANELIST,
  'approver': UserRole.APPROVER,
  'auditor': UserRole.AUDITOR,
  'bidder': UserRole.BIDDER,
  'viewer': UserRole.VIEWER,
};

export function mapApiRole(role: number | string): UserRole {
  if (typeof role === 'number') {
    return ROLE_MAP[role] ?? UserRole.BIDDER;
  }
  // Check exact match first (already correct format)
  const values = Object.values(UserRole) as string[];
  if (values.includes(role)) {
    return role as UserRole;
  }
  // Handle PascalCase from backend (e.g. "Admin", "TenderManager")
  const normalized = role.toLowerCase();
  if (STRING_ROLE_MAP[normalized]) {
    return STRING_ROLE_MAP[normalized];
  }
  return UserRole.BIDDER;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface LoginResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface RegisterData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  phone?: string;
  company?: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  newPassword: string;
}
