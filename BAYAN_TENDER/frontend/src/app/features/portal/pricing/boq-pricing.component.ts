import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
  inject,
  signal,
  computed,
  effect
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil, interval } from 'rxjs';

// PrimeNG
import { AccordionModule } from 'primeng/accordion';
import { CardModule } from 'primeng/card';
import { TreeTableModule } from 'primeng/treetable';
import { InputNumberModule } from 'primeng/inputnumber';
import { ButtonModule } from 'primeng/button';
import { ProgressBarModule } from 'primeng/progressbar';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { MessageModule } from 'primeng/message';
import { ToastModule } from 'primeng/toast';
import { MessageService, TreeNode } from 'primeng/api';

import { BoqPricingService, PricingEntry, PricingView, PricingViewSection, PricingViewItem } from '../../../core/services/boq-pricing.service';
import { PricingLevel } from '../../../core/models/boq.model';

@Component({
  selector: 'app-boq-pricing',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    AccordionModule,
    CardModule,
    TreeTableModule,
    InputNumberModule,
    ButtonModule,
    ProgressBarModule,
    TagModule,
    TooltipModule,
    MessageModule,
    ToastModule
  ],
  providers: [MessageService],
  template: `
    <p-toast></p-toast>

    <div class="boq-pricing-container" data-testid="boq-pricing">
      <!-- Header with completion and total -->
      <div class="pricing-header">
        <div class="completion-section">
          <span class="completion-label">Completion:</span>
          <p-progressBar
            [value]="completionPercent()"
            [style]="{ height: '20px', width: '200px' }"
            [showValue]="true"
          ></p-progressBar>
        </div>
        <div class="grand-total-section">
          <span class="total-label">Grand Total:</span>
          <span class="total-value">AED {{ grandTotal() | number:'1.0-2' }}</span>
        </div>
        @if (isDirty()) {
          <p-tag value="Unsaved changes" severity="warn" styleClass="ml-2"></p-tag>
        }
        @if (lastSaved()) {
          <span class="last-saved">Last saved: {{ lastSaved() }}</span>
        }
      </div>

      <!-- Validation Warnings -->
      @if (validationWarnings().length > 0) {
        <p-message
          severity="warn"
          [text]="validationWarnings().length + ' items have zero or missing rates'"
          styleClass="w-full mb-3"
        ></p-message>
      }

      <!-- Loading -->
      @if (pricingService.isLoading() && !pricingView()) {
        <div class="loading-container">
          <p>Loading pricing data...</p>
        </div>
      } @else if (!pricingView()) {
        <p-message
          severity="info"
          text="No BOQ data available for pricing."
          styleClass="w-full"
        ></p-message>
      } @else {
        <!-- BILL Level: Accordion with lump sum inputs -->
        @if (pricingView()!.pricingLevel === 'Bill') {
          <p-accordion [multiple]="true">
            @for (section of pricingView()!.sections; track section.sectionId) {
              <p-accordionTab [header]="section.sectionNumber + ' - ' + section.title">
                <div class="bill-pricing">
                  <div class="bill-details">
                    <p class="bill-item-count">{{ section.items.length }} items in this bill</p>
                    <div class="bill-items-preview">
                      @for (item of section.items; track item.itemId) {
                        <div class="preview-item">
                          <span class="preview-num">{{ item.itemNumber }}</span>
                          <span class="preview-desc">{{ item.description }}</span>
                          <span class="preview-qty">{{ item.quantity }} {{ item.uom }}</span>
                        </div>
                      }
                    </div>
                  </div>
                  <div class="bill-input">
                    <label>Lump Sum Amount (AED)</label>
                    <p-inputNumber
                      [(ngModel)]="sectionAmounts[section.sectionId]"
                      mode="decimal"
                      [minFractionDigits]="2"
                      [maxFractionDigits]="2"
                      [min]="0"
                      (onInput)="onAmountChange()"
                      styleClass="w-full"
                      placeholder="Enter lump sum..."
                    ></p-inputNumber>
                  </div>
                </div>
              </p-accordionTab>
            }
          </p-accordion>
        }

        <!-- ITEM Level: Cards per bill with item table -->
        @if (pricingView()!.pricingLevel === 'Item') {
          @for (section of pricingView()!.sections; track section.sectionId) {
            <p-card [header]="section.sectionNumber + ' - ' + section.title" styleClass="mb-3">
              <div class="item-pricing-table">
                <table class="pricing-table">
                  <thead>
                    <tr>
                      <th style="width: 12%">Item #</th>
                      <th style="width: 30%">Description</th>
                      <th style="width: 10%">Qty</th>
                      <th style="width: 8%">UOM</th>
                      <th style="width: 20%">Unit Rate (AED)</th>
                      <th style="width: 20%">Amount (AED)</th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (item of section.items; track item.itemId) {
                      <tr [class.zero-rate]="!itemRates[item.itemId]">
                        <td>{{ item.itemNumber }}</td>
                        <td>{{ item.description }}</td>
                        <td>{{ item.quantity | number:'1.0-2' }}</td>
                        <td>{{ item.uom }}</td>
                        <td>
                          <p-inputNumber
                            [(ngModel)]="itemRates[item.itemId]"
                            mode="decimal"
                            [minFractionDigits]="2"
                            [maxFractionDigits]="2"
                            [min]="0"
                            (onInput)="onAmountChange()"
                            styleClass="rate-input"
                            placeholder="0.00"
                          ></p-inputNumber>
                        </td>
                        <td class="amount-col">
                          {{ getItemAmount(item) | number:'1.0-2' }}
                        </td>
                      </tr>
                    }
                  </tbody>
                  <tfoot>
                    <tr class="subtotal-row">
                      <td colspan="5" class="subtotal-label">Section Subtotal</td>
                      <td class="subtotal-value">{{ getSectionSubtotal(section) | number:'1.0-2' }}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </p-card>
          }
        }

        <!-- SUB-ITEM Level: Full TreeTable with editable rates on leaves -->
        @if (pricingView()!.pricingLevel === 'SubItem') {
          <p-treeTable
            [value]="pricingTreeNodes()"
            [scrollable]="true"
            scrollHeight="calc(100vh - 450px)"
            styleClass="p-treetable-sm"
          >
            <ng-template pTemplate="header">
              <tr>
                <th style="width: 14%">Item #</th>
                <th style="width: 30%">Description</th>
                <th style="width: 10%">Qty</th>
                <th style="width: 8%">UOM</th>
                <th style="width: 18%">Unit Rate (AED)</th>
                <th style="width: 20%">Amount (AED)</th>
              </tr>
            </ng-template>
            <ng-template pTemplate="body" let-rowNode let-rowData="rowData">
              <tr [ttRow]="rowNode"
                  [class.section-row]="rowData.isSection"
                  [class.group-row]="rowData.isGroup"
                  [class.zero-rate]="!rowData.isSection && !rowData.isGroup && !rowData.rate">
                <td>
                  <p-treeTableToggler [rowNode]="rowNode"></p-treeTableToggler>
                  {{ rowData.itemNumber }}
                </td>
                <td>{{ rowData.description }}</td>
                <td>{{ rowData.isSection || rowData.isGroup ? '' : (rowData.quantity | number:'1.0-2') }}</td>
                <td>{{ rowData.isSection || rowData.isGroup ? '' : rowData.uom }}</td>
                <td>
                  @if (!rowData.isSection && !rowData.isGroup && !rowData.hasChildren) {
                    <p-inputNumber
                      [(ngModel)]="itemRates[rowData.itemId]"
                      mode="decimal"
                      [minFractionDigits]="2"
                      [maxFractionDigits]="2"
                      [min]="0"
                      (onInput)="onAmountChange()"
                      styleClass="rate-input"
                      placeholder="0.00"
                    ></p-inputNumber>
                  }
                </td>
                <td class="amount-col">
                  @if (rowData.isSection || rowData.isGroup) {
                    <strong>{{ rowData.subtotal | number:'1.0-2' }}</strong>
                  } @else {
                    {{ getItemAmountById(rowData.itemId, rowData.quantity) | number:'1.0-2' }}
                  }
                </td>
              </tr>
            </ng-template>
          </p-treeTable>
        }

        <!-- Summary Panel -->
        <div class="pricing-summary">
          <div class="summary-title">Bill Breakdown</div>
          @for (section of pricingView()!.sections; track section.sectionId) {
            <div class="summary-row">
              <span class="summary-section-name">{{ section.sectionNumber }} - {{ section.title }}</span>
              <span class="summary-section-amount">AED {{ getSectionSubtotal(section) | number:'1.0-2' }}</span>
            </div>
          }
          <div class="summary-row grand-total-row">
            <span class="summary-section-name">Grand Total</span>
            <span class="summary-section-amount">AED {{ grandTotal() | number:'1.0-2' }}</span>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .boq-pricing-container {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .pricing-header {
      display: flex;
      align-items: center;
      gap: 1.5rem;
      padding: 1rem;
      background: var(--bayan-accent, #EEF2FF);
      border-radius: var(--bayan-radius, 0.5rem);
      flex-wrap: wrap;
    }

    .completion-section {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .completion-label, .total-label {
      font-size: 0.875rem;
      font-weight: 500;
      color: var(--bayan-slate-700, #334155);
    }

    .grand-total-section {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-left: auto;
    }

    .total-value {
      font-size: 1.25rem;
      font-weight: 700;
      color: #1F3864;
    }

    .last-saved {
      font-size: 0.75rem;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .loading-container {
      padding: 3rem;
      text-align: center;
      color: var(--bayan-muted-foreground, #64748B);
    }

    /* Bill-level pricing */
    .bill-pricing {
      display: flex;
      gap: 2rem;
      align-items: flex-start;
    }

    .bill-details {
      flex: 1;
    }

    .bill-item-count {
      font-weight: 500;
      margin-bottom: 0.5rem;
      color: var(--bayan-slate-700, #334155);
    }

    .bill-items-preview {
      max-height: 200px;
      overflow-y: auto;
      border: 1px solid var(--bayan-border, #E2E8F0);
      border-radius: var(--bayan-radius, 0.5rem);
      padding: 0.5rem;
    }

    .preview-item {
      display: flex;
      gap: 0.5rem;
      padding: 0.25rem 0;
      font-size: 0.8rem;
      color: var(--bayan-slate-600, #475569);
    }

    .preview-num {
      font-weight: 500;
      min-width: 60px;
    }

    .preview-desc {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .preview-qty {
      min-width: 80px;
      text-align: right;
    }

    .bill-input {
      min-width: 250px;
    }

    .bill-input label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 500;
      color: var(--bayan-slate-700, #334155);
    }

    /* Item-level table */
    .pricing-table {
      width: 100%;
      border-collapse: collapse;
    }

    .pricing-table th {
      background: var(--bayan-slate-100, #F1F5F9);
      padding: 0.75rem 0.5rem;
      text-align: left;
      font-weight: 600;
      font-size: 0.8rem;
      color: var(--bayan-slate-700, #334155);
      border-bottom: 2px solid var(--bayan-border, #E2E8F0);
    }

    .pricing-table td {
      padding: 0.5rem;
      border-bottom: 1px solid var(--bayan-border, #E2E8F0);
      font-size: 0.875rem;
    }

    .pricing-table .zero-rate {
      background: #FFFBEB;
    }

    .amount-col {
      text-align: right;
      font-variant-numeric: tabular-nums;
      font-weight: 500;
    }

    .subtotal-row {
      background: var(--bayan-slate-100, #F1F5F9);
    }

    .subtotal-label {
      text-align: right;
      font-weight: 600;
      padding-right: 1rem !important;
    }

    .subtotal-value {
      text-align: right;
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }

    :host ::ng-deep .rate-input {
      width: 100%;
    }

    :host ::ng-deep .rate-input .p-inputnumber-input {
      width: 100%;
      text-align: right;
    }

    /* TreeTable sub-item level */
    :host ::ng-deep .p-treetable .section-row {
      background: #F0F4FA !important;
      font-weight: 700;
    }

    :host ::ng-deep .p-treetable .group-row {
      background: #F8F9FA !important;
      font-weight: 500;
      font-style: italic;
    }

    :host ::ng-deep .p-treetable .zero-rate {
      background: #FFFBEB !important;
    }

    /* Summary panel */
    .pricing-summary {
      padding: 1rem;
      background: var(--bayan-slate-50, #F8FAFC);
      border: 1px solid var(--bayan-border, #E2E8F0);
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .summary-title {
      font-weight: 600;
      margin-bottom: 0.75rem;
      color: var(--bayan-slate-800, #1E293B);
    }

    .summary-row {
      display: flex;
      justify-content: space-between;
      padding: 0.5rem 0;
      border-bottom: 1px solid var(--bayan-border, #E2E8F0);
    }

    .summary-row:last-child {
      border-bottom: none;
    }

    .grand-total-row {
      border-top: 2px solid #1F3864;
      margin-top: 0.5rem;
      padding-top: 0.75rem;
    }

    .grand-total-row .summary-section-name,
    .grand-total-row .summary-section-amount {
      font-weight: 700;
      color: #1F3864;
      font-size: 1.1rem;
    }

    .summary-section-amount {
      font-variant-numeric: tabular-nums;
      font-weight: 500;
    }

    :host ::ng-deep .ml-2 {
      margin-left: 0.5rem;
    }
  `]
})
export class BoqPricingComponent implements OnInit, OnDestroy {
  @Input() tenderId!: string;
  @Output() pricingCompleted = new EventEmitter<PricingEntry[]>();

