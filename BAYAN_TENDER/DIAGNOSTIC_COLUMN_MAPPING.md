# BOQ Column Mapping Diagnostic

## Issue
Master BOQ (02_BOQ_Master_No_Prices.xlsx) columns aren't auto-mapping, so "Next" button stays disabled.

## Expected Behavior
**Master BOQ Headers:** `Bill No. | Item No. | Sub-Item | Description | Qty | Unit`

**Required Mappings (for Next button):**
- `Item No.` → `itemNumber`
- `Description` → `description`
- `Qty` → `quantity`
- `Unit` → `uom`

## Diagnostic Steps

### Step 1: Check Backend Response
Open browser DevTools (F12) → Network tab → Upload the Master BOQ → Find the `upload-for-preview` request → Check the response:

```json
{
  "importSessionId": "...",
  "suggestedMappings": [
    { "excelColumn": "Item No.", "boqField": 1, "confidence": 95 },
    { "excelColumn": "Description", "boqField": 2, "confidence": 95 },
    { "excelColumn": "Qty", "boqField": 3, "confidence": 95 },
    { "excelColumn": "Unit", "boqField": 4, "confidence": 95 }
  ]
}
```

**If `suggestedMappings` is empty or missing these 4 items → Backend issue**
**If `suggestedMappings` looks correct → Frontend issue**

### Step 2: Check Frontend Mapping Application
Add console.log to the frontend:

Open `boq-import-dialog.component.ts` line 911-923 in `autoMapColumns()`:

```typescript
autoMapColumns(): void {
  this.columnMappings = {};

  // Add debugging
  console.log('🔍 suggestedMappings from backend:', this.uploadPreview?.suggestedMappings);

  if (this.uploadPreview?.suggestedMappings?.length) {
    for (const mapping of this.uploadPreview.suggestedMappings) {
      const fieldKey = BOQ_FIELD_REVERSE[mapping.boqField];

      // Add debugging
      console.log(`Mapping: "${mapping.excelColumn}" (BoqField=${mapping.boqField}) → fieldKey="${fieldKey}"`);

      if (fieldKey && mapping.excelColumn) {
        this.columnMappings[mapping.excelColumn] = fieldKey;
      }
    }
  }

  // Add debugging
  console.log('✅ Final columnMappings:', this.columnMappings);
  console.log('✅ hasRequiredMappings:', this.hasRequiredMappings());
}
```

### Step 3: Check Required Mappings Logic
The `hasRequiredMappings()` function (line 936) checks:

```typescript
private hasRequiredMappings(): boolean {
  const required = ['itemNumber', 'description', 'quantity', 'uom'];
  const mapped = Object.values(this.columnMappings).filter(v => v !== null);
  return required.every(field => mapped.includes(field));
}
```

**Expected after auto-mapping:**
- `columnMappings = { "Item No.": "itemNumber", "Description": "description", "Qty": "quantity", "Unit": "uom" }`
- `mapped = ["itemNumber", "description", "quantity", "uom"]`
- `hasRequiredMappings() = true` ✓

## Possible Issues

### Issue A: Backend Not Detecting Headers
**Symptom:** `suggestedMappings` is empty in network response

**Cause:** Headers don't match regex patterns

**Fix:** Check if Excel file has extra spaces or different casing in headers

### Issue B: Frontend Field Key Mismatch
**Symptom:** Console shows `fieldKey=undefined`

**Cause:** `BOQ_FIELD_REVERSE` mapping is broken

**Current mapping:**
```typescript
const BOQ_FIELD: Record<string, number> = {
  itemNumber: 1,
  description: 2,
  quantity: 3,
  uom: 4,
  // ...
};
```

**Backend enum:**
```csharp
public enum BoqField {
  ItemNumber = 1,
  Description = 2,
  Quantity = 3,
  Uom = 4,
  // ...
}
```

Values match, so this should work.

### Issue C: Headers Have Leading/Trailing Spaces
**Symptom:** Backend returns `"Item No. "` (with space) but UI shows `"Item No."`

**Fix:** Trim headers when parsing Excel

## Quick Fix

If diagnostics show backend is working but frontend isn't applying mappings, try this manual workaround:

**After upload, manually select dropdowns:**
- `Item No.` → Select "Item Number"
- `Description` → Select "Description"
- `Qty` → Select "Quantity"
- `Unit` → Select "Unit"

Then click Next.

## Permanent Fix

Based on diagnostic results, I can provide the exact code fix.
