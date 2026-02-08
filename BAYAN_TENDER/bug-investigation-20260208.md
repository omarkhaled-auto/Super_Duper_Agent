# BOQ Export Template Bug Investigation Report

**Date:** 2026-02-08
**System:** BAYAN Tender Management System
**Issue:** BOQ export template not working (manual BOQ item addition works fine)
**Severity:** HIGH - Core feature non-functional
**Status:** ROOT CAUSE IDENTIFIED

---

## Executive Summary

The BOQ export template feature is completely non-functional due to a **HTTP method mismatch** and **data structure incompatibility** between frontend and backend. The frontend collects detailed export options (column selections, locking preferences) through a dialog but discards them by calling the wrong API endpoint. The backend has the correct implementation ready, but it's never utilized.

**Root Cause:** Frontend uses GET endpoint with query parameters that ignores user-selected options instead of POST endpoint that accepts full configuration.

---

## Investigation Flow

### 1. Frontend Export Dialog Component
**File:** `C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER\frontend\src\app\features\tenders\tender-details\boq\boq-export-dialog.component.ts`

**What it does:**
- Lines 45-159: Collects detailed export options from user
  - Column selections (8 checkboxes): itemNumber, description, quantity, uom, type, notes, unitRate, totalAmount
  - Lock columns checkbox
  - Include instructions checkbox
  - Language dropdown (English/Arabic/Bilingual)

**The call (Line 294):**
```typescript
this.boqService.exportToExcel(this.tenderId, this.options).subscribe({...})
```

**Options passed:**
```typescript
options: BoqExportOptions = {
  columns: {
    itemNumber: true,
    description: true,
    quantity: true,
    uom: true,
    type: true,
    notes: true,
    unitRate: true,
    totalAmount: true
  },
  lockColumns: true,
  includeInstructions: true,
  language: 'en'
}
```

**Issue:** All these options are collected but most are NEVER sent to the backend.

---

### 2. Frontend BOQ Service
**File:** `C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER\frontend\src\app\core\services\boq.service.ts`

**exportToExcel() implementation (Lines 532-548):**
```typescript
exportToExcel(tenderId: number, options: BoqExportOptions): Observable<Blob> {
  this._isLoading.set(true);
  this._error.set(null);

  // Map frontend language option to backend TemplateLanguage enum (0=English, 1=Arabic, 2=Both)
  const languageMap: Record<string, number> = { en: 0, ar: 1, both: 2 };
  const language = languageMap[options.language] ?? 0;

  return this.api.download(`/tenders/${tenderId}/boq/export-template?language=${language}&includeInstructions=${options.includeInstructions}`).pipe(
    tap(() => this._isLoading.set(false)),
    catchError(error => {
      this._isLoading.set(false);
      this._error.set(error.message || 'Failed to export BOQ');
      return throwError(() => error);
    })
  );
}
```

**CRITICAL FINDINGS:**
1. Uses `api.download()` which only supports GET requests
2. Only passes `language` and `includeInstructions` as query parameters
3. **Completely ignores** `options.columns` (8 boolean fields)
4. **Completely ignores** `options.lockColumns` boolean

**Actual API call made:**
```
GET /tenders/{tenderId}/boq/export-template?language=0&includeInstructions=true
```

---

### 3. Frontend API Service
**File:** `C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER\frontend\src\app\core\services\api.service.ts`

**download() method (Lines 111-117):**
```typescript
download(endpoint: string, filename?: string): Observable<Blob> {
  return this.http.get(`${this.baseUrl}${endpoint}`, {
    responseType: 'blob'
  }).pipe(
    catchError(this.handleError)
  );
}
```

**Limitation:** Only supports GET method, cannot send request body.

**Available alternative (Lines 76-81):**
```typescript
post<T>(endpoint: string, data: unknown): Observable<T> {
  return this.http.post<ApiResponse<T>>(`${this.baseUrl}${endpoint}`, data).pipe(
    map(response => response.data),
    catchError(this.handleError)
  );
}
```

**Issue:** The `post()` method expects `ApiResponse<T>` wrapper, but file downloads return raw Blob without wrapper.

