import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError, of, delay, map } from 'rxjs';
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

@Injectable({
  providedIn: 'root'
})
export class BoqService {
  private readonly api = inject(ApiService);
  private readonly endpoint = '/boq';

  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  // Mock data for development
  private mockSections: BoqSection[] = [
    {
      id: 1,
      tenderId: 1,
      parentSectionId: null,
      sectionNumber: '1',
      title: 'General Requirements',
      description: 'General project requirements and preliminaries',
      sortOrder: 1,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15'),
      itemCount: 5,
      totalValue: 150000
    },
    {
      id: 2,
      tenderId: 1,
      parentSectionId: 1,
      sectionNumber: '1.1',
      title: 'Site Mobilization',
      description: 'Site setup and mobilization activities',
      sortOrder: 1,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15'),
      itemCount: 3,
      totalValue: 75000
    },
    {
      id: 3,
      tenderId: 1,
      parentSectionId: 1,
      sectionNumber: '1.2',
      title: 'Temporary Facilities',
      description: 'Temporary site facilities',
      sortOrder: 2,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15'),
      itemCount: 2,
      totalValue: 75000
    },
    {
      id: 4,
      tenderId: 1,
      parentSectionId: null,
      sectionNumber: '2',
      title: 'Civil Works',
      description: 'Civil and structural works',
      sortOrder: 2,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15'),
      itemCount: 8,
      totalValue: 500000
    },
    {
      id: 5,
      tenderId: 1,
      parentSectionId: 4,
      sectionNumber: '2.1',
      title: 'Earthworks',
      description: 'Excavation and earthworks',
      sortOrder: 1,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15'),
      itemCount: 4,
      totalValue: 200000
    },
    {
      id: 6,
      tenderId: 1,
      parentSectionId: 4,
      sectionNumber: '2.2',
      title: 'Concrete Works',
      description: 'Concrete supply and installation',
      sortOrder: 2,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15'),
      itemCount: 4,
      totalValue: 300000
    }
  ];

  private mockItems: BoqItem[] = [
    {
      id: 1,
      tenderId: 1,
      sectionId: 2,
      itemNumber: '1.1.1',
      description: 'Site establishment including temporary office, storage, and welfare facilities',
      quantity: 1,
      uom: 'LS',
      type: 'base',
      notes: 'As per site layout drawing',
      sortOrder: 1,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15')
    },
    {
      id: 2,
      tenderId: 1,
      sectionId: 2,
      itemNumber: '1.1.2',
      description: 'Site security and hoarding for the duration of the project',
      quantity: 500,
      uom: 'LM',
      type: 'base',
      sortOrder: 2,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15')
    },
    {
      id: 3,
      tenderId: 1,
      sectionId: 2,
      itemNumber: '1.1.3',
      description: 'Equipment mobilization and demobilization',
      quantity: 1,
      uom: 'LS',
      type: 'base',
      sortOrder: 3,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15')
    },
    {
      id: 4,
      tenderId: 1,
      sectionId: 3,
      itemNumber: '1.2.1',
      description: 'Portable toilets for site workers - monthly rental',
      quantity: 12,
      uom: 'MTH',
      type: 'base',
      sortOrder: 1,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15')
    },
    {
      id: 5,
      tenderId: 1,
      sectionId: 3,
      itemNumber: '1.2.2',
      description: 'Temporary power supply installation',
      quantity: 1,
      uom: 'LS',
      type: 'provisional_sum',
      notes: 'Subject to utility connection availability',
      sortOrder: 2,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15')
    },
    {
      id: 6,
      tenderId: 1,
      sectionId: 5,
      itemNumber: '2.1.1',
      description: 'Excavation in ordinary soil including disposal',
      quantity: 2500,
      uom: 'M3',
      type: 'base',
      sortOrder: 1,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15')
    },
    {
      id: 7,
      tenderId: 1,
      sectionId: 5,
      itemNumber: '2.1.2',
      description: 'Excavation in rock including disposal',
      quantity: 500,
      uom: 'M3',
      type: 'alternate',
      notes: 'If encountered during excavation',
      sortOrder: 2,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15')
    },
    {
      id: 8,
      tenderId: 1,
      sectionId: 5,
      itemNumber: '2.1.3',
      description: 'Backfilling with approved material',
      quantity: 1800,
      uom: 'M3',
      type: 'base',
      sortOrder: 3,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15')
    },
    {
      id: 9,
      tenderId: 1,
      sectionId: 5,
      itemNumber: '2.1.4',
      description: 'Dewatering - daywork rate',
      quantity: 100,
      uom: 'HR',
      type: 'daywork',
      notes: 'Rate per hour for dewatering equipment and operator',
      sortOrder: 4,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15')
    },
    {
      id: 10,
      tenderId: 1,
      sectionId: 6,
      itemNumber: '2.2.1',
      description: 'Supply and place Grade 40 concrete for foundations',
      quantity: 350,
      uom: 'M3',
      type: 'base',
      sortOrder: 1,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15')
    },
    {
      id: 11,
      tenderId: 1,
      sectionId: 6,
      itemNumber: '2.2.2',
      description: 'Supply and place Grade 40 concrete for columns',
      quantity: 200,
      uom: 'M3',
      type: 'base',
      sortOrder: 2,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15')
    },
    {
      id: 12,
      tenderId: 1,
      sectionId: 6,
      itemNumber: '2.2.3',
      description: 'Steel reinforcement including cutting, bending and fixing',
      quantity: 75000,
      uom: 'KG',
      type: 'base',
      sortOrder: 3,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15')
    },
    {
      id: 13,
      tenderId: 1,
      sectionId: 6,
      itemNumber: '2.2.4',
      description: 'Formwork to concrete surfaces',
      quantity: 1200,
      uom: 'M2',
      type: 'base',
      sortOrder: 4,
      createdAt: new Date('2026-01-15'),
      updatedAt: new Date('2026-01-15')
    }
  ];

