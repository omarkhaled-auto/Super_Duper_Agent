import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpEventType, HttpEvent } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, throwError, map, BehaviorSubject, of } from 'rxjs';
import { environment } from '../../../environments/environment';
import { StorageService } from './storage.service';
import { ApiResponse } from '../models/api-response.model';
import {
  PortalLoginCredentials,
  PortalUser,
  PortalAuthResponse,
  PortalTenderInfo,
  TenderDocument,
  TenderAddendum,
  DocumentFolder,
  DocumentCategory,
  DOCUMENT_CATEGORY_CONFIG,
  PortalClarification,
  PortalBulletin,
  SubmitQuestionDto,
  PortalBidDocument,
  PortalBidDocumentType,
  PortalBidUploadProgress,
  PortalBidSubmission,
  SubmitBidDto,
  PortalBidReceipt,
  BoqSectionOption
} from '../models/portal.model';

export interface ActivateAccountRequest {
  email: string;
  activationToken: string;
  password: string;
  confirmPassword: string;
}

const PORTAL_TOKEN_KEY = 'portal_access_token';
const PORTAL_REFRESH_TOKEN_KEY = 'portal_refresh_token';
const PORTAL_USER_KEY = 'portal_user';
const PORTAL_TENDER_KEY = 'portal_tender';