  readonly pricingService = inject(BoqPricingService);
  private readonly messageService = inject(MessageService);
  private readonly destroy$ = new Subject<void>();

  pricingView = signal<PricingView | null>(null);

  // Rate inputs keyed by itemId
  itemRates: Record<string, number> = {};
  // Amount inputs keyed by sectionId (bill-level pricing)
  sectionAmounts: Record<string, number> = {};

  isDirty = signal(false);
  lastSaved = signal<string | null>(null);

  // Trigger signal for computed re-evaluation when rates/amounts change
  private rateVersion = signal(0);

  private autoSaveInterval$ = interval(30000);

  // Computed: grand total (depends on rateVersion to re-evaluate on rate/amount changes)
  grandTotal = computed(() => {
    this.rateVersion(); // trigger dependency
    const view = this.pricingView();
    if (!view) return 0;

    if (view.pricingLevel === 'Bill') {
      return Object.values(this.sectionAmounts).reduce((sum, amt) => sum + (amt || 0), 0);
    }

    return view.sections.reduce((sum, section) => sum + this.getSectionSubtotal(section), 0);
  });

  // Computed: completion percentage
  completionPercent = computed(() => {
    this.rateVersion(); // trigger dependency
    const view = this.pricingView();
    if (!view) return 0;

    if (view.pricingLevel === 'Bill') {
      const total = view.sections.length;
      if (total === 0) return 100;
      const filled = view.sections.filter(s => (this.sectionAmounts[s.sectionId] ?? 0) > 0).length;
      return Math.round((filled / total) * 100);
    }

    const allItems = view.sections.flatMap(s => this.flattenItems(s.items));
    const total = allItems.filter(i => !i.isGroup).length;
    if (total === 0) return 100;
    const filled = allItems.filter(i => !i.isGroup && (this.itemRates[i.itemId] ?? 0) > 0).length;
    return Math.round((filled / total) * 100);
  });

