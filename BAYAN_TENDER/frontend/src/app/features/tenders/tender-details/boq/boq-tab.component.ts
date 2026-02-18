import {
  Component,
  Input,
  OnInit,
  OnDestroy,
  ViewChild,
  inject,
  signal,
  computed
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil, forkJoin } from 'rxjs';
import { TreeTableModule } from 'primeng/treetable';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { MenuModule } from 'primeng/menu';
import { DialogModule } from 'primeng/dialog';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageModule } from 'primeng/message';
import { SelectButtonModule } from 'primeng/selectbutton';
import { MenuItem, MessageService, ConfirmationService, TreeNode } from 'primeng/api';
import { Menu } from 'primeng/menu';

import { BoqService } from '../../../../core/services/boq.service';
import {
  BoqTreeNode,
  BoqSection,
  BoqItem,
  BoqSummary,
  BOQ_ITEM_TYPE_CONFIG,
  BoqItemType,
  PricingLevel
} from '../../../../core/models/boq.model';
import { BoqSectionDialogComponent } from './boq-section-dialog.component';
import { BoqItemDialogComponent } from './boq-item-dialog.component';
import { BoqImportDialogComponent } from './boq-import-dialog.component';
import { BoqExportDialogComponent } from './boq-export-dialog.component';