---

### 4. Backend Controller
**File:** `C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER\backend\Bayan.API\Controllers\BoqController.cs`

**TWO EXPORT ENDPOINTS EXIST:**

#### Endpoint 1: POST (CORRECT - But unused by frontend)
**Lines 459-493:**
```csharp
[HttpPost("tenders/{tenderId:guid}/boq/export-template")]
public async Task<IActionResult> ExportTemplate(
    Guid tenderId,
    [FromBody] ExportBoqTemplateDto? dto = null,
    CancellationToken cancellationToken = default)
{
    // Use defaults if no DTO provided
    dto ??= new ExportBoqTemplateDto();

    var command = new ExportBoqTemplateCommand
    {
        TenderId = tenderId,
        IncludeColumns = dto.IncludeColumns,      // ✓ Supports column selection
        LockColumns = dto.LockColumns,            // ✓ Supports column locking
        IncludeInstructions = dto.IncludeInstructions,
        Language = dto.Language
    };

    var result = await _mediator.Send(command, cancellationToken);
    return File(result.FileContent, result.ContentType, result.FileName);
}
```

#### Endpoint 2: GET (INCOMPLETE - Currently called by frontend)
**Lines 503-532:**
```csharp
[HttpGet("tenders/{tenderId:guid}/boq/export-template")]
public async Task<IActionResult> ExportTemplateGet(
    Guid tenderId,
    [FromQuery] TemplateLanguage language = TemplateLanguage.English,
    [FromQuery] bool includeInstructions = true,
    CancellationToken cancellationToken = default)
{
    var command = new ExportBoqTemplateCommand
    {
        TenderId = tenderId,
        Language = language,                       // ✓ Supported
        IncludeInstructions = includeInstructions  // ✓ Supported
        // ✗ IncludeColumns: Uses defaults (not customizable)
        // ✗ LockColumns: Uses defaults (not customizable)
    };

    var result = await _mediator.Send(command, cancellationToken);
    return File(result.FileContent, result.ContentType, result.FileName);
}
```

**CRITICAL FINDING:** GET endpoint only accepts 2 of 4 parameters, always uses default column settings.

---

### 5. Backend Export Command
**File:** `C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER\backend\Bayan.Application\Features\Boq\Commands\ExportBoqTemplate\ExportBoqTemplateCommand.cs`

```csharp
public class ExportBoqTemplateCommand : IRequest<ExportResultDto>
{
    public Guid TenderId { get; set; }

    /// Columns to include in the export.
    public List<string> IncludeColumns { get; set; } = new()
    {
        "ItemNumber", "Description", "Quantity", "Uom", "UnitRate", "Amount"
    };

    /// Columns to lock (read-only) in the exported template.
    public List<string> LockColumns { get; set; } = new()
    {
        "ItemNumber", "Description", "Quantity", "Uom"
    };

    public bool IncludeInstructions { get; set; } = true;
    public TemplateLanguage Language { get; set; } = TemplateLanguage.English;
}
```

**Expected data format:** String arrays, not boolean objects.

---

### 6. Backend Export Handler
**File:** `C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER\backend\Bayan.Application\Features\Boq\Commands\ExportBoqTemplate\ExportBoqTemplateCommandHandler.cs`

**Lines 67-70:**
```csharp
var generationRequest = new BoqTemplateGenerationRequest
{
    // ... other fields ...
    IncludeColumns = request.IncludeColumns,  // Properly passed through
    LockColumns = request.LockColumns,        // Properly passed through
    IncludeInstructions = request.IncludeInstructions,
    Language = request.Language
};
```

**Verification:** Backend correctly processes all options when provided.

---

### 7. Frontend Model Definition
**File:** `C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER\frontend\src\app\core\models\boq.model.ts`

**Lines 106-120:**
```typescript
export interface BoqExportOptions {
  columns: {
    itemNumber: boolean;
    description: boolean;
    quantity: boolean;
    uom: boolean;
    type: boolean;
    notes: boolean;
    unitRate: boolean;
    totalAmount: boolean;
  };
  lockColumns: boolean;        // Single boolean, not array
  includeInstructions: boolean;
  language: 'en' | 'ar' | 'both';
}
```

