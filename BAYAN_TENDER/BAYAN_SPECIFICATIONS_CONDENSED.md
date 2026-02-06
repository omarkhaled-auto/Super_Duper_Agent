# BAYAN TENDER MANAGEMENT SYSTEM
## Complete Product Requirements Document (PRD) for Claude Code

**Version:** 2.0
**Date:** February 2026
**Target Builder:** Claude Code (Autonomous AI Builder)
**Stack:** .NET 8 Backend, Angular 18 Frontend, PostgreSQL Database
**Build Type:** Complete MVP from Scratch

---

# TABLE OF CONTENTS

1. Executive Summary
2. Technology Stack & Architecture
3. Database Schema
4. User Roles & Permissions
5. Module 1: Authentication
6. Module 2: Tender Management
7. Module 3: BOQ Management
8. Module 4: Document Control & RFIs
9. Module 5: Bid Collection & Submission Portal
10. Module 6: BOQ Analysis & Comparable Sheet
11. Module 7: Vendor Pricing Tracking
12. Module 8: Dashboard & Reporting
13. Module 9: Admin & Settings
14. Cross-Cutting Concerns
15. Feature Integration Map
16. Comprehensive Testing Plan

---

# 1. EXECUTIVE SUMMARY

## 1.1 What is Bayan?

Bayan is an enterprise-grade SaaS tender management platform for the UAE/GCC construction industry. It digitizes the complete tender lifecycle from creation through evaluation and award. The MVP focuses on these core workflows:

1. **Tender Creation** - Multi-step wizard to create and manage tenders with dates, criteria, and bidder invitations
2. **BOQ Management** - Hierarchical Bill of Quantities with Excel import/export, section/item management
3. **RFIs & Clarifications** - Q&A system between tender managers, bidders, and clients
4. **Tender Submission Portal** - Secure bidder-facing portal for uploading priced BOQs and supporting documents
5. **BOQ Analysis & Comparable Sheet** - Side-by-side bid comparison with normalization (currency, UOM), outlier detection, and color-coded analysis
6. **Vendor Pricing Tracking** - Historical tracking of bidder rates across tenders over time for trend analysis
7. **Tender Analysis** - Evaluation scoring (technical + commercial), combined scorecards, and approval workflows

## 1.2 Key Business Rules

- Submission deadline must be > clarification deadline + 3 days
- Minimum 3 bidders required per tender to proceed to evaluation
- Technical evaluation runs in blind mode (commercial data hidden until technical scores are locked)
- Commercial scoring formula: `Score = (Lowest Price / Bidder Price) × 100`
- Combined score: `(Tech Weight × Tech Score) + (Commercial Weight × Commercial Score)`
- All prices normalized to tender base currency and standard UOMs before comparison
- Outlier thresholds: >20% above average = Red, 10-20% = Yellow, <10% = Green
- Late bid submissions are flagged but can be accepted/rejected by tender manager
- Approval workflow is sequential (Level 1 → Level 2 → Level 3)
- All actions are audit-logged with user, timestamp, and IP address

## 1.3 Users

| Role | Description |
|------|-------------|
| Admin | System administrator, manages users, settings, master data |
| TenderManager | Creates/manages tenders, invites bidders, reviews bids, initiates approvals |
| CommercialAnalyst | Imports bids, normalizes data, manages comparable sheet |
| TechnicalPanelist | Scores bidder technical submissions (blind to commercial data) |
| Approver | Reviews and approves/rejects award recommendations |
| Auditor | Read-only access to all data and audit logs |
| Bidder | External user who registers, downloads documents, submits bids, asks questions |

---

# 2. TECHNOLOGY STACK & ARCHITECTURE

## 2.1 Stack

| Layer | Technology | Version | License |
|-------|-----------|---------|---------|
| Frontend | Angular | 18 | MIT |
| UI Components | PrimeNG | 18 | MIT |
| Frontend Grid | AG Grid Community | 31+ | MIT |
| State Management | NgRx (Signals) | 18 | MIT |
| i18n | @ngx-translate/core | 15 | MIT |
| Backend | .NET | 8 | MIT |
| CQRS | MediatR | 12 | Apache 2.0 |
| Validation | FluentValidation | 11 | Apache 2.0 |
| ORM | Entity Framework Core | 8 | MIT |
| Micro ORM | Dapper | 2 | Apache 2.0 |
| Object Mapping | AutoMapper | 12 | MIT |
| Database | PostgreSQL | 16 | PostgreSQL License |
| Cache | Redis | 7 | BSD |
| Object Storage | MinIO | Latest | AGPL v3 |
| Authentication | Custom JWT | - | - |
| Email | MailKit + Resend | - | MIT |
| Excel Processing | ClosedXML | 0.102 | MIT |
| Excel Reading | ExcelDataReader | 3.6 | MIT |
| PDF Generation | QuestPDF | 2024 | Community Free |
| Background Jobs | Hangfire | 1.8 | LGPL v3 |
| Logging | Serilog | 8 | Apache 2.0 |
| Fuzzy Matching | FuzzySharp | - | MIT |
| Containerization | Docker | - | Apache 2.0 |

## 2.2 Architecture Pattern

```
Clean Architecture with CQRS

├── Bayan.Domain/                    # Entities, Value Objects, Enums, Domain Events
│   ├── Entities/
│   ├── Enums/
│   ├── ValueObjects/
│   ├── Events/
│   └── Common/                      # BaseEntity, IAuditableEntity
│
├── Bayan.Application/               # Use Cases, DTOs, Interfaces
│   ├── Common/
│   │   ├── Behaviors/               # ValidationBehavior, LoggingBehavior
│   │   ├── Interfaces/              # IApplicationDbContext, ICurrentUserService
│   │   ├── Models/                  # Result<T>, PaginatedList<T>
│   │   └── Mappings/                # AutoMapper profiles
│   ├── Features/
│   │   ├── Auth/
│   │   │   ├── Commands/            # Login, Register, ResetPassword
│   │   │   └── Queries/             # GetCurrentUser
│   │   ├── Tenders/
│   │   │   ├── Commands/            # CreateTender, UpdateTender, PublishTender
│   │   │   ├── Queries/             # GetTenders, GetTenderById
│   │   │   └── DTOs/
│   │   ├── Boq/
│   │   │   ├── Commands/            # ImportBoq, AddBoqItem, UpdateBoqItem
│   │   │   ├── Queries/             # GetBoqStructure, ExportBoqTemplate
│   │   │   └── DTOs/
│   │   ├── Clarifications/
│   │   │   ├── Commands/            # SubmitQuestion, DraftAnswer, PublishBulletin
│   │   │   └── Queries/             # GetClarifications
│   │   ├── Bids/
│   │   │   ├── Commands/            # SubmitBid, ImportBidBoq, NormalizeBid
│   │   │   ├── Queries/             # GetBids, GetBidDetails
│   │   │   └── DTOs/
│   │   ├── Evaluation/
│   │   │   ├── Commands/            # ScoreBidder, LockScores, CalculateCombined
│   │   │   ├── Queries/             # GetComparableSheet, GetScorecard
│   │   │   └── DTOs/
│   │   ├── Approval/
│   │   │   ├── Commands/            # InitiateApproval, SubmitDecision
│   │   │   └── Queries/             # GetApprovalStatus
│   │   ├── VendorPricing/
│   │   │   ├── Commands/            # TrackPricing, SnapshotRates
│   │   │   └── Queries/             # GetPricingHistory, GetPriceTrends
│   │   └── Admin/
│   │       ├── Commands/            # CreateUser, UpdateSettings
│   │       └── Queries/             # GetUsers, GetAuditLogs
│   └── DependencyInjection.cs
│
├── Bayan.Infrastructure/            # Data Access, External Services
│   ├── Data/
│   │   ├── ApplicationDbContext.cs
│   │   ├── Configurations/          # EF Core Fluent API configs per entity
│   │   └── Migrations/
│   ├── Services/
│   │   ├── CurrentUserService.cs
│   │   ├── DateTimeService.cs
│   │   ├── EmailService.cs
│   │   ├── FileStorageService.cs    # MinIO integration
│   │   ├── ExcelService.cs          # ClosedXML + ExcelDataReader
│   │   ├── PdfService.cs            # QuestPDF
│   │   ├── FuzzyMatchingService.cs  # FuzzySharp
│   │   └── CacheService.cs          # Redis
│   ├── Identity/
│   │   ├── JwtTokenService.cs
│   │   └── PasswordHasher.cs
│   └── DependencyInjection.cs
│
├── Bayan.API/                       # Controllers, Middleware, Filters
│   ├── Controllers/
│   │   ├── AuthController.cs
│   │   ├── TendersController.cs
│   │   ├── BoqController.cs
│   │   ├── ClarificationsController.cs
│   │   ├── BidsController.cs
│   │   ├── EvaluationController.cs
│   │   ├── ApprovalController.cs
│   │   ├── VendorPricingController.cs
│   │   ├── DashboardController.cs
│   │   └── AdminController.cs
│   ├── Middleware/
│   │   ├── ExceptionHandlingMiddleware.cs
│   │   ├── RequestLoggingMiddleware.cs
│   │   └── AuditLogMiddleware.cs
│   ├── Filters/
│   │   └── ValidationFilter.cs
│   └── Program.cs
│
├── Bayan.Tests/
│   ├── Unit/
│   ├── Integration/
│   └── Common/
│
└── Frontend (Angular 18)/
    └── src/app/
        ├── core/                    # Guards, interceptors, services, models
        │   ├── auth/
        │   ├── interceptors/
        │   ├── guards/
        │   ├── services/
        │   └── models/
        ├── shared/                  # Shared components, pipes, directives
        │   ├── components/
        │   ├── pipes/
        │   └── directives/
        ├── features/                # Feature modules (lazy loaded)
        │   ├── auth/
        │   ├── dashboard/
        │   ├── tenders/
        │   ├── boq/
        │   ├── clarifications/
        │   ├── bids/
        │   ├── evaluation/
        │   ├── approval/
        │   ├── vendor-pricing/
        │   ├── bidder-portal/
        │   └── admin/
        └── layout/                  # Shell, sidebar, header
```

## 2.3 API Response Standard

Every API response follows this structure:

```csharp
public class ApiResponse<T>
{
    public bool Success { get; set; }
    public T? Data { get; set; }
    public string? Message { get; set; }
    public List<string> Errors { get; set; } = new();
    public Dictionary<string, string[]>? ValidationErrors { get; set; }
}

public class PaginatedList<T>
{
    public List<T> Items { get; set; } = new();
    public int TotalCount { get; set; }
    public int Page { get; set; }
    public int PageSize { get; set; }
    public int TotalPages => (int)Math.Ceiling(TotalCount / (double)PageSize);
    public bool HasPreviousPage => Page > 1;
    public bool HasNextPage => Page < TotalPages;
}
```

## 2.4 CQRS Pattern

Every feature follows this pattern:

```csharp
// Command
public record CreateTenderCommand(string Title, Guid ClientId, ...) : IRequest<Result<Guid>>;

// Validator
public class CreateTenderCommandValidator : AbstractValidator<CreateTenderCommand>
{
    public CreateTenderCommandValidator(IApplicationDbContext context)
    {
        RuleFor(x => x.Title).NotEmpty().MaximumLength(500);
        // ... more rules
    }
}

// Handler
public class CreateTenderCommandHandler : IRequestHandler<CreateTenderCommand, Result<Guid>>
{
    private readonly IApplicationDbContext _context;
    public async Task<Result<Guid>> Handle(CreateTenderCommand request, CancellationToken ct)
    {
        var entity = Tender.Create(request.Title, ...);
        _context.Tenders.Add(entity);
        await _context.SaveChangesAsync(ct);
        return Result<Guid>.Success(entity.Id);
    }
}
```

## 2.5 Frontend Pattern

Every feature follows this structure:

```typescript
// Standalone component with PrimeNG
@Component({
  selector: 'app-tender-list',
  standalone: true,
  imports: [CommonModule, TableModule, ButtonModule, ...],
  templateUrl: './tender-list.component.html',
  styleUrls: ['./tender-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TenderListComponent implements OnInit {
  private tenderService = inject(TenderService);
  tenders = signal<TenderDto[]>([]);
  loading = signal(false);
  // ...
}
```

---

# 3. DATABASE SCHEMA

## 3.1 Core Tables

```sql
-- =============================================
-- USERS & AUTHENTICATION
-- =============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(500) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(50),
    role VARCHAR(50) NOT NULL, -- Admin, TenderManager, CommercialAnalyst, TechnicalPanelist, Approver, Auditor
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
-- ... (677 lines truncated for brevity) ...
-- (clarification_buffer_days, 3, Integer, Minimum days between clarification and submission deadlines)
-- (session_timeout_minutes, 60, Integer, Session timeout)
-- (password_min_length, 8, Integer, Minimum password length)
-- (default_language, en, String, Default system language)
-- (date_format, dd-MMM-yyyy, String, Date display format)
```

---

# 4. USER ROLES & PERMISSIONS

## 4.1 Permission Matrix

| Permission | Admin | TenderManager | CommercialAnalyst | TechnicalPanelist | Approver | Auditor | Bidder |
|---|---|---|---|---|---|---|---|
| Manage Users | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Manage System Settings | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Create Tender | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Edit Tender | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| View All Tenders | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Invite Bidders | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Upload Documents | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Issue Addendum | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Manage Clarifications | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Manage BOQ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Import Bids | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| View Comparable Sheet | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ |
| Score Technical | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| View Technical Scores | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ |
| Lock Scores | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| View Combined Scorecard | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ |
| Initiate Approval | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Approve/Reject | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| View Audit Logs | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| View Vendor Pricing | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Submit Bid | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Submit Question | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| View Tender Documents | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (if qualified) |

---

# 5. MODULE 1: AUTHENTICATION

## 5.1 Screens

### AUTH-01: Login Screen
**Route:** `/auth/login`

**Components:**
- App logo and branding
- Language toggle (EN/AR) top-right
- Email input with validation
- Password input with show/hide toggle
- "Remember me" checkbox
- "Login" primary button
- "Forgot password?" link

**API:**
```
POST /api/auth/login
Body: { email: string, password: string, rememberMe: boolean }
Response: { accessToken: string, refreshToken: string, user: UserDto }
```

**Validation:** email required + format, password required (min 8 chars)
**On success:** Store tokens in localStorage, redirect to dashboard based on role
**On error:** Display "Invalid credentials" or "Account locked" message

### AUTH-02: Forgot Password
**Route:** `/auth/forgot-password`

**API:**
```
POST /api/auth/forgot-password
Body: { email: string }
Response: { message: string }
```

### AUTH-03: Reset Password
**Route:** `/auth/reset-password?token=xxx`

**API:**
```
POST /api/auth/reset-password
Body: { token: string, newPassword: string, confirmPassword: string }
Response: { message: string }
```

**Validation:** Password strength (8+ chars, uppercase, number, symbol), match check

---

# 6. MODULE 2: TENDER MANAGEMENT

## 6.1 TEND-01: Tender List
**Route:** `/tenders`
**Roles:** Admin, TenderManager, CommercialAnalyst, TechnicalPanelist, Approver, Auditor

**Components:**
- PrimeNG Table (p-table) with lazy loading
- Columns: Tender Name, Client, Reference, Submission Deadline, Status (badge), Actions
- Status badges: Draft (gray), Active (blue), Evaluation (orange), Awarded (green), Cancelled (red)
- Advanced filters panel (collapsible): Status checkboxes, date range picker, client dropdown, currency dropdown
- Search bar for tender name/client
- Bulk actions: Export to Excel
- Row click navigates to TEND-03

**API:**
```
GET /api/tenders?page=1&pageSize=20&status=Active&search=villa&sortBy=submissionDeadline&sortDir=desc
Response: PaginatedList<TenderListDto>

TenderListDto: { id, title, reference, clientName, submissionDeadline, status, bidderCount, createdAt }
```

## 6.2 TEND-02: Create Tender (Multi-Step Wizard)
**Route:** `/tenders/create`
**Roles:** Admin, TenderManager

**Layout:** PrimeNG Stepper (p-steps) with 4 steps

### Step 1: Basic Information
**Form Fields:**
| Field | Type | Validation | Notes |
|-------|------|------------|-------|
| Tender Title* | text input | Required, max 500 chars | Character counter |
| Client Name* | autocomplete dropdown | Required | Search existing or [+ Add New Client] inline modal |
| Tender Reference* | text input | Required, unique | Auto-generate button: "TNR-{YEAR}-{SEQ}" |
| Description | rich text editor (PrimeNG Editor) | Max 2000 chars | |
| Tender Type* | radio group | Required | Open / Selective / Negotiated |
| Base Currency* | dropdown | Required | AED, USD, EUR, GBP, SAR |
| Bid Validity Period | number input | Min 30, Max 365, Default 90 | Label: "days" |

**Client Inline Creation Modal:**
When user clicks [+ Add New Client], show PrimeNG Dialog with fields: Name*, Contact Person, Email, Phone. On save, create client via `POST /api/clients`, return new client to autocomplete, and auto-select it.

### Step 2: Key Dates
**Form Fields:**
| Field | Type | Validation |
|-------|------|------------|
| Issue Date* | PrimeNG Calendar | Required, default today |
| Clarification Deadline* | PrimeNG Calendar | Required, must be > issue date |
| Submission Deadline* | PrimeNG Calendar | Required, must be > clarification deadline + 3 days |
| Opening Date* | PrimeNG Calendar | Required, default = submission deadline |

**Visual Element:** Timeline showing all 4 dates with relative positions. Dates with validation errors highlighted in red.

### Step 3: Evaluation Criteria
**Form Fields:**
- Technical/Commercial Weight Split: Two number inputs that must sum to 100. E.g., Technical [40] Commercial [60]
- Criteria Table (PrimeNG Table, editable):
  - Columns: Criterion Name, Weight %, Guidance Notes
  - Default rows pre-populated: Compliance (10%), Methodology (25%), Team CVs (20%), Program (20%), QA/QC (15%), HSE (10%)
  - [+ Add Criterion] button adds new editable row
  - Delete button per row (confirm before delete)
  - Footer row: Total Weight (must = 100%, show validation error if not)

### Step 4: Review & Create
- Summary cards showing all entered data organized by step
- [Edit] links per section jump back to that step
- Confirmation checkbox: "I confirm all information is correct"
- Buttons: [← Back] [Save as Draft] [Create Tender]

**API Endpoints:**
```
POST /api/tenders                    # Create new tender (status = Draft or Active)
PUT  /api/tenders/{id}               # Update existing tender
POST /api/tenders/{id}/publish       # Change status Draft → Active
GET  /api/tenders/{id}               # Get full tender details
POST /api/clients                    # Create client (inline)
GET  /api/clients?search=abc         # Search clients for autocomplete
GET  /api/tenders/next-reference     # Get next available reference number
```

**Critical Implementation Notes:**
1. When "Save as Draft" is clicked, POST to create tender with status "Draft", store returned tender ID, and navigate to TEND-03.
2. When "Create Tender" is clicked, POST with status "Active" and navigate to TEND-03.
3. If editing an existing draft, use PUT instead of POST. Track tender ID in component state.
4. Currency field must persist correctly - the enum value must match between frontend dropdown and backend entity. Use string ISO codes (AED, USD, etc.), not numeric enums.
5. Evaluation criteria are saved as nested objects within the tender creation payload.

## 6.3 TEND-03: Tender Details (Tabbed Hub)
**Route:** `/tenders/:id`
**Roles:** All (with permission-based content)

**Layout:**
- Breadcrumb: Dashboard > Tenders > {Tender Title}
- Header: Tender title, status badge, client name, reference, [Edit] [Archive] [More ⋮] buttons
- Tab Navigation: Overview | Documents | Clarifications | BOQ | Bids | Evaluation | Approval

**Overview Tab Content:**
- Key Dates card (list with countdown timers)
- Bidder Status card (Invited: X, Registered: Y, Submitted: Z)
- Visual Timeline (horizontal markers: Issue → Clarification → Submission → Opening)
- Invited Bidders Table (Company, Contact, Email, NDA Status, Bid Status, Actions)
- Activity Feed (sidebar, recent actions)

**API:**
```
GET /api/tenders/{id}                         # Full tender details
GET /api/tenders/{id}/bidders                 # Invited bidders list
GET /api/tenders/{id}/activity                # Activity feed
```

## 6.4 TEND-04: Edit Tender
**Route:** `/tenders/:id/edit`
Same form as TEND-02 but pre-filled. PUT instead of POST. Warning banner if tender is Active. Lock currency field if any bids received.

## 6.5 TEND-05: Invite Bidders
**Route:** `/tenders/:id/invite-bidders`

