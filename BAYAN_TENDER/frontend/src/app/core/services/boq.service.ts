import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError, map, switchMap } from 'rxjs';
import { ApiService } from './api.service';
import {
  BoqSection,
  BoqItem,
  BoqTreeNode,
  BoqItemType,
  CreateBoqSectionDto,
  UpdateBoqSectionDto,
  CreateBoqItemDto,
  UpdateBoqItemDto,
  BoqImportMapping,
  BoqImportResult,
  BoqImportRow,
  BoqExportOptions,
  BoqSummary
} from '../models/boq.model';

/** Maps backend numeric BoqItemType enum to frontend string values */
const ITEM_TYPE_FROM_BACKEND: Record<number, BoqItemType> = {
  0: 'base',
  1: 'alternate',
  2: 'provisional_sum',
  3: 'daywork'
};

/** Maps frontend string BoqItemType to backend numeric enum */
const ITEM_TYPE_TO_BACKEND: Record<BoqItemType, number> = {
  base: 0,
  alternate: 1,
  provisional_sum: 2,
  daywork: 3
};

@Injectable({
  providedIn: 'root'
})
export class BoqService {
  private readonly api = inject(ApiService);

  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  /** Tracks the current tender context for operations that need tenderId in the URL. */
  private _currentTenderId: number | null = null;

  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  /**
   * Get all BOQ sections for a tender.
   * Derives flat section list from the hierarchical tree endpoint.
   */
  getSections(tenderId: number): Observable<BoqSection[]> {
    this._isLoading.set(true);
    this._error.set(null);
    this._currentTenderId = tenderId;

    return this.api.get<any[]>(`/tenders/${tenderId}/boq`).pipe(
      map(tree => this.flattenSectionsFromTree(tree, tenderId)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load BOQ sections');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get all BOQ items for a tender.
   * Derives flat item list from the hierarchical tree endpoint.
   */
  getItems(tenderId: number): Observable<BoqItem[]> {
    this._isLoading.set(true);
    this._error.set(null);
    this._currentTenderId = tenderId;

    return this.api.get<any[]>(`/tenders/${tenderId}/boq`).pipe(
      map(tree => this.flattenItemsFromTree(tree, tenderId)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load BOQ items');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get BOQ as tree structure for TreeTable display
   */
  getBoqTree(tenderId: number): Observable<BoqTreeNode[]> {
    this._isLoading.set(true);
    this._error.set(null);
    this._currentTenderId = tenderId;

    return this.api.get<any[]>(`/tenders/${tenderId}/boq`).pipe(
      map(backendNodes => backendNodes.map(node => this.mapBackendTreeNode(node, tenderId))),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load BOQ tree');
        return throwError(() => error);
      })
    );
  }

  /**
   * Maps a backend BoqTreeNodeDto to the frontend BoqTreeNode.
   * Backend returns sections with nested children and items arrays.
   */
  private mapBackendTreeNode(node: any, tenderId: number): BoqTreeNode {
    const section: BoqSection = {
      id: node.id,
      tenderId,
      parentSectionId: node.parentSectionId ?? null,
      sectionNumber: node.sectionNumber,
      title: node.title,
      sortOrder: node.sortOrder,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      itemCount: (node.items ?? []).length,
      totalValue: 0
    };

    const childSectionNodes: BoqTreeNode[] = (node.children ?? [])
      .map((child: any) => this.mapBackendTreeNode(child, tenderId));

    const itemNodes: BoqTreeNode[] = (node.items ?? [])
      .map((item: any) => this.mapBackendItemToTreeNode(item, tenderId));

    const children = [...childSectionNodes, ...itemNodes];

    return {
      key: `section-${node.id}`,
      data: section,
      type: 'section',
      children: children.length > 0 ? children : undefined,
      expanded: true,
      itemNumber: node.sectionNumber,
      description: node.title,
      quantity: null,
      uom: '',
      itemType: null
    };
  }

  /**
   * Maps a backend BoqItemDto to a frontend BoqTreeNode of type 'item'.
   */
  private mapBackendItemToTreeNode(item: any, tenderId: number): BoqTreeNode {
    const mapped = this.mapBackendItem(item, tenderId);
    return {
      key: `item-${item.id}`,
      data: mapped,
      type: 'item',
      itemNumber: mapped.itemNumber,
      description: mapped.description,
      quantity: mapped.quantity,
      uom: mapped.uom,
      itemType: mapped.type
    };
  }

  /**
   * Maps a backend BoqItemDto to a frontend BoqItem.
   */
  private mapBackendItem(item: any, tenderId: number): BoqItem {
    return {
      id: item.id,
      tenderId,
      sectionId: item.sectionId,
      itemNumber: item.itemNumber,
      description: item.description,
      quantity: item.quantity,
      uom: item.uom,
      type: ITEM_TYPE_FROM_BACKEND[item.itemType] ?? 'base',
      notes: item.notes,
      sortOrder: item.sortOrder,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
  }

  /**
   * Maps a backend BoqSectionDto to a frontend BoqSection.
   */
  private mapBackendSection(section: any, tenderId: number): BoqSection {
    return {
      id: section.id,
      tenderId,
      parentSectionId: section.parentSectionId ?? null,
      sectionNumber: section.sectionNumber,
      title: section.title,
      sortOrder: section.sortOrder,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      itemCount: (section.items ?? []).length,
      totalValue: 0
    };
  }

  /**
   * Recursively flattens the backend tree into a flat array of BoqSection.
   */
  private flattenSectionsFromTree(nodes: any[], tenderId: number): BoqSection[] {
    const result: BoqSection[] = [];
    for (const node of nodes) {
      result.push(this.mapBackendSection(node, tenderId));
      if (node.children?.length) {
        result.push(...this.flattenSectionsFromTree(node.children, tenderId));
      }
    }
    return result;
  }

  /**
   * Recursively flattens the backend tree into a flat array of BoqItem.
   */
  private flattenItemsFromTree(nodes: any[], tenderId: number): BoqItem[] {
    const result: BoqItem[] = [];
    for (const node of nodes) {
      if (node.items?.length) {
        result.push(...node.items.map((item: any) => this.mapBackendItem(item, tenderId)));
      }
      if (node.children?.length) {
        result.push(...this.flattenItemsFromTree(node.children, tenderId));
      }
    }
    return result;
  }

  /**
   * Get BOQ summary statistics.
   * Computed client-side from the tree endpoint (no dedicated backend summary endpoint).
   */
  getSummary(tenderId: number): Observable<BoqSummary> {
    return this.api.get<any[]>(`/tenders/${tenderId}/boq`).pipe(
      map(tree => {
        const sections = this.flattenSectionsFromTree(tree, tenderId);
        const items = this.flattenItemsFromTree(tree, tenderId);

        const rootSections = sections.filter(s => !s.parentSectionId);
        const subSections = sections.filter(s => s.parentSectionId);

        const itemsByType: Record<BoqItemType, number> = {
          base: 0,
          alternate: 0,
          provisional_sum: 0,
          daywork: 0
        };

        items.forEach(item => {
          itemsByType[item.type]++;
        });

        return {
          totalSections: rootSections.length,
          totalSubsections: subSections.length,
          totalItems: items.length,
          itemsByType
        };
      })
    );
  }

  /**
   * Create a new BOQ section
   */
  createSection(data: CreateBoqSectionDto): Observable<BoqSection> {
    this._isLoading.set(true);
    this._error.set(null);

    const body = {
      sectionNumber: data.sectionNumber,
      title: data.title,
      sortOrder: 0,
      parentSectionId: data.parentSectionId ?? null
    };

    return this.api.post<any>(`/tenders/${data.tenderId}/boq/sections`, body).pipe(
      map(result => this.mapBackendSection(result, data.tenderId as number)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to create section');
        return throwError(() => error);
      })
    );
  }

  /**
   * Update an existing BOQ section
   */
  updateSection(id: number, data: UpdateBoqSectionDto): Observable<BoqSection> {
    this._isLoading.set(true);
    this._error.set(null);

    const tenderId = this._currentTenderId!;
    const body = {
      sectionNumber: data.sectionNumber ?? '',
      title: data.title ?? '',
      sortOrder: 0,
      parentSectionId: data.parentSectionId ?? null
    };

    return this.api.put<any>(`/tenders/${tenderId}/boq/sections/${id}`, body).pipe(
      map(result => this.mapBackendSection(result, tenderId)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update section');
        return throwError(() => error);
      })
    );
  }

  /**
   * Delete a BOQ section
   */
  deleteSection(id: number): Observable<void> {
    this._isLoading.set(true);
    this._error.set(null);

    const tenderId = this._currentTenderId!;

    return this.api.delete<void>(`/tenders/${tenderId}/boq/sections/${id}`).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to delete section');
        return throwError(() => error);
      })
    );
  }

