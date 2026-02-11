import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError, forkJoin, of, map, switchMap } from 'rxjs';
import { ApiService } from './api.service';
import {
  SystemSettings,
  GeneralSettings,
  TenderSettings,
  NotificationSettings,
  SecuritySettings
} from '../models/settings.model';

/** Maps a flat key-value setting row from the API */
interface SettingRow {
  id: string;
  key: string;
  value: string;
  dataType: string;
  category: string;
  isEditable: boolean;
  displayOrder: number;
}

/** The shape the backend GET /admin/settings returns (inside ApiResponse.data) */
interface GetSettingsApiResponse {
  settings: SettingRow[];
  unitsOfMeasure: unknown[];
}

@Injectable({
  providedIn: 'root'
})
export class SettingsService {
  private readonly api = inject(ApiService);
  private readonly endpoint = '/admin/settings';

  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);
  private readonly _settings = signal<SystemSettings | null>(null);

  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();
  readonly settings = this._settings.asReadonly();

  // ─── Helpers ───────────────────────────────────────────────

  /** Build a lookup map from the flat settings array */
  private buildMap(rows: SettingRow[]): Map<string, string> {
    const m = new Map<string, string>();
    for (const r of rows) {
      m.set(r.key, r.value);
    }
    return m;
  }

  private str(m: Map<string, string>, key: string, fallback: string): string {
    return m.get(key) ?? fallback;
  }

  private num(m: Map<string, string>, key: string, fallback: number): number {
    const v = m.get(key);
    if (v == null) return fallback;
    const n = Number(v);
    return isNaN(n) ? fallback : n;
  }

  private bool(m: Map<string, string>, key: string, fallback: boolean): boolean {
    const v = m.get(key);
    if (v == null) return fallback;
    return v === 'true' || v === '1' || v === 'True';
  }

  // ─── GET ───────────────────────────────────────────────────

  getSettings(): Observable<SystemSettings> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<GetSettingsApiResponse>(this.endpoint).pipe(
      map(response => {
        // response may already be unwrapped by ApiService, or may be the raw wrapper
        const rows: SettingRow[] = (response as any)?.settings ?? [];
        return this.mapRowsToSystemSettings(rows);
      }),
      tap(settings => {
        this._settings.set(settings);
        this._isLoading.set(false);
      }),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load settings');
        return throwError(() => error);
      })
    );
  }

  private mapRowsToSystemSettings(rows: SettingRow[]): SystemSettings {
    const m = this.buildMap(rows);
    const defaults = this.getDefaultSettings();

    return {
      general: {
        siteName: this.str(m, 'site_name', defaults.general.siteName),
        siteNameAr: this.str(m, 'site_name_ar', defaults.general.siteNameAr),
        supportEmail: this.str(m, 'support_email', defaults.general.supportEmail),
        supportPhone: this.str(m, 'support_phone', defaults.general.supportPhone),
        defaultLanguage: this.str(m, 'default_language', defaults.general.defaultLanguage) as 'en' | 'ar',
        timezone: this.str(m, 'timezone', defaults.general.timezone),
        dateFormat: this.str(m, 'date_format', defaults.general.dateFormat),
        currency: this.str(m, 'currency', defaults.general.currency),
      },
      tender: {
        defaultBidValidityDays: this.num(m, 'default_bid_validity_days', defaults.tender.defaultBidValidityDays),
        minBidAmount: this.num(m, 'min_bid_amount', defaults.tender.minBidAmount),
        maxBidAmount: this.num(m, 'max_bid_amount', defaults.tender.maxBidAmount),
        allowLateSubmissions: this.bool(m, 'allow_late_submissions', defaults.tender.allowLateSubmissions),
        lateSubmissionPenaltyPercent: this.num(m, 'late_submission_penalty_percent', defaults.tender.lateSubmissionPenaltyPercent),
        requireBankGuarantee: this.bool(m, 'require_bank_guarantee', defaults.tender.requireBankGuarantee),
        bankGuaranteePercent: this.num(m, 'bank_guarantee_percent', defaults.tender.bankGuaranteePercent),
        autoExtendDeadline: this.bool(m, 'auto_extend_deadline', defaults.tender.autoExtendDeadline),
        autoExtendMinutes: this.num(m, 'auto_extend_minutes', defaults.tender.autoExtendMinutes),
      },
      notification: {
        emailNotifications: this.bool(m, 'email_notifications', defaults.notification.emailNotifications),
        smsNotifications: this.bool(m, 'sms_notifications', defaults.notification.smsNotifications),
        tenderPublishedNotify: this.bool(m, 'tender_published_notify', defaults.notification.tenderPublishedNotify),
        bidReceivedNotify: this.bool(m, 'bid_received_notify', defaults.notification.bidReceivedNotify),
        tenderClosingNotify: this.bool(m, 'tender_closing_notify', defaults.notification.tenderClosingNotify),
        closingReminderHours: this.num(m, 'closing_reminder_hours', defaults.notification.closingReminderHours),
        awardNotify: this.bool(m, 'award_notify', defaults.notification.awardNotify),
      },
      security: {
        sessionTimeoutMinutes: this.num(m, 'session_timeout_minutes', defaults.security.sessionTimeoutMinutes),
        maxLoginAttempts: this.num(m, 'max_login_attempts', defaults.security.maxLoginAttempts),
        lockoutDurationMinutes: this.num(m, 'lockout_duration_minutes', defaults.security.lockoutDurationMinutes),
        passwordMinLength: this.num(m, 'password_min_length', defaults.security.passwordMinLength),
        passwordRequireUppercase: this.bool(m, 'password_require_uppercase', defaults.security.passwordRequireUppercase),
        passwordRequireLowercase: this.bool(m, 'password_require_lowercase', defaults.security.passwordRequireLowercase),
        passwordRequireNumbers: this.bool(m, 'password_require_numbers', defaults.security.passwordRequireNumbers),
        passwordRequireSpecial: this.bool(m, 'password_require_special', defaults.security.passwordRequireSpecial),
        twoFactorEnabled: this.bool(m, 'two_factor_enabled', defaults.security.twoFactorEnabled),
        twoFactorMandatory: this.bool(m, 'two_factor_mandatory', defaults.security.twoFactorMandatory),
      }
    };
  }

  // ─── SAVE (individual PUTs per key) ────────────────────────

  /** Save a single setting key-value pair */
  private saveSetting(key: string, value: string): Observable<unknown> {
    return this.api.put(`${this.endpoint}/${key}`, { value });
  }

  /** Save a batch of key-value pairs sequentially via forkJoin */
  private saveSettingsBatch(pairs: Record<string, string>): Observable<unknown> {
    const calls = Object.entries(pairs).map(([key, value]) =>
      this.saveSetting(key, value)
    );
    if (calls.length === 0) return of(null);
    return forkJoin(calls);
  }

  updateGeneralSettings(data: GeneralSettings): Observable<GeneralSettings> {
    this._isLoading.set(true);
    this._error.set(null);

    const pairs: Record<string, string> = {
      'site_name': data.siteName,
      'site_name_ar': data.siteNameAr,
      'support_email': data.supportEmail,
      'support_phone': data.supportPhone,
      'default_language': data.defaultLanguage,
      'timezone': data.timezone,
      'date_format': data.dateFormat,
      'currency': data.currency,
    };

    return this.saveSettingsBatch(pairs).pipe(
      map(() => data),
      tap(settings => {
        const current = this._settings();
        if (current) {
          this._settings.set({ ...current, general: { ...current.general, ...settings } });
        }
        this._isLoading.set(false);
      }),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update general settings');
        return throwError(() => error);
      })
    );
  }

  updateTenderSettings(data: TenderSettings): Observable<TenderSettings> {
    this._isLoading.set(true);
    this._error.set(null);

    const pairs: Record<string, string> = {
      'default_bid_validity_days': String(data.defaultBidValidityDays),
      'min_bid_amount': String(data.minBidAmount),
      'max_bid_amount': String(data.maxBidAmount),
      'allow_late_submissions': String(data.allowLateSubmissions),
      'late_submission_penalty_percent': String(data.lateSubmissionPenaltyPercent),
      'require_bank_guarantee': String(data.requireBankGuarantee),
      'bank_guarantee_percent': String(data.bankGuaranteePercent),
      'auto_extend_deadline': String(data.autoExtendDeadline),
      'auto_extend_minutes': String(data.autoExtendMinutes),
    };

    return this.saveSettingsBatch(pairs).pipe(
      map(() => data),
      tap(settings => {
        const current = this._settings();
        if (current) {
          this._settings.set({ ...current, tender: { ...current.tender, ...settings } });
        }
        this._isLoading.set(false);
      }),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update tender settings');
        return throwError(() => error);
      })
    );
  }

  updateNotificationSettings(data: NotificationSettings): Observable<NotificationSettings> {
    this._isLoading.set(true);
    this._error.set(null);

    const pairs: Record<string, string> = {
      'email_notifications': String(data.emailNotifications),
      'sms_notifications': String(data.smsNotifications),
      'tender_published_notify': String(data.tenderPublishedNotify),
      'bid_received_notify': String(data.bidReceivedNotify),
      'tender_closing_notify': String(data.tenderClosingNotify),
      'closing_reminder_hours': String(data.closingReminderHours),
      'award_notify': String(data.awardNotify),
    };

    return this.saveSettingsBatch(pairs).pipe(
      map(() => data),
      tap(settings => {
        const current = this._settings();
        if (current) {
          this._settings.set({ ...current, notification: { ...current.notification, ...settings } });
        }
        this._isLoading.set(false);
      }),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update notification settings');
        return throwError(() => error);
      })
    );
  }

  updateSecuritySettings(data: SecuritySettings): Observable<SecuritySettings> {
    this._isLoading.set(true);
    this._error.set(null);

    const pairs: Record<string, string> = {
      'session_timeout_minutes': String(data.sessionTimeoutMinutes),
      'max_login_attempts': String(data.maxLoginAttempts),
      'lockout_duration_minutes': String(data.lockoutDurationMinutes),
      'password_min_length': String(data.passwordMinLength),
      'password_require_uppercase': String(data.passwordRequireUppercase),
      'password_require_lowercase': String(data.passwordRequireLowercase),
      'password_require_numbers': String(data.passwordRequireNumbers),
      'password_require_special': String(data.passwordRequireSpecial),
      'two_factor_enabled': String(data.twoFactorEnabled),
      'two_factor_mandatory': String(data.twoFactorMandatory),
    };

    return this.saveSettingsBatch(pairs).pipe(
      map(() => data),
      tap(settings => {
        const current = this._settings();
        if (current) {
          this._settings.set({ ...current, security: { ...current.security, ...settings } });
        }
        this._isLoading.set(false);
      }),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update security settings');
        return throwError(() => error);
      })
    );
  }

  // ─── Defaults ──────────────────────────────────────────────

  getDefaultSettings(): SystemSettings {
    return {
      general: {
        siteName: 'Bayan Tender',
        siteNameAr: 'بيان للمناقصات',
        supportEmail: 'support@bayan.sa',
        supportPhone: '+966 11 000 0000',
        defaultLanguage: 'ar',
        timezone: 'Asia/Riyadh',
        dateFormat: 'DD/MM/YYYY',
        currency: 'AED'
      },
      tender: {
        defaultBidValidityDays: 90,
        minBidAmount: 1000,
        maxBidAmount: 100000000,
        allowLateSubmissions: false,
        lateSubmissionPenaltyPercent: 5,
        requireBankGuarantee: true,
        bankGuaranteePercent: 5,
        autoExtendDeadline: true,
        autoExtendMinutes: 30
      },
      notification: {
        emailNotifications: true,
        smsNotifications: true,
        tenderPublishedNotify: true,
        bidReceivedNotify: true,
        tenderClosingNotify: true,
        closingReminderHours: 24,
        awardNotify: true
      },
      security: {
        sessionTimeoutMinutes: 30,
        maxLoginAttempts: 5,
        lockoutDurationMinutes: 15,
        passwordMinLength: 8,
        passwordRequireUppercase: true,
        passwordRequireLowercase: true,
        passwordRequireNumbers: true,
        passwordRequireSpecial: true,
        twoFactorEnabled: false,
        twoFactorMandatory: false
      }
    };
  }

  clearError(): void {
    this._error.set(null);
  }
}
