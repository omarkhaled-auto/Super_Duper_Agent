import { Component, OnInit, inject, signal, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../../environments/environment';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { InputTextarea } from 'primeng/inputtextarea';
import { CheckboxModule } from 'primeng/checkbox';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { BadgeModule } from 'primeng/badge';
import { TooltipModule } from 'primeng/tooltip';
import { DividerModule } from 'primeng/divider';
import { PanelModule } from 'primeng/panel';
import { ToastModule } from 'primeng/toast';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { DialogModule } from 'primeng/dialog';
import { DialogService, DynamicDialog, DynamicDialogRef } from 'primeng/dynamicdialog';
import { ConfirmationService, MessageService } from 'primeng/api';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { DropdownModule } from 'primeng/dropdown';
import {
  Bidder,
  TenderBidder,
  PrequalificationStatus,
  TradeSpecialization,
  InvitationStatus,
  QualificationStatus
} from '../../../../core/models/bidder.model';
import { BidderService } from '../../../../core/services/bidder.service';
import { BidderFormDialogComponent, BidderFormDialogData } from '../../../admin/bidders/bidder-form-dialog.component';

interface Tender {
  id: number;
  title: string;
  referenceNumber: string;
  deadline: Date;
}

@Component({
  selector: 'app-invite-bidders',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule,
    InputTextModule,
    InputTextarea,
    CheckboxModule,
    TableModule,
    TagModule,
    BadgeModule,
    TooltipModule,
    DividerModule,
    PanelModule,
    ToastModule,
    ConfirmDialogModule,
    DialogModule,
    DynamicDialog,
    IconFieldModule,
    InputIconModule,
    DropdownModule
  ],
  providers: [MessageService, ConfirmationService, DialogService],
  template: `
    <p-toast></p-toast>
    <div class="invite-bidders-container">
      <div class="page-header">
        <div>
          <h2>Invite Bidders</h2>
          <p>Select bidders to invite to this tender</p>
        </div>
        <p-badge [value]="selectedBidders().length.toString()" severity="info" styleClass="selected-badge">
        </p-badge>
        <span class="selected-label">{{ selectedBidders().length }} selected</span>
      </div>

      <div class="split-panel">
        <!-- Available Bidders Panel -->
        <p-card styleClass="bidders-panel">
          <ng-template pTemplate="header">
            <div class="panel-header">
              <h3>Available Bidders</h3>
              <button
                pButton
                label="Add New Bidder"
                icon="pi pi-plus"
                class="p-button-sm p-button-outlined"
                (click)="openAddBidderDialog()"
              ></button>
            </div>
          </ng-template>

          <!-- Filters -->
          <div class="filters">
            <p-iconField iconPosition="left" class="search-field">
              <p-inputIcon styleClass="pi pi-search"></p-inputIcon>
              <input
                pInputText
                type="text"
                [(ngModel)]="searchTerm"
                placeholder="Search bidders..."
                (input)="onSearch()"
              />
            </p-iconField>

            <p-dropdown
              [options]="tradeOptions"
              [(ngModel)]="selectedTrade"
              placeholder="Trade"
              [showClear]="true"
              (onChange)="onFilter()"
            ></p-dropdown>
          </div>

          <p-table
            [value]="filteredAvailableBidders()"
            [paginator]="true"
            [rows]="5"
            [rowsPerPageOptions]="[5, 10, 20]"
            styleClass="p-datatable-sm"
          >
            <ng-template pTemplate="header">
              <tr>
                <th style="width: 40px">
                  <p-checkbox
                    [binary]="true"
                    [(ngModel)]="selectAllAvailable"
                    (onChange)="onSelectAllAvailable($event)"
                  ></p-checkbox>
                </th>
                <th>Company</th>
                <th>Trade</th>
                <th>Status</th>
              </tr>
            </ng-template>
            <ng-template pTemplate="body" let-bidder>
              <tr [class.selected-row]="isBidderSelected(bidder)">
                <td>
                  <p-checkbox
                    [binary]="true"
                    [ngModel]="isBidderSelected(bidder)"
                    (onChange)="onBidderCheckChange(bidder, $event)"
                  ></p-checkbox>
                </td>
                <td>
                  <div class="bidder-info">
                    <span class="company-name">{{ bidder.companyNameEn }}</span>
                    <span class="email">{{ bidder.email }}</span>
                  </div>
                </td>
                <td>
                  <div class="trade-tags">
                    @for (trade of bidder.tradeSpecializations.slice(0, 1); track trade) {
                      <p-tag [value]="getTradeLabel(trade)" severity="info" styleClass="trade-tag-sm"></p-tag>
                    }
                    @if (bidder.tradeSpecializations.length > 1) {
                      <span class="more-count">+{{ bidder.tradeSpecializations.length - 1 }}</span>
                    }
                  </div>
                </td>
                <td>
                  <p-tag
                    [value]="getPrequalificationLabel(bidder.prequalificationStatus)"
                    [severity]="getPrequalificationSeverity(bidder.prequalificationStatus)"
                    styleClass="status-tag-sm"
                  ></p-tag>
                </td>
              </tr>
            </ng-template>
            <ng-template pTemplate="emptymessage">
              <tr>
                <td colspan="4" class="text-center p-3">
                  <span class="text-muted">No bidders found</span>
                </td>
              </tr>
            </ng-template>
          </p-table>
        </p-card>

        <!-- Selected Bidders Panel -->
        <p-card styleClass="bidders-panel selected-panel">
          <ng-template pTemplate="header">
            <div class="panel-header">
              <h3>Selected Bidders ({{ selectedBidders().length }})</h3>
              @if (selectedBidders().length > 0) {
                <button
                  pButton
                  label="Clear All"
                  icon="pi pi-times"
                  class="p-button-sm p-button-text p-button-danger"
                  (click)="clearSelectedBidders()"
                ></button>
              }
            </div>
          </ng-template>

          <p-table
            [value]="selectedBidders()"
            styleClass="p-datatable-sm"
            [scrollable]="true"
            scrollHeight="300px"
          >
            <ng-template pTemplate="header">
              <tr>
                <th>Company</th>
                <th>Email</th>
                <th style="width: 100px">Status</th>
                <th style="width: 120px">Actions</th>
              </tr>
            </ng-template>
            <ng-template pTemplate="body" let-bidder>
              <tr>
                <td>
                  <span class="company-name">{{ bidder.companyNameEn }}</span>
                </td>
                <td>
                  <span class="email">{{ bidder.email }}</span>
                </td>
                <td>
                  @if (bidder.qualificationStatus) {
                    <p-tag
                      [value]="bidder.qualificationStatus"
                      [severity]="getQualificationSeverity(bidder.qualificationStatus)"
                      styleClass="status-tag-sm"
                    ></p-tag>
                  } @else {
                    <p-tag value="Pending" severity="warn" styleClass="status-tag-sm"></p-tag>
                  }
                </td>
                <td>
                  <div style="display: flex; gap: 0.25rem;">
                    <button
                      pButton
                      icon="pi pi-check"
                      class="p-button-text p-button-sm p-button-success"
                      pTooltip="Qualify"
                      (click)="openQualifyDialog(bidder)"
                    ></button>
                    <button
                      pButton
                      icon="pi pi-times"
                      class="p-button-text p-button-sm p-button-danger"
                      pTooltip="Reject"
                      (click)="openRejectDialog(bidder)"
                    ></button>
                    <button
                      pButton
                      icon="pi pi-trash"
                      class="p-button-text p-button-sm p-button-secondary"
                      pTooltip="Remove"
                      (click)="removeBidderFromSelection(bidder)"
                    ></button>
                  </div>
                </td>
              </tr>
            </ng-template>
            <ng-template pTemplate="emptymessage">
              <tr>
                <td colspan="4" class="text-center p-4">
                  <div class="empty-selection">
                    <i class="pi pi-users" style="font-size: 2rem; color: var(--bayan-muted-foreground, #71717a); opacity: 0.5;"></i>
                    <p>No bidders selected</p>
                    <small>Select bidders from the available list</small>
                  </div>
                </td>
              </tr>
            </ng-template>
          </p-table>
        </p-card>
      </div>

      <!-- Email Preview Section -->
      @if (selectedBidders().length > 0) {
        <p-panel header="Email Preview" [toggleable]="true" styleClass="email-preview-panel">
          <div class="email-preview">
            <div class="merge-fields-info">
              <h4>Available Merge Fields:</h4>
              <div class="merge-fields">
                <code>{{ '{{BidderName}}' }}</code>
                <code>{{ '{{TenderTitle}}' }}</code>
                <code>{{ '{{DeadlineDate}}' }}</code>
                <code>{{ '{{PortalLink}}' }}</code>
              </div>
            </div>

            <p-divider></p-divider>

            <div class="email-content">
              <label for="customMessage">Custom Message (Optional)</label>
              <textarea
                pInputTextarea
                id="customMessage"
                [(ngModel)]="customMessage"
                placeholder="Add a custom message to include in the invitation email..."
                rows="4"
                class="w-full"
              ></textarea>
            </div>

            <p-divider></p-divider>

            <div class="email-sample">
              <h4>Sample Email Preview:</h4>
              <div class="email-body">
                <p>Dear <strong>{{ '{{BidderName}}' }}</strong>,</p>
                <p>
                  You are invited to participate in the tender:
                  <strong>{{ tender?.title || '{{TenderTitle}}' }}</strong>
                </p>
                @if (customMessage) {
                  <p class="custom-message">{{ customMessage }}</p>
                }
                <p>
                  <strong>Submission Deadline:</strong>
                  {{ tender?.deadline ? (tender?.deadline | date:'fullDate') : '{{DeadlineDate}}' }}
                </p>
                <p>
                  Please access the tender portal to view details and submit your bid:
                  <a href="#">{{ '{{PortalLink}}' }}</a>
                </p>
                <p>Best regards,<br/>Bayan Tender Management System</p>
              </div>
            </div>
          </div>
        </p-panel>
      }

      <!-- Action Buttons -->
      <div class="action-buttons">
        <button
          pButton
          label="Cancel"
          class="p-button-text"
          (click)="onCancel()"
        ></button>
        <button
          pButton
          label="Send Invitations"
          icon="pi pi-send"
          [disabled]="selectedBidders().length === 0"
          [loading]="isLoading()"
          (click)="sendInvitations()"
        ></button>
      </div>

      <p-confirmDialog></p-confirmDialog>

      <!-- Qualification Dialog -->
      <p-dialog
        [(visible)]="showQualificationDialog"
        [header]="qualificationAction === 'Qualified' ? 'Qualify Bidder' : 'Reject Bidder'"
        [modal]="true"
        [style]="{width: '450px'}"
        [closable]="true"
      >
        <div class="qualification-dialog">
          @if (qualificationBidder) {
            <p>
              Are you sure you want to <strong>{{ qualificationAction === 'Qualified' ? 'qualify' : 'reject' }}</strong>
              <strong>{{ qualificationBidder.companyNameEn }}</strong>?
            </p>
          }
          <div class="form-field" style="margin-top: 1rem;">
            <label for="qualificationReason">Reason (Optional)</label>
            <textarea
              pInputTextarea
              id="qualificationReason"
              [(ngModel)]="qualificationReason"
              placeholder="Enter reason for this decision..."
              rows="3"
              class="w-full"
            ></textarea>
          </div>
        </div>
        <ng-template pTemplate="footer">
          <button
            pButton
            label="Cancel"
            class="p-button-text"
            (click)="showQualificationDialog = false"
          ></button>
          <button
            pButton
            [label]="qualificationAction === 'Qualified' ? 'Qualify' : 'Reject'"
            [icon]="qualificationAction === 'Qualified' ? 'pi pi-check' : 'pi pi-times'"
            [class]="qualificationAction === 'Qualified' ? '' : 'p-button-danger'"
            [loading]="qualificationLoading()"
            (click)="confirmQualification()"
          ></button>
        </ng-template>
      </p-dialog>
    </div>
  `,
  styles: [`
    .invite-bidders-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .page-header {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .page-header h2 {
      margin: 0;
      font-size: 1.5rem;
      color: var(--bayan-foreground, #09090b);
    }

    .page-header p {
      margin: 0.25rem 0 0;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .selected-label {
      color: var(--bayan-primary, #18181b);
      font-weight: 500;
    }

    .split-panel {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
    }

    @media (max-width: 1024px) {
      .split-panel {
        grid-template-columns: 1fr;
      }
    }

    :host ::ng-deep .bidders-panel {
      .p-card-header {
        padding: 1rem;
        border-bottom: 1px solid var(--bayan-border, #e4e4e7);
      }

      .p-card-body {
        padding: 0;
      }

      .p-card-content {
        padding: 1rem;
      }
    }

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .panel-header h3 {
      margin: 0;
      font-size: 1.1rem;
      color: var(--bayan-foreground, #09090b);
    }

    .filters {
      display: flex;
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .search-field {
      flex: 1;
    }

    .search-field input {
      width: 100%;
    }

    .bidder-info {
      display: flex;
      flex-direction: column;
    }

    .company-name {
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
    }

    .email {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .trade-tags {
      display: flex;
      align-items: center;
      gap: 0.25rem;
    }

    :host ::ng-deep .trade-tag-sm {
      font-size: 0.7rem;
      padding: 0.15rem 0.4rem;
    }

    :host ::ng-deep .status-tag-sm {
      font-size: 0.75rem;
    }

    .more-count {
      font-size: 0.75rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .selected-row {
      background-color: var(--bayan-accent, #f4f4f5) !important;
    }

    :host ::ng-deep .selected-panel {
      border: 2px solid var(--bayan-primary, #18181b);
    }

    .empty-selection {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.5rem;
      padding: 1rem;
    }

    .empty-selection p {
      margin: 0;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .empty-selection small {
      color: var(--bayan-muted-foreground, #71717a);
    }

    :host ::ng-deep .email-preview-panel {
      .p-panel-content {
        padding: 1rem;
      }
    }

    .email-preview {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .merge-fields-info h4 {
      margin: 0 0 0.5rem;
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .merge-fields {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .merge-fields code {
      background: var(--bayan-accent, #f4f4f5);
      padding: 0.25rem 0.5rem;
      border-radius: var(--bayan-radius-sm, 0.375rem);
      font-size: 0.875rem;
      color: var(--bayan-primary, #18181b);
    }

    .email-content label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
    }

    .email-sample h4 {
      margin: 0 0 0.5rem;
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .email-body {
      background: var(--bayan-accent, #f4f4f5);
      padding: 1rem;
      border-radius: var(--bayan-radius, 0.5rem);
      border: 1px solid var(--bayan-border, #e4e4e7);
    }

    .email-body p {
      margin: 0.5rem 0;
      line-height: 1.6;
    }

    .custom-message {
      background: #fff3cd;
      padding: 0.75rem;
      border-radius: var(--bayan-radius-sm, 0.375rem);
      border-left: 4px solid #ffc107;
    }

    .action-buttons {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
      padding-top: 1rem;
      border-top: 1px solid var(--bayan-border, #e4e4e7);
    }
  `]
})
export class InviteBiddersComponent implements OnInit {
  private readonly bidderService = inject(BidderService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly dialogService = inject(DialogService);
  private readonly http = inject(HttpClient);

  @Input() tender?: Tender;
  @Input() existingBidderIds: number[] = [];
  @Output() invitationsSent = new EventEmitter<Bidder[]>();
  @Output() cancelled = new EventEmitter<void>();

  availableBidders = signal<Bidder[]>([]);
  filteredAvailableBidders = signal<Bidder[]>([]);
  selectedBidders = signal<Bidder[]>([]);
  isLoading = this.bidderService.isLoading;

  searchTerm = '';
  selectedTrade: TradeSpecialization | null = null;
  selectAllAvailable = false;
  customMessage = '';

  // Qualification management
  showQualificationDialog = false;
  qualificationAction: 'Qualified' | 'Rejected' = 'Qualified';
  qualificationReason = '';
  qualificationBidder: Bidder | null = null;
  qualificationLoading = signal(false);

  private dialogRef: DynamicDialogRef | null = null;

  tradeOptions = [
    { label: 'IT Services', value: TradeSpecialization.IT_SERVICES },
    { label: 'Construction', value: TradeSpecialization.CONSTRUCTION },
    { label: 'Consulting', value: TradeSpecialization.CONSULTING },
    { label: 'Supplies', value: TradeSpecialization.SUPPLIES },
    { label: 'Maintenance', value: TradeSpecialization.MAINTENANCE },
    { label: 'Security', value: TradeSpecialization.SECURITY },
    { label: 'Logistics', value: TradeSpecialization.LOGISTICS },
    { label: 'Healthcare', value: TradeSpecialization.HEALTHCARE },
    { label: 'Education', value: TradeSpecialization.EDUCATION },
    { label: 'Financial', value: TradeSpecialization.FINANCIAL },
    { label: 'Engineering', value: TradeSpecialization.ENGINEERING },
    { label: 'Telecommunications', value: TradeSpecialization.TELECOMMUNICATIONS },
    { label: 'Other', value: TradeSpecialization.OTHER }
  ];

  ngOnInit(): void {
    this.loadAvailableBidders();
  }

  private loadAvailableBidders(): void {
    // Mock data - in production, fetch from API excluding already invited bidders
    const mockBidders: Bidder[] = [
      {
        id: 1,
        companyNameEn: 'Tech Solutions Ltd',
        companyNameAr: 'حلول تقنية المحدودة',
        email: 'info@techsolutions.sa',
        phone: '+966 11 234 5678',
        crNumber: '1010123456',
        tradeSpecializations: [TradeSpecialization.IT_SERVICES, TradeSpecialization.TELECOMMUNICATIONS],
        prequalificationStatus: PrequalificationStatus.APPROVED,
        ndaStatus: 'signed' as any,
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date()
      },
      {
        id: 2,
        companyNameEn: 'Al-Bina Construction',
        companyNameAr: 'البناء للمقاولات',
        email: 'contact@albina.sa',
        tradeSpecializations: [TradeSpecialization.CONSTRUCTION, TradeSpecialization.ENGINEERING],
        prequalificationStatus: PrequalificationStatus.APPROVED,
        ndaStatus: 'signed' as any,
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date()
      },
      {
        id: 3,
        companyNameEn: 'Global Supplies Co',
        email: 'sales@globalsupplies.sa',
        tradeSpecializations: [TradeSpecialization.SUPPLIES, TradeSpecialization.LOGISTICS],
        prequalificationStatus: PrequalificationStatus.PENDING,
        ndaStatus: 'sent' as any,
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date()
      },
      {
        id: 4,
        companyNameEn: 'Strategic Consulting Group',
        email: 'hello@strategicconsulting.sa',
        tradeSpecializations: [TradeSpecialization.CONSULTING, TradeSpecialization.FINANCIAL],
        prequalificationStatus: PrequalificationStatus.APPROVED,
        ndaStatus: 'signed' as any,
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date()
      },
      {
        id: 5,
        companyNameEn: 'SecureTech Solutions',
        email: 'info@securetech.sa',
        tradeSpecializations: [TradeSpecialization.SECURITY, TradeSpecialization.IT_SERVICES],
        prequalificationStatus: PrequalificationStatus.APPROVED,
        ndaStatus: 'signed' as any,
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date()
      }
    ].filter(b => !this.existingBidderIds.includes(b.id));

    this.availableBidders.set(mockBidders);
    this.filteredAvailableBidders.set(mockBidders);
  }

  onSearch(): void {
    this.applyFilters();
  }

  onFilter(): void {
    this.applyFilters();
  }

  private applyFilters(): void {
    let result = [...this.availableBidders()];

    if (this.searchTerm) {
      const term = this.searchTerm.toLowerCase();
      result = result.filter(b =>
        b.companyNameEn.toLowerCase().includes(term) ||
        b.email.toLowerCase().includes(term)
      );
    }

    if (this.selectedTrade) {
      result = result.filter(b => b.tradeSpecializations.includes(this.selectedTrade!));
    }

    this.filteredAvailableBidders.set(result);
  }

  isBidderSelected(bidder: Bidder): boolean {
    return this.selectedBidders().some(b => b.id === bidder.id);
  }

  onBidderCheckChange(bidder: Bidder, event: any): void {
    if (event.checked) {
      this.selectedBidders.update(selected => [...selected, bidder]);
    } else {
      this.selectedBidders.update(selected => selected.filter(b => b.id !== bidder.id));
    }
    this.updateSelectAllState();
  }

  onSelectAllAvailable(event: any): void {
    if (event.checked) {
      const currentFiltered = this.filteredAvailableBidders();
      const currentSelected = this.selectedBidders();
      const newSelections = currentFiltered.filter(
        b => !currentSelected.some(s => s.id === b.id)
      );
      this.selectedBidders.update(selected => [...selected, ...newSelections]);
    } else {
      const filteredIds = this.filteredAvailableBidders().map(b => b.id);
      this.selectedBidders.update(selected =>
        selected.filter(b => !filteredIds.includes(b.id))
      );
    }
  }

  private updateSelectAllState(): void {
    const filtered = this.filteredAvailableBidders();
    const selected = this.selectedBidders();
    this.selectAllAvailable = filtered.length > 0 &&
      filtered.every(b => selected.some(s => s.id === b.id));
  }

  removeBidderFromSelection(bidder: Bidder): void {
    this.selectedBidders.update(selected => selected.filter(b => b.id !== bidder.id));
    this.updateSelectAllState();
  }

  clearSelectedBidders(): void {
    this.confirmationService.confirm({
      message: 'Are you sure you want to clear all selected bidders?',
      header: 'Confirm Clear',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.selectedBidders.set([]);
        this.selectAllAvailable = false;
      }
    });
  }

