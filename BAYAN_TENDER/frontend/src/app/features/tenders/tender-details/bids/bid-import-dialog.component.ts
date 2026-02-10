import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnChanges,
  SimpleChanges,
  inject,
  signal,
  computed
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DialogModule } from 'primeng/dialog';
import { StepsModule } from 'primeng/steps';
import { TableModule } from 'primeng/table';
import { DropdownModule } from 'primeng/dropdown';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { MessageModule } from 'primeng/message';
import { ProgressBarModule } from 'primeng/progressbar';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { TooltipModule } from 'primeng/tooltip';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { CheckboxModule } from 'primeng/checkbox';
import { PanelModule } from 'primeng/panel';
import { DividerModule } from 'primeng/divider';
import { AutoCompleteModule } from 'primeng/autocomplete';
import { MenuItem } from 'primeng/api';

import { BidImportService } from '../../../../core/services/bid-import.service';
import {
  ParseResult,
  ParsedExcelRow,
  ColumnMapping,
  MappingValidation,
  BidImportColumnType,
  BID_IMPORT_COLUMN_OPTIONS,
  MatchResult,
  MatchedItem,
  NormalizationResult,
  UomMismatch,
  ValidationResult,
  ValidationIssue,
  BidImportResponse,
  CURRENCY_OPTIONS,
  DEFAULT_FX_RATES
} from '../../../../core/models/bid-import.model';
import { BidDocument } from '../../../../core/models/bid.model';

