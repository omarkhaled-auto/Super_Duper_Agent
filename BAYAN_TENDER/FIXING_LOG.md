# BAYAN Tender Management System - Fixing Log

**Started:** 2026-02-07
**System:** Angular 18 + .NET 8 API + Docker Compose (PostgreSQL 16, Redis 7, MinIO, Nginx)

---

## Issue #1: UI Freezes After Login (CRITICAL)

**Symptom:** User logs in at `http://localhost:4200`, login succeeds (confirmed by nginx logs showing POST /api/auth/login -> 200), but then the page freezes completely. Refreshing the page also fails to load. Nginx logs show a 47-second gap between login response and any subsequent browser request.

**Root Cause:** The `SidebarComponent` used a **getter** (`get menuItems(): MenuItem[]`) that created new array instances on every Angular change detection cycle. PrimeNG's `PanelMenu` component detects input changes by reference. Since the getter returns a new array reference every time, PanelMenu sees "changed" input -> re-renders -> triggers change detection -> getter called again -> **infinite synchronous loop** that blocks the main JavaScript thread.

**File:** `frontend/src/app/layout/sidebar/sidebar.component.ts`

**Fix:** Replaced the getter with an Angular `computed()` signal. Computed signals cache their value and only recalculate when their dependencies (signals they read) change. This means the array is created once and reused across change detection cycles.

```typescript
// BEFORE (broken - creates new array every change detection)
get menuItems(): MenuItem[] {
    const baseItems: MenuItem[] = [...];
    return baseItems;
}

// AFTER (fixed - caches array, recalculates only when user signal changes)
menuItems = computed<MenuItem[]>(() => {
    const user = this.currentUser(); // dependency on user signal
    const baseItems: MenuItem[] = [...];
    return baseItems;
});
```

Template also updated from `[model]="menuItems"` to `[model]="menuItems()"` (signal invocation).

**Status:** FIXED

---

## Issue #2: Role Type Mismatch - API Returns Numeric, Frontend Expects String

**Symptom:** `hasRole()` in `AuthService` always returns `false`. Admin users don't see the Administration menu in the sidebar. Role-based guards (roleGuard) would always reject users.

**Root Cause:** The .NET backend stores and returns roles as numeric enum values:
- `Admin = 0`, `TenderManager = 1`, `CommercialAnalyst = 2`, `TechnicalPanelist = 3`, `Approver = 4`, `Auditor = 5`, `Bidder = 6`

But the Angular frontend `UserRole` enum uses string values:
- `ADMIN = 'admin'`, `TENDER_MANAGER = 'tender_manager'`, etc.

When the API returns `{ role: 0 }`, the frontend stores it as-is. Then `hasRole(['admin', 'tender_manager'])` does `['admin', 'tender_manager'].includes(0)` which is always `false`.

**Files:**
- `frontend/src/app/core/models/user.model.ts`
- `frontend/src/app/core/auth/auth.service.ts`

**Fix:**
1. Added all 7 backend roles to the `UserRole` enum (was missing `COMMERCIAL_ANALYST`, `TECHNICAL_PANELIST`, `APPROVER`)
2. Created a `mapApiRole(role: number | string): UserRole` function that converts numeric API values to string enum values
3. Applied mapping in `handleAuthSuccess()` (login flow) and `loadUserFromStorage()` (page refresh flow)

```typescript
// user.model.ts - new mapping function
const ROLE_MAP: Record<number, UserRole> = {
  0: UserRole.ADMIN,
  1: UserRole.TENDER_MANAGER,
  2: UserRole.COMMERCIAL_ANALYST,
  3: UserRole.TECHNICAL_PANELIST,
  4: UserRole.APPROVER,
  5: UserRole.AUDITOR,
  6: UserRole.BIDDER,
};

export function mapApiRole(role: number | string): UserRole {
  if (typeof role === 'number') return ROLE_MAP[role] ?? UserRole.BIDDER;
  // If already a string, validate it
  const values = Object.values(UserRole) as string[];
  return values.includes(role) ? role as UserRole : UserRole.BIDDER;
}

// auth.service.ts - applied in both auth success and storage load
const user = { ...data.user, role: mapApiRole(data.user.role as any) };
```

**Status:** FIXED

---