**Components:**
- Search bar to find bidders from master registry
- Master bidder list with checkboxes (Company, Trade, License #, Last Invited, Prequalification)
- Filter by trade dropdown
- Selected bidders counter
- [+ Add New Bidder] button → modal (Company Name*, Contact Person*, Email*, Phone, Trade)
- Invitation message template editor with merge fields: {{tender_title}}, {{deadline}}, {{portal_link}}
- [Send Invitations] button

**API:**
```
GET  /api/bidders?search=xyz&trade=Civil      # Search bidder registry
POST /api/bidders                              # Create new bidder
POST /api/tenders/{id}/invite                  # Send invitations
Body: { bidderIds: UUID[], messageTemplate: string }
```

---

# 7. MODULE 3: BOQ MANAGEMENT

## 7.1 BOQ-01: BOQ Structure (Tab in TEND-03)
**Route:** `/tenders/:id` (BOQ tab)
**Roles:** Admin, TenderManager, CommercialAnalyst

**Components:**
- Toolbar: [Import from Excel] [Export Template] [+ Add Section] [+ Add Item]
- Tree Grid (PrimeNG TreeTable):
  - Columns: Item #, Description, Qty, UOM, Type (Base/Alt/PS/Daywork), Actions
  - Expandable rows: Sections → Subsections → Items
  - Inline editing for quick changes
- Item Actions (3-dot menu): Edit, Delete, Duplicate
- Summary Footer: Total Items count, Sections count

**API:**
```
GET    /api/tenders/{id}/boq                          # Get full BOQ tree structure
POST   /api/tenders/{id}/boq/sections                 # Add section
PUT    /api/tenders/{id}/boq/sections/{sectionId}     # Update section
DELETE /api/tenders/{id}/boq/sections/{sectionId}     # Delete section
POST   /api/tenders/{id}/boq/items                    # Add item
PUT    /api/tenders/{id}/boq/items/{itemId}           # Update item
DELETE /api/tenders/{id}/boq/items/{itemId}           # Delete item
```

**Response Structure:**
```typescript
interface BoqTreeNode {
  id: string;
  type: 'section' | 'item';
  number: string;       // "1", "1.1", "1.1.1"
  title?: string;       // For sections
  description?: string; // For items
  quantity?: number;
  uom?: string;
  itemType?: string;    // Base, Alternate, ProvisionalSum, Daywork
  children?: BoqTreeNode[];
}
```

## 7.2 BOQ-02: Import BOQ from Excel
**Route:** Modal/dialog from BOQ-01

**3-Step Wizard:**

### Step 1: Upload File
- Drag-drop zone (PrimeNG FileUpload)
- "Download sample template" link
- Accepted formats: .xlsx, .xls
- Max size: 50MB

### Step 2: Map Columns
- Show Excel preview (first 5-10 rows in a read-only table)
- Column mapping dropdowns for each detected Excel column:
  - Excel Column A → BOQ Field: [Item Number ▼]
  - Excel Column B → BOQ Field: [Description ▼]
  - Excel Column C → BOQ Field: [Quantity ▼]
  - Excel Column D → BOQ Field: [UOM ▼]
- Auto-mapping logic: Detect headers like "Item No", "Description", "Qty", "Unit", etc. and suggest mappings
- [Auto-Map] button applies suggested mappings
- Required mappings: Item Number, Description (minimum)

### Step 3: Validate & Import
- Validation results display:
  - ✅ X items valid
  - ⚠️ Y items with warnings (UOM not recognized, missing quantity)
  - ❌ Z items with errors (missing required fields)
- Error/warning list (expandable accordion per item)
- Section detection: Parse item numbers to auto-create sections (1.x → Section 1, 2.x → Section 2)
- [Import Valid Items] [Fix & Reimport] buttons

**API:**
```
POST /api/tenders/{id}/boq/import/upload          # Upload Excel file
Body: multipart/form-data
Response: { fileId: string, detectedColumns: ColumnInfo[], previewRows: any[][] }

POST /api/tenders/{id}/boq/import/validate        # Validate with column mapping
Body: { fileId: string, columnMappings: { excelColumn: number, boqField: string }[] }
Response: { validItems: number, warnings: ValidationIssue[], errors: ValidationIssue[], parsedSections: SectionPreview[] }

POST /api/tenders/{id}/boq/import/execute         # Execute import
Body: { fileId: string, columnMappings: ..., importWarnings: boolean }
Response: { importedItems: number, importedSections: number, skippedItems: number }
```

**Excel Parsing Implementation Notes:**
1. Use ExcelDataReader to read .xlsx/.xls files
2. Auto-detect header row (first row with text content)
3. Parse item numbers to determine section hierarchy: "1" → top-level section, "1.1" → subsection, "1.1.1" → item
4. Handle merged cells (common in BOQ spreadsheets)
5. Validate UOM codes against uom_master table
6. Handle empty rows (skip them)
7. Store original file in MinIO for reference

## 7.3 BOQ-03: Add/Edit BOQ Item
**Route:** Modal dialog from BOQ-01

**Form Fields:**
| Field | Type | Validation |
|-------|------|------------|
| Section* | Dropdown (search) | Required, from existing sections |
| Item Number* | Text | Required, auto-suggest next number |
| Description* | Textarea | Required, max 500 chars |
| Quantity* | Number | Required, > 0 |
| UOM* | Dropdown from uom_master | Required |
| Type | Radio | Base / Alternate / ProvisionalSum / Daywork |
| Notes | Textarea | Optional |

## 7.4 BOQ-04: BOQ Template Generator
**Route:** Dialog from BOQ-01

**Purpose:** Generate blank Excel template for bidders to price

**Options:**
- Include columns (checkboxes): Item #, Description, Qty, UOM, Unit Rate, Amount
- Lock columns (checkboxes): Item #, Description, Qty, UOM (recommended locked)
- Include instructions sheet? (checkbox, default true)
- Language: English / Arabic / Both

**API:**
```
POST /api/tenders/{id}/boq/export-template
Body: { includeColumns: string[], lockColumns: string[], includeInstructions: boolean, language: string }
Response: File download (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)
```

**Template Generation Notes (using ClosedXML):**
1. Create workbook with branded header (Tender title, reference, deadline)
2. Lock specified columns (set cell protection)
3. Add data validation for UOM column
4. Add Amount formula: =Qty × Unit Rate
5. Add conditional formatting for empty Unit Rate cells (highlight yellow)
6. Add instructions sheet with submission rules

---

# 8. MODULE 4: DOCUMENT CONTROL & RFIs

## 8.1 DOC-01: Document Library (Tab in TEND-03)
**Route:** `/tenders/:id` (Documents tab)

**Layout:**
- Toolbar: [Upload Files ↑] [New Folder +] [Download Selected]
- Split pane: Folder Tree (30%) | File List (70%)
- Default folders per tender: RFP Package, Drawings, Specifications, BOQ, Contract Forms, Addenda, Clarifications

**File List Table Columns:** Name, Type (icon), Size, Uploaded By, Upload Date, Version, Actions
**Row Actions:** Download, Preview (DOC-02), Delete, View History

**API:**
```
GET    /api/tenders/{id}/documents?folder=RFP Package     # List documents
POST   /api/tenders/{id}/documents/upload                 # Upload files (multipart)
DELETE /api/tenders/{id}/documents/{docId}                 # Delete document
POST   /api/tenders/{id}/documents/folders                # Create folder
GET    /api/tenders/{id}/documents/{docId}/download        # Download file (presigned URL)
GET    /api/tenders/{id}/documents/{docId}/versions        # Get version history
```

## 8.2 DOC-02: Document Preview Modal
- PrimeNG Dialog (80% screen width)
- PDF viewer (embedded iframe or pdf.js)
- File metadata sidebar: Name, size, type, uploaded by, date
- [Download] button
- Version history link

## 8.3 DOC-03: Issue Addendum
**Route:** `/tenders/:id/addenda/create`

**Form:**
| Field | Type | Notes |
|-------|------|-------|
| Addendum Number | Read-only | Auto-incremented |
| Issue Date | Calendar | Default: today |
| Summary* | Textarea | Max 500 chars |
| Affected Documents | Checklist from library | Multi-select |
| Upload New/Revised Files | Drag-drop zone | |
| Extend Deadline? | Checkbox | If checked, show new deadline picker |
| New Deadline | Calendar | Must be > current deadline |

**API:**
```
POST /api/tenders/{id}/addenda
Body: { summary, issueDate, affectedDocumentIds, files (multipart), extendDeadline, newDeadline }
Response: { addendumId, addendumNumber }
```

**On Issue:** Auto-email all qualified bidders with download link. Track acknowledgments.

## 8.4 CLAR-01: Clarifications Register (Tab in TEND-03)
**Route:** `/tenders/:id` (Clarifications tab)
**Roles:** Admin, TenderManager (full access), Bidder (submit only, view published)

**Layout:**
- Toolbar: [+ New Internal RFI] [Publish Q&A Bulletin]
- Filters: Status dropdown (All, Submitted, Pending, DraftAnswer, Answered, Published), Section dropdown, Search
- Q&A Table (PrimeNG Table with row expansion):
  - Collapsed: Reference, Subject, Bidder (or "Anonymous"), Date, Status badge
  - Expanded: Full question text, Answer area (if pending), Action buttons

**Status Workflow:**
```
SUBMITTED → PENDING → DRAFT_ANSWER → ANSWERED → PUBLISHED
                ↓
            DUPLICATE / REJECTED
```

**Actions by Status:**
| Status | Actions |
|--------|---------|
| Submitted | Assign to section, Draft answer, Mark duplicate, Reject |
| Pending | Draft answer, Mark duplicate, Reject |
| DraftAnswer | Edit answer, Approve answer, Discard |
| Answered | Publish, Edit, Mark internal only |
| Published | (Locked) |

**API:**
```
GET  /api/tenders/{id}/clarifications?status=&section=&search=
POST /api/tenders/{id}/clarifications                    # Submit question (bidder)
POST /api/tenders/{id}/clarifications/{clarId}/answer    # Draft/update answer
PUT  /api/tenders/{id}/clarifications/{clarId}/status    # Change status
POST /api/tenders/{id}/clarifications/{clarId}/approve   # Approve answer
```

## 8.5 CLAR-02: Submit Internal RFI
**Route:** Dialog from CLAR-01

**Form:** Subject*, Related BOQ Section (dropdown), Question* (rich text), Attachments, Priority (Normal/Urgent), Due Date

**API:**
```
POST /api/tenders/{id}/clarifications/internal-rfi
```

## 8.6 CLAR-03: Publish Q&A Bulletin
**Route:** Dialog from CLAR-01

**Steps:**
1. Select questions to include (checkboxes, only status = Answered)
2. Set bulletin details: Bulletin Number (auto), Issue Date, Introduction text, Closing notes
3. Preview generated PDF
4. [Publish & Send] → Generate PDF, email to all qualified bidders

**API:**
```
POST /api/tenders/{id}/clarification-bulletins
Body: { clarificationIds: UUID[], issueDate, introduction, closingNotes }
Response: { bulletinId, bulletinNumber, pdfPath }
```

---

# 9. MODULE 5: BID COLLECTION & SUBMISSION PORTAL

## 9.1 BID-01: Bid Submission Portal (Bidder-Facing)
**Route:** `/portal/tenders/:id/submit`
**Roles:** Bidder (authenticated, qualified)
**UI:** Separate layout from main app - cleaner, bidder-branded portal

**Layout:**
- Header: Tender title, company name, countdown timer to deadline
- Tab Navigation: Documents (view RFP) | Clarifications (view Q&A) | Submit

**Submit Tab Components:**
- Warning banner: "Ensure all documents are uploaded before submitting!"
- Upload sections (each with drag-drop zone):
  - Commercial Bid: Upload Priced BOQ* (Excel)
  - Technical Bid: Upload Methodology*, Upload Team CVs*, Upload Program*, Upload HSE Plan*
  - Supporting Documents: Upload Additional Files (optional)
- Bid Validity input: Number, default 90 days
- Confirmation checkbox: "I confirm all information is correct"
- [Submit Bid] button (disabled until all required files uploaded and checkbox checked)

**Deadline Enforcement:**
- If before deadline: Normal submission
- If after deadline: Warning "Deadline has passed. Your bid will be marked as late."
- After submission: Cannot edit. Show receipt (BID-02).

**API:**
```
POST /api/portal/tenders/{id}/bids/upload        # Upload individual files
Body: multipart/form-data { file, documentType }
Response: { fileId, fileName, fileSize }

POST /api/portal/tenders/{id}/bids/submit        # Final submission
Body: { bidValidityDays, fileIds: { pricedBoq, methodology, teamCvs, program, hsePlan, supporting[] } }
Response: { bidId, receiptNumber, submissionTime, isLate }
```

## 9.2 BID-02: Bid Receipt Confirmation
**Route:** `/portal/bids/:bidId/receipt`

**Components:**
- Success icon and message
- Receipt details: Tender name, Company, Submission time, Files list, Receipt number
- [Download Receipt PDF] button
- [Return to Portal] button

## 9.3 BID-03: Bid Management (Tab in TEND-03)
**Route:** `/tenders/:id` (Bids tab)
**Roles:** Admin, TenderManager, CommercialAnalyst

**Layout:**
- Header stats: X bids received | Y late bids
- Buttons: [Download All Bids] [Open Bids]
- Bids Table:
  - Columns: Checkbox, Bidder, Submission Time, Status (On-time/Late), Bid Amount (hidden until opened), Files, Actions
  - Status badges: Submitted (blue), Opened (green), Late (red), Imported (purple)
  - Actions: View Files, Download, Import BOQ
- Late Bids Section (collapsible): List with [Accept] [Reject] per late bid

**"Open Bids" Action:** Confirmation dialog → Reveals bid amounts → Status changes to "Opened". This is an irreversible action.

**API:**
```
GET  /api/tenders/{id}/bids                       # List all bids
POST /api/tenders/{id}/bids/open                  # Open bids (reveal amounts)
POST /api/tenders/{id}/bids/{bidId}/accept-late   # Accept late bid
POST /api/tenders/{id}/bids/{bidId}/reject-late   # Reject late bid
GET  /api/tenders/{id}/bids/download-all          # Download all bids as ZIP
```

## 9.4 BID-04: Bid Details & Files
**Route:** `/tenders/:id/bids/:bidId`

**Components:**
- Bidder name, submission time, status header
- Files organized by category (Commercial, Technical, Supporting) with [Download] [Preview] per file
- Bid Summary (after import): Total Bid Amount, Currency, Validity, Exceptions count
- Actions: [Download All] [Import BOQ] [Flag for Review]

## 9.5 BID-05: Import & Normalize Bid Data
**Route:** Dialog from BID-03 or BID-04

**5-Step Wizard:**

### Step 1: Upload & Parse
- File already uploaded as part of bid submission
- [Parse File] button → Detect columns, count items
- Display: "✅ 120 items detected from boq-priced.xlsx"

### Step 2: Map Columns
- Same pattern as BOQ-02 Step 2
- Auto-map: "Item No" → Item Number, "Rate" → Unit Rate, etc.
- Required mappings: Item Number, Unit Rate (minimum)

### Step 3: Match to Master BOQ
- Auto-matching algorithm:
  1. Exact match by Item Number
  2. If no exact match, fuzzy match on Description (FuzzySharp, threshold: 80% similarity)
  3. Flag remaining as unmatched
- Results display:
  - ✅ X items matched automatically
  - ⚠️ Y items need manual matching
  - ❌ Z items not in master BOQ (extra items)
- Manual Matching Interface: For each unmatched item, show dropdown to search master BOQ items or [Mark as Extra Item]
- Extra Items: For each, checkbox to include/exclude from total

### Step 4: Currency & UOM Normalization
**Currency:**
- Detected currency from bid: [AED ▼] (editable)
- Tender base currency: AED (read-only)
- FX Rate: [1.0000] (auto = 1.0 if same currency)
- For different currencies: Manual input or [Fetch Live Rate] from API
- [Lock Rate] button
- Preview: "1 USD = 3.67 AED"

**UOM Normalization:**
- Table of items with UOM mismatches between bidder and master BOQ:
  - Columns: Item, Bidder UOM, Master UOM, Conversion Factor, Auto-Convert?
  - Examples:
    - Item 45: sqft → m² × 0.092903 [✅ Auto-convert]
    - Item 78: ft → LM × 0.3048 [✅ Auto-convert]
    - Item 102: LS → m² [❌ Cannot convert] → Mark as non-comparable
- For non-convertible UOMs: Exclude from rate comparison, include as lump sum

### Step 5: Validate & Import
**Validation Checks:**
- Formula: Amount ≈ Quantity × Unit Rate (tolerance ±1%)
- Data: Unit Rate > 0, no negative values
- Coverage: All master BOQ items accounted for (matched or marked "No Bid")
- Outlier pre-detection: Flag items >50% above or below average (if other bids imported)

**Results:**
- ✅ X items valid
- ⚠️ Y items with formula corrections (auto-corrected within tolerance)
- ❌ Z items with errors (missing rates → mark "No Bid")
- 🔍 W items flagged as outliers (informational)

**[Import with Warnings] button:** Imports all valid data, flags issues for review. Stores both native and normalized values in bid_pricing table.

**API:**
```
POST /api/tenders/{id}/bids/{bidId}/import/parse
Response: { detectedColumns, itemCount, previewRows }

POST /api/tenders/{id}/bids/{bidId}/import/map-columns
Body: { columnMappings }
Response: { mappedItems }

POST /api/tenders/{id}/bids/{bidId}/import/match-items
Response: { exactMatches, fuzzyMatches, unmatched, extraItems }

POST /api/tenders/{id}/bids/{bidId}/import/normalize
Body: { currency, fxRate, uomConversions }
Response: { normalizedItems, nonComparableItems }

POST /api/tenders/{id}/bids/{bidId}/import/validate
Response: { validItems, formulaCorrections, errors, outliers, summary }

POST /api/tenders/{id}/bids/{bidId}/import/execute
Body: { manualMappings, extraItemInclusions, acceptWarnings }
Response: { importedCount, totalNativeAmount, totalNormalizedAmount }
```

---

# 10. MODULE 6: BOQ ANALYSIS & COMPARABLE SHEET

## 10.1 EVAL-01: Comparable Sheet (Tab in TEND-03)
**Route:** `/tenders/:id` (Evaluation tab → Comparable Sheet sub-tab)
**Roles:** Admin, TenderManager, CommercialAnalyst, Approver, Auditor

**THIS IS THE MOST COMPLEX UI SCREEN IN THE APPLICATION.**

**Layout:**
- Toolbar: [Export to Excel] [Toggle Outliers] [⚙️ Settings]
- Filters: Section dropdown (All sections), Outlier filter (All / Only Outliers / Hide Outliers), Search
- Summary Stats: Total Items, Bidders Count, Outliers Count (High/Medium), Max Deviation
- Grid (AG Grid Community):
  - Frozen columns: Item #, Description, Qty, UOM (always visible when scrolling)
  - Dynamic columns: One per bidder (generated from imported bids)
  - Cell values: Normalized unit rate
  - Cell color-coding:
    - Green (#d4edda): <10% below average
    - Yellow (#fff3cd): 10-20% deviation from average
    - Red (#ffcccc): >20% above average
    - Gray: "NB" (No Bid)
    - Light purple: Non-comparable
  - Section subtotals: Sum of each bidder's amounts per section
  - Grand total row: Sum of all sections per bidder
  - Rank row: Final rank per bidder (1 = lowest total)
  - Column header: Bidder name + total amount
- Legend: Color code explanation (top-right)

**Outlier Detection Algorithm:**
```
For each BOQ item:
  1. Collect all bidder rates (exclude NoBid and NonComparable)
  2. Calculate average = sum(rates) / count
  3. For each bidder rate:
     deviation_pct = abs(rate - average) / average * 100
     if deviation_pct > 20: outlier_severity = "High" (red)
     elif deviation_pct > 10: outlier_severity = "Medium" (yellow)
     else: outlier_severity = "Low" (green)
  4. Store in bid_pricing.deviation_from_average and bid_pricing.outlier_severity
```

**Tooltip on cell hover:** Rate value, Average rate, Deviation %, Bidder's original UOM and rate

**Export to Excel:** Use ClosedXML on backend to generate formatted Excel with:
- Frozen panes matching grid
- Color-coded cells matching grid
- Section totals and grand totals
- Auto-filter on header row
- Formatted as currency

**API:**
```
GET /api/tenders/{id}/evaluation/comparable-sheet?section=&outlierFilter=&search=
Response: {
  summary: { totalItems, bidderCount, outlierCount, maxDeviation },
  bidders: [{ id, companyName, totalNormalizedAmount, rank }],
  items: [{
    boqItemId, itemNumber, description, quantity, uom, sectionId, sectionName,
    bidderRates: [{
      bidderId, nativeRate, normalizedRate, nativeAmount, normalizedAmount,
      isOutlier, outlierSeverity, deviationFromAverage, isNoBid, isNonComparable
    }]
  }],
  sectionTotals: [{ sectionId, sectionName, bidderTotals: [{ bidderId, total }] }],
  grandTotals: [{ bidderId, grandTotal }]
}

GET /api/tenders/{id}/evaluation/comparable-sheet/export-excel
Response: File download
```

**Performance Notes:**
- Cache comparable sheet data in Redis for 5 minutes
- Use Dapper for complex grid queries (better performance than EF Core for this use case)
- Pagination: For BOQs with 500+ items, implement virtual scrolling on AG Grid

## 10.2 Commercial Scoring
**Auto-calculated after all bids are imported and comparable sheet is ready.**

**Formula:** `Score = (Lowest Total Price / Bidder Total Price) × 100`
- Lowest bidder always gets 100 points
- Higher prices get proportionally lower scores

**Include/Exclude Toggles:**
- Include Provisional Sums: checkbox (default false)
- Include Alternates: checkbox (default false)
- Recalculate on toggle change

**API:**
```
POST /api/tenders/{id}/evaluation/calculate-commercial-scores
Body: { includeProvisionalSums: boolean, includeAlternates: boolean }
Response: { scores: [{ bidderId, normalizedTotal, commercialScore, rank }] }
```

---

# 11. MODULE 7: VENDOR PRICING TRACKING

## 11.1 Purpose
Track how individual vendors price similar items across different tenders over time. This enables:
- Identifying vendor pricing trends (getting more expensive or cheaper)
- Comparing a vendor's current rates against their historical rates
- Spotting anomalous pricing for specific items
- Building a historical rate database for future tender estimation

## 11.2 Data Collection
**When:** After a bid is imported and normalized (post BID-05 Step 5)
**What:** Snapshot bidder's rates into `vendor_pricing_snapshots` and `vendor_item_rates` tables
**Triggered by:** Background job after successful bid import

**API:**
```
POST /api/tenders/{id}/bids/{bidId}/snapshot-pricing     # Create vendor pricing snapshot
# Called automatically after bid import, or manually triggered
```

## 11.3 Vendor Pricing Dashboard
**Route:** `/vendor-pricing`
**Roles:** Admin, TenderManager, CommercialAnalyst, Auditor

**Components:**

### 11.3.1 Vendor Search & Selection
- Search/select vendor from bidder registry
- Filter by trade specialization
- Date range filter for history

### 11.3.2 Vendor Rate History Table
- Columns: Tender Name, Date, Item Description, UOM, Rate (Normalized), Currency, Total Items Priced
- Sort by date (newest first)
- Filter by item description (full-text search)
- Export to Excel

### 11.3.3 Rate Trend Chart
- Line chart (Chart.js or PrimeNG Charts) showing rate trends for selected items
- X-axis: Tender date
- Y-axis: Normalized unit rate
- Multiple lines for different items
- Tooltip: Tender name, rate, date

### 11.3.4 Vendor Comparison
- Select 2-5 vendors to compare
- Select specific BOQ items or categories
- Side-by-side rate comparison across tenders
- Highlight: Which vendor is cheapest/most expensive for each item

### 11.3.5 Rate Analytics
- Average rate per item across all tenders
- Rate volatility (standard deviation)
- Price trend direction (up/down/stable)
- Anomaly detection (rates significantly different from vendor's own history)

**API:**
```
GET /api/vendor-pricing/vendors                           # List vendors with pricing history
GET /api/vendor-pricing/vendors/{bidderId}/history?dateFrom=&dateTo=&search=
Response: { snapshots: [{ tenderId, tenderTitle, date, totalAmount, itemCount }] }

GET /api/vendor-pricing/vendors/{bidderId}/rates?itemDescription=&dateFrom=&dateTo=
Response: { rates: [{ tenderTitle, date, itemDescription, uom, normalizedRate, currency }] }

GET /api/vendor-pricing/compare
Body: { bidderIds: UUID[], itemDescriptions: string[], dateFrom, dateTo }
Response: { comparisons: [{ itemDescription, vendorRates: [{ bidderId, companyName, rates: [{ date, rate }] }] }] }

GET /api/vendor-pricing/analytics/{bidderId}
Response: { averageRates, volatility, trends, anomalies }

GET /api/vendor-pricing/export?bidderId=&dateFrom=&dateTo=
Response: Excel file download
```

## 11.4 Integration with Comparable Sheet
When viewing the comparable sheet, each cell can show an additional tooltip indicator:
- ↑ Rate is higher than this vendor's historical average for similar items
- ↓ Rate is lower than this vendor's historical average
- = Rate is consistent with history
- This provides contextual pricing intelligence directly in the evaluation view

---

# 12. MODULE 8: DASHBOARD & REPORTING

## 12.1 DASH-01: Tender Manager Dashboard
**Route:** `/dashboard`

**KPI Cards (4 across):**
| Card | Value | Icon |
|------|-------|------|
| Active Tenders | Count | 📋 |
| In Evaluation | Count | ⭐ |
| Awarded This Month | Count | ✅ |
| Overdue Tasks | Count | ⚠️ |

**Quick Actions:** [+ New Tender] [Import Bidders]

**Active Tenders Table:** Same as TEND-01 but limited to recent/active

**Upcoming Deadlines Widget:** List of deadlines within next 7 days with countdown

**API:**
```
GET /api/dashboard/tender-manager
Response: { kpis, activeTenders, upcomingDeadlines, recentActivity }
```

## 12.2 DASH-02: Approver Dashboard
**Route:** `/dashboard` (for Approver role)

**Pending Approvals Section:** Card-based layout of tenders awaiting approval. Each card shows: Tender name, value, submitted date, urgency indicator
**Recent Activity Feed:** Approved/rejected items
**My Approval Stats:** Bar chart (approved vs rejected vs pending)

## 12.3 Technical Evaluation

### EVAL-02: Technical Evaluation Setup
**Route:** `/tenders/:id/evaluation/setup`

**Components:**
- Panel Members: Select users with TechnicalPanelist role (min 2, max 5)
- Criteria Review: Table from tender creation (read-only or editable)
- Scoring Method: Numeric (0-10) or Star (1-5)
- Blind Mode: Checkbox (default checked) - Hide commercial data from panelists
- Deadline: Date picker for technical evaluation deadline
- [Start Evaluation] → Lock criteria, notify panelists via email

### EVAL-03: Technical Scoring (Panelist View)
**Route:** `/tenders/:id/evaluation/score`
**Roles:** TechnicalPanelist only

**Layout:**
- Progress: X of Y bidders scored
- Current bidder header
- Document links: [View Methodology] [View Team CVs] [View Program] [View HSE Plan] → Opens DOC-02 modal
- Scoring form: One section per criterion
  - Criterion name + weight + guidance notes
  - Score slider (0-10) or star rating
  - Comment box (mandatory if score <3 or >8)
- [Save Draft] (saves, can edit later)
- [Submit Score] (locks score for this bidder, cannot undo)
- Navigation: [← Previous Bidder] [Next Bidder →]

**API:**
```
GET  /api/tenders/{id}/evaluation/my-assignments              # Panelist's assigned bidders
GET  /api/tenders/{id}/evaluation/bidders/{bidderId}/documents # Bidder's technical docs
GET  /api/tenders/{id}/evaluation/scores/{bidderId}           # Get my scores for this bidder
POST /api/tenders/{id}/evaluation/scores                      # Save/submit scores
Body: { bidderId, scores: [{ criterionId, score, comment }], isDraft: boolean }
```

### EVAL-04: Technical Scores Summary
**Route:** `/tenders/:id/evaluation/summary`

**Components:**
- Status: X/Y panelists completed
- Raw Scores Table: Matrix of panelist scores per bidder
- Aggregated Scores: Average score per bidder, rank
- Variance Alerts: Flag bidders where score StdDev > 2 across panelists
- [Lock Scores] → Finalizes technical evaluation, reveals commercial data
- [View Detailed Comments] → EVAL-05

### EVAL-06: Combined Scorecard
**Route:** `/tenders/:id/evaluation/scorecard`

**Components:**
- Weight Adjuster: Tech [40] Commercial [60] (must sum to 100, real-time recalc)
- Scorecard Table:
  - Columns: Bidder, Tech Score, Tech Rank, Commercial Score, Commercial Rank, Combined Score, Final Rank
  - Highlight winner (green row)
- Recommendation: "Recommended Award: {Bidder Name}"
- [Sensitivity Analysis] → Modal showing rank changes at different weight splits
- [Generate Award Pack] → Creates PDF via QuestPDF
- [Start Approval] → Initiates approval workflow

**Combined Score Formula:**
```
Combined = (TechWeight/100 × TechScore) + (CommWeight/100 × CommScore)
```

**API:**
```
GET  /api/tenders/{id}/evaluation/combined-scorecard?techWeight=40&commWeight=60
POST /api/tenders/{id}/evaluation/calculate-combined
GET  /api/tenders/{id}/evaluation/sensitivity-analysis
Response: { analyses: [{ techWeight, commWeight, rankings: [{ bidderId, rank }] }] }
```

---

# 13. MODULE 9: ADMIN & SETTINGS

## 13.1 ADMIN-01: User Management
**Route:** `/admin/users`

**Components:** Users table (Name, Email, Role, Status, Last Login, Actions), Search, Filter by role/status, [+ Add User] button → Modal (Name*, Email*, Role*, Send invitation email?)

## 13.2 ADMIN-02: Master Data Management
**Route:** `/admin/master-data`

**Tabs:**
- **Clients:** CRUD table
- **Bidders:** Master bidder registry
- **UOMs:** Unit of measure library with conversion factors
- **Trades:** Trade specializations
- **Email Templates:** Edit templates (subject + body with merge fields)

## 13.3 ADMIN-03: System Settings
**Route:** `/admin/settings`

**Sections:**
- General: Default currency, default bid validity, clarification buffer days
- Notifications: Enable/disable per type, reminder days
- Security: Password policy, session timeout
- Localization: Default language, date format, number format

---

# 14. CROSS-CUTTING CONCERNS

## 14.1 Audit Logging
**Every mutation** (create, update, delete) is logged to `audit_logs` table:
```csharp
// Implement as MediatR Pipeline Behavior
public class AuditLogBehavior<TRequest, TResponse> : IPipelineBehavior<TRequest, TResponse>
{
    // Automatically logs: UserId, Action, EntityType, EntityId, OldValues, NewValues, IP, Timestamp
}
```

## 14.2 Error Handling
Global exception middleware returns consistent JSON:
```json
{
  "success": false,
  "message": "An error occurred",
  "errors": ["Detailed error message"],
  "validationErrors": { "fieldName": ["Validation message"] }
}
```

HTTP status codes: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 500 Internal Error

## 14.3 Validation
All commands validated via FluentValidation before handler execution:
```csharp
public class ValidationBehavior<TRequest, TResponse> : IPipelineBehavior<TRequest, TResponse>
{
    // Runs all validators for the request type
    // Throws ValidationException with field-level errors
}
```

## 14.4 Caching Strategy
- Comparable sheet: Redis cache, 5-minute TTL, invalidate on bid import
- Dashboard KPIs: Redis cache, 10-minute TTL
- Tender list: Redis cache, 2-minute TTL, invalidate on tender create/update
- UOM master: Redis cache, 24-hour TTL (rarely changes)

## 14.5 File Storage (MinIO)
```
Buckets:
  tender-documents/       # RFP docs, addenda, drawings
    {tenderId}/
      {folder}/
        {fileName}
  bid-submissions/        # Bidder uploads
    {tenderId}/
      {bidderId}/
        {fileName}
  generated-reports/      # PDFs, Excel exports
    {type}/
      {fileName}
```

## 14.6 Email Service
Use MailKit for SMTP, Resend for production (3k free/month).
Templates use Scriban or simple string interpolation with merge fields:
- {{tender_title}}, {{deadline}}, {{portal_link}}, {{bidder_name}}, {{receipt_number}}

Email types: TenderInvitation, AddendumNotice, ClarificationBulletin, DeadlineReminder (3d, 1d), BidReceipt, ApprovalRequest, ApprovalDecision

## 14.7 Background Jobs (Hangfire)
- Deadline reminder emails: Recurring job, runs daily at 8 AM
- NDA expiry check: Recurring job, runs daily
- Cache warmup: On application start
- Vendor pricing snapshot: Triggered after bid import

## 14.8 Security
- JWT tokens: 1-hour access token, 7-day refresh token
- Password hashing: BCrypt
- Rate limiting: 100 requests/minute per user
- Input sanitization: All string inputs trimmed and HTML-encoded
- File upload: Whitelist extensions (.pdf, .docx, .xlsx, .xls, .dwg, .zip, .jpg, .png), max 100MB
- CORS: Whitelist frontend origin only

---

# 15. FEATURE INTEGRATION MAP

This section documents how features connect to each other. This is critical for Claude Code to understand dependencies and ensure seamless integration.

```
TENDER CREATION (TEND-02)
    │
    ├──→ Creates Tender entity → stored in DB
    ├──→ Creates Evaluation Criteria → stored in evaluation_criteria table
    ├──→ Creates Client (inline) → stored in clients table
    │
    ▼
TENDER DETAILS (TEND-03) ← Central hub, all other features are tabs here
    │
    ├──→ BIDDER INVITATION (TEND-05)
    │       │
    │       ├──→ Creates tender_bidders records
    │       ├──→ Sends invitation emails
    │       └──→ Bidders access BIDDER PORTAL
    │
    ├──→ DOCUMENT UPLOAD (DOC-01)
    │       │
    │       ├──→ Stores files in MinIO
    │       ├──→ Creates document records
    │       └──→ Referenced by: Addenda, Clarifications, Bid Documents
    │
    ├──→ BOQ MANAGEMENT (BOQ-01)
    │       │
    │       ├──→ Import from Excel (BOQ-02)
    │       │       └──→ Creates boq_sections + boq_items
    │       ├──→ Export Template (BOQ-04)
    │       │       └──→ Generated Excel sent to bidders
    │       └──→ BOQ structure is the MASTER against which all bids are compared
    │
    ├──→ CLARIFICATIONS (CLAR-01)
    │       │
    │       ├──→ Bidders submit questions via portal
    │       ├──→ TM drafts answers
    │       ├──→ Published as bulletins (CLAR-03) → emailed to bidders
    │       └──→ References: BOQ sections, Documents
    │
    ├──→ BID COLLECTION (BID-03)
    │       │
    │       ├──→ Bidders submit via portal (BID-01)
    │       │       └──→ Creates bid_submissions + bid_documents
    │       ├──→ Import & Normalize (BID-05)
    │       │       ├──→ Parses Excel
    │       │       ├──→ Matches to master BOQ (boq_items)
    │       │       ├──→ Applies currency conversion (fx_rate)
    │       │       ├──→ Applies UOM normalization (uom_master)
    │       │       ├──→ Stores in bid_pricing (native + normalized)
    │       │       └──→ Triggers VENDOR PRICING SNAPSHOT
    │       │
    │       └──→ After all bids imported → COMPARABLE SHEET available
    │
    ├──→ EVALUATION (EVAL-01)
    │       │
    │       ├──→ Comparable Sheet ← Reads from bid_pricing (normalized values)
    │       │       ├──→ Color-coded outlier detection
    │       │       ├──→ Section totals and grand totals
    │       │       ├──→ Bidder ranking
    │       │       └──→ Export to Excel
    │       │
    │       ├──→ Technical Evaluation (EVAL-02 → EVAL-04)
    │       │       ├──→ Uses evaluation_criteria from tender
    │       │       ├──→ Panelists score from bid_documents (technical)
    │       │       ├──→ Blind mode: commercial data hidden
    │       │       ├──→ Scores stored in technical_scores
    │       │       └──→ Lock scores → reveals commercial data
    │       │
    │       ├──→ Commercial Scoring (auto-calculated)
    │       │       ├──→ Uses normalized totals from bid_pricing
    │       │       ├──→ Formula: (Lowest / This) × 100
    │       │       └──→ Stored in commercial_scores
    │       │
    │       └──→ Combined Scorecard (EVAL-06)
    │               ├──→ Merges technical_scores + commercial_scores
    │               ├──→ Applies weights from tender
    │               ├──→ Stored in combined_scorecards
    │               ├──→ Sensitivity analysis
    │               └──→ Generates Award Pack PDF → APPROVAL
    │
    └──→ APPROVAL (APPR-01 → APPR-03)
            │
            ├──→ Award pack PDF generated (QuestPDF)
            ├──→ Sequential approval levels
            ├──→ Approve → next level (or final = Awarded)
            ├──→ Reject → back to TM with comments
            └──→ Final approval → Tender status = "Awarded"

VENDOR PRICING (Parallel system)
    │
    ├──→ Snapshots created after each bid import
    ├──→ Cross-tender rate comparison
    ├──→ Trend analysis over time
    └──→ Tooltip integration in Comparable Sheet
```

## 15.1 Key Data Flow Dependencies

| Step | Prerequisite | Creates |
|------|-------------|---------|
| Create Tender | Client exists | Tender, EvaluationCriteria |
| Import BOQ | Tender exists | BoqSections, BoqItems |
| Invite Bidders | Tender exists, Bidders in registry | TenderBidders |
| Upload Documents | Tender exists | Documents |
| Submit Bid | Bidder qualified, Tender active, Before deadline | BidSubmission, BidDocuments |
| Import Bid BOQ | Bid submitted, Master BOQ exists | BidPricing |
| Calculate Comparable Sheet | At least 2 bids imported | (Read from BidPricing) |
| Technical Scoring | Evaluation setup done, Panelists assigned | TechnicalScores |
| Lock Technical Scores | All panelists completed | EvaluationState.technicalScoresLocked |
| Commercial Scoring | Bids imported, Technical scores locked | CommercialScores |
| Combined Scorecard | Technical + Commercial scores exist | CombinedScorecards |
| Initiate Approval | Combined scorecard calculated | ApprovalWorkflow, ApprovalLevels |
| Award Tender | All approval levels approved | Tender.status = Awarded |
| Vendor Pricing Snapshot | Bid imported and normalized | VendorPricingSnapshot, VendorItemRates |

---

# 16. COMPREHENSIVE TESTING PLAN

## 16.1 Testing Strategy

| Test Type | Framework | Coverage Target | Focus |
|-----------|-----------|----------------|-------|
| Unit Tests | xUnit + Moq (backend), Jasmine (frontend) | 70% | Business logic, validators, handlers |
| Integration Tests | xUnit + TestContainers | Key flows | API endpoints, DB operations |
| E2E Tests | Playwright or Cypress | Critical paths | User journeys end-to-end |

## 16.2 Unit Test Plan

### 16.2.1 Authentication Tests
```
TEST GROUP: Auth.Login
├── Should return tokens for valid credentials
├── Should return 401 for invalid password
├── Should return 401 for non-existent user
├── Should return 401 for inactive user
├── Should set refresh token in database
├── Should include user role in JWT claims

TEST GROUP: Auth.RefreshToken
├── Should return new tokens for valid refresh token
├── Should return 401 for expired refresh token
├── Should return 401 for revoked refresh token

TEST GROUP: Auth.ResetPassword
├── Should send reset email for existing user
├── Should not reveal if email exists (security)
├── Should reset password with valid token
├── Should reject expired reset token
├── Should enforce password strength requirements
```

### 16.2.2 Tender Management Tests
```
TEST GROUP: Tenders.Create
├── Should create tender with valid data and status = Draft
├── Should create tender with status = Active when published
├── Should auto-generate reference number (TNR-{YEAR}-{SEQ})
├── Should validate title is required and max 500 chars
├── Should validate client exists
├── Should validate submission deadline > clarification deadline + 3 days
├── Should validate technical + commercial weights = 100
├── Should validate evaluation criteria weights sum to 100
├── Should create associated evaluation criteria
├── Should log audit entry

TEST GROUP: Tenders.Update
├── Should update draft tender fields
├── Should prevent currency change after bids received
├── Should warn when editing active tender
├── Should update audit log
├── Should not create duplicate (INSERT vs UPDATE logic)

TEST GROUP: Tenders.StatusTransition
├── Should transition Draft → Active on publish
├── Should prevent publishing without required fields
├── Should transition Active → Evaluation after submission deadline
├── Should prevent transition backwards (Evaluation → Active)
├── Should transition Evaluation → Awarded after approval
├── Should allow Cancel from any status except Awarded
```

### 16.2.3 BOQ Management Tests
```
TEST GROUP: BOQ.Structure
├── Should create section with valid data
├── Should create nested subsection under parent
├── Should create item under section
├── Should enforce unique item numbers per tender
├── Should validate quantity > 0
├── Should validate UOM exists in uom_master

TEST GROUP: BOQ.Import
├── Should parse xlsx file and detect columns
├── Should auto-map common column headers (Item No → itemNumber)
├── Should validate required mappings (Item Number, Description)
├── Should detect section hierarchy from item numbers (1.1.1 → Section 1 → Subsection 1.1)
├── Should handle empty rows gracefully
├── Should handle merged cells
├── Should validate UOM codes against uom_master
├── Should report validation errors (missing fields, invalid UOM)
├── Should import valid items and skip invalid ones
├── Should create sections automatically from item number pattern
├── Should handle duplicate item numbers (report error)
├── Should persist all imported items to database

TEST GROUP: BOQ.Export
├── Should generate xlsx with correct columns
├── Should lock specified columns (Item #, Description, Qty, UOM)
├── Should include Amount formula (Qty × Unit Rate)
├── Should include tender branding header
├── Should include instructions sheet when requested
```

### 16.2.4 Clarification Tests
```
TEST GROUP: Clarifications.Submit
├── Should create question from bidder
├── Should enforce clarification deadline
├── Should auto-generate reference number (CL-001, CL-002)
├── Should handle anonymous submissions

TEST GROUP: Clarifications.Answer
├── Should save draft answer
├── Should approve answer (status → Answered)
├── Should mark as duplicate with reference
├── Should reject with reason

TEST GROUP: Clarifications.Publish
├── Should create bulletin with selected questions
├── Should generate PDF bulletin
├── Should email all qualified bidders
├── Should mark included questions as Published
├── Should track email delivery status
```

### 16.2.5 Bid Collection Tests
```
TEST GROUP: Bids.Submit
├── Should create bid submission with receipt number
├── Should store all uploaded files in MinIO
├── Should flag late submissions (after deadline)
├── Should prevent duplicate submissions per bidder per tender
├── Should send receipt email
├── Should generate receipt PDF

TEST GROUP: Bids.Import
├── Should parse uploaded Excel and detect columns
├── Should auto-map columns
├── Should match items to master BOQ by item number (exact)
├── Should fuzzy match by description (>80% similarity)
├── Should flag unmatched items for manual mapping
├── Should apply currency conversion correctly
│   ├── Same currency: rate = 1.0, no conversion
│   ├── Different currency: rate applied to all prices
│   └── FX rate locked per bid (not changed retroactively)
├── Should apply UOM conversion correctly
│   ├── sqft → m²: multiply rate by conversion factor
│   ├── LS → m²: mark as non-comparable
│   └── Same UOM: no conversion needed
├── Should validate formula (Amount ≈ Qty × Rate, ±1% tolerance)
├── Should store both native and normalized values
├── Should calculate total bid amount (native + normalized)
├── Should detect outliers against imported bids
├── Should mark "No Bid" items
├── Should handle extra items from bidder (include/exclude)
├── Should trigger vendor pricing snapshot after import

TEST GROUP: Bids.Open
├── Should require confirmation before opening
├── Should reveal bid amounts after opening
├── Should be irreversible
├── Should log audit entry

TEST GROUP: Bids.Late
├── Should allow accepting late bid
├── Should allow rejecting late bid
├── Should log decision in audit
```

### 16.2.6 Comparable Sheet Tests
```
TEST GROUP: ComparableSheet.Data
├── Should return all BOQ items as rows
├── Should return all bidders as columns
├── Should use normalized rates (not native)
├── Should calculate correct section totals
├── Should calculate correct grand totals
├── Should rank bidders by total (lowest = rank 1)

TEST GROUP: ComparableSheet.Outliers
├── Should calculate average rate per item
├── Should flag items >20% above avg as High (red)
├── Should flag items 10-20% above avg as Medium (yellow)
├── Should mark items <10% deviation as Low (green)
├── Should handle NoBid items (exclude from average calc)
├── Should handle NonComparable items (exclude from average calc)
├── Should filter to show only outlier items
├── Should filter to hide outlier items

TEST GROUP: ComparableSheet.Export
├── Should generate Excel with correct data
├── Should apply color coding in Excel cells
├── Should include section totals and grand totals
├── Should freeze panes (BOQ columns + header)
├── Should format numbers as currency
```

### 16.2.7 Evaluation Tests
```
TEST GROUP: TechnicalEvaluation.Setup
├── Should assign panelists (min 2)
├── Should validate criteria weights sum to 100
├── Should enable blind mode by default
├── Should send notification emails to panelists

TEST GROUP: TechnicalEvaluation.Scoring
├── Should save draft scores
├── Should submit final scores (locks them)
├── Should require comment when score < 3 or > 8
├── Should validate score range (0-10)
├── Should prevent editing after submission
├── Should track progress (X of Y bidders scored)
├── Should restrict panelist to only technical documents (blind mode)

TEST GROUP: TechnicalEvaluation.Summary
├── Should aggregate scores (average per bidder)
├── Should calculate variance (StdDev per bidder)
├── Should flag high variance (StdDev > 2)
├── Should rank bidders by average score
├── Should lock scores (irreversible)
├── Should reveal commercial data after lock

TEST GROUP: CommercialScoring
├── Should calculate score: (Lowest / This) × 100
├── Should give lowest bidder score = 100
├── Should rank by score (highest = rank 1)
├── Should recalculate when toggles change (include/exclude PS, Alternates)

TEST GROUP: CombinedScorecard
├── Should calculate: (TechWeight × TechScore) + (CommWeight × CommScore)
├── Should rank by combined score
├── Should identify recommended bidder (highest combined)
├── Should recalculate when weights adjusted
├── Should generate sensitivity analysis (test 5 different weight splits)
```

### 16.2.8 Approval Tests
```
TEST GROUP: Approval.Workflow
├── Should create workflow with approval levels
├── Should notify Level 1 approver
├── Should progress to next level on approval
├── Should return to tender manager on rejection
├── Should mark tender as Awarded on final approval
├── Should generate award pack PDF
├── Should log all decisions in audit

TEST GROUP: Approval.Decision
├── Should require comment for rejection
├── Should require comment for return-for-revision
├── Should allow approval without comment
├── Should prevent duplicate decisions
├── Should update workflow status correctly
```

### 16.2.9 Vendor Pricing Tests
```
TEST GROUP: VendorPricing.Snapshot
├── Should create snapshot after bid import
├── Should store normalized rates per item
├── Should store tender reference and date
├── Should handle multiple tenders for same vendor

TEST GROUP: VendorPricing.History
├── Should return rate history for a vendor
├── Should filter by date range
├── Should filter by item description (full-text search)
├── Should calculate trend direction (up/down/stable)
├── Should detect anomalous rates

TEST GROUP: VendorPricing.Comparison
├── Should compare rates across multiple vendors
├── Should identify cheapest vendor per item
├── Should calculate average rate per item across vendors
```

## 16.3 Integration Test Plan

### 16.3.1 End-to-End Flow: Complete Tender Lifecycle
```
TEST: Full tender lifecycle from creation to award
1. Admin creates users and assigns roles
2. TenderManager creates tender (Basic Info → Dates → Criteria → Review)
   VERIFY: Tender saved with status Draft, all fields persisted
3. TenderManager publishes tender
   VERIFY: Status = Active
4. TenderManager imports BOQ from Excel (150 items)
   VERIFY: 150 items in boq_items, sections auto-created
5. TenderManager invites 5 bidders
   VERIFY: 5 records in tender_bidders, invitation emails sent
6. TenderManager uploads RFP documents
   VERIFY: Files in MinIO, records in documents table
7. Bidder submits 3 clarification questions
   VERIFY: 3 records in clarifications with status = Submitted
8. TenderManager answers and publishes Q&A bulletin
   VERIFY: Bulletin PDF generated, emails sent
9. TenderManager issues addendum
   VERIFY: Addendum record created, bidders notified
10. 5 bidders submit bids (3 in AED, 2 in USD)
    VERIFY: 5 bid_submissions, files stored, receipts generated
11. TenderManager accepts 1 late bid
    VERIFY: late_accepted = true
12. CommercialAnalyst imports all 5 bids
    VERIFY: bid_pricing records with native AND normalized values
    VERIFY: Currency conversion applied (USD × 3.67)
    VERIFY: UOM normalization applied where needed
    VERIFY: Vendor pricing snapshots created
13. CommercialAnalyst views comparable sheet
    VERIFY: Grid shows 150 items × 5 bidders
    VERIFY: Outliers detected and color-coded
    VERIFY: Section totals and grand totals correct
    VERIFY: Bidders ranked by total
14. TenderManager sets up technical evaluation (3 panelists)
    VERIFY: Panel assignments created, notifications sent
15. 3 panelists score all 5 bidders
    VERIFY: Scores stored, progress tracked
16. TenderManager locks technical scores
    VERIFY: Technical scores frozen, commercial data revealed
17. Commercial scores auto-calculated
    VERIFY: Lowest bidder = 100, others proportional
18. Combined scorecard generated (40/60 split)
    VERIFY: Combined scores correct, ranking determined
19. TenderManager generates award pack PDF
    VERIFY: PDF contains all sections, saved in MinIO
20. Approval workflow initiated (3 levels)
    VERIFY: Level 1 notified
21. All 3 levels approve
    VERIFY: Workflow completed, tender status = Awarded
22. Audit log verified
    VERIFY: All actions logged with user, timestamp, details
```

### 16.3.2 Integration: BOQ Import → Bid Import → Comparable Sheet
```
TEST: Data flows correctly from BOQ master through bid import to comparable sheet
1. Import master BOQ (100 items across 5 sections)
2. Import Bid A (all items matched, same currency/UOM)
3. Import Bid B (95 items matched, 5 need manual mapping, different currency)
4. Import Bid C (98 items, 2 with UOM mismatch, 1 extra item)
5. Load comparable sheet
   VERIFY: 100 rows × 3 bidder columns
   VERIFY: Bid B rates converted from USD to AED
   VERIFY: Bid C UOM-converted items show correct rates
   VERIFY: Bid C's 2 non-comparable items marked correctly
   VERIFY: Extra item from Bid C handled (included or excluded per setting)
   VERIFY: "No Bid" cells shown for Bid B's 5 unmatched items
   VERIFY: Section totals include only matched items
   VERIFY: Grand totals correct
   VERIFY: Outlier detection runs against all 3 bids
```

### 16.3.3 Integration: Vendor Pricing Across Tenders
```
TEST: Vendor rates tracked across multiple tenders
1. Create Tender 1, import BOQ (civil works items)
2. Import Bid from Vendor X for Tender 1
   VERIFY: Pricing snapshot created
3. Create Tender 2 (6 months later), import similar BOQ
4. Import Bid from Vendor X for Tender 2
   VERIFY: New pricing snapshot created
5. View Vendor X pricing history
   VERIFY: Both tenders shown
   VERIFY: Rate trends calculated (up/down/stable)
6. Compare Vendor X rates between Tender 1 and Tender 2
   VERIFY: Item-by-item comparison available
   VERIFY: Anomalous rates flagged
```

## 16.4 Frontend Test Plan

### 16.4.1 Component Tests
```
TEST: TenderCreationWizard
├── Should render all 4 steps
├── Should validate required fields before allowing next step
├── Should maintain form state across step navigation
├── Should call POST /api/tenders on Create
├── Should call PUT /api/tenders/{id} on Update (edit mode)
├── Should save draft and navigate to tender details
├── Should show validation errors inline
├── Should auto-generate reference number
├── Should search clients in autocomplete
├── Should open client creation modal and use returned client

TEST: BOQTreeTable
├── Should render hierarchical tree structure
├── Should expand/collapse sections
├── Should show inline edit on item click
├── Should trigger import dialog
├── Should trigger export dialog
├── Should delete item with confirmation

TEST: ComparableSheetGrid
├── Should render AG Grid with frozen columns
├── Should apply cell color based on outlier severity
├── Should show tooltip on cell hover with details
├── Should filter by section
├── Should filter by outlier status
├── Should trigger Excel export
├── Should display section totals
├── Should display grand totals and rank

TEST: BidImportWizard
├── Should progress through 5 steps
├── Should preview parsed data
├── Should show column mapping dropdowns
├── Should display matching results (exact, fuzzy, unmatched)
├── Should show manual mapping interface
├── Should display currency and UOM conversion options
├── Should show validation results with error details
├── Should trigger import and refresh parent
```

## 16.5 Critical Integration Test Checklist

These tests verify that features are properly connected:

| # | Test | Touches |
|---|------|---------|
| 1 | Create tender → appears in list → editable → publishable | TEND-02, TEND-01, TEND-04, Status |
| 2 | Import BOQ from Excel → items appear in tree → match during bid import | BOQ-02, BOQ-01, BID-05 |
| 3 | Invite bidder → bidder logs in → sees tender → downloads docs | TEND-05, Portal, DOC-01 |
| 4 | Submit clarification → TM answers → publishes bulletin → bidder sees | CLAR-01, CLAR-03, Portal |
| 5 | Issue addendum → deadline extends → bidders notified → acknowledged | DOC-03, DOC-04, Emails |
| 6 | Bidder submits bid → appears in bid list → import normalizes → comparable sheet shows | BID-01, BID-03, BID-05, EVAL-01 |
| 7 | Currency conversion: USD bid → AED comparable sheet → correct rates | BID-05, EVAL-01 |
| 8 | UOM conversion: sqft bid → m² comparable sheet → correct rates | BID-05, EVAL-01 |
| 9 | Technical scoring (blind) → lock → commercial scores → combined scorecard | EVAL-02..06 |
| 10 | Combined scorecard → award pack PDF → approval workflow → awarded | EVAL-06, APPR-01..03 |
| 11 | Bid import → vendor pricing snapshot → historical rates accessible | BID-05, VendorPricing |
| 12 | All actions → audit log entries created | All modules → AuditLog |
| 13 | Draft tender → save → reload page → all data persisted | TEND-02, DB persistence |
| 14 | BOQ items → save → reload page → items still visible | BOQ-01, DB persistence |
| 15 | Evaluation criteria total must = 100% (frontend + backend validation) | TEND-02, Validation |

---

# APPENDIX A: SEED DATA

## A.1 Default UOMs
```sql
INSERT INTO uom_master (code, name, category, base_unit_code, conversion_to_base, is_system) VALUES
('m2', 'Square Meter', 'Area', 'm2', 1.0, true),
('sqft', 'Square Foot', 'Area', 'm2', 0.09290304, true),
('sqm', 'Square Meter', 'Area', 'm2', 1.0, true),
('m3', 'Cubic Meter', 'Volume', 'm3', 1.0, true),
('cft', 'Cubic Foot', 'Volume', 'm3', 0.02831685, true),
('LM', 'Linear Meter', 'Length', 'LM', 1.0, true),
('m', 'Meter', 'Length', 'LM', 1.0, true),
('ft', 'Foot', 'Length', 'LM', 0.3048, true),
('kg', 'Kilogram', 'Weight', 'kg', 1.0, true),
('ton', 'Metric Ton', 'Weight', 'kg', 1000.0, true),
('lb', 'Pound', 'Weight', 'kg', 0.45359237, true),
('LS', 'Lump Sum', 'Lump', NULL, NULL, true),
('No', 'Number/Each', 'Count', 'No', 1.0, true),
('set', 'Set', 'Count', 'No', 1.0, true),
('L', 'Liter', 'Volume', 'L', 1.0, true),
('gal', 'Gallon (US)', 'Volume', 'L', 3.78541, true);
```

## A.2 Default System Settings
```sql
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('default_currency', 'AED', 'String', 'Default currency for new tenders'),
('default_bid_validity_days', '90', 'Integer', 'Default bid validity period in days'),
('clarification_buffer_days', '3', 'Integer', 'Minimum days between clarification and submission deadlines'),
('session_timeout_minutes', '60', 'Integer', 'Session timeout in minutes'),
('password_min_length', '8', 'Integer', 'Minimum password length'),
('default_language', 'en', 'String', 'Default system language'),
('date_format', 'dd-MMM-yyyy', 'String', 'Date display format'),
('number_format', '#,##0.00', 'String', 'Number display format'),
('deadline_reminder_days', '3,1', 'String', 'Days before deadline to send reminders');
```

## A.3 Default Email Templates
```sql
INSERT INTO system_settings (setting_key, setting_value, setting_type, description) VALUES
('email_template_tender_invitation', '{"subject":"Invitation to Tender: {{tender_title}}","body":"Dear {{bidder_name}},\n\nYou are invited to submit a bid for {{tender_title}}.\n\nSubmission Deadline: {{deadline}}\n\nAccess the tender portal: {{portal_link}}\n\nRegards,\nBayan Tender Management"}', 'Json', 'Tender invitation email template'),
('email_template_bid_receipt', '{"subject":"Bid Receipt Confirmation - {{tender_title}}","body":"Dear {{bidder_name}},\n\nYour bid for {{tender_title}} has been received.\n\nReceipt Number: {{receipt_number}}\nSubmission Time: {{submission_time}}\n\nRegards,\nBayan Tender Management"}', 'Json', 'Bid receipt email template');
```

## A.4 Demo Users (for development)
```sql
INSERT INTO users (email, password_hash, first_name, last_name, role) VALUES
('admin@bayan.ae', '<bcrypt_hash>', 'System', 'Admin', 'Admin'),
('tm@bayan.ae', '<bcrypt_hash>', 'Ahmed', 'Manager', 'TenderManager'),
('ca@bayan.ae', '<bcrypt_hash>', 'Sara', 'Analyst', 'CommercialAnalyst'),
('tp1@bayan.ae', '<bcrypt_hash>', 'Omar', 'Engineer', 'TechnicalPanelist'),
('tp2@bayan.ae', '<bcrypt_hash>', 'Fatima', 'Architect', 'TechnicalPanelist'),
('approver@bayan.ae', '<bcrypt_hash>', 'Khalid', 'Director', 'Approver'),
('auditor@bayan.ae', '<bcrypt_hash>', 'Layla', 'Auditor', 'Auditor');
```

---

# APPENDIX B: IMPLEMENTATION ORDER

Build features in this exact order to maintain dependencies:

```
Phase 1: Foundation
1. Database schema + migrations
2. Authentication (login, JWT, roles)
3. User management (CRUD)
4. Client management (CRUD)
5. System settings

Phase 2: Tender Core
6. Tender CRUD (create, update, list, details)
7. Tender status transitions
8. Bidder registry (CRUD)
9. Bidder invitation
10. Document upload/download (MinIO integration)

Phase 3: BOQ & Clarifications
11. BOQ section/item CRUD
12. BOQ Excel import
13. BOQ template export
14. Clarifications Q&A system
15. Clarification bulletins
16. Addendum workflow
17. Email notifications

Phase 4: Bid Collection
18. Bidder portal (login, view docs, view Q&A)
19. Bid submission (file upload, deadline check)
20. Bid receipt generation
21. Bid management (list, open, accept/reject late)

Phase 5: Analysis & Normalization
22. Bid import wizard (parse, map columns, match items)
23. Currency conversion
24. UOM normalization
25. Bid pricing storage (native + normalized)
26. Comparable sheet (grid, outliers, totals, export)
27. Vendor pricing snapshots
28. Vendor pricing history & trends

Phase 6: Evaluation & Approval
29. Technical evaluation setup
30. Technical scoring interface
31. Technical scores summary
32. Commercial scoring (auto-calculation)
33. Combined scorecard
34. Sensitivity analysis
35. Award pack PDF generation
36. Approval workflow
37. Audit logging (all modules)

Phase 7: Dashboard & Polish
38. Tender manager dashboard
39. Approver dashboard
40. Vendor pricing dashboard
41. Performance optimization (caching, pagination)
42. Error handling & validation polish
```

---

# APPENDIX C: DOCKER COMPOSE

```yaml
version: '3.8'

services:
  api:
    build: ./backend
    container_name: bayan-api
    ports:
      - "5000:80"
    environment:
      - ConnectionStrings__DefaultConnection=Host=db;Database=bayan;Username=postgres;Password=postgres
      - ConnectionStrings__Redis=redis:6379
      - MinIO__Endpoint=minio:9000
      - MinIO__AccessKey=admin
      - MinIO__SecretKey=minio123
-- ... (55 lines truncated for brevity) ...
      - "8025:8025"

volumes:
  postgres_data:
  minio_data:
```

---

*End of Bayan Tender Management System PRD*
*Optimized for Claude Code autonomous implementation*
*All features, APIs, data models, and tests fully specified*
