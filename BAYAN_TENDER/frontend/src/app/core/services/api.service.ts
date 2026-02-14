import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { ApiResponse, PaginatedResponse, QueryParams } from '../models';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  private buildHttpParams(params?: QueryParams): HttpParams {
    let httpParams = new HttpParams();
    if (!params) return httpParams;

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        httpParams = httpParams.set(key, String(value));
      }
    });

    return httpParams;
  }

  private handleError = (error: HttpErrorResponse): Observable<never> => {
    let errorMessage = 'An unexpected error occurred';
    const validationErrors = this.extractValidationErrors(error.error?.errors);

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = error.error.message;
    } else {
      // Server-side error
      if (error.error?.message) {
        errorMessage = error.error.message;
        if (error.status === 400 && validationErrors.length > 0) {
          errorMessage = `${errorMessage}: ${validationErrors.join('; ')}`;
        }
      } else if (error.status === 0) {
        errorMessage = 'Unable to connect to the server';
      } else if (error.status === 401) {
        errorMessage = 'Unauthorized access';
      } else if (error.status === 403) {
        errorMessage = 'Access forbidden';
      } else if (error.status === 404) {
        errorMessage = 'Resource not found';
      } else if (error.status === 500) {
        errorMessage = 'Internal server error';
      }
    }

    return throwError(() => ({
      message: errorMessage,
      status: error.status,
      errors: validationErrors
    }));
  };

  private extractValidationErrors(errors: unknown): string[] {
    if (!Array.isArray(errors)) {
      return [];
    }

    return errors
      .map((error: any) => {
        const message = typeof error?.message === 'string' ? error.message.trim() : '';
        if (!message) return null;

        const property = typeof error?.property === 'string' ? error.property.trim() : '';
        return property ? `${property}: ${message}` : message;
      })
      .filter((message: string | null): message is string => Boolean(message));
  }

  get<T>(endpoint: string, params?: QueryParams): Observable<T> {
    return this.http.get<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, {
      params: this.buildHttpParams(params)
    }).pipe(
      map(response => response.data),
      catchError(this.handleError)
    );
  }

  getList<T>(endpoint: string, params?: QueryParams): Observable<PaginatedResponse<T>> {
    return this.http.get<ApiResponse<any>>(`${this.baseUrl}${endpoint}`, {
      params: this.buildHttpParams(params)
    }).pipe(
      map(response => {
        const raw = response.data;
        // Backend PaginatedList returns a flat structure with items, pageNumber, totalCount, etc.
        // Map it to the frontend PaginatedResponse<T> shape.
        if (raw && raw.items && !raw.pagination) {
          return {
            items: raw.items,
            pagination: {
              currentPage: raw.pageNumber ?? raw.page ?? 1,
              pageSize: raw.pageSize ?? 10,
              totalItems: raw.totalCount ?? raw.total ?? 0,
              totalPages: raw.totalPages ?? 1,
              hasNextPage: raw.hasNextPage ?? false,
              hasPreviousPage: raw.hasPreviousPage ?? false
            }
          } as PaginatedResponse<T>;
        }
        return raw as PaginatedResponse<T>;
      }),
      catchError(this.handleError)
    );
  }

  post<T>(endpoint: string, data: unknown): Observable<T> {
    return this.http.post<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, data).pipe(
      map(response => response.data),
      catchError(this.handleError)
    );
  }

  put<T>(endpoint: string, data: unknown): Observable<T> {
    return this.http.put<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, data).pipe(
      map(response => response?.data ?? (null as unknown as T)),
      catchError(this.handleError)
    );
  }

  patch<T>(endpoint: string, data: unknown): Observable<T> {
    return this.http.patch<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, data).pipe(
      map(response => response.data),
      catchError(this.handleError)
    );
  }

  delete<T>(endpoint: string): Observable<T> {
    return this.http.delete<ApiResponse<T>>(`${this.baseUrl}${endpoint}`).pipe(
      map(response => (response?.data ?? undefined) as T),
      catchError(this.handleError)
    );
  }

  upload<T>(endpoint: string, formData: FormData): Observable<T> {
    return this.http.post<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, formData).pipe(
      map(response => response.data),
      catchError(this.handleError)
    );
  }

  download(endpoint: string, filename?: string): Observable<Blob> {
    return this.http.get(`${this.baseUrl}${endpoint}`, {
      responseType: 'blob'
    }).pipe(
      catchError(this.handleError)
    );
  }

  downloadPost(endpoint: string, data: unknown): Observable<Blob> {
    return this.http.post(`${this.baseUrl}${endpoint}`, data, {
      responseType: 'blob'
    }).pipe(
      catchError(this.handleError)
    );
  }
}
