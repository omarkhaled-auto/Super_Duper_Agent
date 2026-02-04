// =============================================================================
// CashFlow Type Definitions
// Single source of truth for all data models
// All monetary fields are INTEGER CENTS (e.g., $150.00 = 15000)
// =============================================================================

// ---------------------------------------------------------------------------
// Union Types
// ---------------------------------------------------------------------------

export type AccountType = 'checking' | 'savings' | 'credit' | 'investment';

export type TransactionType = 'income' | 'expense' | 'transfer';

export type BudgetPeriod = 'weekly' | 'monthly' | 'yearly';

export type GoalStatus = 'on-track' | 'behind' | 'ahead' | 'completed';

export type RecurrenceFrequency = 'daily' | 'weekly' | 'biweekly' | 'monthly' | 'yearly';

// ---------------------------------------------------------------------------
// Entity Interfaces
// ---------------------------------------------------------------------------

/** Bank/financial account */
export interface Account {
  id: string;
  name: string;
  type: AccountType;
  institution: string;
  balance: number; // cents
  color: string; // hex
  icon: string; // Lucide icon name
  isActive: boolean;
  createdAt: string; // ISO 8601
  updatedAt: string; // ISO 8601
}

/** Individual financial transaction */
export interface Transaction {
  id: string;
  type: TransactionType;
  amount: number; // cents, always positive
  date: string; // ISO 8601 date
  description: string;
  categoryId: string;
  accountId: string;
  notes: string;
  tags: string[];
  isRecurring: boolean;
  recurringId: string | null;
  transferToAccountId: string | null;
  createdAt: string; // ISO 8601
  updatedAt: string; // ISO 8601
}

/** Transaction/budget category */
export interface Category {
  id: string;
  name: string;
  icon: string; // Lucide icon name
  color: string; // hex
  type: 'income' | 'expense';
  isDefault: boolean;
  sortOrder: number;
  createdAt: string; // ISO 8601
  updatedAt: string; // ISO 8601
}

/** Budget limit for a category */
export interface Budget {
  id: string;
  name: string;
  categoryId: string;
  amount: number; // cents - budget limit
  period: BudgetPeriod;
  alertThreshold: number; // 0-100 percentage
  isActive: boolean;
  createdAt: string; // ISO 8601
  updatedAt: string; // ISO 8601
}

/** Savings/financial goal */
export interface Goal {
  id: string;
  name: string;
  description: string;
  targetAmount: number; // cents
  currentAmount: number; // cents
  deadline: string | null; // ISO date or null (open-ended)
  monthlyContribution: number; // cents
  icon: string;
  color: string;
  status: GoalStatus;
  linkedAccountId: string | null;
  createdAt: string; // ISO 8601
  updatedAt: string; // ISO 8601
}

/** Rule for recurring transactions */
export interface RecurringTransaction {
  id: string;
  type: TransactionType;
  amount: number; // cents
  description: string;
  categoryId: string;
  accountId: string;
  frequency: RecurrenceFrequency;
  nextDate: string; // ISO date
  endDate: string | null;
  isActive: boolean;
  transferToAccountId: string | null;
  createdAt: string; // ISO 8601
  updatedAt: string; // ISO 8601
}

/** User application preferences */
export interface UserPreferences {
  theme: 'dark' | 'light' | 'system';
  currency: string;
  locale: string;
  dateFormat: string;
  sidebarCollapsed: boolean;
}

// ---------------------------------------------------------------------------
// Filter / Form Types
// ---------------------------------------------------------------------------

/** Filters for the transactions list */
export interface TransactionFilters {
  search: string;
  type: TransactionType | null;
  categoryId: string | null;
  accountId: string | null;
  dateRange: { start: Date | null; end: Date | null };
  amountRange: { min: number | null; max: number | null };
}