  /**
   * Create a new BOQ item
   */
  createItem(data: CreateBoqItemDto): Observable<BoqItem> {
    this._isLoading.set(true);
    this._error.set(null);

    const body = {
      sectionId: data.sectionId,
      itemNumber: data.itemNumber,
      description: data.description,
      quantity: data.quantity,
      uom: data.uom,
      itemType: ITEM_TYPE_TO_BACKEND[data.type],
      notes: data.notes ?? null,
      sortOrder: 0
    };

    return this.api.post<any>(`/tenders/${data.tenderId}/boq/items`, body).pipe(
      map(result => this.mapBackendItem(result, data.tenderId as number)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to create item');
        return throwError(() => error);
      })
    );
  }

  /**
   * Update an existing BOQ item
   */
  updateItem(id: number, data: UpdateBoqItemDto): Observable<BoqItem> {
    this._isLoading.set(true);
    this._error.set(null);

    const tenderId = this._currentTenderId!;
    const body = {
      sectionId: data.sectionId,
      itemNumber: data.itemNumber ?? '',
      description: data.description ?? '',
      quantity: data.quantity ?? 0,
      uom: data.uom ?? '',
      itemType: data.type ? ITEM_TYPE_TO_BACKEND[data.type] : 0,
      notes: data.notes ?? null,
      sortOrder: 0
    };

    return this.api.put<any>(`/tenders/${tenderId}/boq/items/${id}`, body).pipe(
      map(result => this.mapBackendItem(result, tenderId)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to update item');
        return throwError(() => error);
      })
    );
  }

  /**
   * Delete a BOQ item
   */
  deleteItem(id: number): Observable<void> {
    this._isLoading.set(true);
    this._error.set(null);

    const tenderId = this._currentTenderId!;

    return this.api.delete<void>(`/tenders/${tenderId}/boq/items/${id}`).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to delete item');
        return throwError(() => error);
      })
    );
  }

  /**
   * Duplicate a BOQ item
   */
  duplicateItem(id: number): Observable<BoqItem> {
    const tenderId = this._currentTenderId!;

    return this.api.post<any>(`/tenders/${tenderId}/boq/items/${id}/duplicate`, {}).pipe(
      map(result => this.mapBackendItem(result, tenderId))
    );
  }

  /**
   * Upload an Excel file for import preview.
   * Returns the parsed preview with columns, sample rows, and suggested mappings.
   */
  uploadForPreview(tenderId: number, file: File): Observable<any> {
    this._isLoading.set(true);
    this._error.set(null);

    const formData = new FormData();
    formData.append('file', file);

    return this.api.upload<any>(`/tenders/${tenderId}/boq/import/upload`, formData).pipe(
      tap(preview => {
        this._lastImportSessionId = preview.importSessionId;
        this._isLoading.set(false);
      }),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to upload file');
        return throwError(() => error);
      })
    );
  }

  /**
   * Validate an already-uploaded import session with column mappings.
   * Returns validation results with row-level issues.
   */
  validateSession(tenderId: number, sessionId: string, mappings: any[]): Observable<any> {
    this._isLoading.set(true);
    this._error.set(null);

    const validateBody = {
      importSessionId: sessionId,
      mappings,
      sheetIndex: 0,
      headerRowOverride: null
    };

    return this.api.post<any>(`/tenders/${tenderId}/boq/import/validate`, validateBody).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to validate import');
        return throwError(() => error);
      })
    );
  }

  /**
   * Validate import data and return preview.
   * Uploads the file first, then validates with the provided column mapping.
   */
  validateImport(tenderId: number, file: File, mapping: BoqImportMapping): Observable<BoqImportResult> {
    this._isLoading.set(true);
    this._error.set(null);

    const formData = new FormData();
    formData.append('file', file);

    // Step 1: Upload file -> Step 2: Validate with mapping
    return this.api.upload<any>(`/tenders/${tenderId}/boq/import/upload`, formData).pipe(
      switchMap(preview => {
        const mappings = this.buildColumnMappings(mapping, preview.columns ?? []);
        const validateBody = {
          importSessionId: preview.importSessionId,
          mappings,
          sheetIndex: 0,
          headerRowOverride: null
        };

        // Store session ID for the execute step
        this._lastImportSessionId = preview.importSessionId;

        return this.api.post<any>(`/tenders/${tenderId}/boq/import/validate`, validateBody).pipe(
          map(validation => this.mapValidationToImportResult(validation, preview))
        );
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to validate import');
        return throwError(() => error);
      })
    );
  }

  /** Stored import session ID for the execute step. */
  private _lastImportSessionId: string | null = null;

  /**
   * Maps backend ImportValidationResultDto + ExcelPreviewDto to frontend BoqImportResult.
   */
  private mapValidationToImportResult(validation: any, preview: any): BoqImportResult {
    const issues: any[] = validation.issues ?? [];
    const rows: BoqImportRow[] = (preview.previewRows ?? []).map((row: any, i: number) => {
      const rowIssues = issues.filter((issue: any) => issue.rowNumber === i + 1);
      const errors = rowIssues.filter((issue: any) => issue.severity === 2).map((issue: any) => issue.message);
      const warnings = rowIssues.filter((issue: any) => issue.severity === 1).map((issue: any) => issue.message);
      const status: 'valid' | 'warning' | 'error' = errors.length > 0 ? 'error' : warnings.length > 0 ? 'warning' : 'valid';

      return {
        rowNumber: i + 1,
        data: row,
        status,
        errors: errors.length > 0 ? errors : undefined,
        warnings: warnings.length > 0 ? warnings : undefined
      };
    });

    return {
      totalRows: validation.totalRows ?? preview.totalRowCount ?? rows.length,
      validRows: validation.validCount ?? rows.filter(r => r.status === 'valid').length,
      warningRows: validation.warningCount ?? rows.filter(r => r.status === 'warning').length,
      errorRows: validation.errorCount ?? rows.filter(r => r.status === 'error').length,
      rows,
      detectedSections: (validation.detectedSections ?? []).map(
        (s: any) => `${s.sectionNumber} - ${s.title}`
      )
    };
  }

  /**
   * Import validated items (executes the import after validation)
   */
  importItems(tenderId: number, validRows: BoqImportRow[], clearExisting = false): Observable<{ imported: number; failed: number }> {
    this._isLoading.set(true);
    this._error.set(null);

    const body = {
      importSessionId: this._lastImportSessionId,
      clearExisting,
      defaultSectionTitle: null,
      skipWarnings: false
    };

    return this.api.post<any>(`/tenders/${tenderId}/boq/import/execute`, body).pipe(
      map(result => ({
        imported: result.importedItems ?? 0,
        failed: result.skippedRows ?? 0
      })),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to import items');
        return throwError(() => error);
      })
    );
  }

  /**
   * Export BOQ to Excel
   */
  exportToExcel(tenderId: number, options: BoqExportOptions): Observable<Blob> {
    this._isLoading.set(true);
    this._error.set(null);

    // Map frontend language option to backend TemplateLanguage enum (0=English, 1=Arabic, 2=Both)
    const languageMap: Record<string, number> = { en: 0, ar: 1, both: 2 };
    const language = languageMap[options.language] ?? 0;

    // Map frontend boolean columns to backend string array
    const columnNameMap: Record<string, string> = {
      section: 'Section',
      itemNumber: 'ItemNumber',
      description: 'Description',
      quantity: 'Quantity',
      uom: 'Uom',
      notes: 'Notes',
      unitRate: 'UnitRate',
      totalAmount: 'Amount'
    };
    const includeColumns = Object.entries(options.columns)
      .filter(([, enabled]) => enabled)
      .map(([key]) => columnNameMap[key])
      .filter(Boolean);

    // When lockColumns is true, lock the read-only columns; otherwise empty array
    const lockColumns = options.lockColumns
      ? includeColumns.filter(c => ['ItemNumber', 'Description', 'Quantity', 'Uom'].includes(c))
      : [];

    const dto = {
      includeColumns,
      lockColumns,
      includeInstructions: options.includeInstructions,
      language
    };

    return this.api.downloadPost(`/tenders/${tenderId}/boq/export-template`, dto).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to export BOQ');
        return throwError(() => error);
      })
    );
  }

  /**
   * Download sample import template.
   * Uses the current tender context or a generic template endpoint.
   */
  downloadTemplate(): Observable<Blob> {
    const tenderId = this._currentTenderId;
    if (!tenderId) {
      return throwError(() => new Error('No tender context set. Load BOQ data first.'));
    }

    return this.api.download(`/tenders/${tenderId}/boq/export-template?language=0&includeInstructions=true`);
  }

  /**
   * Builds backend ColumnMappingDto[] from frontend BoqImportMapping and detected columns.
   * Maps field names to backend BoqField enum values.
   */
  private buildColumnMappings(mapping: BoqImportMapping, columns: any[]): any[] {
    // Backend BoqField enum: None=0, ItemNumber=1, Description=2, Quantity=3,
    // Uom=4, SectionTitle=5, Notes=6, UnitRate=7, Amount=8, Specification=9
    const fieldMap: Record<string, number> = {
      itemNumber: 1,
      description: 2,
      quantity: 3,
      uom: 4,
      sectionTitle: 5,
      sectionNumber: 5,
      notes: 6,
      type: 0 // No direct backend mapping for 'type'
    };

    const result: any[] = [];
    for (const [field, columnHeader] of Object.entries(mapping)) {
      if (columnHeader && fieldMap[field] !== undefined && fieldMap[field] !== 0) {
        result.push({
          excelColumn: columnHeader,
          boqField: fieldMap[field],
          confidence: null,
          isAutoDetected: false
        });
      }
    }

    return result;
  }

  clearError(): void {
    this._error.set(null);
  }
}
