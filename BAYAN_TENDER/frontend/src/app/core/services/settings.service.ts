import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError, of } from 'rxjs';
import { ApiService } from './api.service';
import {
  SystemSettings,
  GeneralSettings,
  TenderSettings,
  NotificationSettings,
  SecuritySettings
} from '../models/settings.model';

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

  getSettings(): Observable<SystemSettings> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<SystemSettings>(this.endpoint).pipe(
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

  updateGeneralSettings(data: Partial<GeneralSettings>): Observable<GeneralSettings> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.put<GeneralSettings>(`${this.endpoint}/general`, data).pipe(
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

  updateTenderSettings(data: Partial<TenderSettings>): Observable<TenderSettings> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.put<TenderSettings>(`${this.endpoint}/tender`, data).pipe(
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

  updateNotificationSettings(data: Partial<NotificationSettings>): Observable<NotificationSettings> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.put<NotificationSettings>(`${this.endpoint}/notification`, data).pipe(
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

  updateSecuritySettings(data: Partial<SecuritySettings>): Observable<SecuritySettings> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.put<SecuritySettings>(`${this.endpoint}/security`, data).pipe(
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

  // Get default settings (for initial setup or testing)
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
        currency: 'SAR'
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