  // Computed: validation warnings
  validationWarnings = computed(() => {
    this.rateVersion(); // trigger dependency
    const view = this.pricingView();
    if (!view) return [];

    const warnings: string[] = [];
    if (view.pricingLevel === 'Bill') {
      view.sections.forEach(s => {
        if (!this.sectionAmounts[s.sectionId]) {
          warnings.push(`${s.sectionNumber}: No amount entered`);
        }
      });
    } else {
      view.sections.forEach(s => {
        const items = this.flattenItems(s.items).filter(i => !i.isGroup);
        items.forEach(item => {
          if (!this.itemRates[item.itemId]) {
            warnings.push(`${item.itemNumber}: Zero rate`);
          }
        });
      });
    }
    return warnings;
  });

  // Computed: tree nodes for SubItem level
  pricingTreeNodes = computed((): TreeNode[] => {
    this.rateVersion(); // trigger dependency
    const view = this.pricingView();
    if (!view) return [];

    return view.sections.map(section => ({
      key: `section-${section.sectionId}`,
      data: {
        isSection: true,
        isGroup: false,
        hasChildren: true,
        itemNumber: section.sectionNumber,
        description: section.title,
        quantity: null,
        uom: '',
        rate: null,
        itemId: null,
        subtotal: this.getSectionSubtotal(section)
      },
      children: section.items.map(item => this.mapItemToTreeNode(item)),
      expanded: true
    }));
  });