  openAddBidderDialog(): void {
    const dialogData: BidderFormDialogData = {
      mode: 'create'
    };

    this.dialogRef = this.dialogService.open(BidderFormDialogComponent, {
      header: 'Add New Bidder',
      width: '700px',
      contentStyle: { overflow: 'auto' },
      data: dialogData
    });

    this.dialogRef.onClose.subscribe((result: Bidder | undefined) => {
      if (result) {
        // Add new bidder to available list and select it
        this.availableBidders.update(bidders => [...bidders, result]);
        this.selectedBidders.update(selected => [...selected, result]);
        this.applyFilters();
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Bidder created and added to selection'
        });
      }
    });
  }

  sendInvitations(): void {
    if (this.selectedBidders().length === 0) {
      return;
    }

    this.confirmationService.confirm({
      message: `Are you sure you want to send invitations to ${this.selectedBidders().length} bidder(s)?`,
      header: 'Confirm Send Invitations',
      icon: 'pi pi-send',
      accept: () => {
        // In production: call bidderService.inviteBiddersToTender()
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: `Invitations sent to ${this.selectedBidders().length} bidder(s)`
        });
        this.invitationsSent.emit(this.selectedBidders());
      }
    });
  }

  onCancel(): void {
    this.cancelled.emit();
  }

  openQualifyDialog(bidder: Bidder): void {
    this.qualificationBidder = bidder;
    this.qualificationAction = 'Qualified';
    this.qualificationReason = '';
    this.showQualificationDialog = true;
  }

  openRejectDialog(bidder: Bidder): void {
    this.qualificationBidder = bidder;
    this.qualificationAction = 'Rejected';
    this.qualificationReason = '';
    this.showQualificationDialog = true;
  }

  confirmQualification(): void {
    if (!this.qualificationBidder || !this.tender) return;

    this.qualificationLoading.set(true);

    const apiUrl = environment.apiUrl;

    this.http.put(`${apiUrl}/tenders/${this.tender.id}/bidders/${this.qualificationBidder.id}/qualification`, {
      qualificationStatus: this.qualificationAction,
      reason: this.qualificationReason || undefined
    }).subscribe({
      next: () => {
        this.qualificationLoading.set(false);
        this.showQualificationDialog = false;
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: `Bidder ${this.qualificationAction === 'Qualified' ? 'qualified' : 'rejected'} successfully`
        });
        // Update the bidder's qualification status in the selected list
        if (this.qualificationBidder) {
          this.selectedBidders.update(bidders =>
            bidders.map(b =>
              b.id === this.qualificationBidder!.id
                ? { ...b, qualificationStatus: this.qualificationAction as any }
                : b
            )
          );
        }
      },
      error: (error: any) => {
        this.qualificationLoading.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: error.error?.message || 'Failed to update qualification status'
        });
      }
    });
  }

  getQualificationSeverity(status: string): 'success' | 'warn' | 'danger' | 'info' {
    switch (status) {
      case 'Qualified': return 'success';
      case 'Rejected': return 'danger';
      case 'Pending': return 'warn';
      default: return 'info';
    }
  }

  getTradeLabel(trade: TradeSpecialization): string {
    const option = this.tradeOptions.find(o => o.value === trade);
    return option?.label || trade;
  }

  getPrequalificationLabel(status: PrequalificationStatus): string {
    const labels: Record<PrequalificationStatus, string> = {
      [PrequalificationStatus.PENDING]: 'Pending',
      [PrequalificationStatus.APPROVED]: 'Approved',
      [PrequalificationStatus.REJECTED]: 'Rejected'
    };
    return labels[status];
  }

  getPrequalificationSeverity(status: PrequalificationStatus): 'success' | 'warn' | 'danger' {
    const severities: Record<PrequalificationStatus, 'success' | 'warn' | 'danger'> = {
      [PrequalificationStatus.PENDING]: 'warn',
      [PrequalificationStatus.APPROVED]: 'success',
      [PrequalificationStatus.REJECTED]: 'danger'
    };
    return severities[status];
  }
}
