import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CardModule } from 'primeng/card';
import { TabViewModule } from 'primeng/tabview';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { DropdownModule } from 'primeng/dropdown';
import { CheckboxModule } from 'primeng/checkbox';
import { ButtonModule } from 'primeng/button';
import { ToastModule } from 'primeng/toast';
import { DividerModule } from 'primeng/divider';
import { MessageService } from 'primeng/api';
import { SettingsService } from '../../../core/services/settings.service';
import {
  SystemSettings,
  GeneralSettings,
  TenderSettings,
  NotificationSettings,
  SecuritySettings
} from '../../../core/models/settings.model';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    TabViewModule,
    InputTextModule,
    InputNumberModule,
    DropdownModule,
    CheckboxModule,
    ButtonModule,
    ToastModule,
    DividerModule
  ],
  providers: [MessageService],
  template: `
    <p-toast></p-toast>
    <div class="settings-container" data-testid="settings-page">
      <div class="page-header">
        <div>
          <h1>System Settings</h1>
          <p>Configure system-wide settings and preferences</p>
        </div>
      </div>

      <p-tabView>
        <!-- General Settings -->
        <p-tabPanel header="General" leftIcon="pi pi-cog">
          <p-card>
            <div class="settings-section">
              <h3>Site Information</h3>
              <div class="settings-grid">
                <div class="setting-item">
                  <label for="siteName">Site Name (English)</label>
                  <input pInputText id="siteName" [(ngModel)]="generalSettings.siteName" class="w-full" />
                </div>
                <div class="setting-item">
                  <label for="siteNameAr">Site Name (Arabic)</label>
                  <input pInputText id="siteNameAr" [(ngModel)]="generalSettings.siteNameAr" class="w-full" dir="rtl" />
                </div>
                <div class="setting-item">
                  <label for="supportEmail">Support Email</label>
                  <input pInputText id="supportEmail" type="email" [(ngModel)]="generalSettings.supportEmail" class="w-full" />
                </div>
                <div class="setting-item">
                  <label for="supportPhone">Support Phone</label>
                  <input pInputText id="supportPhone" [(ngModel)]="generalSettings.supportPhone" class="w-full" />
                </div>
              </div>

              <p-divider></p-divider>

              <h3>Regional Settings</h3>
              <div class="settings-grid">
                <div class="setting-item">
                  <label for="defaultLanguage">Default Language</label>
                  <p-dropdown
                    id="defaultLanguage"
                    [options]="languageOptions"
                    [(ngModel)]="generalSettings.defaultLanguage"
                    styleClass="w-full"
                  ></p-dropdown>
                </div>
                <div class="setting-item">
                  <label for="timezone">Timezone</label>
                  <p-dropdown
                    id="timezone"
                    [options]="timezoneOptions"
                    [(ngModel)]="generalSettings.timezone"
                    styleClass="w-full"
                  ></p-dropdown>
                </div>
                <div class="setting-item">
                  <label for="dateFormat">Date Format</label>
                  <p-dropdown
                    id="dateFormat"
                    [options]="dateFormatOptions"
                    [(ngModel)]="generalSettings.dateFormat"
                    styleClass="w-full"
                  ></p-dropdown>
                </div>
                <div class="setting-item">
                  <label for="currency">Currency</label>
                  <p-dropdown
                    id="currency"
                    [options]="currencyOptions"
                    [(ngModel)]="generalSettings.currency"
                    styleClass="w-full"
                  ></p-dropdown>
                </div>
              </div>

              <div class="actions">
                <button pButton label="Save General Settings" icon="pi pi-save" (click)="saveGeneralSettings()" [loading]="isSaving()"></button>
              </div>
            </div>
          </p-card>
        </p-tabPanel>

        <!-- Tender Settings -->
        <p-tabPanel header="Tender" leftIcon="pi pi-file">
          <p-card>
            <div class="settings-section">
              <h3>Bid Settings</h3>
              <div class="settings-grid">
                <div class="setting-item">
                  <label for="defaultBidValidityDays">Default Bid Validity (Days)</label>
                  <p-inputNumber
                    id="defaultBidValidityDays"
                    [(ngModel)]="tenderSettings.defaultBidValidityDays"
                    [min]="1"
                    [max]="365"
                    styleClass="w-full"
                  ></p-inputNumber>
                </div>
                <div class="setting-item">
                  <label for="minBidAmount">Minimum Bid Amount (SAR)</label>
                  <p-inputNumber
                    id="minBidAmount"
                    [(ngModel)]="tenderSettings.minBidAmount"
                    [min]="0"
                    mode="currency"
                    currency="SAR"
                    locale="en-SA"
                    styleClass="w-full"
                  ></p-inputNumber>
                </div>
                <div class="setting-item">
                  <label for="maxBidAmount">Maximum Bid Amount (SAR)</label>
                  <p-inputNumber
                    id="maxBidAmount"
                    [(ngModel)]="tenderSettings.maxBidAmount"
                    [min]="0"
                    mode="currency"
                    currency="SAR"
                    locale="en-SA"
                    styleClass="w-full"
                  ></p-inputNumber>
                </div>
              </div>

              <p-divider></p-divider>

              <h3>Late Submission Policy</h3>
              <div class="settings-grid">
                <div class="setting-item checkbox-item">
                  <p-checkbox
                    [(ngModel)]="tenderSettings.allowLateSubmissions"
                    [binary]="true"
                    inputId="allowLateSubmissions"
                  ></p-checkbox>
                  <label for="allowLateSubmissions">Allow Late Submissions</label>
                </div>
                @if (tenderSettings.allowLateSubmissions) {
                  <div class="setting-item">
                    <label for="lateSubmissionPenaltyPercent">Late Submission Penalty (%)</label>
                    <p-inputNumber
                      id="lateSubmissionPenaltyPercent"
                      [(ngModel)]="tenderSettings.lateSubmissionPenaltyPercent"
                      [min]="0"
                      [max]="100"
                      suffix="%"
                      styleClass="w-full"
                    ></p-inputNumber>
                  </div>
                }
              </div>

              <p-divider></p-divider>

              <h3>Bank Guarantee</h3>
              <div class="settings-grid">
                <div class="setting-item checkbox-item">
                  <p-checkbox
                    [(ngModel)]="tenderSettings.requireBankGuarantee"
                    [binary]="true"
                    inputId="requireBankGuarantee"
                  ></p-checkbox>
                  <label for="requireBankGuarantee">Require Bank Guarantee</label>
                </div>
                @if (tenderSettings.requireBankGuarantee) {
                  <div class="setting-item">
                    <label for="bankGuaranteePercent">Bank Guarantee Percentage (%)</label>
                    <p-inputNumber
                      id="bankGuaranteePercent"
                      [(ngModel)]="tenderSettings.bankGuaranteePercent"
                      [min]="0"
                      [max]="100"
                      suffix="%"
                      styleClass="w-full"
                    ></p-inputNumber>
                  </div>
                }
              </div>

              <p-divider></p-divider>

              <h3>Auto-Extend Deadline</h3>
              <div class="settings-grid">
                <div class="setting-item checkbox-item">
                  <p-checkbox
                    [(ngModel)]="tenderSettings.autoExtendDeadline"
                    [binary]="true"
                    inputId="autoExtendDeadline"
                  ></p-checkbox>
                  <label for="autoExtendDeadline">Auto-Extend Deadline on New Bids</label>
                </div>
                @if (tenderSettings.autoExtendDeadline) {
                  <div class="setting-item">
                    <label for="autoExtendMinutes">Extension Duration (Minutes)</label>
                    <p-inputNumber
                      id="autoExtendMinutes"
                      [(ngModel)]="tenderSettings.autoExtendMinutes"
                      [min]="5"
                      [max]="120"
                      styleClass="w-full"
                    ></p-inputNumber>
                  </div>
                }
              </div>

              <div class="actions">
                <button pButton label="Save Tender Settings" icon="pi pi-save" (click)="saveTenderSettings()" [loading]="isSaving()"></button>
              </div>
            </div>
          </p-card>
        </p-tabPanel>

        <!-- Notification Settings -->
        <p-tabPanel header="Notifications" leftIcon="pi pi-bell">
          <p-card>
            <div class="settings-section">
              <h3>Notification Channels</h3>
              <div class="settings-grid">
                <div class="setting-item checkbox-item">
                  <p-checkbox
                    [(ngModel)]="notificationSettings.emailNotifications"
                    [binary]="true"
                    inputId="emailNotifications"
                  ></p-checkbox>
                  <label for="emailNotifications">Enable Email Notifications</label>
                </div>
                <div class="setting-item checkbox-item">
                  <p-checkbox
                    [(ngModel)]="notificationSettings.smsNotifications"
                    [binary]="true"
                    inputId="smsNotifications"
                  ></p-checkbox>
                  <label for="smsNotifications">Enable SMS Notifications</label>
                </div>
              </div>

              <p-divider></p-divider>

              <h3>Notification Events</h3>
              <div class="settings-grid">
                <div class="setting-item checkbox-item">
                  <p-checkbox
                    [(ngModel)]="notificationSettings.tenderPublishedNotify"
                    [binary]="true"
                    inputId="tenderPublishedNotify"
                  ></p-checkbox>
                  <label for="tenderPublishedNotify">Notify on Tender Published</label>
                </div>
                <div class="setting-item checkbox-item">
                  <p-checkbox
                    [(ngModel)]="notificationSettings.bidReceivedNotify"
                    [binary]="true"
                    inputId="bidReceivedNotify"
                  ></p-checkbox>
                  <label for="bidReceivedNotify">Notify on Bid Received</label>
                </div>
                <div class="setting-item checkbox-item">
                  <p-checkbox
                    [(ngModel)]="notificationSettings.tenderClosingNotify"
                    [binary]="true"
                    inputId="tenderClosingNotify"
                  ></p-checkbox>
                  <label for="tenderClosingNotify">Notify on Tender Closing Soon</label>
                </div>
                @if (notificationSettings.tenderClosingNotify) {
                  <div class="setting-item">
                    <label for="closingReminderHours">Closing Reminder (Hours Before)</label>
                    <p-inputNumber
                      id="closingReminderHours"
                      [(ngModel)]="notificationSettings.closingReminderHours"
                      [min]="1"
                      [max]="168"
                      styleClass="w-full"
                    ></p-inputNumber>
                  </div>
                }
                <div class="setting-item checkbox-item">
                  <p-checkbox
                    [(ngModel)]="notificationSettings.awardNotify"
                    [binary]="true"
                    inputId="awardNotify"
                  ></p-checkbox>
                  <label for="awardNotify">Notify on Tender Award</label>
                </div>
              </div>

              <div class="actions">
                <button pButton label="Save Notification Settings" icon="pi pi-save" (click)="saveNotificationSettings()" [loading]="isSaving()"></button>
              </div>
            </div>
          </p-card>
        </p-tabPanel>

        <!-- Security Settings -->
        <p-tabPanel header="Security" leftIcon="pi pi-shield">
          <p-card>
            <div class="settings-section">
              <h3>Session Security</h3>
              <div class="settings-grid">
                <div class="setting-item">
                  <label for="sessionTimeoutMinutes">Session Timeout (Minutes)</label>
                  <p-inputNumber
                    id="sessionTimeoutMinutes"
                    [(ngModel)]="securitySettings.sessionTimeoutMinutes"
                    [min]="5"
                    [max]="1440"
                    styleClass="w-full"
                  ></p-inputNumber>
                </div>
                <div class="setting-item">
                  <label for="maxLoginAttempts">Max Login Attempts</label>
                  <p-inputNumber
                    id="maxLoginAttempts"
                    [(ngModel)]="securitySettings.maxLoginAttempts"
                    [min]="1"
                    [max]="20"
                    styleClass="w-full"
                  ></p-inputNumber>
                </div>
                <div class="setting-item">
                  <label for="lockoutDurationMinutes">Lockout Duration (Minutes)</label>
                  <p-inputNumber
                    id="lockoutDurationMinutes"
                    [(ngModel)]="securitySettings.lockoutDurationMinutes"
                    [min]="1"
                    [max]="1440"
                    styleClass="w-full"
                  ></p-inputNumber>
                </div>
              </div>

              <p-divider></p-divider>

              <h3>Password Policy</h3>
              <div class="settings-grid">
                <div class="setting-item">
                  <label for="passwordMinLength">Minimum Password Length</label>
                  <p-inputNumber
                    id="passwordMinLength"
                    [(ngModel)]="securitySettings.passwordMinLength"
                    [min]="6"
                    [max]="32"
                    styleClass="w-full"
                  ></p-inputNumber>
                </div>
                <div class="setting-item checkbox-item">
                  <p-checkbox
                    [(ngModel)]="securitySettings.passwordRequireUppercase"
                    [binary]="true"
                    inputId="passwordRequireUppercase"
                  ></p-checkbox>
                  <label for="passwordRequireUppercase">Require Uppercase Letter</label>
                </div>
                <div class="setting-item checkbox-item">
                  <p-checkbox
                    [(ngModel)]="securitySettings.passwordRequireLowercase"
                    [binary]="true"
                    inputId="passwordRequireLowercase"
                  ></p-checkbox>
                  <label for="passwordRequireLowercase">Require Lowercase Letter</label>
                </div>
                <div class="setting-item checkbox-item">
                  <p-checkbox
                    [(ngModel)]="securitySettings.passwordRequireNumbers"
                    [binary]="true"
                    inputId="passwordRequireNumbers"
                  ></p-checkbox>
                  <label for="passwordRequireNumbers">Require Number</label>
                </div>
                <div class="setting-item checkbox-item">
                  <p-checkbox
                    [(ngModel)]="securitySettings.passwordRequireSpecial"
                    [binary]="true"
                    inputId="passwordRequireSpecial"
                  ></p-checkbox>
                  <label for="passwordRequireSpecial">Require Special Character</label>
                </div>
              </div>

              <p-divider></p-divider>

              <h3>Two-Factor Authentication</h3>
              <div class="settings-grid">
                <div class="setting-item checkbox-item">
                  <p-checkbox
                    [(ngModel)]="securitySettings.twoFactorEnabled"
                    [binary]="true"
                    inputId="twoFactorEnabled"
                  ></p-checkbox>
                  <label for="twoFactorEnabled">Enable Two-Factor Authentication</label>
                </div>
                @if (securitySettings.twoFactorEnabled) {
                  <div class="setting-item checkbox-item">
                    <p-checkbox
                      [(ngModel)]="securitySettings.twoFactorMandatory"
                      [binary]="true"
                      inputId="twoFactorMandatory"
                    ></p-checkbox>
                    <label for="twoFactorMandatory">Make 2FA Mandatory for All Users</label>
                  </div>
                }
              </div>

              <div class="actions">
                <button pButton label="Save Security Settings" icon="pi pi-save" (click)="saveSecuritySettings()" [loading]="isSaving()"></button>
              </div>
            </div>
          </p-card>
        </p-tabPanel>
      </p-tabView>
    </div>
  `,
  styles: [`
    .settings-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .page-header h1 {
      margin: 0;
      font-size: 1.75rem;
      color: var(--bayan-foreground, #09090b);
    }

    .page-header p {
      margin: 0.25rem 0 0;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .settings-section h3 {
      margin: 0 0 1rem;
      font-size: 1.125rem;
      color: var(--bayan-foreground, #09090b);
    }

    .settings-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1.5rem;
    }

    .setting-item {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .setting-item label {
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
    }

    .setting-item.checkbox-item {
      flex-direction: row;
      align-items: center;
    }

    .setting-item.checkbox-item label {
      margin-left: 0.5rem;
      cursor: pointer;
    }

    .actions {
      display: flex;
      justify-content: flex-end;
      margin-top: 1.5rem;
      padding-top: 1rem;
      border-top: 1px solid var(--bayan-border, #e4e4e7);
    }

    :host ::ng-deep {
      .p-tab {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1.25rem;
      }

      .p-tabpanels {
        padding: 1.5rem 0;
      }

      .p-card {
        margin-bottom: 1rem;
      }

      .p-inputnumber,
      .p-dropdown {
        width: 100%;
      }
    }
  `]
})
export class SettingsComponent implements OnInit {
  private readonly settingsService = inject(SettingsService);
  private readonly messageService = inject(MessageService);

