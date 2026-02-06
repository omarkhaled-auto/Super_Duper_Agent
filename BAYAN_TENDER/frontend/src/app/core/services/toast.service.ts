import { Injectable, inject } from '@angular/core';
import { MessageService } from 'primeng/api';

export interface ToastOptions {
  summary?: string;
  detail: string;
  life?: number;
  sticky?: boolean;
  closable?: boolean;
  key?: string;
}

/**
 * Global toast notification service using PrimeNG Toast.
 * Provides a centralized way to show notifications throughout the application.
 */
@Injectable({
  providedIn: 'root'
})
export class ToastService {
  private messageService: MessageService | null = null;

  /**
   * Initialize the toast service with a MessageService instance.
   * This should be called from the AppComponent to set up the global message service.
   */
  initialize(messageService: MessageService): void {
    this.messageService = messageService;
  }

  /**
   * Shows a success toast notification.
   */
  success(options: ToastOptions | string): void {
    this.show('success', options);
  }

  /**
   * Shows an info toast notification.
   */
  info(options: ToastOptions | string): void {
    this.show('info', options);
  }

  /**
   * Shows a warning toast notification.
   */
  warn(options: ToastOptions | string): void {
    this.show('warn', options);
  }

  /**
   * Shows an error toast notification.
   */
  error(options: ToastOptions | string): void {
    this.show('error', options);
  }

  /**
   * Shows a toast with a retry action.
   */
  errorWithRetry(detail: string, retryAction: () => void): void {
    if (!this.messageService) {
      console.error('ToastService not initialized. Call initialize() first.');
      return;
    }

    this.messageService.add({
      severity: 'error',
      summary: 'Error',
      detail,
      life: 10000,
      closable: true,
      data: { retryAction }
    });
  }

  /**
   * Clears all toast notifications.
   */
  clear(key?: string): void {
    if (!this.messageService) {
      return;
    }

    this.messageService.clear(key);
  }

  private show(severity: 'success' | 'info' | 'warn' | 'error', options: ToastOptions | string): void {
    if (!this.messageService) {
      console.error('ToastService not initialized. Call initialize() first.');
      return;
    }

    const config = typeof options === 'string'
      ? { detail: options }
      : options;

    const summaryMap = {
      success: 'Success',
      info: 'Information',
      warn: 'Warning',
      error: 'Error'
    };

    this.messageService.add({
      severity,
      summary: config.summary || summaryMap[severity],
      detail: config.detail,
      life: config.life || 5000,
      sticky: config.sticky || false,
      closable: config.closable !== false,
      key: config.key
    });
  }
}