  ngOnInit(): void {
    this.loadPricingView();
    this.setupAutoSave();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadPricingView(): void {
    this.pricingService.getContractorView(this.tenderId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (view) => {
          this.pricingView.set(view);
          this.initializeRates(view);
        },
        error: (err) => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: err.message || 'Failed to load pricing data'
          });
        }
      });
  }

  private initializeRates(view: PricingView): void {
    if (view.pricingLevel === 'Bill') {
      view.sections.forEach(section => {
        this.sectionAmounts[section.sectionId] = section.subtotal || 0;
      });
    } else {
      view.sections.forEach(section => {
        const items = this.flattenItems(section.items);
        items.forEach(item => {
          if (item.unitRate != null) {
            this.itemRates[item.itemId] = item.unitRate;
          }
        });
      });
    }
  }

  private setupAutoSave(): void {
    this.autoSaveInterval$
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        if (this.isDirty()) {
          this.saveDraft();
        }
      });
  }

  onAmountChange(): void {
    this.isDirty.set(true);
    this.rateVersion.update(v => v + 1);
  }

  private saveDraft(): void {
    const entries = this.buildEntries();
    this.pricingService.saveDraft(this.tenderId, entries)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.isDirty.set(false);
          const now = new Date();
          this.lastSaved.set(now.toLocaleTimeString());
        },
        error: () => {
          // Silent fail for auto-save
        }
      });
  }

  private buildEntries(): PricingEntry[] {
    const view = this.pricingView();
    if (!view) return [];

    const entries: PricingEntry[] = [];

    if (view.pricingLevel === 'Bill') {
      view.sections.forEach(section => {
        entries.push({
          boqSectionId: section.sectionId,
          unitRate: 0,
          amount: this.sectionAmounts[section.sectionId] || 0
        });
      });
    } else {
      view.sections.forEach(section => {
        const items = this.flattenItems(section.items).filter(i => !i.isGroup);
        items.forEach(item => {
          const rate = this.itemRates[item.itemId] || 0;
          entries.push({
            boqItemId: item.itemId,
            unitRate: rate,
            amount: item.quantity * rate
          });
        });
      });
    }

    return entries;
  }

  getItemAmount(item: PricingViewItem): number {
    return item.quantity * (this.itemRates[item.itemId] || 0);
  }

  getItemAmountById(itemId: string, quantity: number): number {
    return quantity * (this.itemRates[itemId] || 0);
  }

  getSectionSubtotal(section: PricingViewSection): number {
    const view = this.pricingView();
    if (view?.pricingLevel === 'Bill') {
      return this.sectionAmounts[section.sectionId] || 0;
    }

    const items = this.flattenItems(section.items).filter(i => !i.isGroup);
    return items.reduce((sum, item) => sum + item.quantity * (this.itemRates[item.itemId] || 0), 0);
  }

  getEntries(): PricingEntry[] {
    return this.buildEntries();
  }

  private flattenItems(items: PricingViewItem[]): PricingViewItem[] {
    const result: PricingViewItem[] = [];
    for (const item of items) {
      result.push(item);
      if (item.childItems?.length) {
        result.push(...this.flattenItems(item.childItems));
      }
    }
    return result;
  }

  private mapItemToTreeNode(item: PricingViewItem): TreeNode {
    const hasChildren = !!(item.childItems?.length);
    return {
      key: `item-${item.itemId}`,
      data: {
        isSection: false,
        isGroup: item.isGroup,
        hasChildren,
        itemNumber: item.itemNumber,
        description: item.description,
        quantity: item.quantity,
        uom: item.uom,
        rate: this.itemRates[item.itemId] || null,
        itemId: item.itemId,
        subtotal: hasChildren ? this.computeGroupSubtotal(item) : null
      },
      children: item.childItems?.map(child => this.mapItemToTreeNode(child)),
      expanded: hasChildren
    };
  }

  private computeGroupSubtotal(item: PricingViewItem): number {
    if (!item.childItems?.length) {
      return item.quantity * (this.itemRates[item.itemId] || 0);
    }
    return item.childItems.reduce((sum, child) => sum + this.computeGroupSubtotal(child), 0);
  }
}
