using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Common.Interfaces;

/// <summary>
/// Interface for the application database context.
/// </summary>
public interface IApplicationDbContext
{
    /// <summary>
    /// Gets the Users DbSet.
    /// </summary>
    DbSet<User> Users { get; }

    /// <summary>
    /// Gets the RefreshTokens DbSet.
    /// </summary>
    DbSet<RefreshToken> RefreshTokens { get; }

    /// <summary>
    /// Gets the Clients DbSet.
    /// </summary>
    DbSet<Client> Clients { get; }

    /// <summary>
    /// Gets the SystemSettings DbSet.
    /// </summary>
    DbSet<SystemSetting> SystemSettings { get; }

    /// <summary>
    /// Gets the UnitsOfMeasure DbSet.
    /// </summary>
    DbSet<UnitOfMeasure> UnitsOfMeasure { get; }

    /// <summary>
    /// Gets the Tenders DbSet.
    /// </summary>
    DbSet<Tender> Tenders { get; }

    /// <summary>
    /// Gets the EvaluationCriteria DbSet.
    /// </summary>
    DbSet<EvaluationCriteria> EvaluationCriteria { get; }

    /// <summary>
    /// Gets the TenderBidders DbSet.
    /// </summary>
    DbSet<TenderBidder> TenderBidders { get; }

    /// <summary>
    /// Gets the Bidders DbSet.
    /// </summary>
    DbSet<Bidder> Bidders { get; }

    /// <summary>
    /// Gets the BidSubmissions DbSet.
    /// </summary>
    DbSet<BidSubmission> BidSubmissions { get; }

    /// <summary>
    /// Gets the BidDocuments DbSet.
    /// </summary>
    DbSet<BidDocument> BidDocuments { get; }

    /// <summary>
    /// Gets the Clarifications DbSet.
    /// </summary>
    DbSet<Clarification> Clarifications { get; }

    /// <summary>
    /// Gets the ClarificationBulletins DbSet.
    /// </summary>
    DbSet<ClarificationBulletin> ClarificationBulletins { get; }

    /// <summary>
    /// Gets the ClarificationAttachments DbSet.
    /// </summary>
    DbSet<ClarificationAttachment> ClarificationAttachments { get; }

    /// <summary>
    /// Gets the Addenda DbSet.
    /// </summary>
    DbSet<Addendum> Addenda { get; }

    /// <summary>
    /// Gets the Documents DbSet.
    /// </summary>
    DbSet<Document> Documents { get; }

    /// <summary>
    /// Gets the AddendumAcknowledgments DbSet.
    /// </summary>
    DbSet<AddendumAcknowledgment> AddendumAcknowledgments { get; }

    /// <summary>
    /// Gets the EmailLogs DbSet.
    /// </summary>
    DbSet<EmailLog> EmailLogs { get; }

    /// <summary>
    /// Gets the BoqSections DbSet.
    /// </summary>
    DbSet<BoqSection> BoqSections { get; }

    /// <summary>
    /// Gets the BoqItems DbSet.
    /// </summary>
    DbSet<BoqItem> BoqItems { get; }

    /// <summary>
    /// Gets the UomMasters DbSet.
    /// </summary>
    DbSet<UomMaster> UomMasters { get; }

    /// <summary>
    /// Gets the BidderRefreshTokens DbSet.
    /// </summary>
    DbSet<BidderRefreshToken> BidderRefreshTokens { get; }

    /// <summary>
    /// Gets the AuditLogs DbSet.
    /// </summary>
    DbSet<AuditLog> AuditLogs { get; }

    /// <summary>
    /// Gets the BidPricings DbSet.
    /// </summary>
    DbSet<BidPricing> BidPricings { get; }

    /// <summary>
    /// Gets the VendorPricingSnapshots DbSet.
    /// </summary>
    DbSet<VendorPricingSnapshot> VendorPricingSnapshots { get; }

    /// <summary>
    /// Gets the VendorItemRates DbSet.
    /// </summary>
    DbSet<VendorItemRate> VendorItemRates { get; }

    /// <summary>
    /// Gets the EvaluationPanels DbSet.
    /// </summary>
    DbSet<EvaluationPanel> EvaluationPanels { get; }

    /// <summary>
    /// Gets the TechnicalScores DbSet.
    /// </summary>
    DbSet<TechnicalScore> TechnicalScores { get; }

    /// <summary>
    /// Gets the EvaluationStates DbSet.
    /// </summary>
    DbSet<EvaluationState> EvaluationStates { get; }

    /// <summary>
    /// Gets the CommercialScores DbSet.
    /// </summary>
    DbSet<CommercialScore> CommercialScores { get; }

    /// <summary>
    /// Gets the CombinedScorecards DbSet.
    /// </summary>
    DbSet<CombinedScorecard> CombinedScorecards { get; }

    /// <summary>
    /// Gets the BidExceptions DbSet.
    /// </summary>
    DbSet<BidException> BidExceptions { get; }

    /// <summary>
    /// Gets the ApprovalWorkflows DbSet.
    /// </summary>
    DbSet<ApprovalWorkflow> ApprovalWorkflows { get; }

    /// <summary>
    /// Gets the ApprovalLevels DbSet.
    /// </summary>
    DbSet<ApprovalLevel> ApprovalLevels { get; }

    /// <summary>
    /// Gets the NotificationPreferences DbSet.
    /// </summary>
    DbSet<NotificationPreference> NotificationPreferences { get; }

    /// <summary>
    /// Saves changes to the database.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Number of state entries written to the database.</returns>
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
}
