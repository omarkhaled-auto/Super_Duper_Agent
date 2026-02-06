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
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ
);

-- =============================================
-- CLIENTS (Companies issuing tenders)
-- =============================================
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(300) NOT NULL,
    contact_person VARCHAR(200),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================
-- TENDERS
-- =============================================
CREATE TABLE tenders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    reference VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    client_id UUID NOT NULL REFERENCES clients(id),
    tender_type VARCHAR(50) NOT NULL, -- Open, Selective, Negotiated
    base_currency VARCHAR(3) NOT NULL DEFAULT 'AED', -- ISO currency code
    bid_validity_days INTEGER NOT NULL DEFAULT 90,
    
    -- Key Dates
    issue_date TIMESTAMPTZ NOT NULL,
    clarification_deadline TIMESTAMPTZ NOT NULL,
    submission_deadline TIMESTAMPTZ NOT NULL,
    opening_date TIMESTAMPTZ NOT NULL,
    
    -- Evaluation Weights
    technical_weight INTEGER NOT NULL DEFAULT 40, -- percentage
    commercial_weight INTEGER NOT NULL DEFAULT 60, -- percentage
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'Draft', -- Draft, Active, Evaluation, Awarded, Cancelled
    
    -- Metadata
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ,
    awarded_at TIMESTAMPTZ,
    
    CONSTRAINT chk_weights CHECK (technical_weight + commercial_weight = 100),
    CONSTRAINT chk_clarification_before_submission CHECK (clarification_deadline < submission_deadline),
    CONSTRAINT chk_dates_order CHECK (issue_date <= clarification_deadline AND clarification_deadline < submission_deadline)
);

CREATE INDEX idx_tenders_status ON tenders(status);
CREATE INDEX idx_tenders_client ON tenders(client_id);
CREATE INDEX idx_tenders_created_by ON tenders(created_by);
CREATE INDEX idx_tenders_submission_deadline ON tenders(submission_deadline);

-- =============================================
-- EVALUATION CRITERIA
-- =============================================
CREATE TABLE evaluation_criteria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    weight_percentage DECIMAL(5,2) NOT NULL, -- e.g., 25.00
    guidance_notes TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_eval_criteria_tender ON evaluation_criteria(tender_id);

-- =============================================
-- BIDDERS (Master registry)
-- =============================================
CREATE TABLE bidders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(300) NOT NULL,
    license_number VARCHAR(100),
    contact_person VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    trade_specialization VARCHAR(200),
    prequalification_status VARCHAR(50) DEFAULT 'Pending', -- Pending, Qualified, Rejected
    company_profile_path VARCHAR(1000), -- MinIO path
    is_active BOOLEAN NOT NULL DEFAULT true,
    -- Login credentials for bidder portal
    password_hash VARCHAR(500),
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_bidders_email ON bidders(email);
CREATE INDEX idx_bidders_trade ON bidders(trade_specialization);

-- =============================================
-- TENDER-BIDDER RELATIONSHIP
-- =============================================
CREATE TABLE tender_bidders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    bidder_id UUID NOT NULL REFERENCES bidders(id),
    
    -- Invitation tracking
    invitation_sent_at TIMESTAMPTZ,
    invitation_opened_at TIMESTAMPTZ,
    registered_at TIMESTAMPTZ,
    
    -- NDA tracking
    nda_status VARCHAR(50) DEFAULT 'Pending', -- Pending, Signed, Expired
    nda_document_path VARCHAR(1000),
    nda_signed_date DATE,
    nda_expiry_date DATE,
    
    -- Qualification
    qualification_status VARCHAR(50) DEFAULT 'Pending', -- Pending, Qualified, Rejected, Removed
    qualified_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_tender_bidder UNIQUE (tender_id, bidder_id)
);

CREATE INDEX idx_tender_bidders_tender ON tender_bidders(tender_id);
CREATE INDEX idx_tender_bidders_bidder ON tender_bidders(bidder_id);

