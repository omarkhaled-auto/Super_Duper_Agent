# PRD: BAYAN TENDER UI-Only Visual Transformation

## Overview

Transform the Bayan Tender Management System frontend from its current basic zinc/shadcn palette to a polished, enterprise-grade **Slate-Indigo** design system. This is a **pure visual transformation** — zero functionality changes.

The complete design system specification is in **UI_REQUIREMENTS.md** (same directory). Every color, spacing, typography, shadow, and component pattern token is defined there. Agents MUST read and follow UI_REQUIREMENTS.md for all styling decisions.

## Target State

- **Primary brand color**: Indigo-600 (`#4F46E5`) replacing zinc-900 (`#18181b`)
- **Neutral palette**: Slate scale replacing zinc scale
- **Sidebar**: Dark sidebar (`#0F172A` Slate-900) with white text and indigo active indicators
- **Header**: Clean white header with indigo brand accent
- **Cards**: Subtle shadows instead of flat borders
- **Focus rings**: Indigo brand color instead of gray
- **Status badges**: Refined pill badges with consistent theming
- **Tables**: Professional striped/hover patterns with indigo column headers
- **All 63 components**: Consistently themed with design tokens from UI_REQUIREMENTS.md

---

## CRITICAL CONSTRAINTS — ALL AGENTS MUST FOLLOW

### PROHIBITED CHANGES (HARD RULES)
1. **NO TypeScript class body changes** — Do NOT modify methods, signals, computed properties, services, subscriptions, event handlers, or any logic inside the `export class` block
2. **NO route/guard/navigation changes** — Do NOT modify app.routes.ts, *.routes.ts, auth.guard.ts, or any routing configuration
3. **NO model/interface/type changes** — Do NOT modify files in core/models/, core/services/, or any .model.ts/.service.ts file
4. **NO new dependencies** — Do NOT add new npm packages or libraries
5. **NO file creation or deletion** — Only modify existing files
6. **NO backend changes** — Do NOT touch any file outside `frontend/src/`

### ALLOWED CHANGES (WHITELIST)
1. **`template:` blocks** in component .ts files — HTML structure, CSS classes, inline styles, PrimeNG component attributes (styleClass, style bindings)
2. **`styles:` blocks** in component .ts files — All CSS/SCSS within component styles arrays
3. **`imports:` arrays** in @Component decorators — ONLY to add PrimeNG modules needed for template attributes (e.g., TooltipModule, RippleModule)
4. **`styles.scss`** — Global design tokens, PrimeNG overrides, utility classes
5. **`index.html`** — Meta theme-color, loading spinner colors

### VERIFICATION RULE
After every file edit, mentally verify: "Did I change anything inside `export class { ... }` method bodies?" If yes, REVERT that change immediately.

---

## Milestone 1: Design System Foundation + Layout Shell

**Components (5 files):**
- `frontend/src/styles.scss` — Global design tokens and PrimeNG overrides
- `frontend/src/index.html` — Meta theme-color, loading spinner
- `frontend/src/app/layout/layout.component.ts` — Main layout wrapper
- `frontend/src/app/layout/header/header.component.ts` — Top navigation bar
- `frontend/src/app/layout/sidebar/sidebar.component.ts` — Side navigation

**Requirements:**

### STYLES-001: Replace Zinc tokens with Slate-Indigo tokens
Replace ALL CSS custom properties in `:root` with the Slate-Indigo palette from UI_REQUIREMENTS.md Section 1. Key changes:
- `--bayan-primary`: `#18181b` → `#4F46E5` (Indigo-600)
- `--bayan-primary-foreground`: `#fafafa` → `#ffffff`
- All `--bayan-zinc-*` → `--bayan-slate-*` with Slate hex values
- `--bayan-sidebar-bg`: `#fafafa` → `#0F172A` (dark sidebar)
- `--bayan-sidebar-foreground`: `#09090b` → `#F8FAFC` (white text)
- `--bayan-ring`: `#a1a1aa` → `#4F46E5` (indigo focus)
- Add `--bayan-primary-hover: #4338CA` and `--bayan-primary-active: #3730A3`
- Status colors: green-600, amber-600, red-600, blue-600