@Component({
  selector: 'app-bid-import-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    DialogModule,
    StepsModule,
    TableModule,
    DropdownModule,
    ButtonModule,
    TagModule,
    MessageModule,
    ProgressBarModule,
    ProgressSpinnerModule,
    TooltipModule,
    InputTextModule,
    InputNumberModule,
    CheckboxModule,
    PanelModule,
    DividerModule,
    AutoCompleteModule
  ],
  template: `
    <p-dialog
      header="Import Bid BOQ"
      [(visible)]="visible"
      (visibleChange)="onVisibleChange($event)"
      [modal]="true"
      [style]="{ width: '95vw', maxWidth: '1200px', height: '90vh' }"
      [contentStyle]="{ overflow: 'auto', display: 'flex', flexDirection: 'column' }"
      [draggable]="false"
      [resizable]="false"
    >
      <!-- Steps Header -->
      <p-steps
        [model]="steps"
        [activeIndex]="activeStep()"
        [readonly]="true"
        styleClass="mb-4"
      ></p-steps>

      <div class="step-content">
        <!-- Step 1: Upload & Parse -->
        @if (activeStep() === 0) {
          <div class="upload-step">
            <div class="file-info-card">
              <h4>Bid File Information</h4>
              @if (bidDocument) {
                <div class="file-details">
                  <div class="file-icon">
                    <i class="pi pi-file-excel"></i>
                  </div>
                  <div class="file-meta">
                    <span class="file-name">{{ bidDocument.originalFilename }}</span>
                    <span class="file-size">{{ formatFileSize(bidDocument.fileSize) }}</span>
                  </div>
                </div>
              }
            </div>

            <div class="parse-section">
              @if (!parseResult()) {
                <button
                  pButton
                  label="Parse File"
                  icon="pi pi-cog"
                  class="p-button-lg"
                  [loading]="isParsing()"
                  (click)="parseFile()"
                ></button>
                <p class="parse-hint">Click to analyze the Excel file and detect items</p>
              } @else {
                <div class="parse-result">
                  <div class="result-summary">
                    <i class="pi pi-check-circle success-icon"></i>
                    <span class="result-text">
                      <strong>{{ parseResult()!.totalRows }}</strong> items detected from
                      <strong>{{ parseResult()!.filename }}</strong>
                    </span>
                  </div>

                  <h5>Preview (First 10 rows)</h5>
                  <div class="preview-table-container">
                    <p-table
                      [value]="parseResult()!.previewRows"
                      [scrollable]="true"
                      scrollHeight="250px"
                      styleClass="p-datatable-sm p-datatable-gridlines"
                    >
                      <ng-template pTemplate="header">
                        <tr>
                          <th style="width: 60px">#</th>
                          @for (col of parseResult()!.detectedColumns; track col) {
                            <th style="min-width: 120px">{{ col }}</th>
                          }
                        </tr>
                      </ng-template>
                      <ng-template pTemplate="body" let-row>
                        <tr>
                          <td>{{ row.rowIndex }}</td>
                          @for (col of parseResult()!.detectedColumns; track col) {
                            <td>{{ row.cells[col] }}</td>
                          }
                        </tr>
                      </ng-template>
                    </p-table>
                  </div>
                </div>
              }
            </div>
          </div>
        }

        <!-- Step 2: Map Columns -->
        @if (activeStep() === 1) {
          <div class="mapping-step">
            <div class="mapping-header">
              <div>
                <h4>Map Excel Columns to BOQ Fields</h4>
                <p>Map each column from the Excel file to the corresponding BOQ field. Required fields are highlighted.</p>
              </div>
              <button
                pButton
                label="Auto-Map"
                icon="pi pi-magic"
                class="p-button-outlined"
                (click)="autoMapColumns()"
              ></button>
            </div>

            <div class="mapping-table-container">
              <p-table
                [value]="parseResult()!.previewRows.slice(0, 5)"
                [scrollable]="true"
                scrollHeight="300px"
                styleClass="p-datatable-sm p-datatable-gridlines"
              >
                <ng-template pTemplate="header">
                  <tr>
                    @for (col of parseResult()!.detectedColumns; track col) {
                      <th style="min-width: 160px">
                        <div class="column-mapping-header">
                          <span class="excel-col-label">Column {{ col }}</span>
                          <p-dropdown
                            [options]="columnFieldOptions"
                            [(ngModel)]="columnMappings()[col]"
                            (ngModelChange)="onMappingChange(col, $event)"
                            placeholder="Select field"
                            [showClear]="true"
                            optionLabel="label"
                            optionValue="value"
                            styleClass="mapping-dropdown"
                            [style]="{ width: '100%' }"
                          ></p-dropdown>
                          @if (isRequiredField(columnMappings()[col])) {
                            <span class="required-badge">Required</span>
                          }
                        </div>
                      </th>
                    }
                  </tr>
                </ng-template>
                <ng-template pTemplate="body" let-row>
                  <tr>
                    @for (col of parseResult()!.detectedColumns; track col) {
                      <td [class.mapped-cell]="columnMappings()[col] && columnMappings()[col] !== 'ignore'">
                        {{ row.cells[col] }}
                      </td>
                    }
                  </tr>
                </ng-template>
              </p-table>
            </div>

            @if (mappingValidation()) {
              <div class="mapping-feedback">
                @for (error of mappingValidation()!.errors; track error) {
                  <p-message severity="error" [text]="error" styleClass="w-full mb-2"></p-message>
                }
                @for (warning of mappingValidation()!.warnings; track warning) {
                  <p-message severity="warn" [text]="warning" styleClass="w-full mb-2"></p-message>
                }
                @if (mappingValidation()!.isValid) {
                  <p-message severity="success" text="Column mappings are valid" styleClass="w-full"></p-message>
                }
              </div>
            }
          </div>
        }

        <!-- Step 3: Match to BOQ -->
        @if (activeStep() === 2) {
          <div class="matching-step">
            @if (isMatching()) {
              <div class="matching-state">
                <p-progressSpinner [style]="{ width: '60px', height: '60px' }" strokeWidth="4"></p-progressSpinner>
                <p>Matching bidder items to BOQ...</p>
              </div>
            } @else if (matchResult()) {
              <div class="match-summary">
                <div class="summary-card exact">
                  <i class="pi pi-check-circle"></i>
                  <div class="summary-content">
                    <span class="summary-value">{{ matchResult()!.exactMatches }}</span>
                    <span class="summary-label">Exact Matches</span>
                  </div>
                </div>
                <div class="summary-card fuzzy">
                  <i class="pi pi-search"></i>
                  <div class="summary-content">
                    <span class="summary-value">{{ matchResult()!.fuzzyMatches }}</span>
                    <span class="summary-label">Fuzzy Matches</span>
                  </div>
                </div>
                <div class="summary-card unmatched">
                  <i class="pi pi-question-circle"></i>
                  <div class="summary-content">
                    <span class="summary-value">{{ matchResult()!.unmatchedItems }}</span>
                    <span class="summary-label">Unmatched</span>
                  </div>
                </div>
                <div class="summary-card extra">
                  <i class="pi pi-plus-circle"></i>
                  <div class="summary-content">
                    <span class="summary-value">{{ matchResult()!.extraItems }}</span>
                    <span class="summary-label">Extra Items</span>
                  </div>
                </div>
              </div>

              <!-- Unmatched Items Section -->
              @if (unmatchedItems().length > 0) {
                <p-panel header="Unmatched Items - Manual Matching Required" [toggleable]="true" [collapsed]="false" styleClass="mt-3">
                  <div class="unmatched-list">
                    @for (item of unmatchedItems(); track item.bidderItemId) {
                      <div class="unmatched-item">
                        <div class="item-info">
                          <span class="item-number">{{ item.bidderItemNumber }}</span>
                          <span class="item-desc">{{ item.bidderDescription }}</span>
                        </div>
                        <div class="match-controls">
                          <p-autoComplete
                            [(ngModel)]="item.boqItemId"
                            [suggestions]="boqSuggestions()"
                            (completeMethod)="searchBoqItems($event)"
                            field="label"
                            [dropdown]="true"
                            placeholder="Search BOQ item..."
                            [style]="{ width: '300px' }"
                            (onSelect)="onBoqItemSelected(item, $event)"
                          ></p-autoComplete>
                          <button
                            pButton
                            label="Mark as Extra"
                            icon="pi pi-plus"
                            class="p-button-outlined p-button-secondary p-button-sm"
                            (click)="markAsExtra(item)"
                          ></button>
                        </div>
                      </div>
                    }
                  </div>
                </p-panel>
              }

              <!-- Fuzzy Matches for Review -->
              @if (fuzzyMatches().length > 0) {
                <p-panel header="Fuzzy Matches - Review Required" [toggleable]="true" [collapsed]="true" styleClass="mt-3">
                  <div class="fuzzy-list">
                    @for (item of fuzzyMatches(); track item.bidderItemId) {
                      <div class="fuzzy-item">
                        <div class="fuzzy-match-info">
                          <div class="bidder-side">
                            <span class="side-label">Bidder:</span>
                            <span class="item-number">{{ item.bidderItemNumber }}</span>
                            <span class="item-desc">{{ item.bidderDescription }}</span>
                          </div>
                          <div class="match-arrow">
                            <i class="pi pi-arrow-right"></i>
                            <span class="confidence">{{ item.confidenceScore }}%</span>
                          </div>
                          <div class="boq-side">
                            <span class="side-label">BOQ:</span>
                            <span class="item-number">{{ item.boqItemNumber }}</span>
                            <span class="item-desc">{{ item.boqDescription }}</span>
                          </div>
                        </div>
                        <div class="fuzzy-actions">
                          <p-checkbox
                            [(ngModel)]="item.isIncluded"
                            [binary]="true"
                            label="Accept match"
                          ></p-checkbox>
                        </div>
                      </div>
                    }
                  </div>
                </p-panel>
              }

              <!-- Extra Items Section -->
              @if (extraItems().length > 0) {
                <p-panel header="Extra Items" [toggleable]="true" [collapsed]="true" styleClass="mt-3">
                  <p class="extra-note">These items are not in the master BOQ. Select which ones to include.</p>
                  <div class="extra-list">
                    @for (item of extraItems(); track item.bidderItemId) {
                      <div class="extra-item">
                        <p-checkbox
                          [(ngModel)]="item.isIncluded"
                          [binary]="true"
                        ></p-checkbox>
                        <span class="item-number">{{ item.bidderItemNumber }}</span>
                        <span class="item-desc">{{ item.bidderDescription }}</span>
                        <span class="item-amount">{{ item.bidderAmount | number:'1.0-0' }}</span>
                      </div>
                    }
                  </div>
                </p-panel>
              }
            }
          </div>
        }

        <!-- Step 4: Normalize -->
        @if (activeStep() === 3) {
          <div class="normalize-step">
            @if (isNormalizing()) {
              <div class="normalizing-state">
                <p-progressSpinner [style]="{ width: '60px', height: '60px' }" strokeWidth="4"></p-progressSpinner>
                <p>Normalizing currencies and units...</p>
              </div>
            } @else if (normalizationResult()) {
              <!-- Currency Section -->
              <div class="normalize-section">
                <h4><i class="pi pi-money-bill"></i> Currency Conversion</h4>
                <div class="currency-form">
                  <div class="form-row">
                    <div class="form-field">
                      <label>Detected Currency</label>
                      <p-dropdown
                        [options]="currencyOptions"
                        [(ngModel)]="normalizationResult()!.currency.detectedCurrency"
                        optionLabel="label"
                        optionValue="value"
                        [style]="{ width: '100%' }"
                      ></p-dropdown>
                    </div>
                    <div class="form-field">
                      <label>Tender Base Currency</label>
                      <input
                        pInputText
                        [value]="normalizationResult()!.currency.baseCurrency"
                        [disabled]="true"
                        class="w-full"
                      />
                    </div>
                    <div class="form-field">
                      <label>FX Rate</label>
                      <p-inputNumber
                        [(ngModel)]="normalizationResult()!.currency.fxRate"
                        [minFractionDigits]="4"
                        [maxFractionDigits]="6"
                        [step]="0.0001"
                        [style]="{ width: '100%' }"
                      ></p-inputNumber>
                    </div>
                  </div>
                  <div class="fx-preview">
                    <span>1 {{ normalizationResult()!.currency.detectedCurrency }} = {{ normalizationResult()!.currency.fxRate }} {{ normalizationResult()!.currency.baseCurrency }}</span>
                  </div>
                </div>
              </div>

              <p-divider></p-divider>

              <!-- UOM Mismatches Section -->
              <div class="normalize-section">
                <h4><i class="pi pi-tags"></i> Unit of Measure Mismatches</h4>
                @if (normalizationResult()!.uomMismatches.length === 0) {
                  <p-message severity="success" text="No UOM mismatches detected" styleClass="w-full"></p-message>
                } @else {
                  <p-table
                    [value]="normalizationResult()!.uomMismatches"
                    styleClass="p-datatable-sm p-datatable-striped"
                  >
                    <ng-template pTemplate="header">
                      <tr>
                        <th>Item</th>
                        <th>Bidder UOM</th>
                        <th>Master UOM</th>
                        <th>Factor</th>
                        <th>Can Convert</th>
                        <th>Action</th>
                      </tr>
                    </ng-template>
                    <ng-template pTemplate="body" let-mismatch>
                      <tr>
                        <td>{{ mismatch.itemNumber }}</td>
                        <td>{{ mismatch.bidderUom }}</td>
                        <td>{{ mismatch.masterUom }}</td>
                        <td>
                          @if (mismatch.conversionFactor) {
                            {{ mismatch.conversionFactor }}
                          } @else {
                            <span class="text-red-500">N/A</span>
                          }
                        </td>
                        <td>
                          <p-tag
                            [value]="mismatch.canConvert ? 'Yes' : 'No'"
                            [severity]="mismatch.canConvert ? 'success' : 'danger'"
                          ></p-tag>
                        </td>
                        <td>
                          @if (mismatch.canConvert) {
                            <p-checkbox
                              [(ngModel)]="mismatch.autoConvert"
                              [binary]="true"
                              label="Auto-convert"
                            ></p-checkbox>
                          } @else {
                            <p-checkbox
                              [(ngModel)]="mismatch.markAsNonComparable"
                              [binary]="true"
                              label="Mark non-comparable"
                              [disabled]="true"
                            ></p-checkbox>
                          }
                        </td>
                      </tr>
                    </ng-template>
                  </p-table>
                }
              </div>
            }
          </div>
        }

        <!-- Step 5: Validate & Import -->
        @if (activeStep() === 4) {
          <div class="validate-step">
            @if (isValidating()) {
              <div class="validating-state">
                <p-progressSpinner [style]="{ width: '60px', height: '60px' }" strokeWidth="4"></p-progressSpinner>
                <p>Validating import data...</p>
              </div>
            } @else if (validationResult()) {
              <!-- Validation Summary -->
              <div class="validation-summary">
                <div class="summary-card valid">
                  <i class="pi pi-check-circle"></i>
                  <div class="summary-content">
                    <span class="summary-value">{{ validationResult()!.validItemCount }}</span>
                    <span class="summary-label">Valid Items</span>
                  </div>
                </div>
                <div class="summary-card warning">
                  <i class="pi pi-exclamation-triangle"></i>
                  <div class="summary-content">
                    <span class="summary-value">{{ validationResult()!.warningCount }}</span>
                    <span class="summary-label">Warnings</span>
                  </div>
                </div>
                <div class="summary-card error">
                  <i class="pi pi-times-circle"></i>
                  <div class="summary-content">
                    <span class="summary-value">{{ validationResult()!.errorCount }}</span>
                    <span class="summary-label">Errors</span>
                  </div>
                </div>
              </div>

              <!-- Issues List -->
              @if (validationResult()!.issues.length > 0) {
                <p-panel header="Validation Issues" [toggleable]="true" [collapsed]="false" styleClass="mt-3">
                  <div class="issues-list">
                    @for (issue of validationResult()!.issues; track issue.itemId + issue.field) {
                      <div class="issue-item" [class]="'issue-' + issue.severity">
                        <i [class]="getIssueIcon(issue.severity)"></i>
                        <div class="issue-content">
                          <span class="issue-item-ref">{{ issue.itemNumber }}</span>
                          <span class="issue-message">{{ issue.message }}</span>
                        </div>
                        @if (!issue.canProceed) {
                          <p-tag value="Blocking" severity="danger"></p-tag>
                        }
                      </div>
                    }
                  </div>
                </p-panel>
              }

              <!-- Import Actions -->
              @if (validationResult()!.isValid || validationResult()!.warningCount > 0) {
                <div class="import-actions">
                  @if (validationResult()!.warningCount > 0) {
                    <p-message
                      severity="warn"
                      text="There are warnings. You can proceed but review the items above."
                      styleClass="w-full mb-3"
                    ></p-message>
                    <button
                      pButton
                      label="Import with Warnings"
                      icon="pi pi-check"
                      class="p-button-warning p-button-lg"
                      [loading]="isImporting()"
                      (click)="executeImport()"
                    ></button>
                  } @else {
                    <button
                      pButton
                      label="Import Items"
                      icon="pi pi-check"
                      class="p-button-success p-button-lg"
                      [loading]="isImporting()"
                      (click)="executeImport()"
                    ></button>
                  }
                </div>
              } @else {
                <p-message
                  severity="error"
                  text="Cannot proceed due to validation errors. Please fix the issues above."
                  styleClass="w-full mt-3"
                ></p-message>
              }

              <!-- Import Result -->
              @if (importResult()) {
                <div class="import-result">
                  <i class="pi pi-check-circle success-icon"></i>
                  <h3>Import Completed</h3>
                  <div class="result-details">
                    <p><strong>{{ importResult()!.importedCount }}</strong> items imported successfully</p>
                    <p><strong>{{ importResult()!.totalAmount | number:'1.0-0' }} {{ importResult()!.currency }}</strong> total bid amount</p>
                    @if (importResult()!.skippedCount > 0) {
                      <p class="skipped">{{ importResult()!.skippedCount }} items skipped</p>
                    }
                  </div>
                </div>
              }
            }
          </div>
        }
      </div>

      <!-- Footer Actions -->
      <div class="dialog-footer">
        <button
          pButton
          label="Cancel"
          class="p-button-text"
          (click)="onCancel()"
        ></button>

        <div class="nav-buttons">
          @if (activeStep() > 0 && !importResult()) {
            <button
              pButton
              label="Back"
              icon="pi pi-arrow-left"
              class="p-button-outlined"
              (click)="previousStep()"
            ></button>
          }

          @if (activeStep() < 4 && !importResult()) {
            <button
              pButton
              label="Next"
              icon="pi pi-arrow-right"
              iconPos="right"
              [disabled]="!canProceed()"
              (click)="nextStep()"
            ></button>
          }

          @if (importResult()) {
            <button
              pButton
              label="Close"
              icon="pi pi-check"
              class="p-button-success"
              (click)="onComplete()"
            ></button>
          }
        </div>
      </div>
    </p-dialog>
  `,
  styles: [`
    .step-content {
      flex: 1;
      overflow: auto;
      padding: 1rem 0;
    }

    /* Step 1: Upload */
    .upload-step {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .file-info-card {
      padding: 1.5rem;
      background-color: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .file-info-card h4 {
      margin: 0 0 1rem;
      color: var(--bayan-foreground, #09090b);
    }

    .file-details {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .file-icon {
      font-size: 2.5rem;
      color: var(--bayan-success, #22c55e);
    }

    .file-meta {
      display: flex;
      flex-direction: column;
    }

    .file-name {
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
    }

    .file-size {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .parse-section {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      padding: 2rem;
      background-color: #fff;
      border: 2px dashed var(--bayan-border, #e4e4e7);
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .parse-hint {
      margin: 0;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .parse-result {
      width: 100%;
    }

    .result-summary {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 1rem;
      background-color: var(--bayan-success-bg, #f0fdf4);
      border-radius: var(--bayan-radius, 0.5rem);
      margin-bottom: 1rem;
    }

    .success-icon {
      font-size: 1.5rem;
      color: var(--bayan-success, #22c55e);
    }

    .result-text {
      color: #16a34a;
    }

    .preview-table-container {
      overflow: auto;
    }

    /* Step 2: Mapping */
    .mapping-step {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .mapping-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 1rem;
    }

    .mapping-header h4 {
      margin: 0;
      color: var(--bayan-foreground, #09090b);
    }

    .mapping-header p {
      margin: 0.25rem 0 0;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .column-mapping-header {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      padding: 0.5rem 0;
    }

    .excel-col-label {
      font-weight: 600;
      color: var(--bayan-primary, #18181b);
    }

    .required-badge {
      font-size: 0.7rem;
      padding: 0.15rem 0.4rem;
      background-color: var(--bayan-danger-bg, #fef2f2);
      color: #dc2626;
      border-radius: var(--bayan-radius-sm, 0.375rem);
    }

    .mapped-cell {
      background-color: var(--bayan-muted, #f4f4f5) !important;
    }

    .mapping-feedback {
      margin-top: 1rem;
    }

    /* Step 3: Matching */
    .matching-step {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .matching-state,
    .normalizing-state,
    .validating-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      padding: 3rem;
    }

    .match-summary,
    .validation-summary {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem;
    }

    @media (max-width: 768px) {
      .match-summary,
      .validation-summary {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    .summary-card {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1.25rem;
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .summary-card i {
      font-size: 2rem;
    }

    .summary-card.exact,
    .summary-card.valid {
      background-color: var(--bayan-success-bg, #f0fdf4);
      color: #16a34a;
    }

    .summary-card.fuzzy {
      background-color: var(--bayan-muted, #f4f4f5);
      color: var(--bayan-primary, #18181b);
    }

    .summary-card.unmatched,
    .summary-card.warning {
      background-color: var(--bayan-warning-bg, #fffbeb);
      color: #d97706;
    }

    .summary-card.extra {
      background-color: #faf5ff;
      color: #9333ea;
    }

    .summary-card.error {
      background-color: var(--bayan-danger-bg, #fef2f2);
      color: #dc2626;
    }

    .summary-content {
      display: flex;
      flex-direction: column;
    }

    .summary-value {
      font-size: 1.75rem;
      font-weight: 700;
    }

    .summary-label {
      font-size: 0.875rem;
    }

    .unmatched-list,
    .fuzzy-list {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .unmatched-item,
    .fuzzy-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem;
      background-color: #fff;
      border: 1px solid var(--bayan-border, #e4e4e7);
      border-radius: var(--bayan-radius, 0.5rem);
      gap: 1rem;
      flex-wrap: wrap;
    }

    .item-info {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .item-number {
      font-family: monospace;
      font-weight: 600;
      color: var(--bayan-primary, #18181b);
      min-width: 80px;
    }

    .item-desc {
      color: var(--bayan-foreground, #09090b);
    }

    .match-controls {
      display: flex;
      gap: 0.5rem;
      align-items: center;
    }

    .fuzzy-match-info {
      display: flex;
      align-items: center;
      gap: 1rem;
      flex: 1;
    }

    .bidder-side,
    .boq-side {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      flex: 1;
    }

    .side-label {
      font-size: 0.75rem;
      color: var(--bayan-muted-foreground, #71717a);
      text-transform: uppercase;
    }

    .match-arrow {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.25rem;
    }

    .confidence {
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--bayan-primary, #18181b);
    }

    .extra-note {
      margin: 0 0 1rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .extra-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .extra-item {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 0.75rem;
      background-color: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius-sm, 0.375rem);
    }

    .item-amount {
      margin-left: auto;
      font-weight: 600;
    }

    /* Step 4: Normalize */
    .normalize-step {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .normalize-section h4 {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin: 0 0 1rem;
      color: var(--bayan-foreground, #09090b);
    }

    .currency-form {
      padding: 1rem;
      background-color: var(--bayan-accent, #f4f4f5);
      border-radius: var(--bayan-radius, 0.5rem);
    }

    .form-row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1rem;
    }

    @media (max-width: 768px) {
      .form-row {
        grid-template-columns: 1fr;
      }
    }

    .form-field {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .form-field label {
      font-weight: 500;
      color: var(--bayan-foreground, #09090b);
    }

    .fx-preview {
      margin-top: 1rem;
      padding: 0.75rem;
      background-color: var(--bayan-muted, #f4f4f5);
      border-radius: var(--bayan-radius-sm, 0.375rem);
      text-align: center;
      font-weight: 500;
      color: var(--bayan-primary, #18181b);
    }

    /* Step 5: Validate */
    .validate-step {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .issues-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .issue-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem;
      border-radius: var(--bayan-radius-sm, 0.375rem);
    }

    .issue-item.issue-error {
      background-color: var(--bayan-danger-bg, #fef2f2);
    }

    .issue-item.issue-warning {
      background-color: var(--bayan-warning-bg, #fffbeb);
    }

    .issue-item.issue-info {
      background-color: var(--bayan-muted, #f4f4f5);
    }

    .issue-item i {
      font-size: 1.25rem;
    }

    .issue-content {
      display: flex;
      flex-direction: column;
      flex: 1;
    }

    .issue-item-ref {
      font-family: monospace;
      font-weight: 600;
    }

    .issue-message {
      font-size: 0.875rem;
      color: var(--bayan-muted-foreground, #71717a);
    }

    .import-actions {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      margin-top: 1.5rem;
    }

    .import-result {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      padding: 2rem;
      background-color: var(--bayan-success-bg, #f0fdf4);
      border-radius: var(--bayan-radius, 0.5rem);
      margin-top: 1.5rem;
    }

    .import-result .success-icon {
      font-size: 3rem;
    }

    .import-result h3 {
      margin: 0;
      color: #16a34a;
    }

    .result-details {
      text-align: center;
    }

    .result-details p {
      margin: 0.5rem 0;
    }

    .result-details .skipped {
      color: #d97706;
    }

    /* Footer */
    .dialog-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 1rem;
      border-top: 1px solid var(--bayan-border, #e4e4e7);
      margin-top: auto;
    }

    .nav-buttons {
      display: flex;
      gap: 0.5rem;
    }
  `]
})
export class BidImportDialogComponent implements OnChanges {
  @Input() visible = false;
  @Input() tenderId!: number;
  @Input() bidId!: number;
  @Input() bidDocument: BidDocument | null = null;

  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() imported = new EventEmitter<BidImportResponse>();