-- =============================================
-- DOCUMENTS
-- =============================================
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    folder_path VARCHAR(500) NOT NULL, -- e.g., "RFP Package", "Drawings", "Addenda/Addendum 01"
    file_name VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL, -- MinIO path
    file_size_bytes BIGINT NOT NULL,
    content_type VARCHAR(200) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_latest BOOLEAN NOT NULL DEFAULT true,
    uploaded_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_documents_tender ON documents(tender_id);
CREATE INDEX idx_documents_folder ON documents(tender_id, folder_path);

-- =============================================
-- ADDENDA
-- =============================================
CREATE TABLE addenda (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    addendum_number INTEGER NOT NULL,
    issue_date DATE NOT NULL,
    summary TEXT NOT NULL,
    extends_deadline BOOLEAN NOT NULL DEFAULT false,
    new_deadline TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'Draft', -- Draft, Issued
    issued_by UUID REFERENCES users(id),
    issued_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_addendum_number UNIQUE (tender_id, addendum_number)
);

-- =============================================
-- ADDENDUM ACKNOWLEDGMENTS
-- =============================================
CREATE TABLE addendum_acknowledgments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    addendum_id UUID NOT NULL REFERENCES addenda(id) ON DELETE CASCADE,
    bidder_id UUID NOT NULL REFERENCES bidders(id),
    email_sent_at TIMESTAMPTZ,
    email_opened_at TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ,
    
    CONSTRAINT uq_addendum_ack UNIQUE (addendum_id, bidder_id)
);

-- =============================================
-- CLARIFICATIONS (RFIs / Q&A)
-- =============================================
CREATE TABLE clarifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    reference_number VARCHAR(50) NOT NULL, -- CL-001, CL-002, etc.
    
    -- Question
    subject VARCHAR(500) NOT NULL,
    question TEXT NOT NULL,
    submitted_by_bidder_id UUID REFERENCES bidders(id), -- NULL if internal RFI
    submitted_by_user_id UUID REFERENCES users(id), -- NULL if from bidder
    related_boq_section VARCHAR(200),
    related_document_id UUID REFERENCES documents(id),
    is_anonymous BOOLEAN NOT NULL DEFAULT false,
    priority VARCHAR(20) DEFAULT 'Normal', -- Normal, Urgent
    
    -- Answer
    answer TEXT,
    answered_by UUID REFERENCES users(id),
    answered_at TIMESTAMPTZ,
    
    -- Type & Status
    clarification_type VARCHAR(50) NOT NULL DEFAULT 'BidderQuestion', -- BidderQuestion, InternalRFI, ClientRFI
    status VARCHAR(50) NOT NULL DEFAULT 'Submitted', -- Submitted, Pending, DraftAnswer, Answered, Published, Duplicate, Rejected
    duplicate_of_id UUID REFERENCES clarifications(id),
    
    -- Publication
    published_in_bulletin_id UUID, -- FK set after bulletin created
    published_at TIMESTAMPTZ,
    
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_clarification_ref UNIQUE (tender_id, reference_number)
);

CREATE INDEX idx_clarifications_tender ON clarifications(tender_id);
CREATE INDEX idx_clarifications_status ON clarifications(tender_id, status);
CREATE INDEX idx_clarifications_bidder ON clarifications(submitted_by_bidder_id);

-- =============================================
-- CLARIFICATION BULLETINS
-- =============================================
CREATE TABLE clarification_bulletins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    bulletin_number INTEGER NOT NULL,
    issue_date DATE NOT NULL,
    introduction TEXT,
    closing_notes TEXT,
    pdf_path VARCHAR(1000), -- Generated PDF path in MinIO
    published_by UUID NOT NULL REFERENCES users(id),
    published_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_bulletin_number UNIQUE (tender_id, bulletin_number)
);