### STYLES-002: Expand PrimeNG overrides
Add/update overrides for ALL PrimeNG components used across the app (see UI_REQUIREMENTS.md Section 8):
- Buttons: indigo primary, proper hover/active states
- Cards: subtle shadow elevation instead of flat border-only
- Tables (p-datatable): slate-50 header background, indigo sort indicators
- Dialogs: larger border-radius, backdrop blur
- Forms: indigo focus rings (box-shadow: 0 0 0 3px rgba(79,70,229,0.15))
- TabView: indigo active tab indicator
- Steps/Stepper: indigo active step number
- Toast: severity-colored left border
- Badge: pill shape with status colors
- Dropdown/MultiSelect panels: elevated shadow
- Tooltip: dark slate background
- ConfirmDialog: styled action buttons
- Menu/Popup: consistent shadow and radius

### STYLES-003: Dark mode update
Update `.dark-mode` block with Slate-Indigo dark palette from UI_REQUIREMENTS.md Section 9.

### LAYOUT-001: Header transformation
- White background with subtle bottom border
- Logo area: Add indigo brand accent (indigo icon color or left border)
- User avatar: indigo background instead of zinc-900
- Notification badge: keep danger severity
- Hover states: slate-100 backgrounds

### LAYOUT-002: Sidebar transformation (MOST DRAMATIC)
- Dark background: `--bayan-sidebar-bg` = `#0F172A` (Slate-900)
- White text on all menu items
- Active menu item: indigo-600 left border indicator + `rgba(79,70,229,0.1)` background
- Hover: `rgba(248,250,252,0.08)` background
- Panel menu header: white text, no background
- Submenu items: slightly indented, `slate-400` text, white on hover
- Footer version text: `slate-500` color
- Scrollbar: dark-themed

### INDEX-001: Update index.html
- `meta[name="theme-color"]`: `#18181b` → `#4F46E5`
- Loading spinner: `border-top-color`: `#18181b` → `#4F46E5`
- Loading background: `#f5f7fa` → `#F8FAFC` (slate-50)

---

## Milestone 2: Authentication Pages + Portal Auth

**Components (5 files):**
- `frontend/src/app/features/auth/login/login.component.ts`
- `frontend/src/app/features/auth/forgot-password/forgot-password.component.ts`
- `frontend/src/app/features/auth/unauthorized/unauthorized.component.ts`
- `frontend/src/app/features/portal/auth/portal-login.component.ts`
- `frontend/src/app/features/portal/activate/portal-activate.component.ts`

**Requirements:**

### AUTH-001: Login page
- Centered card layout on subtle gradient background (slate-50 to slate-100)
- Card: white, rounded-xl, shadow-lg, max-width 420px
- Logo section at top: "Bayan Tender" with indigo icon
- Form inputs: indigo focus rings
- Primary button: full-width, indigo-600, rounded-lg
- "Forgot password" link: indigo-600 text
- Error messages: red-600 with pi-exclamation-circle icon

### AUTH-002: Forgot password page
- Same centered card pattern as login
- Back link with pi-arrow-left icon
- Email input with indigo focus
- Submit button: indigo-600

### AUTH-003: Unauthorized page
- Centered layout with large pi-lock icon (slate-300)
- "Access Denied" heading in slate-900
- Descriptive text in slate-500
- "Go Back" button: outlined style with slate border

### AUTH-004: Portal login + activate
- Similar centered card pattern but with a distinct portal visual treatment
- Portal branding: "Bidder Portal" subtitle under logo
- Activation page: token input field, success/error states

---

## Milestone 3: Dashboards

**Components (4 files):**
- `frontend/src/app/features/dashboard/dashboard.component.ts`
- `frontend/src/app/features/dashboard/overview-dashboard.component.ts`
- `frontend/src/app/features/dashboard/approver-dashboard.component.ts`
- `frontend/src/app/features/home/home.component.ts`

**Requirements:**

### DASH-001: KPI cards
- White cards with subtle shadow-sm
- Left colored border (4px) indicating metric type (indigo for primary, green for success, amber for warning, red for danger)
- Metric value: large text (1.5rem), semibold, slate-900
- Metric label: small text (0.8rem), slate-500
- Icon: colored circle background matching the metric type

### DASH-002: Chart styling
- Chart.js containers: white card with proper padding
- Chart colors: use indigo-600, indigo-400, slate-400, emerald-500 palette
- Axis labels: slate-500, 0.75rem
- Grid lines: slate-200

### DASH-003: Activity timeline / recent items
- Vertical timeline with slate-200 connector line
- Each item: small colored dot, timestamp in slate-400, description in slate-700
- Hover: subtle slate-50 background

### DASH-004: Approver dashboard
- Pending items: amber left border cards
- Approved items: green left border
- Rejected items: red left border
- Action buttons: indigo primary, outlined secondary