## Issue #3: Missing Logo Image (assets/images/logo.png)

**Symptom:** Browser console shows 404 for `assets/images/logo.png`. Nginx logs show the same 404. Broken image icon appears in the header.

**Root Cause:** The `src/assets/images/` directory was never created. The `HeaderComponent` template references `<img src="assets/images/logo.png">` but the file doesn't exist.

**File:** `frontend/src/app/layout/header/header.component.ts`

**Fix:** Replaced the `<img>` tag with a PrimeNG icon (`pi pi-briefcase`) that's always available since PrimeIcons CSS is bundled in the build. No external image file needed.

```html
<!-- BEFORE -->
<img src="assets/images/logo.png" alt="Bayan" height="32" *ngIf="!collapsed" />

<!-- AFTER -->
<i class="pi pi-briefcase logo-icon" *ngIf="!collapsed"></i>
```

**Status:** FIXED

---

## Issue #4: Missing Frontend Role Enums

**Symptom:** Frontend only recognized 5 of 7 backend roles. Users with `CommercialAnalyst`, `TechnicalPanelist`, or `Approver` roles would fall through to default handling.

**Root Cause:** The `UserRole` enum in `user.model.ts` only defined:
- `ADMIN`, `TENDER_MANAGER`, `BIDDER`, `VIEWER`, `AUDITOR`

Missing:
- `COMMERCIAL_ANALYST` (backend role 2)
- `TECHNICAL_PANELIST` (backend role 3)
- `APPROVER` (backend role 4)

Also had a phantom `VIEWER` role that doesn't exist in the backend.

**File:** `frontend/src/app/core/models/user.model.ts`

**Fix:** Added all missing roles to match the backend enum exactly.