@Injectable({
  providedIn: 'root'
})
export class PortalService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly storage = inject(StorageService);
  private readonly apiUrl = `${environment.apiUrl}/portal`;

  // Authentication state
  private readonly _currentUser = signal<PortalUser | null>(null);
  private readonly _currentTender = signal<PortalTenderInfo | null>(null);
  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  // Public readonly signals
  readonly currentUser = this._currentUser.asReadonly();
  readonly currentTender = this._currentTender.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();
  readonly isAuthenticated = computed(() => this._currentUser() !== null);

  // Upload progress tracking
  private readonly _uploadProgress = new BehaviorSubject<Map<PortalBidDocumentType, PortalBidUploadProgress>>(new Map());
  readonly uploadProgress$ = this._uploadProgress.asObservable();

  constructor() {
    this.loadFromStorage();
  }

  // ============================================
  // Authentication Methods
  // ============================================

  private loadFromStorage(): void {
    const userStr = localStorage.getItem(PORTAL_USER_KEY);
    const tenderStr = localStorage.getItem(PORTAL_TENDER_KEY);
    const token = localStorage.getItem(PORTAL_TOKEN_KEY);

    if (userStr && token) {
      try {
        this._currentUser.set(JSON.parse(userStr));
      } catch {
        this.clearPortalSession();
      }
    }

    if (tenderStr) {
      try {
        this._currentTender.set(JSON.parse(tenderStr));
      } catch {
        localStorage.removeItem(PORTAL_TENDER_KEY);
      }
    }
  }

  login(credentials: PortalLoginCredentials): Observable<PortalAuthResponse> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.http.post<ApiResponse<PortalAuthResponse>>(`${this.apiUrl}/auth/login`, credentials).pipe(
      tap(response => {
        this.handleAuthSuccess(response.data);
        this._isLoading.set(false);
      }),
      map(response => response.data),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.error?.message || 'Login failed. Please check your credentials.');
        return throwError(() => error);
      })
    );
  }

  private handleAuthSuccess(data: PortalAuthResponse): void {
    localStorage.setItem(PORTAL_TOKEN_KEY, data.accessToken);
    localStorage.setItem(PORTAL_REFRESH_TOKEN_KEY, data.refreshToken);

    // API returns "bidder" not "user" — map to PortalUser
    const user: PortalUser = data.user ?? (data.bidder ? {
      id: Number(data.bidder.id) || 0,
      bidderId: Number(data.bidder.id) || 0,
      companyName: data.bidder.companyName,
      email: data.bidder.email,
      contactPersonName: data.bidder.contactPerson,
      phone: data.bidder.phone,
      crNumber: undefined
    } : { id: 0, bidderId: 0, companyName: '', email: '' });

    // Store user with tenderAccess for the portal landing page
    const userWithAccess = { ...user, tenderAccess: data.bidder?.tenderAccess || [] };
    localStorage.setItem(PORTAL_USER_KEY, JSON.stringify(userWithAccess));
    this._currentUser.set(user);
  }

  logout(): void {
    this.http.post(`${this.apiUrl}/auth/logout`, {}).pipe(
      catchError(() => throwError(() => new Error('Logout failed')))
    ).subscribe({
      complete: () => this.clearPortalSession(),
      error: () => this.clearPortalSession()
    });
  }

  private clearPortalSession(): void {
    localStorage.removeItem(PORTAL_TOKEN_KEY);
    localStorage.removeItem(PORTAL_REFRESH_TOKEN_KEY);
    localStorage.removeItem(PORTAL_USER_KEY);
    localStorage.removeItem(PORTAL_TENDER_KEY);
    this._currentUser.set(null);
    this._currentTender.set(null);
    this._error.set(null);
    this.router.navigate(['/portal/login']);
  }

  getPortalToken(): string | null {
    return localStorage.getItem(PORTAL_TOKEN_KEY);
  }

  refreshToken(): Observable<{ accessToken: string; refreshToken: string }> {
    const refreshToken = localStorage.getItem(PORTAL_REFRESH_TOKEN_KEY);
    if (!refreshToken) {
      return throwError(() => new Error('No refresh token available'));
    }

    return this.http.post<ApiResponse<{ accessToken: string; refreshToken: string }>>(
      `${this.apiUrl}/auth/refresh`,
      { refreshToken }
    ).pipe(
      tap(response => {
        localStorage.setItem(PORTAL_TOKEN_KEY, response.data.accessToken);
        localStorage.setItem(PORTAL_REFRESH_TOKEN_KEY, response.data.refreshToken);
      }),
      map(response => response.data),
      catchError(error => {
        this.clearPortalSession();
        return throwError(() => error);
      })
    );
  }

  clearError(): void {
    this._error.set(null);
  }

  activateAccount(data: ActivateAccountRequest): Observable<any> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.http.post<ApiResponse<any>>(`${this.apiUrl}/auth/activate`, data).pipe(
      tap(() => {
        this._isLoading.set(false);
      }),
      map(response => response.data),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.error?.message || 'Account activation failed. Please try again.');
        return throwError(() => error);
      })
    );
  }

  // ============================================
  // Tender Information
  // ============================================

  getTenderInfo(tenderId: number): Observable<PortalTenderInfo> {
    this._isLoading.set(true);

    return this.http.get<ApiResponse<PortalTenderInfo>>(`${this.apiUrl}/tenders/${tenderId}`).pipe(
      tap(response => {
        this._currentTender.set(response.data);
        localStorage.setItem(PORTAL_TENDER_KEY, JSON.stringify(response.data));
        this._isLoading.set(false);
      }),
      map(response => response.data),
      catchError(error => {
        this._isLoading.set(false);
        return throwError(() => error);
      })
    );
  }

  // ============================================
  // Document Methods
  // ============================================

  getTenderDocuments(tenderId: number): Observable<TenderDocument[]> {
    return this.http.get<ApiResponse<TenderDocument[]>>(`${this.apiUrl}/tenders/${tenderId}/documents`).pipe(
      map(response => response.data),
      catchError(error => throwError(() => error))
    );
  }

  getDocumentsByFolder(tenderId: number): Observable<DocumentFolder[]> {
    return this.getTenderDocuments(tenderId).pipe(
      map(documents => this.organizeDocumentsByCategory(documents))
    );
  }

  private organizeDocumentsByCategory(documents: TenderDocument[]): DocumentFolder[] {
    const folderMap = new Map<DocumentCategory, TenderDocument[]>();

    // Initialize all categories
    Object.keys(DOCUMENT_CATEGORY_CONFIG).forEach(cat => {
      folderMap.set(cat as DocumentCategory, []);
    });

    // Distribute documents to categories
    documents.forEach(doc => {
      const category = doc.category || 'other';
      const existing = folderMap.get(category) || [];
      existing.push(doc);
      folderMap.set(category, existing);
    });

    // Convert to DocumentFolder array
    const folders: DocumentFolder[] = [];
    folderMap.forEach((docs, category) => {
      if (docs.length > 0) {
        const config = DOCUMENT_CATEGORY_CONFIG[category];
        folders.push({
          category,
          displayName: config.label,
          icon: config.icon,
          documents: docs.sort((a, b) => a.fileName.localeCompare(b.fileName)),
          totalSize: docs.reduce((sum, d) => sum + d.fileSize, 0)
        });
      }
    });

    return folders;
  }

  getAddenda(tenderId: number): Observable<TenderAddendum[]> {
    return this.http.get<ApiResponse<TenderAddendum[]>>(`${this.apiUrl}/tenders/${tenderId}/addenda`).pipe(
      map(response => response.data),
      catchError(error => throwError(() => error))
    );
  }

  acknowledgeAddendum(tenderId: number, addendumId: number): Observable<TenderAddendum> {
    return this.http.post<ApiResponse<TenderAddendum>>(
      `${this.apiUrl}/tenders/${tenderId}/addenda/${addendumId}/acknowledge`,
      {}
    ).pipe(
      map(response => response.data),
      catchError(error => throwError(() => error))
    );
  }

  downloadDocument(documentId: number): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/documents/${documentId}/download`, {
      responseType: 'blob'
    }).pipe(
      catchError(error => throwError(() => error))
    );
  }

  // ============================================
  // Clarification Methods
  // ============================================

  getClarifications(tenderId: number): Observable<PortalClarification[]> {
    return this.http.get<ApiResponse<PortalClarification[]>>(
      `${this.apiUrl}/tenders/${tenderId}/clarifications`
    ).pipe(
      map(response => response.data),
      catchError(error => throwError(() => error))
    );
  }

  getBulletins(tenderId: number): Observable<PortalBulletin[]> {
    return this.http.get<ApiResponse<PortalBulletin[]>>(
      `${this.apiUrl}/tenders/${tenderId}/bulletins`
    ).pipe(
      map(response => response.data),
      catchError(error => throwError(() => error))
    );
  }

  submitQuestion(data: SubmitQuestionDto): Observable<PortalClarification> {
    return this.http.post<ApiResponse<PortalClarification>>(
      `${this.apiUrl}/tenders/${data.tenderId}/clarifications`,
      data
    ).pipe(
      map(response => response.data),
      catchError(error => throwError(() => error))
    );
  }

  getBoqSections(tenderId: number): Observable<BoqSectionOption[]> {
    return this.http.get<ApiResponse<BoqSectionOption[]>>(
      `${this.apiUrl}/tenders/${tenderId}/boq-sections`
    ).pipe(
      map(response => response.data),
      catchError(error => throwError(() => error))
    );
  }

  downloadBulletinPdf(bulletinId: number): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/bulletins/${bulletinId}/pdf`, {
      responseType: 'blob'
    }).pipe(
      catchError(error => throwError(() => error))
    );
  }

  // ============================================
  // Bid Submission Methods
  // ============================================

  getDraftBid(tenderId: number): Observable<PortalBidSubmission | null> {
    return this.http.get<ApiResponse<PortalBidSubmission | null>>(
      `${this.apiUrl}/tenders/${tenderId}/bid/draft`
    ).pipe(
      map(response => response.data),
      catchError(error => {
        if (error.status === 404) {
          return of(null);
        }
        return throwError(() => error);
      })
    );
  }

  uploadBidDocument(
    tenderId: number,
    documentType: PortalBidDocumentType,
    file: File
  ): Observable<PortalBidDocument> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('documentType', documentType);

    // Initialize progress tracking
    const progressMap = this._uploadProgress.value;
    progressMap.set(documentType, {
      documentType,
      fileName: file.name,
      progress: 0,
      status: 'uploading'
    });
    this._uploadProgress.next(new Map(progressMap));

    return this.http.post<ApiResponse<PortalBidDocument>>(
      `${this.apiUrl}/tenders/${tenderId}/bid/documents`,
      formData,
      {
        reportProgress: true,
        observe: 'events'
      }
    ).pipe(
      tap((event: HttpEvent<ApiResponse<PortalBidDocument>>) => {
        if (event.type === HttpEventType.UploadProgress && event.total) {
          const progress = Math.round((100 * event.loaded) / event.total);
          const progressMap = this._uploadProgress.value;
          const currentProgress = progressMap.get(documentType);
          if (currentProgress) {
            progressMap.set(documentType, { ...currentProgress, progress, status: 'uploading' });
            this._uploadProgress.next(new Map(progressMap));
          }
        }
      }),
      map(event => {
        if (event.type === HttpEventType.Response) {
          const progressMap = this._uploadProgress.value;
          progressMap.set(documentType, {
            documentType,
            fileName: file.name,
            progress: 100,
            status: 'completed'
          });
          this._uploadProgress.next(new Map(progressMap));
          return event.body!.data;
        }
        return null as unknown as PortalBidDocument;
      }),
      catchError(error => {
        const progressMap = this._uploadProgress.value;
        const currentProgress = progressMap.get(documentType);
        if (currentProgress) {
          progressMap.set(documentType, {
            ...currentProgress,
            status: 'error',
            error: error.error?.message || 'Upload failed'
          });
          this._uploadProgress.next(new Map(progressMap));
        }
        return throwError(() => error);
      })
    ) as Observable<PortalBidDocument>;
  }

  deleteBidDocument(tenderId: number, documentId: number): Observable<void> {
    return this.http.delete<ApiResponse<void>>(
      `${this.apiUrl}/tenders/${tenderId}/bid/documents/${documentId}`
    ).pipe(
      map(response => response.data),
      catchError(error => throwError(() => error))
    );
  }

  submitBid(data: SubmitBidDto): Observable<PortalBidReceipt> {
    this._isLoading.set(true);

    return this.http.post<ApiResponse<PortalBidReceipt>>(
      `${this.apiUrl}/tenders/${data.tenderId}/bid/submit`,
      data
    ).pipe(
      tap(() => this._isLoading.set(false)),
      map(response => response.data),
      catchError(error => {
        this._isLoading.set(false);
        return throwError(() => error);
      })
    );
  }

  getBidReceipt(bidId: number): Observable<PortalBidReceipt> {
    return this.http.get<ApiResponse<PortalBidReceipt>>(
      `${this.apiUrl}/bids/${bidId}/receipt`
    ).pipe(
      map(response => response.data),
      catchError(error => throwError(() => error))
    );
  }

  downloadReceiptPdf(bidId: number): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/bids/${bidId}/receipt/pdf`, {
      responseType: 'blob'
    }).pipe(
      catchError(error => throwError(() => error))
    );
  }

  clearUploadProgress(): void {
    this._uploadProgress.next(new Map());
  }

  // ============================================
  // Utility Methods
  // ============================================

  getDeadlineCountdown(deadline: Date | string): {
    days: number;
    hours: number;
    minutes: number;
    seconds: number;
    isExpired: boolean;
    totalSeconds: number;
  } {
    const deadlineDate = new Date(deadline);
    const now = new Date();
    const diff = deadlineDate.getTime() - now.getTime();

    if (diff <= 0) {
      return { days: 0, hours: 0, minutes: 0, seconds: 0, isExpired: true, totalSeconds: 0 };
    }

    const totalSeconds = Math.floor(diff / 1000);
    const days = Math.floor(totalSeconds / (60 * 60 * 24));
    const hours = Math.floor((totalSeconds % (60 * 60 * 24)) / (60 * 60));
    const minutes = Math.floor((totalSeconds % (60 * 60)) / 60);
    const seconds = totalSeconds % 60;

    return { days, hours, minutes, seconds, isExpired: false, totalSeconds };
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}