### DASH-005: Home page
- Welcome section with user greeting
- Quick action cards: icon + label, hover shadow elevation
- Recent activity list

---

## Milestone 4: Tender List + Creation Wizard

**Components (6 files):**
- `frontend/src/app/features/tenders/tender-list/tender-list.component.ts`
- `frontend/src/app/features/tenders/tender-wizard/tender-wizard.component.ts`
- `frontend/src/app/features/tenders/tender-wizard/basic-info-step.component.ts`
- `frontend/src/app/features/tenders/tender-wizard/dates-step.component.ts`
- `frontend/src/app/features/tenders/tender-wizard/criteria-step.component.ts`
- `frontend/src/app/features/tenders/tender-wizard/review-step.component.ts`

**Requirements:**

### TENDER-001: Tender list page
- Page header: "Tenders" h1, slate-900, with action buttons on right
- Filter panel: collapsible card with slate-50 background, rounded-lg
- Status filter badges: pill-shaped with status colors
- Data table: per global PrimeNG overrides (indigo sort indicators, slate header)
- Status column: colored pill badges (Draft=slate, Published=blue, Closed=amber, Awarded=green, Cancelled=red)
- Hover row: slate-50 background
- Pagination: centered, indigo active page

### TENDER-002: Tender wizard
- Steps indicator: numbered circles, indigo for active/completed, slate-300 for upcoming
- Step connector line: indigo for completed, slate-200 for upcoming
- Current step: indigo filled circle with white number
- Step labels: slate-900 for active, slate-400 for inactive

### TENDER-003: Wizard step forms
- Each step in a white card with shadow-sm
- Form fields: consistent label (slate-700, semibold, 0.875rem), indigo focus rings
- Required field indicator: red-500 asterisk
- Section headers within form: slate-900, font-weight 600, border-bottom slate-200
- Date picker: indigo selected date
- Action bar at bottom: "Previous" outlined, "Next/Submit" indigo primary

---

## Milestone 5: Tender Details — BOQ, Documents, Clarifications

**Components (10 files):**
- `frontend/src/app/features/tenders/tender-details/tender-details.component.ts`
- `frontend/src/app/features/tenders/tender-details/boq/boq-tab.component.ts`
- `frontend/src/app/features/tenders/tender-details/boq/boq-item-dialog.component.ts`
- `frontend/src/app/features/tenders/tender-details/boq/boq-section-dialog.component.ts`
- `frontend/src/app/features/tenders/tender-details/boq/boq-export-dialog.component.ts`
- `frontend/src/app/features/tenders/tender-details/boq/boq-import-dialog.component.ts`
- `frontend/src/app/features/tenders/tender-details/documents/documents-tab.component.ts`
- `frontend/src/app/features/tenders/tender-details/clarifications/clarifications-tab.component.ts`
- `frontend/src/app/features/tenders/tender-details/clarifications/publish-bulletin-dialog.component.ts`
- `frontend/src/app/features/tenders/tender-details/clarifications/internal-rfi-dialog.component.ts`

**Requirements:**

### DETAILS-001: Tender details shell
- Page header: tender title (h2, slate-900), status badge, action buttons
- Tab system: indigo active indicator per global PrimeNG override
- Tab content area: white background, proper padding

### BOQ-001: BOQ tab
- Hierarchical table: indented sections with collapsible rows
- Section headers: slate-100 background, bold text
- Item rows: normal weight, alternating subtle backgrounds
- Totals row: slate-800 background, white text, bold
- Action buttons (add/edit/delete): small, icon-only with tooltips
- Currency formatting: right-aligned, monospace feel

### BOQ-002: BOQ dialogs (item, section, export, import)
- Dialog header: slate-900 text, bottom border
- Form fields: standard form field pattern (indigo focus)
- Footer: right-aligned actions — "Cancel" text button, "Save/Export/Import" indigo primary
- Import dialog: file upload zone with dashed border, slate-300, indigo on hover

### DOCS-001: Documents tab
- File list: card-based or table layout
- File type icons: colored by type (PDF=red, Excel=green, Word=blue, Image=amber)
- Upload area: dashed border, centered icon + text, indigo on hover/drag
- File size: slate-400 text, small
- Download/delete actions: icon buttons with hover

### CLARIF-001: Clarifications tab
- Thread-based layout: question → answer pairs
- Question card: white, left border amber
- Answer card: white, left border green
- Status badges: "Pending" amber, "Answered" green, "Published" blue
- Timestamp: slate-400, small text