  isSaving = signal(false);

  // Settings objects
  generalSettings: GeneralSettings = this.settingsService.getDefaultSettings().general;
  tenderSettings: TenderSettings = this.settingsService.getDefaultSettings().tender;
  notificationSettings: NotificationSettings = this.settingsService.getDefaultSettings().notification;
  securitySettings: SecuritySettings = this.settingsService.getDefaultSettings().security;

  // Dropdown options
  languageOptions = [
    { label: 'Arabic', value: 'ar' },
    { label: 'English', value: 'en' }
  ];

  timezoneOptions = [
    { label: 'Asia/Riyadh (UTC+3)', value: 'Asia/Riyadh' },
    { label: 'Asia/Dubai (UTC+4)', value: 'Asia/Dubai' },
    { label: 'Europe/London (UTC+0)', value: 'Europe/London' },
    { label: 'America/New_York (UTC-5)', value: 'America/New_York' }
  ];

  dateFormatOptions = [
    { label: 'DD/MM/YYYY', value: 'DD/MM/YYYY' },
    { label: 'MM/DD/YYYY', value: 'MM/DD/YYYY' },
    { label: 'YYYY-MM-DD', value: 'YYYY-MM-DD' }
  ];

  currencyOptions = [
    { label: 'SAR - Saudi Riyal', value: 'SAR' },
    { label: 'USD - US Dollar', value: 'USD' },
    { label: 'EUR - Euro', value: 'EUR' },
    { label: 'AED - UAE Dirham', value: 'AED' }
  ];