**Structure mismatch with backend:**
- Frontend: `columns: { itemNumber: boolean, ... }`
- Backend: `IncludeColumns: string[]` (e.g., `["ItemNumber", "Description"]`)
- Frontend: `lockColumns: boolean`
- Backend: `LockColumns: string[]`

---

## Data Mapping Requirements

### Frontend → Backend transformation needed:

**Column Selection:**
```typescript
// Frontend (current):
columns: {
  itemNumber: true,
  description: true,
  quantity: false,
  uom: true,
  type: true,
  notes: false,
  unitRate: true,
  totalAmount: true
}

// Backend (required):
includeColumns: ["ItemNumber", "Description", "Uom", "Type", "UnitRate", "TotalAmount"]
```

**Column Locking:**
```typescript
// Frontend (current):
lockColumns: true  // Boolean flag

// Backend (required):
lockColumns: ["ItemNumber", "Description", "Quantity", "Uom"]  // When true
// OR
lockColumns: []  // When false
```

**Column Name Mapping:**
```typescript
const COLUMN_NAME_MAP = {
  itemNumber: 'ItemNumber',
  description: 'Description',
  quantity: 'Quantity',
  uom: 'Uom',
  type: 'Type',
  notes: 'Notes',
  unitRate: 'UnitRate',
  totalAmount: 'Amount'  // Note: Different backend name
};
```

**Language Mapping (already correct):**
```typescript
const languageMap = { en: 0, ar: 1, both: 2 };  // ✓ Matches TemplateLanguage enum
```

---

## Why Manual BOQ Addition Works

Manual BOQ item creation uses different endpoints that are correctly implemented:

**Frontend calls (boq.service.ts line 357):**
```typescript
POST /tenders/${data.tenderId}/boq/items
```

**Backend endpoint (BoqController.cs line 169):**
```csharp
[HttpPost("tenders/{tenderId:guid}/boq/items")]
public async Task<ActionResult<BoqItemDto>> CreateItem(...)
```

These endpoints have proper POST method + request body implementation, unlike the export feature.

---

## Required Fixes

### Fix 1: Add downloadPost() method to ApiService
**File:** `frontend/src/app/core/services/api.service.ts`

```typescript
downloadPost(endpoint: string, data: unknown): Observable<Blob> {
  return this.http.post(`${this.baseUrl}${endpoint}`, data, {
    responseType: 'blob'
  }).pipe(
    catchError(this.handleError)
  );
}
```

### Fix 2: Update exportToExcel() in BoqService
**File:** `frontend/src/app/core/services/boq.service.ts`

Replace lines 532-548 with:

```typescript
exportToExcel(tenderId: number, options: BoqExportOptions): Observable<Blob> {
  this._isLoading.set(true);
  this._error.set(null);

  // Transform frontend options to backend DTO format
  const includeColumns = this.buildIncludeColumns(options.columns);
  const lockColumns = options.lockColumns
    ? ['ItemNumber', 'Description', 'Quantity', 'Uom']
    : [];

  const languageMap: Record<string, number> = { en: 0, ar: 1, both: 2 };

  const requestBody = {
    includeColumns,
    lockColumns,
    includeInstructions: options.includeInstructions,
    language: languageMap[options.language] ?? 0
  };

  return this.api.downloadPost(`/tenders/${tenderId}/boq/export-template`, requestBody).pipe(
    tap(() => this._isLoading.set(false)),
    catchError(error => {
      this._isLoading.set(false);
      this._error.set(error.message || 'Failed to export BOQ');
      return throwError(() => error);
    })
  );
}

private buildIncludeColumns(columns: BoqExportOptions['columns']): string[] {
  const columnMap: Record<keyof BoqExportOptions['columns'], string> = {
    itemNumber: 'ItemNumber',
    description: 'Description',
    quantity: 'Quantity',
    uom: 'Uom',
    type: 'Type',
    notes: 'Notes',
    unitRate: 'UnitRate',
    totalAmount: 'Amount'
  };

  return Object.entries(columns)
    .filter(([_, enabled]) => enabled)
    .map(([key, _]) => columnMap[key as keyof typeof columnMap]);
}
```