@Component({
  selector: 'app-boq-tab',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TreeTableModule,
    ButtonModule,
    CardModule,
    TagModule,
    TooltipModule,
    MenuModule,
    DialogModule,
    ToastModule,
    ConfirmDialogModule,
    ProgressSpinnerModule,
    MessageModule,
    SelectButtonModule,
    BoqSectionDialogComponent,
    BoqItemDialogComponent,
    BoqImportDialogComponent,
    BoqExportDialogComponent
  ],
  providers: [MessageService, ConfirmationService],
  template: `
    <p-toast></p-toast>
    <p-confirmDialog></p-confirmDialog>

    <div class="boq-tab-container" data-testid="boq-tab">
      <!-- Toolbar -->
      <div class="boq-toolbar">
        <div class="toolbar-left">
          <button
            pButton
            icon="pi pi-upload"
            label="Import from Excel"
            class="p-button-outlined"
            data-testid="import-boq-btn"
            (click)="showImportDialog = true"
          ></button>
          <button
            pButton
            icon="pi pi-download"
            label="Export Template"
            class="p-button-outlined"
            data-testid="export-boq-btn"
            (click)="showExportDialog = true"
          ></button>
        </div>
        <div class="toolbar-center">
          <label class="pricing-level-label">Pricing Level:</label>
          <p-selectButton
            [options]="pricingLevelOptions"
            [(ngModel)]="pricingLevel"
            optionLabel="label"
            optionValue="value"
            (onChange)="onPricingLevelChange($event.value)"
            data-testid="pricing-level-selector"
          ></p-selectButton>
        </div>
        <div class="toolbar-right">
          <button
            pButton
            icon="pi pi-folder-plus"
            label="Add Section"
            class="p-button-outlined"
            data-testid="add-section-btn"
            (click)="openSectionDialog()"
          ></button>
          <button
            pButton
            icon="pi pi-plus"
            label="Add Item"
            data-testid="add-item-btn"
            (click)="openItemDialog()"
          ></button>
        </div>
      </div>

      <!-- Error Message -->
      @if (boqService.error()) {
        <p-message
          severity="error"
          [text]="boqService.error()!"
          styleClass="w-full mb-3"
        ></p-message>
      }

      <!-- Loading State -->
      @if (boqService.isLoading() && boqTree().length === 0) {
        <div class="loading-container">
          <p-progressSpinner
            [style]="{ width: '50px', height: '50px' }"
            strokeWidth="4"
          ></p-progressSpinner>
          <p>Loading BOQ...</p>
        </div>
      } @else if (boqTree().length === 0) {
        <!-- Empty State -->
        <div class="empty-state">
          <i class="pi pi-list" style="font-size: 3rem; color: var(--bayan-border, #E2E8F0);"></i>
          <h3>No Bill of Quantities Items</h3>
          <p>Start by importing from Excel or adding sections and items manually.</p>
          <div class="empty-actions">
            <button
              pButton
              icon="pi pi-upload"
              label="Import from Excel"
              class="p-button-outlined"
              (click)="showImportDialog = true"
            ></button>
            <button
              pButton
              icon="pi pi-folder-plus"
              label="Add First Section"
              (click)="openSectionDialog()"
            ></button>
          </div>
        </div>
      } @else {
        <!-- TreeTable -->
        <p-treeTable
          [value]="treeTableNodes()"
          [scrollable]="true"
          scrollHeight="calc(100vh - 400px)"
          [loading]="boqService.isLoading()"
          styleClass="p-treetable-sm"
          data-testid="boq-tree-table"
        >
          <ng-template pTemplate="header">
            <tr>
              <th style="width: 14%">Item #</th>
              <th style="width: 34%">Description</th>
              <th style="width: 10%">Qty</th>
              <th style="width: 8%">UOM</th>
              <th style="width: 12%">Amount</th>
              <th style="width: 12%">Type</th>
              <th style="width: 10%">Actions</th>
            </tr>
          </ng-template>

          <ng-template pTemplate="body" let-rowNode let-rowData="rowData">
            <tr [ttRow]="rowNode"
                [class.section-row]="rowData.type === 'section'"
                [class.boq-bill-row]="rowData.level === 'bill'"
                [class.boq-item-row]="rowData.level === 'item' && !rowData.isGroup"
                [class.boq-sub-item-row]="rowData.level === 'sub_item'"
                [class.boq-group-row]="rowData.isGroup">
              <td>
                <p-treeTableToggler [rowNode]="rowNode"></p-treeTableToggler>
                <span [class.section-number]="rowData.type === 'section'"
                      [class.bill-number]="rowData.level === 'bill'">
                  {{ rowData.itemNumber }}
                </span>
              </td>
              <td>
                <span
                  [class.section-title]="rowData.type === 'section'"
                  [class.bill-title]="rowData.level === 'bill'"
                  [pTooltip]="rowData.description"
                  tooltipPosition="top"
                >
                  {{ rowData.description | slice:0:80 }}{{ rowData.description?.length > 80 ? '...' : '' }}
                  @if (rowData.isGroup) {
                    <span class="group-indicator">(group)</span>
                  }
                </span>
              </td>
              <td>
                @if (rowData.type === 'item' && !rowData.isGroup) {
                  {{ rowData.quantity | number:'1.0-2' }}
                }
              </td>
              <td>{{ rowData.type === 'item' && !rowData.isGroup ? rowData.uom : '' }}</td>
              <td class="amount-cell">
                @if (rowData.amount != null && rowData.amount > 0) {
                  <span [class.amount-rollup]="rowData.type === 'section' || rowData.isGroup">
                    {{ rowData.amount | number:'1.0-2' }}
                  </span>
                }
              </td>
              <td>
                @if (rowData.type === 'item' && rowData.itemType && !rowData.isGroup) {
                  <p-tag
                    [value]="getItemTypeLabel(rowData.itemType)"
                    [severity]="getItemTypeSeverity(rowData.itemType)"
                  ></p-tag>
                }
                @if (rowData.level) {
                  <p-tag
                    [value]="getLevelLabel(rowData.level)"
                    [severity]="getLevelSeverity(rowData.level)"
                    styleClass="ml-1"
                  ></p-tag>
                }
              </td>
              <td>
                <div class="action-cell">
                  <button
                    pButton
                    icon="pi pi-ellipsis-v"
                    class="p-button-text p-button-sm"
                    (click)="openRowMenu($event, rowData)"
                  ></button>
                </div>
              </td>
            </tr>
          </ng-template>

          <ng-template pTemplate="emptymessage">
            <tr>
              <td colspan="7" class="text-center p-4">
                No BOQ items found.
              </td>
            </tr>
          </ng-template>
        </p-treeTable>

        <!-- Summary Footer -->
        <div class="boq-summary">
          <div class="summary-item">
            <span class="summary-label">Bills:</span>
            <span class="summary-value">{{ summary()?.totalBills || 0 }}</span>
          </div>
          <div class="summary-divider"></div>
          <div class="summary-item">
            <span class="summary-label">Items:</span>
            <span class="summary-value">{{ summary()?.totalItems || 0 }}</span>
          </div>
          <div class="summary-divider"></div>
          <div class="summary-item">
            <span class="summary-label">Sub-Items:</span>
            <span class="summary-value">{{ summary()?.totalSubItems || 0 }}</span>
          </div>
          <div class="summary-divider"></div>
          <div class="summary-item grand-total">
            <span class="summary-label">Grand Total:</span>
            <span class="summary-value">AED {{ summary()?.grandTotal | number:'1.0-2' }}</span>
          </div>
        </div>
      }
    </div>

    <!-- Row Action Menu -->
    <p-menu #rowMenu [model]="rowMenuItems" [popup]="true"></p-menu>

    <!-- Section Dialog -->
    <app-boq-section-dialog
      [visible]="showSectionDialog"
      [tenderId]="tenderId"
      [section]="selectedSection"
      [sections]="sections()"
      [mode]="sectionDialogMode"
      (visibleChange)="showSectionDialog = $event"
      (saved)="onSectionSaved($event)"
    ></app-boq-section-dialog>

    <!-- Item Dialog -->
    <app-boq-item-dialog
      [visible]="showItemDialog"
      [tenderId]="tenderId"
      [item]="selectedItem"
      [sections]="leafSections()"
      [mode]="itemDialogMode"
      (visibleChange)="showItemDialog = $event"
      (saved)="onItemSaved($event)"
    ></app-boq-item-dialog>

    <!-- Import Dialog -->
    <app-boq-import-dialog
      [visible]="showImportDialog"
      [tenderId]="tenderId"
      (visibleChange)="showImportDialog = $event"
      (imported)="onImportComplete($event)"
    ></app-boq-import-dialog>

    <!-- Export Dialog -->
    <app-boq-export-dialog
      [visible]="showExportDialog"
      [tenderId]="tenderId"
      (visibleChange)="showExportDialog = $event"
    ></app-boq-export-dialog>
  `,
  styles: [`
    .boq-tab-container {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .boq-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
      padding: 1rem;
      background-color: var(--bayan-accent, #EEF2FF);
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .toolbar-left,
    .toolbar-center,
    .toolbar-right {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      align-items: center;
    }

    .pricing-level-label {
      font-size: 0.875rem;
      font-weight: 500;
      color: var(--bayan-slate-700, #334155);
    }

    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem;
      gap: 1rem;
    }

    .loading-container p {
      color: var(--bayan-muted-foreground, #64748B);
    }

    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem;
      text-align: center;
      gap: 1rem;
    }

    .empty-state h3 {
      margin: 0;
      color: var(--bayan-foreground, #020617);
    }

    .empty-state p {
      margin: 0;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .empty-actions {
      display: flex;
      gap: 0.5rem;
      margin-top: 1rem;
    }

    :host ::ng-deep .p-treetable .section-row {
      background-color: var(--bayan-slate-100, #F1F5F9) !important;
      color: var(--bayan-slate-800, #1E293B);
      font-weight: 500;
    }

    :host ::ng-deep .p-treetable .section-row:hover {
      background-color: var(--bayan-accent, #EEF2FF) !important;
    }

    /* 3-Level Hierarchy Styles */
    :host ::ng-deep .p-treetable .boq-bill-row {
      background-color: #F0F4FA !important;
      border-left: 4px solid #1F3864;
      font-weight: 700;
    }

    :host ::ng-deep .p-treetable .boq-bill-row:hover {
      background-color: #E3EAF4 !important;
    }

    :host ::ng-deep .p-treetable .boq-item-row {
      background-color: #F8F9FA !important;
      font-weight: 500;
      padding-left: 20px;
    }

    :host ::ng-deep .p-treetable .boq-item-row td:first-child {
      padding-left: 20px;
    }

    :host ::ng-deep .p-treetable .boq-sub-item-row {
      font-weight: 400;
    }

    :host ::ng-deep .p-treetable .boq-sub-item-row td:first-child {
      padding-left: 40px;
    }

    :host ::ng-deep .p-treetable .boq-group-row {
      font-weight: 500;
      font-style: italic;
    }

    .bill-number {
      font-weight: 700;
      color: #1F3864;
    }

    .bill-title {
      font-weight: 700;
      color: #1F3864;
    }

    .group-indicator {
      font-size: 0.75rem;
      color: var(--bayan-muted-foreground, #64748B);
      margin-left: 0.25rem;
      font-style: italic;
    }

    .amount-cell {
      text-align: right;
      font-variant-numeric: tabular-nums;
    }

    .amount-rollup {
      font-weight: 600;
      color: var(--bayan-primary, #4F46E5);
    }

    .section-number {
      font-weight: 600;
      color: var(--bayan-primary, #4F46E5);
    }

    .section-title {
      font-weight: 600;
      color: var(--bayan-slate-800, #1E293B);
    }

    .action-cell {
      display: flex;
      justify-content: center;
    }

    .boq-summary {
      display: flex;
      align-items: center;
      gap: 1.5rem;
      padding: 1rem;
      background-color: var(--bayan-slate-100, #F1F5F9);
      border-radius: var(--bayan-radius, 0.5rem);
      flex-wrap: wrap;
    }

    .summary-item {
      display: flex;
      gap: 0.5rem;
      align-items: center;
    }

    .summary-label {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #64748B);
    }

    .summary-value {
      font-weight: 600;
      font-variant-numeric: tabular-nums;
      color: var(--bayan-foreground, #020617);
    }

    .summary-divider {
      width: 1px;
      height: 20px;
      background-color: var(--bayan-border, #E2E8F0);
    }

    .grand-total .summary-label {
      font-weight: 600;
      color: #1F3864;
    }

    .grand-total .summary-value {
      font-weight: 700;
      color: #1F3864;
      font-size: 1rem;
    }

    :host ::ng-deep .ml-1 {
      margin-left: 0.25rem;
    }

    :host ::ng-deep .p-treetable-scrollable .p-treetable-wrapper {
      overflow: auto;
    }

    @media (max-width: 768px) {
      .boq-toolbar {
        flex-direction: column;
        align-items: stretch;
      }

      .toolbar-left,
      .toolbar-right {
        justify-content: center;
      }

      .boq-summary {
        flex-direction: column;
        align-items: flex-start;
      }

      .summary-divider {
        display: none;
      }
    }
  `]
})
export class BoqTabComponent implements OnInit, OnDestroy {
  @Input() tenderId!: number;

