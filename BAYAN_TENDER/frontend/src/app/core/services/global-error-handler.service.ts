import { ErrorHandler, Injectable, inject, NgZone } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { ToastService } from './toast.service';
import { Router } from '@angular/router';

/**
 * Error details structure for consistent error handling.
 */
export interface ErrorDetails {
  message: string;
  statusCode?: number;
  timestamp: Date;
  path?: string;
  validationErrors?: Array<{ property: string; message: string }>;
}

/**
 * Global error handler that catches all unhandled errors and displays
 * user-friendly error messages using the ToastService.
 */
@Injectable({
  providedIn: 'root'
})
export class GlobalErrorHandlerService implements ErrorHandler {
  private readonly toastService = inject(ToastService);
  private readonly router = inject(Router);
  private readonly ngZone = inject(NgZone);

  /**
   * Handles all unhandled errors in the application.
   */
  handleError(error: Error | HttpErrorResponse): void {
    // Run inside Angular zone to ensure change detection works
    this.ngZone.run(() => {
      const errorDetails = this.parseError(error);

      // Log error to console for debugging
      console.error('Global Error Handler:', error);

      // Show user-friendly message
      this.showErrorToast(errorDetails);
    });
  }

  /**
   * Parses different error types into a consistent format.
   */
  private parseError(error: Error | HttpErrorResponse): ErrorDetails {
    const timestamp = new Date();

    if (error instanceof HttpErrorResponse) {
      return this.parseHttpError(error, timestamp);
    }

    // Client-side error
    return {
      message: error.message || 'An unexpected error occurred',
      timestamp
    };
  }

  /**
   * Parses HTTP errors into user-friendly messages.
   */
  private parseHttpError(error: HttpErrorResponse, timestamp: Date): ErrorDetails {
    const errorDetails: ErrorDetails = {
      message: 'An unexpected error occurred',
      statusCode: error.status,
      timestamp,
      path: error.url || undefined
    };

    // Handle different HTTP status codes
    switch (error.status) {
      case 0:
        errorDetails.message = 'Unable to connect to the server. Please check your internet connection.';
        break;

      case 400:
        errorDetails.message = this.extractErrorMessage(error) || 'Invalid request. Please check your input.';
        if (error.error?.errors) {
          errorDetails.validationErrors = error.error.errors;
        }
        break;

      case 401:
        errorDetails.message = 'Your session has expired. Please log in again.';
        break;

      case 403:
        errorDetails.message = 'You do not have permission to perform this action.';
        break;

      case 404:
        errorDetails.message = 'The requested resource was not found.';
        break;

      case 409:
        errorDetails.message = this.extractErrorMessage(error) || 'A conflict occurred. The resource may have been modified.';
        break;

      case 422:
        errorDetails.message = this.extractErrorMessage(error) || 'Validation failed. Please check your input.';
        if (error.error?.errors) {
          errorDetails.validationErrors = error.error.errors;
        }
        break;

      case 429:
        errorDetails.message = 'Too many requests. Please wait a moment and try again.';
        break;

      case 500:
        errorDetails.message = 'An internal server error occurred. Please try again later.';
        break;

      case 502:
      case 503:
      case 504:
        errorDetails.message = 'The service is temporarily unavailable. Please try again later.';
        break;

      default:
        errorDetails.message = this.extractErrorMessage(error) || 'An unexpected error occurred. Please try again.';
    }

    return errorDetails;
  }

  /**
   * Extracts error message from HTTP error response.
   */
  private extractErrorMessage(error: HttpErrorResponse): string | null {
    if (typeof error.error === 'string') {
      return error.error;
    }

    if (error.error?.message) {
      return error.error.message;
    }

    if (error.error?.error) {
      return error.error.error;
    }

    if (error.message) {
      return error.message;
    }

    return null;
  }

  /**
   * Shows error toast with appropriate formatting.
   */
  private showErrorToast(errorDetails: ErrorDetails): void {
    let detail = errorDetails.message;

    // Add validation errors if present
    if (errorDetails.validationErrors && errorDetails.validationErrors.length > 0) {
      const validationMessages = errorDetails.validationErrors
        .map(e => `${e.property}: ${e.message}`)
        .join('; ');
      detail = `${errorDetails.message} (${validationMessages})`;
    }

    this.toastService.error({
      summary: this.getErrorSummary(errorDetails.statusCode),
      detail,
      life: this.getErrorLifetime(errorDetails.statusCode)
    });
  }

  /**
   * Gets appropriate error summary based on status code.
   */
  private getErrorSummary(statusCode?: number): string {
    if (!statusCode) return 'Error';

    if (statusCode >= 400 && statusCode < 500) {
      return 'Request Error';
    }

    if (statusCode >= 500) {
      return 'Server Error';
    }

    return 'Error';
  }

  /**
   * Gets appropriate toast lifetime based on error severity.
   */
  private getErrorLifetime(statusCode?: number): number {
    // Longer display for server errors and connection issues
    if (!statusCode || statusCode === 0 || statusCode >= 500) {
      return 8000;
    }

    // Standard display for client errors
    return 5000;
  }

  /**
   * Manually handle an error (for use in catch blocks).
   */
  handleHttpError(error: HttpErrorResponse, customMessage?: string): void {
    const errorDetails = this.parseHttpError(error, new Date());

    if (customMessage) {
      errorDetails.message = customMessage;
    }

    this.showErrorToast(errorDetails);
  }

  /**
   * Show a custom error message.
   */
  showError(message: string, summary: string = 'Error'): void {
    this.toastService.error({
      summary,
      detail: message
    });
  }
}
