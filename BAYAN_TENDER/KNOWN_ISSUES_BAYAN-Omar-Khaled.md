# Bayan Tender — Known Issues & Technical Debt

**Created:** 2026-02-11
**Updated:** 2026-02-14 (Playwright E2E sessions — 6 bugs found, 5 fixed, ISSUE-14 resolved)
**Status:** All documented, 1 open (per-bid download), rest fixed or non-blocking
**Source:** Manual E2E testing + Playwright browser automation

---

## Quick Wins (< 1 hour each)

### ISSUE-01: ASP.NET serializes all enums as integers (no JsonStringEnumConverter)

**Severity:** MEDIUM
**Effort:** ~2 hours (including regression check)
**Affected areas:** Every API response containing enum fields (clarification status, priority, source, bid status, qualification status, approval decisions)

**Problem:**
ASP.NET's default JSON serializer sends enum values as integers (e.g., `status: 0` instead of `status: "Submitted"`). The frontend has workaround normalizers in multiple services.

**Current workarounds:**
- `portal.service.ts` → `normalizeClarification()` maps integers to strings
- `clarification.service.ts` → `normalizeClarification()` with `STATUS_INT_MAP`, `PRIORITY_INT_MAP`, `SOURCE_INT_MAP`
- `evaluation.service.ts` → `statusMap`, `decisionMap` for approval workflow enums

**Fix:**
Add one line to `backend/Bayan.API/Program.cs`:
```csharp
builder.Services.AddControllers().AddJsonOptions(options =>
    options.JsonSerializerOptions.Converters.Add(new System.Text.Json.Serialization.JsonStringEnumConverter()));
```

**Risk:**
Frontend normalizers currently expect integers. After this fix, they'll receive strings. The normalizers handle both (they check `typeof status === 'number'`), but every enum-consuming component should be regression-tested. Consider keeping normalizers as backwards-compatible fallbacks.

**Files to modify:**
- `backend/Bayan.API/Program.cs` — add converter
- Regression test: all clarification views (admin + portal), evaluation views, approval views, bid status displays

---

### ISSUE-02: Bidder qualification requires raw SQL (no UI workflow)

**Severity:** HIGH
**Effort:** ~1-2 days
**Affected areas:** Bidder invitation flow, portal access gating

**Problem:**
After inviting a bidder to a tender, their `qualification_status` on `tender_bidders` is `Pending`. The portal's `GetPortalDocumentsQueryHandler` requires `Qualified` status. Currently this is set via raw SQL:
```sql
UPDATE bayan.tender_bidders SET qualification_status = 'Qualified' WHERE bidder_id = '...' AND tender_id = '...';
```

**What's needed:**
1. **Admin UI** — qualification review panel on the tender's Bidders tab:
   - View bidder's submitted prequalification documents
   - Status dropdown: Pending → Qualified / Rejected / Removed
   - Notes/reason field for rejection
   - Notification email to bidder on status change
2. **Backend endpoint exists:** `PUT /api/tenders/{id}/bidders/{bidderId}/qualification` — needs UI wiring
3. **Consider:** Bulk qualification (select multiple bidders → qualify all)

**Files to create/modify:**
- `frontend/src/app/features/tenders/tender-details/bidders/` — qualification review component
- Wire into tender-details bidders tab
- Email template for qualification notification

---

### ISSUE-03: MinIO presigned URLs unreachable from browser (Docker internal hostname)

**Severity:** LOW
**Effort:** ~1 day
**Affected areas:** Document downloads (admin + portal)

**Problem:**
MinIO generates presigned URLs using the Docker internal hostname `minio:9000`, which browsers can't resolve. Both admin and portal controllers now stream files directly through the API (`return File(stream, contentType, fileName)`).

**Current state:** Working correctly via API streaming. This is a performance optimization issue, not a bug.

**Fix (for production):**
1. Expose MinIO behind a reverse proxy with a public hostname (e.g., `storage.bayan.ae`)
2. Configure MinIO client with the public endpoint for presigned URL generation
3. Handle CORS headers for cross-origin downloads
4. Update `PortalController.cs` and `DocumentsController.cs` to return presigned URLs instead of streaming

**When to fix:** Before production deployment with large file volumes. Streaming through API consumes API server memory proportional to file size.

---

### ISSUE-04: Property naming inconsistency (PascalCase DTOs + integer enums)

**Severity:** LOW
**Effort:** ~1 day (audit + cleanup)
**Affected areas:** All frontend service layers