  @ViewChild('rowMenu') rowMenu!: Menu;

  readonly boqService = inject(BoqService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly destroy$ = new Subject<void>();

  // Data signals
  boqTree = signal<BoqTreeNode[]>([]);
  sections = signal<BoqSection[]>([]);
  summary = signal<BoqSummary | null>(null);

  // Pricing level
  pricingLevel: PricingLevel = 'Item';
  pricingLevelOptions = [
    { label: 'Bill', value: 'Bill' as PricingLevel },
    { label: 'Item', value: 'Item' as PricingLevel },
    { label: 'Sub-Item', value: 'SubItem' as PricingLevel }
  ];

  // Dialog states
  showSectionDialog = false;
  showItemDialog = false;
  showImportDialog = false;
  showExportDialog = false;

  // Selected items for editing
  selectedSection: BoqSection | null = null;
  selectedItem: BoqItem | null = null;
  sectionDialogMode: 'create' | 'edit' = 'create';
  itemDialogMode: 'create' | 'edit' = 'create';

  // Current row for menu actions
  private currentRowData: BoqTreeNode | null = null;

  // Row menu items
  rowMenuItems: MenuItem[] = [];

  // Computed: Convert BoqTreeNode to TreeNode for PrimeNG TreeTable
  treeTableNodes = computed(() => {
    return this.convertToTreeNodes(this.boqTree());
  });

  // Computed: Get sections that can contain items (leaf sections or sections without child sections)
  leafSections = computed(() => {
    const allSections = this.sections();
    const parentIds = new Set(allSections.map(s => s.parentSectionId).filter(id => id !== null));
    return allSections.filter(s => !parentIds.has(s.id) || s.parentSectionId !== null);
  });

  ngOnInit(): void {
    this.loadData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadData(): void {
    forkJoin({
      tree: this.boqService.getBoqTree(this.tenderId),
      sections: this.boqService.getSections(this.tenderId),
      summary: this.boqService.getSummary(this.tenderId),
      pricingLevel: this.boqService.getPricingLevel(this.tenderId)
    }).pipe(takeUntil(this.destroy$)).subscribe({
      next: (result) => {
        this.boqTree.set(result.tree);
        this.sections.set(result.sections);
        this.summary.set(result.summary);
        this.pricingLevel = result.pricingLevel;
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to load BOQ data'
        });
      }
    });
  }