-- =============================================
-- BOQ (Bill of Quantities)
-- =============================================
CREATE TABLE boq_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    parent_section_id UUID REFERENCES boq_sections(id), -- NULL for top-level sections
    section_number VARCHAR(50) NOT NULL, -- "1", "1.1", "2", etc.
    title VARCHAR(500) NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_boq_sections_tender ON boq_sections(tender_id);
CREATE INDEX idx_boq_sections_parent ON boq_sections(parent_section_id);

CREATE TABLE boq_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    section_id UUID NOT NULL REFERENCES boq_sections(id) ON DELETE CASCADE,
    item_number VARCHAR(50) NOT NULL, -- "1.1.1", "1.1.2", etc.
    description TEXT NOT NULL,
    quantity DECIMAL(18,4) NOT NULL,
    uom VARCHAR(50) NOT NULL, -- m², m³, LM, kg, ton, LS, etc.
    item_type VARCHAR(50) NOT NULL DEFAULT 'Base', -- Base, Alternate, ProvisionalSum, Daywork
    notes TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_boq_item_number UNIQUE (tender_id, item_number)
);

CREATE INDEX idx_boq_items_tender ON boq_items(tender_id);
CREATE INDEX idx_boq_items_section ON boq_items(section_id);

-- =============================================
-- UOM MASTER & CONVERSIONS
-- =============================================
CREATE TABLE uom_master (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) NOT NULL UNIQUE, -- m², LM, sqft, etc.
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL, -- Area, Length, Volume, Weight, Lump, Count
    base_unit_code VARCHAR(20), -- The standard unit in this category (m² for Area, etc.)
    conversion_to_base DECIMAL(18,10), -- Factor to multiply to get base unit
    is_system BOOLEAN NOT NULL DEFAULT true, -- false for user-added
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed data examples:
-- (m², Square Meter, Area, m², 1.0, true)
-- (sqft, Square Foot, Area, m², 0.09290304, true)
-- (m³, Cubic Meter, Volume, m³, 1.0, true)
-- (cft, Cubic Foot, Volume, m³, 0.02831685, true)
-- (LM, Linear Meter, Length, LM, 1.0, true)
-- (ft, Foot, Length, LM, 0.3048, true)
-- (kg, Kilogram, Weight, kg, 1.0, true)
-- (ton, Metric Ton, Weight, kg, 1000.0, true)
-- (lb, Pound, Weight, kg, 0.45359237, true)
-- (LS, Lump Sum, Lump, NULL, NULL, true) -- Cannot convert LS

-- =============================================
-- BID SUBMISSIONS
-- =============================================
CREATE TABLE bid_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    bidder_id UUID NOT NULL REFERENCES bidders(id),
    
    -- Submission details
    submission_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_late BOOLEAN NOT NULL DEFAULT false,
    late_accepted BOOLEAN,
    late_accepted_by UUID REFERENCES users(id),
    
    -- File references
    original_file_name VARCHAR(500),
    original_file_path VARCHAR(1000), -- MinIO path to uploaded Excel
    
    -- Financial summary (populated after import)
    native_currency VARCHAR(3) NOT NULL DEFAULT 'AED',
    native_total_amount DECIMAL(18,2),
    fx_rate DECIMAL(10,6) DEFAULT 1.0,
    normalized_total_amount DECIMAL(18,2), -- In tender base currency
    
    -- Bid validity
    bid_validity_days INTEGER DEFAULT 90,
    
    -- Import status
    import_status VARCHAR(50) NOT NULL DEFAULT 'Uploaded', -- Uploaded, Parsing, Parsed, Mapping, Mapped, Validated, Imported, Failed
    import_started_at TIMESTAMPTZ,
    import_completed_at TIMESTAMPTZ,
    imported_by UUID REFERENCES users(id),
    validation_summary JSONB, -- JSON: { matched: 115, warnings: 3, errors: 2, outliers: 8 }
    
    -- Receipt
    receipt_number VARCHAR(100) NOT NULL UNIQUE,
    receipt_pdf_path VARCHAR(1000),
    
    status VARCHAR(50) NOT NULL DEFAULT 'Submitted', -- Submitted, Opened, Imported, Disqualified
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_bid_tender_bidder UNIQUE (tender_id, bidder_id)
);

