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

  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An unexpected error occurred';

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = error.error.message;
    } else {
      // Server-side error
      if (error.error?.message) {
        errorMessage = error.error.message;
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
      errors: error.error?.errors || []
    }));
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
    return this.http.get<ApiResponse<PaginatedResponse<T>>>(`${this.baseUrl}${endpoint}`, {
      params: this.buildHttpParams(params)
    }).pipe(
      map(response => response.data),
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
      map(response => response.data),
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
      map(response => response.data),
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
}
