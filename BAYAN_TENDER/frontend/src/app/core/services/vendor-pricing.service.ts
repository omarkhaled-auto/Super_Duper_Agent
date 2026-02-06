import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpParams } from '@angular/common/http';
import { Observable, tap, finalize } from 'rxjs';
import { ApiService } from './api.service';
import {
  VendorPricingDashboard,
  VendorTrends,
  VendorListItem,
  VendorItemRate,
  VendorComparison
} from '../models/vendor-pricing.model';
import { PaginatedResponse } from '../models';

@Injectable({
  providedIn: 'root'
})
export class VendorPricingService {
  private readonly api = inject(ApiService);

  // State signals
  private readonly _isLoading = signal(false);
  private readonly _dashboard = signal<VendorPricingDashboard | null>(null);
  private readonly _selectedVendorTrends = signal<VendorTrends | null>(null);
  private readonly _error = signal<string | null>(null);

  // Public computed values
  readonly isLoading = computed(() => this._isLoading());
  readonly dashboard = computed(() => this._dashboard());
  readonly selectedVendorTrends = computed(() => this._selectedVendorTrends());
  readonly error = computed(() => this._error());

  /**
   * Gets dashboard data for vendor pricing.
   */
  getDashboard(params?: {
    fromDate?: Date;
    toDate?: Date;
    tradeSpecialization?: string;
    topVendorsLimit?: number;
    recentSnapshotsLimit?: number;
  }): Observable<VendorPricingDashboard> {
    this._isLoading.set(true);
    this._error.set(null);

    const queryParams: Record<string, string | number> = {};
    if (params?.fromDate) queryParams['fromDate'] = params.fromDate.toISOString();
    if (params?.toDate) queryParams['toDate'] = params.toDate.toISOString();
    if (params?.tradeSpecialization) queryParams['tradeSpecialization'] = params.tradeSpecialization;
    if (params?.topVendorsLimit) queryParams['topVendorsLimit'] = params.topVendorsLimit;
    if (params?.recentSnapshotsLimit) queryParams['recentSnapshotsLimit'] = params.recentSnapshotsLimit;

    return this.api.get<VendorPricingDashboard>('/vendor-pricing/dashboard', queryParams).pipe(
      tap(data => this._dashboard.set(data)),
      finalize(() => this._isLoading.set(false))
    );
  }

  /**
   * Gets rate trends for a specific vendor.
   */
  getVendorTrends(bidderId: string, params?: {
    fromDate?: Date;
    toDate?: Date;
    maxItemTrends?: number;
    includeItemHistory?: boolean;
    includeTenderParticipation?: boolean;
  }): Observable<VendorTrends> {
    this._isLoading.set(true);
    this._error.set(null);

    const queryParams: Record<string, string | number | boolean> = {};
    if (params?.fromDate) queryParams['fromDate'] = params.fromDate.toISOString();
    if (params?.toDate) queryParams['toDate'] = params.toDate.toISOString();
    if (params?.maxItemTrends) queryParams['maxItemTrends'] = params.maxItemTrends;
    if (params?.includeItemHistory !== undefined) queryParams['includeItemHistory'] = params.includeItemHistory;
    if (params?.includeTenderParticipation !== undefined) queryParams['includeTenderParticipation'] = params.includeTenderParticipation;

    return this.api.get<VendorTrends>(`/vendor-pricing/trends/${bidderId}`, queryParams).pipe(
      tap(data => this._selectedVendorTrends.set(data)),
      finalize(() => this._isLoading.set(false))
    );
  }

  /**
   * Gets a paginated list of vendors with pricing data.
   */
  getVendors(params?: {
    page?: number;
    pageSize?: number;
    search?: string;
    tradeSpecialization?: string;
    onlyWithPricingData?: boolean;
    isActive?: boolean;
  }): Observable<PaginatedResponse<VendorListItem>> {
    const queryParams: Record<string, string | number | boolean> = {};
    if (params?.page) queryParams['page'] = params.page;
    if (params?.pageSize) queryParams['pageSize'] = params.pageSize;
    if (params?.search) queryParams['search'] = params.search;
    if (params?.tradeSpecialization) queryParams['tradeSpecialization'] = params.tradeSpecialization;
    if (params?.onlyWithPricingData !== undefined) queryParams['onlyWithPricingData'] = params.onlyWithPricingData;
    if (params?.isActive !== undefined) queryParams['isActive'] = params.isActive;

    return this.api.getList<VendorListItem>('/vendor-pricing/vendors', queryParams);
  }

  /**
   * Gets rates for a specific vendor.
   */
  getVendorRates(bidderId: string, params?: {
    page?: number;
    pageSize?: number;
    itemDescription?: string;
    uom?: string;
    tenderId?: string;
    latestOnly?: boolean;
  }): Observable<PaginatedResponse<VendorItemRate>> {
    const queryParams: Record<string, string | number | boolean> = {};
    if (params?.page) queryParams['page'] = params.page;
    if (params?.pageSize) queryParams['pageSize'] = params.pageSize;
    if (params?.itemDescription) queryParams['itemDescription'] = params.itemDescription;
    if (params?.uom) queryParams['uom'] = params.uom;
    if (params?.tenderId) queryParams['tenderId'] = params.tenderId;
    if (params?.latestOnly !== undefined) queryParams['latestOnly'] = params.latestOnly;

    return this.api.getList<VendorItemRate>(`/vendor-pricing/vendors/${bidderId}/rates`, queryParams);
  }

  /**
   * Compares rates between multiple vendors.
   */
  compareVendors(request: {
    bidderIds: string[];
    itemDescriptions?: string[];
    uom?: string;
    latestRatesOnly?: boolean;
    maxItems?: number;
  }): Observable<VendorComparison> {
    return this.api.post<VendorComparison>('/vendor-pricing/compare', request);
  }

  /**
   * Exports vendor pricing data to Excel.
   */
  exportToExcel(params?: {
    bidderIds?: string[];
    fromDate?: Date;
    toDate?: Date;
    tradeSpecialization?: string;
    tenderId?: string;
    includeItemDetails?: boolean;
    includeSummary?: boolean;
  }): Observable<Blob> {
    let httpParams = new HttpParams();

    if (params?.bidderIds?.length) {
      params.bidderIds.forEach(id => {
        httpParams = httpParams.append('bidderIds', id);
      });
    }
    if (params?.fromDate) httpParams = httpParams.set('fromDate', params.fromDate.toISOString());
    if (params?.toDate) httpParams = httpParams.set('toDate', params.toDate.toISOString());
    if (params?.tradeSpecialization) httpParams = httpParams.set('tradeSpecialization', params.tradeSpecialization);
    if (params?.tenderId) httpParams = httpParams.set('tenderId', params.tenderId);
    if (params?.includeItemDetails !== undefined) httpParams = httpParams.set('includeItemDetails', String(params.includeItemDetails));
    if (params?.includeSummary !== undefined) httpParams = httpParams.set('includeSummary', String(params.includeSummary));

    return this.api.download('/vendor-pricing/export');
  }

  /**
   * Downloads the exported file.
   */
  downloadExport(params?: {
    bidderIds?: string[];
    fromDate?: Date;
    toDate?: Date;
    tradeSpecialization?: string;
    tenderId?: string;
    includeItemDetails?: boolean;
    includeSummary?: boolean;
  }): void {
    this.exportToExcel(params).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `VendorPricing_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      },
      error: (err) => {
        console.error('Failed to export vendor pricing:', err);
        this._error.set('Failed to export vendor pricing data');
      }
    });
  }

  /**
   * Clears the current error.
   */
  clearError(): void {
    this._error.set(null);
  }
}