  private lastSectionId = 6;
  private lastItemId = 13;

  /**
   * Get all BOQ sections for a tender
   */
  getSections(tenderId: number): Observable<BoqSection[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(300),
      map(() => this.mockSections.filter(s => s.tenderId === tenderId)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load BOQ sections');
        return throwError(() => error);
      })
    );
  }

  /**
   * Get all BOQ items for a tender
   */
  getItems(tenderId: number): Observable<BoqItem[]> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(300),
      map(() => this.mockItems.filter(i => i.tenderId === tenderId)),
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

    return of(null).pipe(
      delay(400),
      map(() => {
        const sections = this.mockSections.filter(s => s.tenderId === tenderId);
        const items = this.mockItems.filter(i => i.tenderId === tenderId);
        return this.buildTreeNodes(sections, items);
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load BOQ tree');
        return throwError(() => error);
      })
    );
  }

  /**
   * Build tree structure from flat sections and items
   */
  private buildTreeNodes(sections: BoqSection[], items: BoqItem[]): BoqTreeNode[] {
    const rootSections = sections
      .filter(s => !s.parentSectionId)
      .sort((a, b) => a.sortOrder - b.sortOrder);

    return rootSections.map(section => this.buildSectionNode(section, sections, items));
  }

  private buildSectionNode(section: BoqSection, allSections: BoqSection[], allItems: BoqItem[]): BoqTreeNode {
    const childSections = allSections
      .filter(s => s.parentSectionId === section.id)
      .sort((a, b) => a.sortOrder - b.sortOrder);

    const sectionItems = allItems
      .filter(i => i.sectionId === section.id)
      .sort((a, b) => a.sortOrder - b.sortOrder);

    const children: BoqTreeNode[] = [
      ...childSections.map(child => this.buildSectionNode(child, allSections, allItems)),
      ...sectionItems.map(item => this.buildItemNode(item))
    ];

    return {
      key: `section-${section.id}`,
      data: section,
      type: 'section',
      children: children.length > 0 ? children : undefined,
      expanded: true,
      itemNumber: section.sectionNumber,
      description: section.title,
      quantity: null,
      uom: '',
      itemType: null
    };
  }

  private buildItemNode(item: BoqItem): BoqTreeNode {
    return {
      key: `item-${item.id}`,
      data: item,
      type: 'item',
      itemNumber: item.itemNumber,
      description: item.description,
      quantity: item.quantity,
      uom: item.uom,
      itemType: item.type
    };
  }

  /**
   * Get BOQ summary statistics
   */
  getSummary(tenderId: number): Observable<BoqSummary> {
    return of(null).pipe(
      delay(200),
      map(() => {
        const sections = this.mockSections.filter(s => s.tenderId === tenderId);
        const items = this.mockItems.filter(i => i.tenderId === tenderId);

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

    return of(null).pipe(
      delay(300),
      map(() => {
        const newSection: BoqSection = {
          ...data,
          id: ++this.lastSectionId,
          sortOrder: this.mockSections.filter(s =>
            s.tenderId === data.tenderId && s.parentSectionId === data.parentSectionId
          ).length + 1,
          itemCount: 0,
          totalValue: 0,
          createdAt: new Date(),
          updatedAt: new Date()
        };
        this.mockSections.push(newSection);
        return newSection;
      }),
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

    return of(null).pipe(
      delay(300),
      map(() => {
        const index = this.mockSections.findIndex(s => s.id === id);
        if (index === -1) {
          throw new Error('Section not found');
        }
        const updated: BoqSection = {
          ...this.mockSections[index],
          ...data,
          updatedAt: new Date()
        };
        this.mockSections[index] = updated;
        return updated;
      }),
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

    return of(null).pipe(
      delay(300),
      map(() => {
        const index = this.mockSections.findIndex(s => s.id === id);
        if (index === -1) {
          throw new Error('Section not found');
        }
        // Also delete child sections and items
        const childSectionIds = this.getChildSectionIds(id);
        const allSectionIds = [id, ...childSectionIds];

        this.mockSections = this.mockSections.filter(s => !allSectionIds.includes(s.id));
        this.mockItems = this.mockItems.filter(i => !allSectionIds.includes(i.sectionId));
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to delete section');
        return throwError(() => error);
      })
    );
  }

  private getChildSectionIds(parentId: number): number[] {
    const children = this.mockSections.filter(s => s.parentSectionId === parentId);
    return children.flatMap(child => [child.id, ...this.getChildSectionIds(child.id)]);
  }

  /**
   * Create a new BOQ item
   */
  createItem(data: CreateBoqItemDto): Observable<BoqItem> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(300),
      map(() => {
        const newItem: BoqItem = {
          ...data,
          id: ++this.lastItemId,
          sortOrder: this.mockItems.filter(i => i.sectionId === data.sectionId).length + 1,
          createdAt: new Date(),
          updatedAt: new Date()
        };
        this.mockItems.push(newItem);
        return newItem;
      }),
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

    return of(null).pipe(
      delay(300),
      map(() => {
        const index = this.mockItems.findIndex(i => i.id === id);
        if (index === -1) {
          throw new Error('Item not found');
        }
        const updated: BoqItem = {
          ...this.mockItems[index],
          ...data,
          updatedAt: new Date()
        };
        this.mockItems[index] = updated;
        return updated;
      }),
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

    return of(null).pipe(
      delay(300),
      map(() => {
        const index = this.mockItems.findIndex(i => i.id === id);
        if (index === -1) {
          throw new Error('Item not found');
        }
        this.mockItems.splice(index, 1);
      }),
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
    const item = this.mockItems.find(i => i.id === id);
    if (!item) {
      return throwError(() => new Error('Item not found'));
    }

    return this.createItem({
      tenderId: item.tenderId,
      sectionId: item.sectionId,
      itemNumber: `${item.itemNumber}-copy`,
      description: `${item.description} (Copy)`,
      quantity: item.quantity,
      uom: item.uom,
      type: item.type,
      notes: item.notes
    });
  }

  /**
   * Validate import data and return preview
   */
  validateImport(tenderId: number, file: File, mapping: BoqImportMapping): Observable<BoqImportResult> {
    this._isLoading.set(true);
    this._error.set(null);

    // Mock implementation - in production, this would parse the Excel file
    return of(null).pipe(
      delay(1000),
      map(() => {
        // Simulated import result
        const result: BoqImportResult = {
          totalRows: 25,
          validRows: 20,
          warningRows: 3,
          errorRows: 2,
          rows: [
            {
              rowNumber: 1,
              data: { A: '3.1.1', B: 'New item description', C: 10, D: 'EA', E: 'Base' },
              status: 'valid'
            },
            {
              rowNumber: 2,
              data: { A: '3.1.2', B: 'Another item', C: 5, D: 'LS', E: 'Alternate' },
              status: 'valid'
            },
            {
              rowNumber: 3,
              data: { A: '3.1.3', B: 'Item with warning', C: 0, D: 'M2', E: 'Base' },
              status: 'warning',
              warnings: ['Quantity is zero']
            },
            {
              rowNumber: 4,
              data: { A: '', B: 'Missing item number', C: 10, D: 'EA', E: 'Base' },
              status: 'error',
              errors: ['Item number is required']
            }
          ],
          detectedSections: ['Section 3 - Mechanical Works', 'Section 3.1 - HVAC']
        };
        return result;
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to validate import');
        return throwError(() => error);
      })
    );
  }

  /**
   * Import validated items
   */
  importItems(tenderId: number, validRows: BoqImportRow[]): Observable<{ imported: number; failed: number }> {
    this._isLoading.set(true);
    this._error.set(null);

    return of(null).pipe(
      delay(1500),
      map(() => {
        // Mock implementation
        return {
          imported: validRows.filter(r => r.status === 'valid').length,
          failed: validRows.filter(r => r.status === 'error').length
        };
      }),
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

    return of(null).pipe(
      delay(1000),
      map(() => {
        // In production, this would generate an Excel file
        return new Blob([''], {
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        });
      }),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to export BOQ');
        return throwError(() => error);
      })
    );
  }

  /**
   * Download sample import template
   */
  downloadTemplate(): Observable<Blob> {
    return of(null).pipe(
      delay(500),
      map(() => {
        return new Blob([''], {
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        });
      })
    );
  }

  clearError(): void {
    this._error.set(null);
  }
}