### CLARIF-002: Dialogs (publish bulletin, internal RFI)
- Standard dialog pattern from UI_REQUIREMENTS.md
- Rich text areas with proper spacing
- Recipient selectors: checkbox or multi-select with indigo

---

## Milestone 6: Tender Details — Bids + Evaluation

**Components (12 files):**
- `frontend/src/app/features/tenders/tender-details/bids/bids-tab.component.ts`
- `frontend/src/app/features/tenders/tender-details/bids/bid-details-dialog.component.ts`
- `frontend/src/app/features/tenders/tender-details/bids/bid-import-dialog.component.ts`
- `frontend/src/app/features/tenders/tender-details/bids/open-bids-dialog.component.ts`
- `frontend/src/app/features/tenders/tender-details/bids/late-bid-rejection-dialog.component.ts`
- `frontend/src/app/features/tenders/tender-details/evaluation/evaluation-setup.component.ts`
- `frontend/src/app/features/tenders/tender-details/evaluation/technical-scoring.component.ts`
- `frontend/src/app/features/tenders/tender-details/evaluation/combined-scorecard.component.ts`
- `frontend/src/app/features/tenders/tender-details/evaluation/comparable-sheet.component.ts`
- `frontend/src/app/features/tenders/tender-details/evaluation/technical-summary.component.ts`
- `frontend/src/app/features/tenders/tender-details/evaluation/exceptions-panel.component.ts`
- `frontend/src/app/features/tenders/tender-details/evaluation/sensitivity-analysis-dialog.component.ts`

**Requirements:**

### BIDS-001: Bids tab
- Bid cards or table with bidder name, amount, status, submission time
- Bid status: colored badges (Submitted=blue, Under Review=amber, Accepted=green, Rejected=red, Late=slate)
- Bid amount: large, semibold, right-aligned
- "Open Bids" action: prominent indigo button with pi-lock-open icon

### BIDS-002: Bid dialogs
- Bid details: comprehensive info layout with labeled sections
- Import dialog: file upload pattern (same as BOQ import)
- Open bids dialog: confirmation-style with warning icon
- Late bid rejection: warning/danger themed dialog with red-600 emphasis

### EVAL-001: Evaluation setup
- Criteria list: editable cards with weight percentages
- Total weight indicator: progress-bar style, green when 100%, red when over/under
- Sub-criteria: nested under main criteria with indent

### EVAL-002: Technical scoring
- Scoring matrix: table with bidders as columns, criteria as rows
- Score cells: editable inputs, colored by score range (red <40%, amber 40-69%, green 70%+)
- Total row: bold, larger text
- Header row: bidder names with avatars/initials

### EVAL-003: Combined scorecard + comparable sheet
- AG Grid styling: consistent with PrimeNG table theme (use AG Grid theme overrides)
- Rank column: medal icons or numbered badges (gold/silver/bronze for top 3)
- Score columns: right-aligned, monospace
- Comparable sheet: side-by-side comparison layout with alternating row backgrounds

### EVAL-004: Technical summary + exceptions panel
- Summary: metric cards at top, detailed breakdown below
- Exceptions panel: warning-themed cards with amber left border
- Exception items: title, description, severity badge, affected bidder

### EVAL-005: Sensitivity analysis dialog
- Chart container with proper card wrapping
- Parameter sliders: indigo track and thumb
- Results table: dynamic coloring based on rank changes

---

## Milestone 7: Approval + Admin Pages

**Components (12 files):**
- `frontend/src/app/features/tenders/tender-details/approval/approval-tab.component.ts`
- `frontend/src/app/features/tenders/tender-details/approval/initiate-approval-dialog.component.ts`
- `frontend/src/app/features/tenders/tender-details/approval/pending-approvals-widget.component.ts`
- `frontend/src/app/features/tenders/tender-details/invite-bidders/invite-bidders.component.ts`
- `frontend/src/app/features/admin/users/user-list.component.ts`
- `frontend/src/app/features/admin/users/user-form-dialog.component.ts`
- `frontend/src/app/features/admin/clients/client-list.component.ts`
- `frontend/src/app/features/admin/clients/client-form-dialog.component.ts`
- `frontend/src/app/features/admin/bidders/bidder-list.component.ts`
- `frontend/src/app/features/admin/bidders/bidder-form-dialog.component.ts`
- `frontend/src/app/features/admin/settings/settings.component.ts`
- `frontend/src/app/features/admin/audit-logs/audit-logs.component.ts`

**Requirements:**

