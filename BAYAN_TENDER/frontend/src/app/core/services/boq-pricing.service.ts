import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, catchError, throwError, map } from 'rxjs';
import { ApiService } from './api.service';
import { BoqTreeNode, PricingLevel } from '../models/boq.model';

export interface PricingEntry {
  boqItemId?: string;
  boqSectionId?: string;
  unitRate: number;
  amount: number;
  notes?: string;
}

export interface PricingView {
  tenderId: string;
  pricingLevel: PricingLevel;
  sections: PricingViewSection[];
  grandTotal: number;
}

export interface PricingViewSection {
  sectionId: string;
  sectionNumber: string;
  title: string;
  items: PricingViewItem[];
  subtotal: number;
}

export interface PricingViewItem {
  itemId: string;
  itemNumber: string;
  description: string;
  quantity: number;
  uom: string;
  unitRate: number | null;
  amount: number | null;
  isGroup: boolean;
  parentItemId?: string | null;
  childItems?: PricingViewItem[];
}

/** Raw backend response shape (ContractorPricingViewDto) */
interface BackendPricingResponse {
  tenderId: string;
  pricingLevel: PricingLevel;
  nodes: BackendPricingNode[];
  draft?: {
    draftId?: string;
    lastSavedAt?: string;
    entries: { nodeId: string; unitRate?: number; lumpSum?: number; amount?: number }[];
    grandTotal: number;
    completionPercentage: number;
  };
}

interface BackendPricingNode {
  id: string;
  nodeType: string;
  number: string;
  description: string;
  quantity?: number;
  uom?: string;
  isPriceable: boolean;
  isReadOnly: boolean;
  children?: BackendPricingNode[];
}

@Injectable({ providedIn: 'root' })
export class BoqPricingService {
  private readonly api = inject(ApiService);

  private readonly _isLoading = signal(false);
  private readonly _error = signal<string | null>(null);

  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  /**
   * Get the contractor's pricing view for a tender.
   * Maps the backend ContractorPricingViewDto (nodes tree) to the
   * frontend PricingView (sections + items) shape.
   */
  getContractorView(tenderId: string): Observable<PricingView> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.get<BackendPricingResponse>(`/portal/tenders/${tenderId}/boq/pricing-view`).pipe(
      map(response => this.mapBackendResponse(response)),
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to load pricing view');
        return throwError(() => error);
      })
    );
  }

  /** Maps backend ContractorPricingViewDto → frontend PricingView */
  private mapBackendResponse(response: BackendPricingResponse): PricingView {
    const draftEntries = new Map<string, { unitRate?: number; lumpSum?: number; amount?: number }>();
    if (response.draft?.entries) {
      for (const entry of response.draft.entries) {
        draftEntries.set(entry.nodeId, entry);
      }
    }

    const sections: PricingViewSection[] = (response.nodes ?? [])
      .filter(n => n.nodeType === 'bill')
      .map(billNode => {
        const items = this.mapNodeChildrenToItems(billNode.children ?? [], draftEntries);
        return {
          sectionId: billNode.id as any,
          sectionNumber: billNode.number,
          title: billNode.description,
          items,
          subtotal: draftEntries.get(billNode.id)?.lumpSum ?? 0
        };
      });

    return {
      tenderId: response.tenderId as any,
      pricingLevel: response.pricingLevel,
      sections,
      grandTotal: response.draft?.grandTotal ?? 0
    };
  }

  /** Recursively maps backend PricingNodeDto children → PricingViewItem[] */
  private mapNodeChildrenToItems(
    nodes: BackendPricingNode[],
    draftEntries: Map<string, { unitRate?: number; lumpSum?: number; amount?: number }>
  ): PricingViewItem[] {
    return nodes.map(node => {
      const draftEntry = draftEntries.get(node.id);
      const childItems = node.children?.length
        ? this.mapNodeChildrenToItems(node.children, draftEntries)
        : undefined;

      return {
        itemId: node.id as any,
        itemNumber: node.number,
        description: node.description,
        quantity: node.quantity ?? 0,
        uom: node.uom ?? '',
        unitRate: draftEntry?.unitRate ?? null,
        amount: draftEntry?.amount ?? null,
        isGroup: node.isReadOnly && !!(node.children?.length),
        parentItemId: null,
        childItems
      };
    });
  }

  /**
   * Save pricing draft (auto-save).
   * Transforms frontend PricingEntry to backend PricingEntryDto format.
   */
  saveDraft(tenderId: string, entries: PricingEntry[]): Observable<void> {
    const backendEntries = this.mapEntriesToBackend(entries);
    return this.api.put<void>(`/portal/tenders/${tenderId}/boq/pricing-draft`, { entries: backendEntries }).pipe(
      catchError(error => {
        this._error.set(error.message || 'Failed to save draft');
        return throwError(() => error);
      })
    );
  }

  /**
   * Submit finalized pricing.
   * Transforms frontend PricingEntry to backend PricingEntryDto format.
   */
  submitPricing(tenderId: string, entries: PricingEntry[]): Observable<{ receiptId: string }> {
    this._isLoading.set(true);
    this._error.set(null);

    const backendEntries = this.mapEntriesToBackend(entries);
    return this.api.post<{ receiptId: string }>(`/portal/tenders/${tenderId}/boq/pricing-submit`, { entries: backendEntries }).pipe(
      tap(() => this._isLoading.set(false)),
      catchError(error => {
        this._isLoading.set(false);
        this._error.set(error.message || 'Failed to submit pricing');
        return throwError(() => error);
      })
    );
  }

  /** Maps frontend PricingEntry[] → backend PricingEntryDto[] */
  private mapEntriesToBackend(entries: PricingEntry[]): { nodeId: any; unitRate?: number; lumpSum?: number; amount?: number }[] {
    return entries.map(entry => ({
      nodeId: entry.boqSectionId ?? entry.boqItemId,
      unitRate: entry.unitRate || undefined,
      lumpSum: entry.boqSectionId ? entry.amount : undefined,
      amount: entry.amount || undefined
    }));
  }

  /**
   * Pure function: compute roll-up totals from leaf items up to bills.
   * Returns a map of sectionId/itemId -> computed amount.
   */
  calculateRollups(nodes: BoqTreeNode[], pricingLevel: PricingLevel): Map<string, number> {
    const rollups = new Map<string, number>();
    this.computeNodeRollup(nodes, rollups);
    return rollups;
  }

  private computeNodeRollup(nodes: BoqTreeNode[], rollups: Map<string, number>): number {
    let total = 0;
    for (const node of nodes) {
      if (node.children?.length) {
        const childTotal = this.computeNodeRollup(node.children, rollups);
        rollups.set(node.key, childTotal);
        total += childTotal;
      } else if (node.type === 'item') {
        const amount = node.amount ?? 0;
        rollups.set(node.key, amount);
        total += amount;
      }
    }
    return total;
  }

  clearError(): void {
    this._error.set(null);
  }
}