CREATE INDEX idx_bid_submissions_tender ON bid_submissions(tender_id);
CREATE INDEX idx_bid_submissions_bidder ON bid_submissions(bidder_id);

-- =============================================
-- BID DOCUMENTS (Supporting files)
-- =============================================
CREATE TABLE bid_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bid_submission_id UUID NOT NULL REFERENCES bid_submissions(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL, -- PricedBOQ, Methodology, TeamCVs, Program, HSEPlan, Supporting
    file_name VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    content_type VARCHAR(200) NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================
-- BID PRICING (Imported line items)
-- =============================================
CREATE TABLE bid_pricing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bid_submission_id UUID NOT NULL REFERENCES bid_submissions(id) ON DELETE CASCADE,
    boq_item_id UUID REFERENCES boq_items(id), -- NULL if extra item from bidder
    
    -- Bidder's original values
    bidder_item_number VARCHAR(50),
    bidder_description TEXT,
    bidder_quantity DECIMAL(18,4),
    bidder_uom VARCHAR(50),
    native_unit_rate DECIMAL(18,4),
    native_amount DECIMAL(18,2),
    native_currency VARCHAR(3) NOT NULL,
    
    -- Normalized values (for comparison)
    normalized_unit_rate DECIMAL(18,4), -- Converted to base currency & base UOM
    normalized_amount DECIMAL(18,2),
    fx_rate_applied DECIMAL(10,6),
    uom_conversion_factor DECIMAL(18,10),
    
    -- Matching metadata
    match_type VARCHAR(50), -- ExactMatch, FuzzyMatch, ManualMatch, ExtraItem, NoBid
    match_confidence DECIMAL(5,2), -- 0-100 percentage
    is_included_in_total BOOLEAN NOT NULL DEFAULT true,
    
    -- Outlier detection
    is_outlier BOOLEAN NOT NULL DEFAULT false,
    outlier_severity VARCHAR(20), -- High, Medium, Low
    deviation_from_average DECIMAL(10,4), -- Percentage
    
    -- Flags
    has_formula_error BOOLEAN NOT NULL DEFAULT false,
    is_no_bid BOOLEAN NOT NULL DEFAULT false,
    is_non_comparable BOOLEAN NOT NULL DEFAULT false, -- When UOM cannot be converted
    
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_bid_pricing_submission ON bid_pricing(bid_submission_id);
CREATE INDEX idx_bid_pricing_boq_item ON bid_pricing(boq_item_id);
CREATE INDEX idx_bid_pricing_outlier ON bid_pricing(bid_submission_id, is_outlier);

-- =============================================
-- VENDOR PRICING HISTORY (Cross-tender tracking)
-- =============================================
CREATE TABLE vendor_pricing_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bidder_id UUID NOT NULL REFERENCES bidders(id),
    tender_id UUID NOT NULL REFERENCES tenders(id),
    bid_submission_id UUID NOT NULL REFERENCES bid_submissions(id),
    snapshot_date DATE NOT NULL,
    tender_base_currency VARCHAR(3) NOT NULL,
    total_bid_amount DECIMAL(18,2) NOT NULL,
    total_items_count INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_vendor_snapshots_bidder ON vendor_pricing_snapshots(bidder_id);
CREATE INDEX idx_vendor_snapshots_tender ON vendor_pricing_snapshots(tender_id);

CREATE TABLE vendor_item_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id UUID NOT NULL REFERENCES vendor_pricing_snapshots(id) ON DELETE CASCADE,
    boq_item_id UUID REFERENCES boq_items(id),
    item_description TEXT NOT NULL, -- Denormalized for cross-tender comparison
    uom VARCHAR(50) NOT NULL,
    normalized_unit_rate DECIMAL(18,4) NOT NULL,
    normalized_currency VARCHAR(3) NOT NULL,
    quantity DECIMAL(18,4),
    total_amount DECIMAL(18,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_vendor_item_rates_snapshot ON vendor_item_rates(snapshot_id);
CREATE INDEX idx_vendor_item_rates_description ON vendor_item_rates USING gin(to_tsvector('english', item_description));

-- =============================================
-- TECHNICAL EVALUATION
-- =============================================
CREATE TABLE evaluation_panels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    panelist_user_id UUID NOT NULL REFERENCES users(id),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    CONSTRAINT uq_panel_member UNIQUE (tender_id, panelist_user_id)
);

CREATE TABLE technical_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    bidder_id UUID NOT NULL REFERENCES bidders(id),
    panelist_user_id UUID NOT NULL REFERENCES users(id),
    criterion_id UUID NOT NULL REFERENCES evaluation_criteria(id),
    score DECIMAL(4,1) NOT NULL, -- 0-10 scale
    comment TEXT,
    is_draft BOOLEAN NOT NULL DEFAULT true,
    submitted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT chk_score_range CHECK (score >= 0 AND score <= 10),
    CONSTRAINT uq_tech_score UNIQUE (tender_id, bidder_id, panelist_user_id, criterion_id)
);

