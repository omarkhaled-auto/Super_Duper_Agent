import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

export interface NotificationPreferences {
  id: string;
  userId: string;
  tenderInvitation: boolean;
  addendumIssued: boolean;
  clarificationPublished: boolean;
  deadlineReminder3Days: boolean;
  deadlineReminder1Day: boolean;
  approvalRequest: boolean;
}

export interface UpdateNotificationPreferencesRequest {
  tenderInvitation: boolean;
  addendumIssued: boolean;
  clarificationPublished: boolean;
  deadlineReminder3Days: boolean;
  deadlineReminder1Day: boolean;
  approvalRequest: boolean;
}

/**
 * Service for managing user notification preferences.
 */
@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private readonly api = inject(ApiService);

  /**
   * Gets the current user's notification preferences.
   */
  getPreferences(): Observable<NotificationPreferences> {
    return this.api.get<NotificationPreferences>('/notifications/preferences');
  }

  /**
   * Updates the current user's notification preferences.
   */
  updatePreferences(preferences: UpdateNotificationPreferencesRequest): Observable<NotificationPreferences> {
    return this.api.put<NotificationPreferences>('/notifications/preferences', preferences);
  }
}