  private readonly bidImportService = inject(BidImportService);

  // Step configuration
  steps: MenuItem[] = [
    { label: 'Upload & Parse' },
    { label: 'Map Columns' },
    { label: 'Match to BOQ' },
    { label: 'Normalize' },
    { label: 'Validate & Import' }
  ];

  // State signals
  activeStep = signal<number>(0);
  isParsing = signal<boolean>(false);
  isMatching = signal<boolean>(false);
  isNormalizing = signal<boolean>(false);
  isValidating = signal<boolean>(false);
  isImporting = signal<boolean>(false);

  // Data signals
  parseResult = signal<ParseResult | null>(null);
  columnMappings = signal<Record<string, BidImportColumnType | null>>({});
  mappingValidation = signal<MappingValidation | null>(null);
  matchResult = signal<MatchResult | null>(null);
  normalizationResult = signal<NormalizationResult | null>(null);
  validationResult = signal<ValidationResult | null>(null);
  importResult = signal<BidImportResponse | null>(null);

  // BOQ search
  boqSuggestions = signal<any[]>([]);

  // Dropdown options
  columnFieldOptions = BID_IMPORT_COLUMN_OPTIONS;
  currencyOptions = CURRENCY_OPTIONS;

  // Computed
  unmatchedItems = computed(() =>
    this.matchResult()?.items.filter(i => i.matchType === 'unmatched') || []
  );

