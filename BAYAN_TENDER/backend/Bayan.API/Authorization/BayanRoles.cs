using Bayan.Domain.Enums;

namespace Bayan.API.Authorization;

/// <summary>
/// Centralized role groupings for API authorization.
/// Keep these aligned with BAYAN_SPECIFICATIONS_CONDENSED.md "User Roles and Permissions".
/// </summary>
public static class BayanRoles
{
    public const string Admin = nameof(UserRole.Admin);
    public const string TenderManager = nameof(UserRole.TenderManager);
    public const string CommercialAnalyst = nameof(UserRole.CommercialAnalyst);
    public const string TechnicalPanelist = nameof(UserRole.TechnicalPanelist);
    public const string Approver = nameof(UserRole.Approver);
    public const string Auditor = nameof(UserRole.Auditor);
    public const string Bidder = nameof(UserRole.Bidder);

    // All internal (non-portal) users.
    public const string InternalUsers =
        Admin + "," +
        TenderManager + "," +
        CommercialAnalyst + "," +
        TechnicalPanelist + "," +
        Approver + "," +
        Auditor;

    // Tender lifecycle operations (create/edit/publish/cancel/invite/addenda/docs/clarifications)
    public const string TenderLifecycleManagers = Admin + "," + TenderManager;

    // BOQ can be handled by commercial analyst as well.
    public const string BoqManagers = Admin + "," + TenderManager + "," + CommercialAnalyst;

    // Bid import/analysis can be handled by commercial analyst as well.
    public const string BidImporters = Admin + "," + TenderManager + "," + CommercialAnalyst;

    // Evaluation read views (comparable sheet + combined scorecard)
    public const string EvaluationViewers = Admin + "," + TenderManager + "," + CommercialAnalyst + "," + Approver + "," + Auditor;

    // Evaluation write actions (recalculate, calculate scores, add exceptions)
    public const string EvaluationEditors = Admin + "," + TenderManager + "," + CommercialAnalyst;

    // Technical evaluation setup is owned by tender lifecycle managers.
    public const string TechnicalEvaluationSetup = TenderLifecycleManagers;

    // Technical scoring is restricted to panelists.
    public const string TechnicalScorers = TechnicalPanelist;

    // Technical scores (matrix/summary) can be viewed by approvers/auditors but not commercial analysts.
    public const string TechnicalScoresViewers = Admin + "," + TenderManager + "," + TechnicalPanelist + "," + Approver + "," + Auditor;

    // Locking is restricted to tender lifecycle managers.
    public const string TechnicalScoresLockers = TenderLifecycleManagers;

    public const string ApprovalInitiators = TenderLifecycleManagers;
    public const string ApprovalDeciders = Approver;

    public const string AuditLogViewers = Admin + "," + Auditor;

    public const string VendorPricingViewers = Admin + "," + TenderManager + "," + CommercialAnalyst + "," + Auditor;
}