  private convertToTreeNodes(nodes: BoqTreeNode[]): TreeNode[] {
    return nodes.map(node => ({
      key: node.key,
      data: {
        type: node.type,
        itemNumber: node.itemNumber,
        description: node.description,
        quantity: node.quantity,
        uom: node.uom,
        itemType: node.itemType,
        level: node.level,
        amount: node.amount,
        isGroup: (node.data as BoqItem)?.isGroup ?? false,
        originalData: node.data
      },
      children: node.children ? this.convertToTreeNodes(node.children) : undefined,
      expanded: node.expanded
    }));
  }

  openRowMenu(event: Event, rowData: any): void {
    this.currentRowData = rowData;

    if (rowData.type === 'section') {
      this.rowMenuItems = [
        {
          label: 'Edit Section',
          icon: 'pi pi-pencil',
          command: () => this.editSection(rowData.originalData)
        },
        {
          label: 'Add Subsection',
          icon: 'pi pi-folder-plus',
          command: () => this.addSubsection(rowData.originalData)
        },
        {
          label: 'Add Item',
          icon: 'pi pi-plus',
          command: () => this.addItemToSection(rowData.originalData)
        },
        { separator: true },
        {
          label: 'Delete Section',
          icon: 'pi pi-trash',
          styleClass: 'p-menuitem-danger',
          command: () => this.confirmDeleteSection(rowData.originalData)
        }
      ];
    } else {
      this.rowMenuItems = [
        {
          label: 'Edit Item',
          icon: 'pi pi-pencil',
          command: () => this.editItem(rowData.originalData)
        },
        {
          label: 'Duplicate',
          icon: 'pi pi-copy',
          command: () => this.duplicateItem(rowData.originalData)
        },
        { separator: true },
        {
          label: 'Delete Item',
          icon: 'pi pi-trash',
          styleClass: 'p-menuitem-danger',
          command: () => this.confirmDeleteItem(rowData.originalData)
        }
      ];
    }

    // Toggle the popup menu
    this.rowMenu.toggle(event);
  }