  fuzzyMatches = computed(() =>
    this.matchResult()?.items.filter(i => i.matchType === 'fuzzy') || []
  );

  extraItems = computed(() =>
    this.matchResult()?.items.filter(i => i.matchType === 'extra') || []
  );

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && this.visible) {
      this.reset();
    }
  }

  private reset(): void {
    this.activeStep.set(0);
    this.parseResult.set(null);
    this.columnMappings.set({});
    this.mappingValidation.set(null);
    this.matchResult.set(null);
    this.normalizationResult.set(null);
    this.validationResult.set(null);
    this.importResult.set(null);
    this.isParsing.set(false);
    this.isMatching.set(false);
    this.isNormalizing.set(false);
    this.isValidating.set(false);
    this.isImporting.set(false);
  }

  formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  parseFile(): void {
    this.isParsing.set(true);

    // Backend reads the file from OriginalFilePath — no file upload needed
    const mockFile = new File([''], 'bid.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });

    this.bidImportService.parseFile(this.tenderId, this.bidId, mockFile).subscribe({
      next: (result) => {
        this.isParsing.set(false);
        this.parseResult.set(result);

        // Initialize column mappings
        const mappings: Record<string, BidImportColumnType | null> = {};
        result.detectedColumns.forEach(col => {
          mappings[col] = null;
        });
        this.columnMappings.set(mappings);
      },
      error: () => {
        this.isParsing.set(false);
      }
    });
  }

  autoMapColumns(): void {
    if (!this.parseResult()) return;

    const result = this.parseResult()!;
    const mappings = this.bidImportService.autoMapColumns(
      result.detectedColumns,
      result.previewRows
    );

    const newMappings: Record<string, BidImportColumnType | null> = {};
    mappings.forEach(m => {
      newMappings[m.excelColumn] = m.targetField;
    });
    this.columnMappings.set(newMappings);

    this.validateMappings();
  }

  onMappingChange(column: string, field: BidImportColumnType | null): void {
    const current = this.columnMappings();
    this.columnMappings.set({ ...current, [column]: field });
    this.validateMappings();
  }

  validateMappings(): void {
    const mappings: ColumnMapping[] = Object.entries(this.columnMappings()).map(
      ([col, field]) => ({ excelColumn: col, targetField: field })
    );
    const validation = this.bidImportService.validateMappings(mappings);
    this.mappingValidation.set(validation);
  }

  isRequiredField(field: BidImportColumnType | null): boolean {
    if (!field) return false;
    const option = BID_IMPORT_COLUMN_OPTIONS.find(o => o.value === field);
    return option?.required || false;
  }

  searchBoqItems(event: { query: string }): void {
    this.bidImportService.getBoqItemsForMatching(this.tenderId).subscribe({
      next: (items) => {
        const filtered = items.filter(item =>
          item.itemNumber.toLowerCase().includes(event.query.toLowerCase()) ||
          item.description.toLowerCase().includes(event.query.toLowerCase())
        ).map(item => ({
          ...item,
          label: `${item.itemNumber} - ${item.description}`
        }));
        this.boqSuggestions.set(filtered);
      }
    });
  }

  onBoqItemSelected(matchedItem: MatchedItem, event: any): void {
    const selected = event.value || event;
    matchedItem.boqItemId = selected.id;
    matchedItem.boqItemNumber = selected.itemNumber;
    matchedItem.boqDescription = selected.description;
    matchedItem.matchType = 'exact';
    matchedItem.manuallyMatched = true;
    matchedItem.isIncluded = true;
  }

  markAsExtra(item: MatchedItem): void {
    item.matchType = 'extra';
    item.isIncluded = true;
  }

  canProceed(): boolean {
    switch (this.activeStep()) {
      case 0:
        return !!this.parseResult();
      case 1:
        return this.mappingValidation()?.isValid || false;
      case 2:
        return !!this.matchResult();
      case 3:
        return !!this.normalizationResult();
      case 4:
        return this.validationResult()?.isValid ||
          (this.validationResult()?.warningCount || 0) > 0;
      default:
        return false;
    }
  }

  nextStep(): void {
    const current = this.activeStep();

    if (current === 1) {
      // Validate mappings before proceeding
      this.validateMappings();
      if (!this.mappingValidation()?.isValid) {
        return;
      }
      // Start matching
      this.activeStep.set(current + 1);
      this.performMatching();
    } else if (current === 2) {
      // Start normalization
      this.activeStep.set(current + 1);
      this.performNormalization();
    } else if (current === 3) {
      // Start validation
      this.activeStep.set(current + 1);
      this.performValidation();
    } else {
      this.activeStep.set(current + 1);
    }
  }

  previousStep(): void {
    this.activeStep.set(this.activeStep() - 1);
  }

  private performMatching(): void {
    if (!this.parseResult()) return;

    this.isMatching.set(true);

    const mappings: ColumnMapping[] = Object.entries(this.columnMappings()).map(
      ([col, field]) => ({ excelColumn: col, targetField: field })
    );

    this.bidImportService.matchToBoq(
      this.tenderId,
      this.bidId,
      this.parseResult()!.previewRows,
      mappings
    ).subscribe({
      next: (result) => {
        this.isMatching.set(false);
        this.matchResult.set(result);
      },
      error: () => {
        this.isMatching.set(false);
      }
    });
  }

  private performNormalization(): void {
    if (!this.matchResult()) return;

    this.isNormalizing.set(true);

    const includedItems = this.matchResult()!.items.filter(i => i.isIncluded);

    this.bidImportService.normalize(this.tenderId, this.bidId, includedItems).subscribe({
      next: (result) => {
        this.isNormalizing.set(false);
        this.normalizationResult.set(result);
      },
      error: () => {
        this.isNormalizing.set(false);
      }
    });
  }

  private performValidation(): void {
    if (!this.normalizationResult()) return;

    this.isValidating.set(true);

    this.bidImportService.validate(this.tenderId, this.bidId, this.normalizationResult()!.normalizedItems).subscribe({
      next: (result) => {
        this.isValidating.set(false);
        this.validationResult.set(result);
      },
      error: () => {
        this.isValidating.set(false);
      }
    });
  }

  executeImport(): void {
    if (!this.normalizationResult() || !this.validationResult()) return;

    this.isImporting.set(true);

    const hasWarnings = (this.validationResult()?.warningCount ?? 0) > 0;

    this.bidImportService.executeImport({
      bidId: this.bidId,
      tenderId: this.tenderId,
      items: this.normalizationResult()!.normalizedItems,
      currency: this.normalizationResult()!.currency,
      includeExtras: true,
      forceImport: hasWarnings
    }).subscribe({
      next: (result) => {
        this.isImporting.set(false);
        this.importResult.set(result);
      },
      error: () => {
        this.isImporting.set(false);
      }
    });
  }

  getIssueIcon(severity: string): string {
    switch (severity) {
      case 'error': return 'pi pi-times-circle text-red-500';
      case 'warning': return 'pi pi-exclamation-triangle text-orange-500';
      case 'info': return 'pi pi-info-circle text-blue-500';
      default: return 'pi pi-question-circle';
    }
  }

  onVisibleChange(visible: boolean): void {
    this.visibleChange.emit(visible);
  }

  onCancel(): void {
    this.visibleChange.emit(false);
  }

  onComplete(): void {
    if (this.importResult()) {
      this.imported.emit(this.importResult()!);
    }
    this.visibleChange.emit(false);
  }
}
