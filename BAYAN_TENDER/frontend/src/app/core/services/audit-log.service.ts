import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { PaginatedResult } from '../models/pagination.model';

export interface AuditLog {
  id: string;
  timestamp: string;
  userId: string | null;
  userEmail: string | null;
  userFullName: string | null;
  action: string;
  entityType: string;
  entityId: string | null;
  oldValues: string | null;
  newValues: string | null;
  ipAddress: string | null;
  userAgent: string | null;
}

export interface GetAuditLogsParams {
  page?: number;
  pageSize?: number;
  userId?: string;
  action?: string;
  entityType?: string;
  entityId?: string;
  startDate?: string;
  endDate?: string;
  search?: string;
}

/**
 * Service for accessing audit logs.
 */
@Injectable({
  providedIn: 'root'
})
export class AuditLogService {
  private readonly api = inject(ApiService);

  /**
   * Gets a paginated list of audit logs with optional filtering.
   */
  getAuditLogs(params: GetAuditLogsParams = {}): Observable<PaginatedResult<AuditLog>> {
    const queryParams: Record<string, string> = {};

    if (params.page) queryParams['page'] = params.page.toString();
    if (params.pageSize) queryParams['pageSize'] = params.pageSize.toString();
    if (params.userId) queryParams['userId'] = params.userId;
    if (params.action) queryParams['action'] = params.action;
    if (params.entityType) queryParams['entityType'] = params.entityType;
    if (params.entityId) queryParams['entityId'] = params.entityId;
    if (params.startDate) queryParams['startDate'] = params.startDate;
    if (params.endDate) queryParams['endDate'] = params.endDate;
    if (params.search) queryParams['search'] = params.search;

    return this.api.get<PaginatedResult<AuditLog>>('/admin/audit-logs', queryParams);
  }

  /**
   * Exports audit logs to a file format.
   */
  exportAuditLogs(params: GetAuditLogsParams = {}): Observable<PaginatedResult<AuditLog>> {
    // Get all matching logs for export
    return this.getAuditLogs({ ...params, pageSize: 10000 });
  }
}
