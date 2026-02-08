import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { ApiService } from './api.service';
import { PaginatedResponse, QueryParams } from '../models';

export interface TenderDocument {
  id: string;
  tenderId: string;
  fileName: string;
  contentType: string;
  fileSize: number;
  folderPath: string;
  version: number;
  uploadedBy: string;
  uploadedAt: string;
  isLatestVersion: boolean;
}

export interface DocumentFolder {
  name: string;
  path: string;
  documentCount: number;
  subFolders?: DocumentFolder[];
}

export interface DocumentDownloadResult {
  url: string;
}

export interface DocumentQueryParams extends QueryParams {
  folder?: string;
  latestOnly?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class DocumentService {
  private readonly api = inject(ApiService);

  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  /**
   * Get paginated list of documents for a tender.
   */
  getDocuments(tenderId: number, params?: DocumentQueryParams): Observable<PaginatedResponse<TenderDocument>> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.getList<TenderDocument>(`/tenders/${tenderId}/documents`, params as QueryParams).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load documents');
        return throwError(() => error);
      })
    );
  }

  /**
   * Upload a document to a tender.
   */
  uploadDocument(tenderId: number, file: File, folderPath: string): Observable<TenderDocument> {
    this._isLoading.set(true);
    this._error.set(null);

    const formData = new FormData();
    formData.append('File', file);
    formData.append('FolderPath', folderPath);

    return this.api.upload<TenderDocument>(`/tenders/${tenderId}/documents/upload`, formData).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to upload document');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get a presigned download URL for a document.
   */
  downloadDocument(tenderId: number, docId: string): Observable<DocumentDownloadResult> {
    return this.api.get<DocumentDownloadResult>(`/tenders/${tenderId}/documents/${docId}/download`).pipe(
      catchError(error => {
        this._error.set(error.message || 'Failed to get download URL');
        return throwError(() => error);
      })
    );
  }

  /**
   * Delete a document.
   */
  deleteDocument(tenderId: number, docId: string, deleteAllVersions: boolean = false): Observable<void> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.delete<void>(`/tenders/${tenderId}/documents/${docId}?deleteAllVersions=${deleteAllVersions}`).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to delete document');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get folder list for a tender.
   */
  getFolders(tenderId: number): Observable<DocumentFolder[]> {
    return this.api.get<DocumentFolder[]>(`/tenders/${tenderId}/documents/folders`).pipe(
      catchError(error => {
        this._error.set(error.message || 'Failed to load folders');
        return throwError(() => error);
      })
    );
  }

  /**
   * Create a new folder.
   */
  createFolder(tenderId: number, folderName: string, parentPath?: string): Observable<DocumentFolder> {
    return this.api.post<DocumentFolder>(`/tenders/${tenderId}/documents/folders`, {
      folderName,
      parentPath: parentPath || null
    }).pipe(
      catchError(error => {
        this._error.set(error.message || 'Failed to create folder');
        return throwError(() => error);
      })
    );
  }

  clearError(): void {
    this._error.set(null);
  }
}