### Fix 3 (Optional): Standardize Backend Endpoint
**File:** `backend/Bayan.API/Controllers/BoqController.cs`

Consider removing the GET endpoint (lines 503-532) or adding a deprecation notice to prevent confusion:

```csharp
[Obsolete("Use POST endpoint for full export customization")]
[HttpGet("tenders/{tenderId:guid}/boq/export-template")]
```

---

## Verification Steps

After implementing fixes:

1. Start Angular dev server: `cd frontend && npm start`
2. Start .NET backend: `cd backend/Bayan.API && dotnet run`
3. Navigate to tender details page
4. Click "Export BOQ Template" button
5. Modify column selections in dialog
6. Toggle "Lock columns" checkbox
7. Click "Download"
8. Open downloaded Excel file
9. Verify:
   - Only selected columns are present
   - Locked columns cannot be edited (if enabled)
   - Unlocked columns are editable
   - Instructions sheet present/absent based on selection
   - Correct language used

---

## Testing Checklist

- [ ] Export with all columns enabled
- [ ] Export with minimal columns (only required)
- [ ] Export with column locking enabled
- [ ] Export with column locking disabled
- [ ] Export in English
- [ ] Export in Arabic
- [ ] Export in Bilingual mode
- [ ] Export with instructions sheet
- [ ] Export without instructions sheet
- [ ] Verify Excel file opens correctly
- [ ] Verify locked cells cannot be edited
- [ ] Verify formulas work in unlocked cells
- [ ] Test with empty BOQ
- [ ] Test with large BOQ (100+ items)

---

## Files Examined

### Frontend
1. `C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER\frontend\src\app\features\tenders\tender-details\boq\boq-export-dialog.component.ts`
2. `C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER\frontend\src\app\core\services\boq.service.ts`
3. `C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER\frontend\src\app\core\services\api.service.ts`
4. `C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER\frontend\src\app\core\models\boq.model.ts`

### Backend
5. `C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER\backend\Bayan.API\Controllers\BoqController.cs`
6. `C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER\backend\Bayan.Application\Features\Boq\Commands\ExportBoqTemplate\ExportBoqTemplateCommand.cs`
7. `C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER\backend\Bayan.Application\Features\Boq\Commands\ExportBoqTemplate\ExportBoqTemplateCommandHandler.cs`
8. `C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER\backend\Bayan.Application\Features\Boq\DTOs\ExportBoqTemplateDto.cs`
9. `C:\Users\Omar Khaled\OneDrive\Desktop\claude-agent-team\BAYAN_TENDER\backend\Bayan.Application\Common\Interfaces\ITemplateExportService.cs`

---

## Impact Assessment

**Current State:**
- Users see a detailed export options dialog
- Users select columns, locking, language
- Export appears to work (file downloads)
- BUT: Export ignores all user selections
- All exports use hardcoded default settings

**User Experience Impact:**
- CRITICAL: Feature appears broken when users expect customized exports
- Users cannot exclude unwanted columns
- Users cannot control column protection
- Users waste time configuring options that have no effect

**Business Impact:**
- Export templates may include sensitive columns that should be hidden
- Bidders may receive incorrect or confusing templates
- Manual workarounds required (editing Excel after export)

---

## Recommended Priority: CRITICAL

**Justification:**
1. Core tender management feature non-functional
2. User interface misleading (collects options but ignores them)
3. Backend implementation complete and working
4. Fix is straightforward (method change + data transformation)
5. High user-facing impact

**Estimated Development Time:** 2-3 hours
**Estimated Testing Time:** 1-2 hours

---

## Additional Notes

- The backend implementation is solid and well-structured
- The POST endpoint exists and is fully functional
- Only frontend needs changes (no backend modifications required)
- Consider adding frontend unit tests for the option transformation logic
- Consider adding E2E test for the complete export flow
