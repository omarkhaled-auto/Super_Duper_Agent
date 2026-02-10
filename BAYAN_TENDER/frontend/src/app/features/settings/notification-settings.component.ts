import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CardModule } from 'primeng/card';
import { InputSwitchModule } from 'primeng/inputswitch';
import { ButtonModule } from 'primeng/button';
import { ToastModule } from 'primeng/toast';
import { DividerModule } from 'primeng/divider';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageService } from 'primeng/api';
import { ApiService } from '../../core/services/api.service';

interface NotificationPreferences {
  id: string;
  userId: string;
  tenderInvitation: boolean;
  addendumIssued: boolean;
  clarificationPublished: boolean;
  deadlineReminder3Days: boolean;
  deadlineReminder1Day: boolean;
  approvalRequest: boolean;
}

@Component({
  selector: 'app-notification-settings',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    InputSwitchModule,
    ButtonModule,
    ToastModule,
    DividerModule,
    ProgressSpinnerModule
  ],
  providers: [MessageService],
  template: `
    <p-toast></p-toast>
    <div class="notification-settings-container">
      <div class="page-header">
        <div>
          <h1>Notification Preferences</h1>
          <p>Manage how and when you receive notifications</p>
        </div>
      </div>

      @if (isLoading()) {
        <div class="loading-container">
          <p-progressSpinner></p-progressSpinner>
          <p>Loading preferences...</p>
        </div>
      } @else {
        <p-card>
          <div class="preferences-section">
            <h3><i class="pi pi-file"></i> Tender Notifications</h3>
            <p class="section-description">Notifications related to tender activities</p>

            <div class="preference-item">
              <div class="preference-info">
                <span class="preference-label">Tender Invitation</span>
                <span class="preference-description">Receive notifications when you are invited to participate in a tender</span>
              </div>
              <p-inputSwitch [(ngModel)]="preferences.tenderInvitation" (onChange)="onPreferenceChange()"></p-inputSwitch>
            </div>

            <div class="preference-item">
              <div class="preference-info">
                <span class="preference-label">Addendum Issued</span>
                <span class="preference-description">Receive notifications when an addendum is issued for a tender you're participating in</span>
              </div>
              <p-inputSwitch [(ngModel)]="preferences.addendumIssued" (onChange)="onPreferenceChange()"></p-inputSwitch>
            </div>

            <div class="preference-item">
              <div class="preference-info">
                <span class="preference-label">Clarification Published</span>
                <span class="preference-description">Receive notifications when clarification responses are published</span>
              </div>
              <p-inputSwitch [(ngModel)]="preferences.clarificationPublished" (onChange)="onPreferenceChange()"></p-inputSwitch>
            </div>

            <p-divider></p-divider>

            <h3><i class="pi pi-clock"></i> Deadline Reminders</h3>
            <p class="section-description">Reminders before submission deadlines</p>

            <div class="preference-item">
              <div class="preference-info">
                <span class="preference-label">3-Day Reminder</span>
                <span class="preference-description">Receive a reminder 3 days before the submission deadline</span>
              </div>
              <p-inputSwitch [(ngModel)]="preferences.deadlineReminder3Days" (onChange)="onPreferenceChange()"></p-inputSwitch>
            </div>

            <div class="preference-item">
              <div class="preference-info">
                <span class="preference-label">1-Day Reminder</span>
                <span class="preference-description">Receive a reminder 1 day before the submission deadline</span>
              </div>
              <p-inputSwitch [(ngModel)]="preferences.deadlineReminder1Day" (onChange)="onPreferenceChange()"></p-inputSwitch>
            </div>

            <p-divider></p-divider>

            <h3><i class="pi pi-check-circle"></i> Approval Notifications</h3>
            <p class="section-description">Notifications related to approval workflows</p>

            <div class="preference-item">
              <div class="preference-info">
                <span class="preference-label">Approval Request</span>
                <span class="preference-description">Receive notifications when your approval is required for a tender decision</span>
              </div>
              <p-inputSwitch [(ngModel)]="preferences.approvalRequest" (onChange)="onPreferenceChange()"></p-inputSwitch>
            </div>

            <div class="actions">
              <button
                pButton
                label="Save Preferences"
                icon="pi pi-save"
                (click)="savePreferences()"
                [loading]="isSaving()"
                [disabled]="!hasChanges()"
              ></button>
              <button
                pButton
                label="Reset to Defaults"
                icon="pi pi-refresh"
                class="p-button-secondary"
                (click)="resetToDefaults()"
              ></button>
            </div>
          </div>
        </p-card>

        <p-card styleClass="info-card">
          <div class="info-content">
            <i class="pi pi-info-circle"></i>
            <div>
              <h4>Email Notifications</h4>
              <p>All notifications are sent to your registered email address. Make sure your email is up to date in your profile settings to receive notifications.</p>
            </div>
          </div>
        </p-card>
      }
    </div>
  `,
  styles: [`
    .notification-settings-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      max-width: 800px;
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

    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem;
      gap: 1rem;
    }

    .loading-container p {
      color: var(--bayan-muted-foreground, #71717a);
    }

    .preferences-section h3 {
      margin: 0 0 0.25rem;
      font-size: 1.1rem;
      color: var(--bayan-foreground, #09090b);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .preferences-section h3 i {
      color: var(--bayan-primary, #18181b);
    }

    .section-description {
      margin: 0 0 1rem;
      color: var(--bayan-muted-foreground, #71717a);
      font-size: 0.875rem;
    }

    .preference-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem;
      background: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius, 0.5rem);
      margin-bottom: 0.75rem;
    }

    .preference-item:last-of-type {
      margin-bottom: 0;
    }

    .preference-info {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      flex: 1;
      margin-right: 1rem;
    }

    .preference-label {
      font-weight: 600;
      color: var(--bayan-foreground, #09090b);
    }

    .preference-description {
      font-size: 0.8rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .actions {
      display: flex;
      gap: 0.75rem;
      margin-top: 1.5rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--bayan-border, #e4e4e7);
    }

    .info-card {
      background: var(--bayan-muted, #f4f4f5);
      border: 1px solid var(--bayan-border, #e4e4e7);
    }

    .info-content {
      display: flex;
      gap: 1rem;
      align-items: flex-start;
    }

    .info-content i {
      font-size: 1.5rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .info-content h4 {
      margin: 0 0 0.25rem;
      color: var(--bayan-foreground, #09090b);
    }

    .info-content p {
      margin: 0;
      color: var(--bayan-muted-foreground, #71717a);
      font-size: 0.875rem;
    }

    :host ::ng-deep {
      .p-inputswitch.p-inputswitch-checked .p-inputswitch-slider {
        background: var(--bayan-primary, #18181b);
      }
    }

    @media (max-width: 576px) {
      .preference-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.75rem;
      }

      .preference-info {
        margin-right: 0;
      }

      .actions {
        flex-direction: column;
      }

      .actions button {
        width: 100%;
      }
    }
  `]
})
export class NotificationSettingsComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly messageService = inject(MessageService);

  isLoading = signal(true);
  isSaving = signal(false);
  hasChanges = signal(false);

  preferences: NotificationPreferences = {
    id: '',
    userId: '',
    tenderInvitation: true,
    addendumIssued: true,
    clarificationPublished: true,
    deadlineReminder3Days: true,
    deadlineReminder1Day: true,
    approvalRequest: true
  };

  private originalPreferences: NotificationPreferences | null = null;

  ngOnInit(): void {
    this.loadPreferences();
  }

  private loadPreferences(): void {
    this.isLoading.set(true);

    this.api.get<NotificationPreferences>('/notifications/preferences').subscribe({
      next: (response) => {
        this.preferences = { ...response };
        this.originalPreferences = { ...response };
        this.isLoading.set(false);
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load notification preferences'
        });
        this.isLoading.set(false);
      }
    });
  }

  onPreferenceChange(): void {
    this.checkForChanges();
  }

  private checkForChanges(): void {
    if (!this.originalPreferences) {
      this.hasChanges.set(false);
      return;
    }

    const hasChanged =
      this.preferences.tenderInvitation !== this.originalPreferences.tenderInvitation ||
      this.preferences.addendumIssued !== this.originalPreferences.addendumIssued ||
      this.preferences.clarificationPublished !== this.originalPreferences.clarificationPublished ||
      this.preferences.deadlineReminder3Days !== this.originalPreferences.deadlineReminder3Days ||
      this.preferences.deadlineReminder1Day !== this.originalPreferences.deadlineReminder1Day ||
      this.preferences.approvalRequest !== this.originalPreferences.approvalRequest;

    this.hasChanges.set(hasChanged);
  }

  savePreferences(): void {
    this.isSaving.set(true);

    const payload = {
      tenderInvitation: this.preferences.tenderInvitation,
      addendumIssued: this.preferences.addendumIssued,
      clarificationPublished: this.preferences.clarificationPublished,
      deadlineReminder3Days: this.preferences.deadlineReminder3Days,
      deadlineReminder1Day: this.preferences.deadlineReminder1Day,
      approvalRequest: this.preferences.approvalRequest
    };

    this.api.put<NotificationPreferences>('/notifications/preferences', payload).subscribe({
      next: (response) => {
        this.preferences = { ...response };
        this.originalPreferences = { ...response };
        this.hasChanges.set(false);
        this.isSaving.set(false);
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Notification preferences saved successfully'
        });
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to save notification preferences'
        });
        this.isSaving.set(false);
      }
    });
  }

  resetToDefaults(): void {
    this.preferences = {
      ...this.preferences,
      tenderInvitation: true,
      addendumIssued: true,
      clarificationPublished: true,
      deadlineReminder3Days: true,
      deadlineReminder1Day: true,
      approvalRequest: true
    };
    this.checkForChanges();
    this.messageService.add({
      severity: 'info',
      summary: 'Reset',
      detail: 'Preferences reset to defaults. Click Save to apply changes.'
    });
  }
}