**Status:** FIXED (as part of Issue #2)

---

## Issue #5: Build Failure - Incomplete Role Enum References in Admin UI

**Symptom:** Docker production build fails with 7 TypeScript errors:
- `TS2339: Property 'VIEWER' does not exist on type 'typeof UserRole'` (5 locations)
- `TS2739: Record<UserRole, string> missing properties: commercial_analyst, technical_panelist, approver` (2 locations)

**Root Cause:** After adding new roles to the `UserRole` enum, two admin components had:
1. `Record<UserRole, string>` type annotations that required ALL enum values but only had 5 entries
2. Role option dropdowns that only listed 4 roles

**Files:**
- `frontend/src/app/features/admin/users/user-list.component.ts`
- `frontend/src/app/features/admin/users/user-form-dialog.component.ts`

**Fix:** Added all 8 roles (including VIEWER for backward compatibility) to:
- Role filter dropdown options (`roleOptions` array)
- Role label mapping (`getRoleLabel` Record)
- Role severity/color mapping (`getRoleSeverity` Record)
- User creation form role dropdown

**Status:** FIXED

---

## Previous Session Fixes (for reference)

### Backend Fixes
- **2 DB migrations**: Schema was out of sync with EF entity configs (missing columns: `bidders.cr_number`, `clarifications.assigned_to_id`, 6 `tender_bidders` timestamps, `approval_levels.updated_at`, entire `evaluation_state` table)
- **2 Dapper query fixes**: EF stores enums as strings, Dapper queries used `(int)` casts -> changed to `.ToString()`
- **12 EF config fixes**: Missing `HasConversion`, wrong column names, nullable mismatches
- **2 null-safety fixes**: `GetApprovalStatusQueryHandler` and `GetComparableSheetQueryHandler` crashed on null navigation properties
- **1 CORS fix**: Added `localhost:4200` and `localhost:4201` to allowed origins

### Frontend Fixes
- **~30 components**: Added missing `imports: [...]` arrays in standalone component decorators
- **3 environment files**: Changed API URLs to match Docker setup
- **1 Dockerfile fix**: Corrected output path from `bayan-ui` to `bayan-tender`

### Docker/Config Fixes
- Added `ui-prod` service with nginx production build on port 4200
- Removed port conflict between base `ui` and `ui-prod` services
- Updated Playwright config BASE_URL from 4201 to 4200

### E2E Test Suite
- Created entire suite (~7,500 lines): 15 page objects, 15 spec files, helpers, fixtures, global setup
- Fixed 10 spec files with safe navigation helpers for production mode

---

## Issue #6: E2E Test Data Uses Wrong Bidder Email

**Symptom:** Login as `bidder@bayan.ae` returns "invalid email or password".

**Root Cause:** The E2E test fixtures (`e2e/fixtures/test-data.ts`) use `bidder@bayan.ae` but the backend seeds the bidder user as `bidder@vendor.ae` (external vendor domain).

**Correct credentials** (all use password `Bayan@2024`):
| Role | Email |
|------|-------|
| Admin | admin@bayan.ae |
| Tender Manager | tendermgr@bayan.ae |
| Commercial Analyst | analyst@bayan.ae |
| Technical Panelist | panelist1@bayan.ae |
| Approver | approver@bayan.ae |
| Auditor | auditor@bayan.ae |
| Bidder | bidder@vendor.ae |

**Status:** Documented (not a bug, just wrong test data)

---

## Issue #7: Portal Login Fails — Bidders Table Not Seeded

**Symptom:** Bidder can log in to the main app (`/login`) with `bidder@vendor.ae` / `Bayan@2024` successfully, but the portal login (`/portal/login`) returns "Invalid email or password."

**Root Cause:** The portal has a **completely separate authentication system**:
- Main app: `POST /api/auth/login` → queries the `users` table
- Portal: `POST /api/portal/auth/login` → queries the `bidders` table via `BidderLoginCommandHandler`

The seed data (`ApplicationDbContextSeed.SeedDemoUsersAsync()`) only populated the `users` table. No `SeedDemoBiddersAsync()` method existed, so the `bidders` table had no entries with login credentials. E2E test runs had created 10 bidder records, but none with the `bidder@vendor.ae` email and none with password hashes.

**Files:**
- `backend/Bayan.Infrastructure/Data/ApplicationDbContextSeed.cs`

**Fix:**
1. Added `SeedDemoBiddersAsync()` method that creates 2 demo bidders:
   - `bidder@vendor.ae` (ABC Construction LLC) — matches the User seed
   - `bidder2@vendor.ae` (Gulf MEP Services) — second vendor for testing
2. Both use the same BCrypt password hash as demo users (`Bayan@2024`)
3. Both set `PrequalificationStatus = Qualified` and `IsActive = true`
4. Seed check uses `AnyAsync(b => b.Email == "bidder@vendor.ae")` instead of `AnyAsync()` to be idempotent even when E2E test data exists
5. Called from `SeedAllAsync()` after `SeedDemoUsersAsync()`

**Status:** FIXED

---

## Issue #8: Missing `bidder_refresh_tokens` Table

**Symptom:** After fixing Issue #7, portal login authenticates the bidder successfully (password hash matches) but returns HTTP 500. Error: `relation "bidder_refresh_tokens" does not exist`.

**Root Cause:** The `BidderLoginCommandHandler` (line 91-102) creates a `BidderRefreshToken` entity and calls `SaveChangesAsync()`. The EF configuration (`BidderRefreshTokenConfiguration`) maps to table `bidder_refresh_tokens`, but no migration ever created this table in the database.

**Fix:** Created the table directly via SQL:
```sql
CREATE TABLE IF NOT EXISTS bidder_refresh_tokens (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bidder_id uuid NOT NULL REFERENCES bidders(id) ON DELETE CASCADE,
    token varchar(500) NOT NULL,
    expires_at timestamp NOT NULL,
    created_at timestamp NOT NULL DEFAULT NOW(),
    revoked_at timestamp,
    is_revoked boolean NOT NULL DEFAULT false,
    created_by_ip varchar(50),
    revoked_by_ip varchar(50),
    replaced_by_token varchar(500)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_bidder_refresh_tokens_token ON bidder_refresh_tokens(token);
```

**Note:** This should be added as a proper EF migration for production environments.

**Status:** FIXED

---

## Issue #9: Portal Login Succeeds at API But Doesn't Navigate — Response Shape Mismatch + Missing Image

**Symptom:** Bidder enters credentials at `/portal/login`, the API returns 200 success, but the UI stays on the login page. Also a broken image icon visible in the branding panel.

**Root Cause (two bugs):**

1. **Response shape mismatch:** The API returns the authenticated user as `data.bidder`, but the Angular `PortalAuthResponse` interface and `handleAuthSuccess()` expect `data.user`. Since `data.user` is `undefined`:
   - `localStorage.setItem(PORTAL_USER_KEY, JSON.stringify(undefined))` stores `"undefined"` string
   - `this._currentUser.set(undefined)` → `isAuthenticated()` returns `false`
   - Navigation to `/portal/tenders` hits a guard checking `isAuthenticated()` → redirects back to login

2. **Missing logo image:** `portal-login.component.ts` line 35 references `assets/images/logo-white.png` which doesn't exist (same as Issue #3 but different image).

**Files:**
- `frontend/src/app/core/models/portal.model.ts`
- `frontend/src/app/core/services/portal.service.ts`
- `frontend/src/app/features/portal/auth/portal-login.component.ts`

**Fix:**
1. Updated `PortalAuthResponse` interface to include `bidder?` field matching the actual API shape
2. Updated `handleAuthSuccess()` to map `data.bidder` → `PortalUser` when `data.user` is absent
3. Replaced `<img src="assets/images/logo-white.png">` with PrimeNG briefcase icon

**Status:** FIXED

---

## Issue #10: Portal Login Succeeds But Redirects Back to Login — Missing Route

**Symptom:** After fixing Issue #9, the portal login API succeeds, the auth state is set correctly (`isAuthenticated()` returns `true`), but the user is immediately redirected back to the login page.

**Root Cause:** After successful login, the component navigates to `/portal/tenders`. However, the portal routes only define `/portal/tenders/:tenderId` (with a required tenderId parameter). There is no route for `/portal/tenders` (without a parameter). The catch-all `**` route catches this and redirects to `/portal/login`.

**Files:**
- `frontend/src/app/features/portal/portal.routes.ts`
- `frontend/src/app/features/portal/tenders/portal-tenders.component.ts` (NEW)
- `frontend/src/app/core/services/portal.service.ts`

**Fix:**
1. Created `PortalTendersComponent` — a landing page that shows the bidder's assigned tenders or a "No Tenders Assigned" message
2. Added route `path: 'tenders'` (without `:tenderId`) in `portal.routes.ts` pointing to the new component, protected by `portalAuthGuard`
3. Updated `handleAuthSuccess` to persist `tenderAccess` array from the API response in localStorage so the landing page can display assigned tenders

**Status:** FIXED

---

## Verification Log

| Time | Test | Result |
|------|------|--------|
| 06:30 | Login as admin@bayan.ae -> Dashboard loads | PASS - KPIs, active tenders, deadlines all render |
| 06:35 | Sidebar shows Administration section (role mapping) | PASS |
| 06:35 | Tenders > All Tenders list page loads | PASS |
| 06:35 | New Tender button -> Wizard opens | PASS |
| 06:38 | Tender Wizard - fill fields, dropdowns, Next step | PASS |
| 06:38 | Tender Details page loads with all tabs | PASS |
| 06:38 | Tab switching (Overview, BOQ, Clarifications, Bids, Evaluation, Approval) | PASS |
| 06:38 | Admin > Users page loads | PASS |
| 06:38 | Admin > Clients page loads | PASS |
| 06:38 | Admin > Bidders page loads | PASS |
| 06:51 | Bidder login (main app) with bidder@vendor.ae | PASS |
| 06:51 | Portal login (bidder@vendor.ae) via /api/portal/auth/login | PASS - JWT token returned |
| 07:04 | Portal UI login + navigation to /portal/tenders landing page | PASS - "No Tenders Assigned" shown |
| 07:06 | Auditor login (auditor@bayan.ae) → Dashboard + 3 sidebar items, no Admin | PASS |
| 07:06 | Approver login (approver@bayan.ae) → Dashboard + 3 sidebar items, no Admin | PASS |
| 07:06 | Analyst login (analyst@bayan.ae) → Dashboard + 3 sidebar items, no Admin | PASS |
| 07:06 | Panelist login (panelist1@bayan.ae) → Dashboard + 3 sidebar items, no Admin | PASS |

---

## Issue #11: Tenders Use Mock In-Memory Data — Disappear on Refresh

**Symptom:** User creates a tender via the wizard, it appears briefly in the list. When the tender is opened, it shows data from a different (mock) tender. On page refresh, the created tender disappears completely.

**Root Cause:** The entire `TenderService` was implemented with mock data using `of(null).pipe(delay(), map(() => mockData))`. All CRUD operations operated on an in-memory `mockTenders[]` array that was reset on every page load. The backend has fully functional API endpoints (`GET /api/tenders`, `POST /api/tenders`, etc.) but the frontend never called them.

Additionally, `TenderDetailsComponent.loadTenderDetails()` (line 949) created its own hardcoded mock tender object instead of calling the service. And the `TenderWizardComponent` used `+params['id']` to convert route params to numbers, which would fail with the backend's GUID IDs (producing `NaN`).

**Files Modified:**
- `frontend/src/app/core/services/tender.service.ts` — Complete rewrite: all mock methods replaced with real API calls
- `frontend/src/app/features/tenders/tender-details/tender-details.component.ts` — Replaced mock tender with `tenderService.getTenderById()` call
- `frontend/src/app/features/tenders/tender-wizard/tender-wizard.component.ts` — Removed `+params['id']` numeric conversion (GUID strings)
- `frontend/src/app/features/tenders/tender-list/tender-list.component.ts` — Changed navigation methods to accept `string | number` IDs

**Key Mapping Challenges:**
| Backend Field | Frontend Field | Notes |
|---------------|----------------|-------|
| `id` (Guid) | `id` (number) | GUID string flows through as-is at runtime |
| `tenderType` (enum 0,1,2) | `type` ('open','selective','negotiated') | Mapped via `TENDER_TYPE_MAP` |
| `status` (enum 0-4) | `status` ('draft','active',...) | Mapped via `TENDER_STATUS_MAP` |
| `baseCurrency` | `currency` | Direct rename |
| `bidValidityDays` | `bidValidityPeriod` | Direct rename |
| `issueDate` (flat) | `dates.issueDate` (nested) | Restructured |
| `evaluationCriteria.weightPercentage` | `evaluationCriteria.weight` | Renamed |
| `PaginatedList` (flat) | `PaginatedResponse` (nested pagination) | `pageNumber→currentPage`, `totalCount→totalItems` |

**Status:** FIXED

---

## Issue #12: Date Picker Crash — `createEmbeddedViewImpl is not a function`

**Symptom:** Clicking any date field in the application throws:
- `Error: t.createEmbeddedViewImpl is not a function`
- `Cannot read properties of undefined (reading 'addEventListener')`

**Root Cause:** PrimeNG v18 deprecated `CalendarModule` / `p-calendar`. The old Calendar component has a known bug in Angular 18 production builds where its internal template rendering mechanism (`createEmbeddedViewImpl`) is broken. PrimeNG v18.0.2 ships the replacement: `DatePickerModule` / `p-datepicker`.

**Files Modified (8 components):**
1. `features/tenders/tender-wizard/steps/dates-step.component.ts` — 4 date picker instances
2. `features/tenders/tender-list/tender-list.component.ts` — 2 date picker instances
3. `features/admin/audit-logs/audit-logs.component.ts` — 1 date picker instance
4. `features/tenders/tender-details/approval/initiate-approval-dialog.component.ts` — 3 instances
5. `features/tenders/tender-details/clarifications/internal-rfi-dialog.component.ts` — 1 instance
6. `features/tenders/tender-details/clarifications/publish-bulletin-dialog.component.ts` — 1 instance
7. `features/portal/submit/vendor-pricing.component.ts` — 1 instance
8. `features/tenders/tender-details/evaluation/evaluation-setup.component.ts` — 1 instance

**Fix per file:**
```typescript
// BEFORE (broken)
import { CalendarModule } from 'primeng/calendar';
imports: [..., CalendarModule]
// template: <p-calendar ...>

// AFTER (fixed)
import { DatePickerModule } from 'primeng/datepicker';
imports: [..., DatePickerModule]
// template: <p-datepicker ...>
```

CSS selectors also updated: `.p-calendar` → `.p-datepicker`

**Status:** FIXED

---

## Issue #13: ALL Services Using Mock Data Instead of Real API (CRITICAL)

**Symptom:** Every feature beyond basic tender CRUD returns fake hardcoded data. Dashboard stats, BOQ items, bids, clarifications, evaluations, approvals — all fake. Data doesn't persist, doesn't reflect real state, and disappears on refresh.

**Root Cause:** The original builder created ALL frontend services with `of(null).pipe(delay(500), map(() => mockData))` patterns — returning hardcoded fake data instead of calling the backend API. This despite every backend controller and endpoint being fully implemented and functional.

**Scale:** 75 mock methods across 8 services, every one with a matching backend controller ready to go.

**Services Wired to Real API:**

| Service | Mock Methods Replaced | Backend Controller | Key Mappings |
|---------|----------------------|-------------------|--------------|
| `dashboard.service.ts` | 2 | DashboardController | Enum status mapping |
| `approval.service.ts` | 5 | ApprovalController | Status/decision enum mapping |
| `boq.service.ts` | 14 | BoqController | Section/item CRUD, import/export |
| `bid.service.ts` | 11 | BidsController | Bid submission, opening, evaluation |
| `clarification.service.ts` | 17 | ClarificationsController | RFI, bulletins, assignments |
| `evaluation.service.ts` | 18 | EvaluationController + TechnicalEvaluationController | Scoring, criteria, sensitivity |
| `bid-import.service.ts` | 5 | BidAnalysisController | File parsing, validation, preview |
| `comparable-sheet.service.ts` | 3 | BidAnalysisController | Sheet generation, export |

**Total: 75 mock methods → 75 real API calls**

**Previously wired (no changes needed):**
- `tender.service.ts` (fixed in Issue #11)
- `bidder.service.ts`, `client.service.ts`, `user.service.ts`, `settings.service.ts`
- `vendor-pricing.service.ts`, `audit-log.service.ts`, `notification.service.ts`

**Result:** BAYAN frontend is now **100% wired to the real backend API**. Zero mock data remaining in any service.

**Status:** FIXED

---

## Manual Testing Progress

### Testing Phases

| Phase | Scope | Status | Notes |
|-------|-------|--------|-------|
| **P1** | Authentication & Navigation | COMPLETE | All 7 roles verified (admin, tender mgr, analyst, panelist, approver, auditor, bidder) |
| **P2** | Portal & Bidder Login | COMPLETE | Portal login, JWT, navigation to /portal/tenders verified |
| **P3** | Tender CRUD (List, Create, Details) | NEEDS RE-TEST | Was tested on mock data; now wired to real API — needs verification |
| **P4** | BOQ Management | NOT STARTED | Create sections/items, import, export |
| **P5** | Clarifications & Bulletins | NOT STARTED | Create RFI, answer, approve, publish bulletin |
| **P6** | Bids & Evaluation | NOT STARTED | Open bids, import BOQ, technical scoring, comparable sheet |
| **P7** | Approval Workflow | NOT STARTED | Initiate, multi-level approval, award pack |

### Issues Fixed So Far: 13
| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 1 | UI freezes after login (infinite change detection) | CRITICAL | FIXED |
| 2 | Role type mismatch (numeric vs string enum) | HIGH | FIXED |
| 3 | Missing logo image (404) | LOW | FIXED |
| 4 | Missing frontend role enums | MEDIUM | FIXED |
| 5 | Build failure from incomplete role refs | HIGH | FIXED |
| 6 | E2E test data uses wrong bidder email | LOW | Documented |
| 7 | Portal login fails — bidders table not seeded | HIGH | FIXED |
| 8 | Missing bidder_refresh_tokens table | HIGH | FIXED |
| 9 | Portal login response shape mismatch | HIGH | FIXED |
| 10 | Portal missing /tenders route | MEDIUM | FIXED |
| 11 | Tender service uses mock data | CRITICAL | FIXED |
| 12 | Date picker crash (CalendarModule deprecated) | HIGH | FIXED |
| 13 | ALL services (75 methods) use mock data | CRITICAL | FIXED |

### Current State
- **Backend**: 67/70 API tests pass, 0 failures — fully functional
- **Frontend**: 100% wired to real API, zero mock data remaining, production build clean
- **Docker**: ui-prod (nginx:4200), api (5000), db (PostgreSQL), redis, minio all healthy
- **Next step**: Resume manual testing at P3 (tender CRUD with real API) and continue through P7

---

*This log is maintained as fixes are applied. Last updated: 2026-02-07*