CREATE INDEX idx_tech_scores_tender ON technical_scores(tender_id);
CREATE INDEX idx_tech_scores_bidder ON technical_scores(tender_id, bidder_id);

-- =============================================
-- EVALUATION STATE
-- =============================================
CREATE TABLE evaluation_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE UNIQUE,
    scoring_method VARCHAR(20) NOT NULL DEFAULT 'Numeric', -- Numeric (0-10), Star (1-5)
    blind_mode BOOLEAN NOT NULL DEFAULT true,
    technical_evaluation_deadline TIMESTAMPTZ,
    technical_scores_locked BOOLEAN NOT NULL DEFAULT false,
    technical_locked_at TIMESTAMPTZ,
    technical_locked_by UUID REFERENCES users(id),
    commercial_scores_calculated BOOLEAN NOT NULL DEFAULT false,
    combined_scores_calculated BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================
-- COMMERCIAL SCORES (Auto-calculated)
-- =============================================
CREATE TABLE commercial_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    bidder_id UUID NOT NULL REFERENCES bidders(id),
    normalized_total_price DECIMAL(18,2) NOT NULL,
    commercial_score DECIMAL(6,2) NOT NULL, -- (Lowest / This) × 100
    rank INTEGER NOT NULL,
    include_provisional_sums BOOLEAN NOT NULL DEFAULT false,
    include_alternates BOOLEAN NOT NULL DEFAULT false,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_commercial_score UNIQUE (tender_id, bidder_id)
);

-- =============================================
-- COMBINED SCORECARD
-- =============================================
CREATE TABLE combined_scorecards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    bidder_id UUID NOT NULL REFERENCES bidders(id),
    technical_score_avg DECIMAL(6,2) NOT NULL,
    technical_rank INTEGER NOT NULL,
    commercial_score DECIMAL(6,2) NOT NULL,
    commercial_rank INTEGER NOT NULL,
    technical_weight INTEGER NOT NULL,
    commercial_weight INTEGER NOT NULL,
    combined_score DECIMAL(6,2) NOT NULL,
    final_rank INTEGER NOT NULL,
    is_recommended BOOLEAN NOT NULL DEFAULT false,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_combined_score UNIQUE (tender_id, bidder_id)
);

-- =============================================
-- EXCEPTIONS / RISK REGISTER
-- =============================================
CREATE TABLE bid_exceptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE,
    bidder_id UUID NOT NULL REFERENCES bidders(id),
    exception_type VARCHAR(50) NOT NULL, -- Technical, Commercial, Contractual
    description TEXT NOT NULL,
    cost_impact DECIMAL(18,2),
    time_impact_days INTEGER,
    risk_level VARCHAR(10) NOT NULL, -- High, Medium, Low
    mitigation TEXT,
    logged_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================