**Problem:**
- Backend C# DTOs use PascalCase (`CompanyName`, `QualificationStatus`)
- ASP.NET serializes to camelCase (`companyName`, `qualificationStatus`) — this is fine
- BUT enum values serialize as integers (see ISSUE-01)
- Different DTOs for the same entity have different field names (e.g., `BidderQuestionDto.statusDisplay` vs `PortalClarificationDto.status`)
- Frontend service layer contains normalization logic to handle all variations

**Fix:**
1. Fix ISSUE-01 first (JsonStringEnumConverter)
2. Audit all DTOs for naming consistency — same concept should use same field name
3. Clean up frontend normalizers that are no longer needed
4. Document the DTO naming convention for future development

**Files affected:**
- `portal.service.ts` — normalizeClarification()
- `clarification.service.ts` — normalizeClarification() with 6 map objects
- `evaluation.service.ts` — statusMap, decisionMap
- `user.service.ts` — role integer mapping
- `bidder.service.ts` — prequalification status mapping

---

### ISSUE-05: 7 components exceed 4.1KB inline style budget

**Severity:** LOW (cosmetic warning)
**Effort:** ~3-4 hours
**Affected areas:** Angular build warnings only — no runtime impact

**Problem:**
Angular CLI warns during `ng build` that 7 components have inline styles exceeding the 4.1KB budget. These are standalone components with large `styles: [...]` blocks.

**Fix:**
Extract inline styles to separate `.scss` files for each affected component:
1. Create `component-name.component.scss` alongside each `.ts` file
2. Move the style content from `styles: [...]` to the `.scss` file
3. Change to `styleUrls: ['./component-name.component.scss']`

**Note:** This is purely a build warning cleanup. No functional impact.

---

### ISSUE-06: DB schema drift — raw SQL columns not in EF Core migrations

**Severity:** HIGH
**Effort:** ~1 day
**Affected areas:** Database recreation, CI/CD pipelines, new developer onboarding

**Problem:**
Several columns and tables were added via raw SQL during E2E testing and bug fixing, bypassing EF Core's migration system:
- `Client` entity: `City`, `Country`, `CRNumber`, `VatNumber`, `ContactEmail`, `ContactPhone` (Fix 35)
- `system_settings` table: 29 additional setting rows (Fix 38)
- `evaluation_state` and `evaluation_panels` records (Fix 25)
- Approver user records (3 additional users)
- Various `tender_bidders.qualification_status` updates

If the Docker DB volume is deleted and recreated, these changes are lost.

**Fix:**
1. Create an EF Core migration that adds the missing columns:
   ```bash
   dotnet ef migrations add AddClientExtendedFields
   ```
2. Create a seed data migration or `DbContext.OnModelCreating` seed for default settings, roles
3. Export current SQL as a backup: `pg_dump -h localhost -U bayan_user bayan > bayan_backup.sql`
4. Test full recreation: delete volume → `docker compose up` → verify migrations apply → verify seed data

**Immediate mitigation:** The SQL statements are documented in E2E_HANDOFF.md Section 4. Run them after any DB recreation.

---

### ISSUE-07: DraftAnswer vs Answered — 2-step flow collapsed to 1

**Severity:** LOW
**Effort:** ~1-2 hours
**Affected areas:** Admin clarification management

**Problem:**
Backend has a 2-step answer flow:
1. Admin writes answer → status becomes `DraftAnswer` (2)
2. Admin approves answer → status becomes `Answered` (3)

But the frontend maps both `DraftAnswer` and `Answered` to the string `'answered'`, effectively collapsing the review step. The `PublishBulletinCommandHandler` has a workaround that auto-approves `DraftAnswer` items before publishing.

**Fix:**
1. Add an "Approve Answer" button to the admin clarification detail view (visible when status is `DraftAnswer`)
2. Wire to existing or new endpoint: `POST /api/tenders/{id}/clarifications/{id}/approve`
3. Show different action buttons for `DraftAnswer` vs `Answered`:
   - `DraftAnswer`: "Edit Answer", "Approve Answer"
   - `Answered`: "Edit Answer", "Ready for Bulletin"
4. Remove the auto-approve workaround from `PublishBulletinCommandHandler` (or keep as fallback)

---

### ISSUE-08: Approver role gets 403 errors on secondary API calls

**Severity:** MEDIUM
**Effort:** 30 min (suppress) or 2 hours (fix properly)
**Affected areas:** Approver user experience when navigating tenders

**Problem:**
When logged in as an Approver, navigating to the Tenders list triggers secondary API calls (dashboard stats, bidder endpoints) that have `[Authorize(Roles = "Admin,TenderManager")]`. These return 403 Forbidden, showing error toasts. The primary tenders list and Approval tab work fine.