### APPROVAL-001: Approval workflow
- Workflow stages: vertical or horizontal stepper with status colors
- Pending stage: amber indicator
- Approved stage: green indicator with checkmark
- Rejected stage: red indicator with X
- Current approver: highlighted with indigo border
- Timeline: connected dots with status colors

### APPROVAL-002: Initiate approval dialog
- Stage configuration form
- Approver selection: multi-select with avatars
- Notes textarea: standard form field pattern

### APPROVAL-003: Pending approvals widget
- Compact card list with tender title, requested date, requester
- "Review" button: indigo outlined
- Count badge: indigo circle with number

### ADMIN-001: CRUD list pattern (users, clients, bidders)
- Consistent page structure: page header + filter bar + data table + pagination
- "Add New" button: indigo primary, top-right
- Search input: with pi-search icon prefix, indigo focus
- Table: standard PrimeNG override styling
- Action column: icon buttons (edit=indigo, delete=red, view=slate)
- Role/status columns: pill badges with appropriate colors

### ADMIN-002: CRUD form dialogs (users, clients, bidders)
- Consistent dialog pattern from UI_REQUIREMENTS.md
- Form layout: two-column grid for wider dialogs
- Validation errors: red-500 text with pi-exclamation-circle icon
- Required indicator: red asterisk after label

### ADMIN-003: Settings page
- Section cards with headers and descriptions
- Toggle switches: indigo when active
- Input groups: label + input + hint text
- Save buttons: indigo primary

### ADMIN-004: Audit logs
- Filterable table with date range, user, action type
- Log entries: timestamp, user avatar/name, action description, affected entity
- Expandable row details
- Date column: slate-500, monospace-style

### ADMIN-005: Invite bidders
- Bidder selection: searchable list or table with checkboxes
- Selected bidders: tag/chip display with remove button
- Email preview: card with email template content
- Send button: indigo primary with pi-send icon

---

## Milestone 8: Portal + Vendor + Settings + Shared

**Components (11 files):**
- `frontend/src/app/features/portal/layout/portal-layout.component.ts`
- `frontend/src/app/features/portal/tenders/portal-tenders.component.ts`
- `frontend/src/app/features/portal/documents/portal-documents.component.ts`
- `frontend/src/app/features/portal/clarifications/portal-clarifications.component.ts`
- `frontend/src/app/features/portal/clarifications/submit-question-dialog.component.ts`
- `frontend/src/app/features/portal/submit/portal-submit.component.ts`
- `frontend/src/app/features/portal/receipt/portal-receipt.component.ts`
- `frontend/src/app/features/vendor-pricing/vendor-pricing.component.ts`
- `frontend/src/app/features/settings/notification-settings.component.ts`
- `frontend/src/app/shared/components/loading-spinner/loading-spinner.component.ts`
- `frontend/src/app/app.component.ts`

**Requirements:**

### PORTAL-001: Portal layout
- Distinct from main layout: dark header bar (`#1E293B` Slate-800)
- "Bidder Portal" branding in header with lighter weight
- Simplified navigation: horizontal menu or minimal sidebar
- Footer: optional, slate-700 background

### PORTAL-002: Portal pages (tenders, documents, clarifications, submit, receipt)
- Consistent card-based layout
- Tender list: simplified card grid or list with key info
- Document list: file cards with download buttons
- Clarification thread: same pattern as internal but read-only question
- Submit page: multi-step or single-page form
- Receipt page: printable receipt card with tender details and confirmation number

### PORTAL-003: Submit question dialog
- Standard dialog pattern
- Textarea for question body
- Reference selector: dropdown for related documents/sections

### VENDOR-001: Vendor pricing
- Data table with pricing columns
- Compare/analyze actions: indigo buttons
- Price cells: right-aligned, formatted currency
- Variance indicators: green for below budget, red for over, amber for near

### SETTINGS-001: Notification settings
- Card with toggle switches for each notification type
- Group headers for notification categories
- Toggle: indigo when active
- Description text: slate-500

### SHARED-001: Loading spinner
- Indigo spinner color (replacing zinc/dark)
- Clean centered layout
- Optional "Loading..." text in slate-500

### APP-001: App component
- Verify global styles application
- Check layout wrapper consistency
- Final smoke test: ensure all milestone styles work together

### REGRESSION-001: Final visual regression sweep
- Check ALL 62+ components render with new tokens
- Verify no hardcoded zinc/gray colors remain in component styles
- Confirm dark mode works with new Slate-Indigo palette
- Ensure `ng build` passes cleanly