  ngOnInit(): void {
    this.loadSettings();
  }

  private loadSettings(): void {
    // In production, load from API
    // this.settingsService.getSettings().subscribe(settings => {
    //   this.generalSettings = settings.general;
    //   this.tenderSettings = settings.tender;
    //   this.notificationSettings = settings.notification;
    //   this.securitySettings = settings.security;
    // });
  }

  saveGeneralSettings(): void {
    this.isSaving.set(true);
    // In production: this.settingsService.updateGeneralSettings(this.generalSettings)
    setTimeout(() => {
      this.isSaving.set(false);
      this.messageService.add({
        severity: 'success',
        summary: 'Success',
        detail: 'General settings saved successfully'
      });
    }, 500);
  }

  saveTenderSettings(): void {
    this.isSaving.set(true);
    // In production: this.settingsService.updateTenderSettings(this.tenderSettings)
    setTimeout(() => {
      this.isSaving.set(false);
      this.messageService.add({
        severity: 'success',
        summary: 'Success',
        detail: 'Tender settings saved successfully'
      });
    }, 500);
  }

  saveNotificationSettings(): void {
    this.isSaving.set(true);
    // In production: this.settingsService.updateNotificationSettings(this.notificationSettings)
    setTimeout(() => {
      this.isSaving.set(false);
      this.messageService.add({
        severity: 'success',
        summary: 'Success',
        detail: 'Notification settings saved successfully'
      });
    }, 500);
  }

  saveSecuritySettings(): void {
    this.isSaving.set(true);
    // In production: this.settingsService.updateSecuritySettings(this.securitySettings)
    setTimeout(() => {
      this.isSaving.set(false);
      this.messageService.add({
        severity: 'success',
        summary: 'Success',
        detail: 'Security settings saved successfully'
      });
    }, 500);
  }
}