**Option A — Suppress errors (30 min):**
Add an HTTP interceptor that silently swallows 403 errors on non-critical endpoints when the user's role is Approver. Or add `catchError(() => of(null))` to the specific service calls.

**Option B — Add read-only access (2 hours):**
Add `Approver` to the `[Authorize(Roles = "...")]` attribute on these endpoints:
- Dashboard overview stats
- Bidder list (read-only)
- Any other endpoints called during tender navigation

**Recommendation:** Option B is cleaner. Approvers should be able to see tender context without errors.

---

### ISSUE-09: Approval workflow hardcoded to exactly 3 levels

**Severity:** MEDIUM
**Effort:** ~4 hours
**Affected areas:** Approval workflow initiation

**Problem:**
`InitiateApprovalCommand` validator requires exactly 3 approver IDs:
```csharp
RuleFor(x => x.ApproverIds).Must(x => x.Count == 3)
    .WithMessage("Exactly 3 approvers must be specified");
```
The frontend auto-fetches the first 3 users with Approver role from `GET /api/approvers`.

**Fix:**
1. **Backend validator:** Change to `Count >= 1 && Count <= MaxLevels` (configurable via system settings)
2. **Level activation logic:** Already works sequentially — just needs to handle variable depth
3. **Final approval trigger:** The "workflow completed" check should look for all levels approved, not hardcoded level 3
4. **System setting:** Add `max_approval_levels` (default: 3) to `system_settings`

**Files to modify:**
- `InitiateApprovalCommand.cs` — validator
- `InitiateApprovalCommandHandler.cs` — level creation loop
- `SubmitApprovalDecisionCommandHandler.cs` — "is final level?" check
- `system_settings` table — new setting row

---

### ISSUE-10: No approver selection UI — auto-assigns first 3

**Severity:** MEDIUM
**Effort:** ~4-6 hours
**Affected areas:** Approval workflow initiation UX

**Problem:**
The Combined Scorecard's "Start Approval" button auto-assigns the first 3 Approver-role users without any selection dialog. In production, the tender manager should choose which approvers and in what order.

**Fix:**
Build an "Initiate Approval" dialog component:
1. **User dropdown** filtered to Approver role (from `GET /api/approvers`)
2. **Drag-to-reorder list** showing Level 1, Level 2, Level 3 (or more if ISSUE-09 is fixed)
3. **Add/remove** approvers from the list
4. **Confirmation** showing the approval chain before initiating
5. Wire the selected + ordered IDs to `startApproval(tenderId, approverIds)`

**Files to create:**
- `frontend/src/app/features/tenders/tender-details/evaluation/initiate-approval-dialog.component.ts`
- Update `combined-scorecard.component.ts` to open the dialog instead of auto-assigning

---

### ISSUE-11: BCrypt password hashes corrupted by shell escaping

**Severity:** LOW (operational, not code)
**Effort:** 0 (documented workaround)
**Affected areas:** Manual DB operations via shell

**Problem:**
BCrypt hashes contain `$` characters (e.g., `$2a$12$hpH3Ub...`). When passed through shell commands (bash, PowerShell), the `$` triggers variable interpolation, corrupting the hash. For example:
```sql
-- BROKEN: shell interprets $2a, $12, etc.
UPDATE bidders SET password_hash = '$2a$12$hpH3Ub...' WHERE email = 'user@email.com';
```

**Workaround (reliable):**
Copy hash from a working account via SQL subquery:
```sql
UPDATE bidders SET password_hash = (
    SELECT password_hash FROM bidders WHERE email = 'known_working@email.com'
) WHERE email = 'target@email.com';
```

**Proper fix (for production):**
- Never set passwords via raw SQL — use the admin UI (Fix 31 added password field to user creation)
- For bidders: use the account activation flow (invitation email → set password)
- For bulk seeding: use a migration script that reads from a seed file, not shell commands

---

### ISSUE-12: Frontend doesn't auto-refresh after backend state transitions

**Severity:** HIGH
**Effort:** ~30 min per component (3-4 components)
**Affected areas:** Approval decisions, tender status changes, bid submission

**Problem:**
After key backend state transitions (e.g., final approval → tender status changes to "Awarded"), the Angular frontend still shows the old state. A full page reload is required to see the updated status.

**Observed in:**
- Approval tab: after submitting a decision, the workflow status doesn't update until reload
- Tender header: after final approval, still shows "Closed" instead of "Awarded" until reload
- Portal tender card: after bid submission, status badge doesn't update until re-login

**Fix options:**

