export interface SystemSettings {
  general: GeneralSettings;
  tender: TenderSettings;
  notification: NotificationSettings;
  security: SecuritySettings;
}

export interface GeneralSettings {
  siteName: string;
  siteNameAr: string;
  supportEmail: string;
  supportPhone: string;
  defaultLanguage: 'en' | 'ar';
  timezone: string;
  dateFormat: string;
  currency: string;
}

export interface TenderSettings {
  defaultBidValidityDays: number;
  minBidAmount: number;
  maxBidAmount: number;
  allowLateSubmissions: boolean;
  lateSubmissionPenaltyPercent: number;
  requireBankGuarantee: boolean;
  bankGuaranteePercent: number;
  autoExtendDeadline: boolean;
  autoExtendMinutes: number;
}

export interface NotificationSettings {
  emailNotifications: boolean;
  smsNotifications: boolean;
  tenderPublishedNotify: boolean;
  bidReceivedNotify: boolean;
  tenderClosingNotify: boolean;
  closingReminderHours: number;
  awardNotify: boolean;
}

export interface SecuritySettings {
  sessionTimeoutMinutes: number;
  maxLoginAttempts: number;
  lockoutDurationMinutes: number;
  passwordMinLength: number;
  passwordRequireUppercase: boolean;
  passwordRequireLowercase: boolean;
  passwordRequireNumbers: boolean;
  passwordRequireSpecial: boolean;
  twoFactorEnabled: boolean;
  twoFactorMandatory: boolean;
}

export interface SettingGroup {
  key: string;
  label: string;
  icon: string;
  settings: SettingItem[];
}

export interface SettingItem {
  key: string;
  label: string;
  description?: string;
  type: 'text' | 'number' | 'boolean' | 'select' | 'email' | 'phone';
  value: unknown;
  options?: { label: string; value: unknown }[];
  min?: number;
  max?: number;
  required?: boolean;
}