-- APPROVAL WORKFLOW
-- =============================================
CREATE TABLE approval_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID NOT NULL REFERENCES tenders(id) ON DELETE CASCADE UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending', -- Pending, InProgress, Approved, Rejected, RevisionNeeded
    initiated_by UUID NOT NULL REFERENCES users(id),
    initiated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    award_pack_pdf_path VARCHAR(1000),
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE approval_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES approval_workflows(id) ON DELETE CASCADE,
    level_number INTEGER NOT NULL,
    approver_user_id UUID NOT NULL REFERENCES users(id),
    deadline TIMESTAMPTZ,
    
    -- Decision
    decision VARCHAR(50), -- Approve, Reject, ReturnForRevision
    decision_comment TEXT,
    decided_at TIMESTAMPTZ,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'Waiting', -- Waiting, Active, Approved, Rejected, Returned
    notified_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_approval_level UNIQUE (workflow_id, level_number)
);

-- =============================================
-- AUDIT LOG
-- =============================================
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    user_email VARCHAR(255),
    action VARCHAR(100) NOT NULL, -- e.g., "Tender.Created", "Bid.Submitted", "Score.Locked"
    entity_type VARCHAR(100) NOT NULL, -- e.g., "Tender", "BidSubmission", "TechnicalScore"
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);

-- =============================================
-- EMAIL LOG
-- =============================================
CREATE TABLE email_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_id UUID REFERENCES tenders(id),
    recipient_email VARCHAR(255) NOT NULL,
    recipient_name VARCHAR(200),
    email_type VARCHAR(100) NOT NULL, -- TenderInvitation, AddendumNotice, ClarificationBulletin, DeadlineReminder, BidReceipt
    subject VARCHAR(500) NOT NULL,
    body TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending', -- Pending, Sent, Failed, Bounced
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================
-- NOTIFICATION PREFERENCES
-- =============================================
CREATE TABLE notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    tender_invitation BOOLEAN NOT NULL DEFAULT true,
    addendum_issued BOOLEAN NOT NULL DEFAULT true,
    clarification_published BOOLEAN NOT NULL DEFAULT true,
    deadline_reminder_3days BOOLEAN NOT NULL DEFAULT true,
    deadline_reminder_1day BOOLEAN NOT NULL DEFAULT true,
    approval_request BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================
-- SYSTEM SETTINGS
-- =============================================
CREATE TABLE system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    setting_type VARCHAR(50) NOT NULL DEFAULT 'String', -- String, Integer, Boolean, Json
    description TEXT,
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed settings:
-- (default_currency, AED, String, Default currency for new tenders)
-- (default_bid_validity_days, 90, Integer, Default bid validity period)
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
      - Jwt__Secret=your-super-secret-key-at-least-32-characters
      - Jwt__Issuer=bayan-api
      - Jwt__Audience=bayan-app
      - Smtp__Host=mailhog
      - Smtp__Port=1025
    depends_on:
      - db
      - redis
      - minio

  ui:
    build: ./frontend
    container_name: bayan-ui
    ports:
      - "4200:80"
    depends_on:
      - api

  db:
    image: postgres:16-alpine
    container_name: bayan-postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: bayan
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    container_name: bayan-redis
    ports:
      - "6379:6379"

  minio:
    image: minio/minio:latest
    container_name: bayan-minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: minio123
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

  mailhog:
    image: mailhog/mailhog:latest
    container_name: bayan-mailhog
    ports:
      - "1025:1025"
      - "8025:8025"

volumes:
  postgres_data:
  minio_data:
```

---

*End of Bayan Tender Management System PRD*
*Optimized for Claude Code autonomous implementation*
*All features, APIs, data models, and tests fully specified*