  openSectionDialog(parentSection?: BoqSection): void {
    this.selectedSection = null;
    this.sectionDialogMode = 'create';
    this.showSectionDialog = true;
  }

  editSection(section: BoqSection): void {
    this.selectedSection = section;
    this.sectionDialogMode = 'edit';
    this.showSectionDialog = true;
  }

  addSubsection(parentSection: BoqSection): void {
    this.selectedSection = { ...parentSection, parentSectionId: parentSection.id } as any;
    this.sectionDialogMode = 'create';
    this.showSectionDialog = true;
  }

  confirmDeleteSection(section: BoqSection): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete section "${section.title}"? This will also delete all subsections and items within it.`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => this.deleteSection(section)
    });
  }

  private deleteSection(section: BoqSection): void {
    this.boqService.deleteSection(section.id).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Section deleted successfully'
        });
        this.loadData();
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to delete section'
        });
      }
    });
  }

  openItemDialog(): void {
    this.selectedItem = null;
    this.itemDialogMode = 'create';
    this.showItemDialog = true;
  }

  addItemToSection(section: BoqSection): void {
    this.selectedItem = { sectionId: section.id } as any;
    this.itemDialogMode = 'create';
    this.showItemDialog = true;
  }

  editItem(item: BoqItem): void {
    this.selectedItem = item;
    this.itemDialogMode = 'edit';
    this.showItemDialog = true;
  }

  duplicateItem(item: BoqItem): void {
    this.boqService.duplicateItem(item.id).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Item duplicated successfully'
        });
        this.loadData();
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to duplicate item'
        });
      }
    });
  }

  confirmDeleteItem(item: BoqItem): void {
    this.confirmationService.confirm({
      message: `Are you sure you want to delete item "${item.itemNumber}"?`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => this.deleteItem(item)
    });
  }

  private deleteItem(item: BoqItem): void {
    this.boqService.deleteItem(item.id).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Item deleted successfully'
        });
        this.loadData();
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.message || 'Failed to delete item'
        });
      }
    });
  }

  onSectionSaved(section: BoqSection): void {
    this.showSectionDialog = false;
    this.messageService.add({
      severity: 'success',
      summary: 'Success',
      detail: this.sectionDialogMode === 'create' ? 'Section created successfully' : 'Section updated successfully'
    });
    this.loadData();
  }

  onItemSaved(item: BoqItem): void {
    this.showItemDialog = false;
    this.messageService.add({
      severity: 'success',
      summary: 'Success',
      detail: this.itemDialogMode === 'create' ? 'Item created successfully' : 'Item updated successfully'
    });
    this.loadData();
  }

  onImportComplete(result: { imported: number; failed: number }): void {
    this.showImportDialog = false;
    this.messageService.add({
      severity: 'success',
      summary: 'Import Complete',
      detail: `${result.imported} items imported successfully${result.failed > 0 ? `, ${result.failed} failed` : ''}`
    });
    this.loadData();
  }

  onPricingLevelChange(level: PricingLevel): void {
    this.boqService.setPricingLevel(this.tenderId, level)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Updated',
            detail: `Pricing level set to ${level}`
          });
        },
        error: (error) => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: error.message || 'Failed to update pricing level'
          });
        }
      });
  }

  getLevelLabel(level: 'bill' | 'item' | 'sub_item'): string {
    switch (level) {
      case 'bill': return 'Bill';
      case 'item': return 'Item';
      case 'sub_item': return 'Sub-Item';
      default: return '';
    }
  }

  getLevelSeverity(level: 'bill' | 'item' | 'sub_item'): 'info' | 'success' | 'secondary' {
    switch (level) {
      case 'bill': return 'info';
      case 'item': return 'success';
      case 'sub_item': return 'secondary';
      default: return 'secondary';
    }
  }

  getItemTypeLabel(type: BoqItemType): string {
    return BOQ_ITEM_TYPE_CONFIG[type]?.label || type;
  }

  getItemTypeSeverity(type: BoqItemType): 'success' | 'info' | 'warn' | 'secondary' {
    return BOQ_ITEM_TYPE_CONFIG[type]?.severity || 'secondary';
  }
}