**Option A — Force reload after key actions (~30 min/component):**
After approval decision submission, tender closing, bid opening:
```typescript
this.approvalService.submitDecision(dto).subscribe({
  next: () => {
    this.messageService.add({ severity: 'success', ... });
    // Force refresh the tender data
    this.loadTenderDetails();
    this.loadApprovalWorkflow();
  }
});
```

**Option B — WebSocket/SSE notifications (~2-3 days):**
Push state changes from backend to connected frontends via SignalR:
- `TenderStatusChanged` event
- `ApprovalDecisionSubmitted` event
- `BidSubmitted` event
Frontend subscribes and updates local state in real-time.

**Recommendation:** Option A for immediate fix, Option B as a future enhancement.

**Files to modify (Option A):**
- `approval-tab.component.ts` — reload after decision
- `tender-details.component.ts` — reload tender data after status change
- `portal-submit.component.ts` — reload after bid submission
- `portal-tenders.component.ts` — reload tender list after navigation back

---

## Fixed Issues (Playwright E2E Session — 2026-02-14)

### FIXED-01: Vendor Pricing AEDNaN display (was showing "AEDNaN" instead of currency values)

**Fixed in:** backend `VendorPricingDto` (added missing `TotalAmount` field) + frontend `vendor-pricing.component.ts` (null guard on currency formatting)
**Verified:** Playwright confirmed "AED 15,296,740" and "AED 11,474,690" display correctly

### FIXED-02: Close Tender used wrong endpoint (/cancel instead of /close)

**Fixed in:**
- Created `CloseTenderCommand.cs`, `CloseTenderCommandHandler.cs`, `CloseTenderCommandValidator.cs` (transitions Active → Evaluation)
- Added `[HttpPost("{id:guid}/close")]` endpoint to `TendersController.cs`
- Fixed `tender.service.ts` line 196: changed `/cancel` to `/close` for 'closed' status

### FIXED-03: Dashboard silent error (no user-facing feedback on API failure)

**Fixed in:** `dashboard.component.ts` — added `loadError` signal, error banner with retry button, `.error-banner` CSS styles

### FIXED-04: Missing internal logout endpoint (404 on POST /api/auth/logout)

**Fixed in:** `AuthController.cs` — added `[HttpPost("logout")]` endpoint (JWT is stateless, returns success for client to clear tokens)

### FIXED-05: Missing portal logout endpoint (404 on POST /api/portal/auth/logout)

**Fixed in:** `PortalController.cs` — added `[HttpPost("auth/logout")]` endpoint (portal uses `/api/portal` base URL prefix)

---

## Open Issues (from Playwright E2E Session)

### ISSUE-13: Per-bid file download endpoint missing

**Severity:** MEDIUM
**Effort:** ~2 hours
**Affected areas:** Bid details dialog — "Download Files" button

**Problem:**
Frontend `bid.service.ts` `downloadBidFiles()` calls `GET /api/tenders/{id}/bids/{bidId}/download` which doesn't exist. Backend `BidsController.cs` only has `[HttpGet("download-all")]` for batch download of all bids.

**Fix:**
Add a per-bid download endpoint to `BidsController.cs`:
```csharp
[HttpGet("{bidId:guid}/download")]
public async Task<IActionResult> DownloadBidFiles(Guid id, Guid bidId, ...)
```
Or zip the bid's documents and stream them.

**Workaround:** Users can use the "Download All Bids" button on the Bids tab instead.

---

### FIXED-06: Tender list Export button — 404 endpoint missing (was ISSUE-14)

**Fixed in:** Session #6 (2026-02-14)
- Created `ExportTendersQuery.cs` and `ExportTendersQueryHandler.cs` — CSV export with UTF-8 BOM (ClosedXML caused Docker exit code 135, switched to StringBuilder CSV)
- Added `[HttpGet("export")]` endpoint to `TendersController.cs`
- Frontend `tender.service.ts` `exportToExcel()` already called correct endpoint — no frontend changes needed
- **Verified:** Playwright confirmed CSV download with 5 tenders, 11 columns

### FIXED-07: mapStatus() bug — Late bids never shown in UI

**Fixed in:** Session #6 (2026-02-14)
- `bid.service.ts` `getBids()` mapping: added `status: (b.isLate && this.mapStatus(b.status) === 'submitted') ? 'late' : this.mapStatus(b.status)`
- Same fix applied to `mapBidDetailToSubmission()`
- **Problem:** `mapStatus()` only mapped backend enum values 0-3 (submitted/opened/imported/disqualified). Template checked `bid.status === 'late'` but mapStatus never returned 'late'. Backend tracks lateness via separate `isLate` boolean.
- **Verified:** Playwright confirmed Late Bids section renders with Accept/Reject buttons when bid has isLate=true
