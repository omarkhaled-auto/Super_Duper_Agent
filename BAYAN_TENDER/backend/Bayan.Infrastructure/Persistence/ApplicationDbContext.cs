using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Common;
using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using System.Reflection;

namespace Bayan.Infrastructure.Persistence;

/// <summary>
/// Application database context for Entity Framework Core.
/// </summary>
public class ApplicationDbContext : DbContext, IApplicationDbContext
{
    private readonly ICurrentUserService _currentUserService;

    public ApplicationDbContext(
        DbContextOptions<ApplicationDbContext> options,
        ICurrentUserService currentUserService)
        : base(options)
    {
        _currentUserService = currentUserService;
    }

    // User & Authentication
    public DbSet<User> Users => Set<User>();
    public DbSet<RefreshToken> RefreshTokens => Set<RefreshToken>();
    public DbSet<BidderRefreshToken> BidderRefreshTokens => Set<BidderRefreshToken>();

    // Clients
    public DbSet<Client> Clients => Set<Client>();

    // Tenders
    public DbSet<Tender> Tenders => Set<Tender>();
    public DbSet<EvaluationCriteria> EvaluationCriteria => Set<EvaluationCriteria>();

    // Bidders
    public DbSet<Bidder> Bidders => Set<Bidder>();
    public DbSet<TenderBidder> TenderBidders => Set<TenderBidder>();

    // Documents
    public DbSet<Document> Documents => Set<Document>();
    public DbSet<Addendum> Addenda => Set<Addendum>();
    public DbSet<AddendumAcknowledgment> AddendumAcknowledgments => Set<AddendumAcknowledgment>();

    // Clarifications
    public DbSet<Clarification> Clarifications => Set<Clarification>();
    public DbSet<ClarificationBulletin> ClarificationBulletins => Set<ClarificationBulletin>();
    public DbSet<ClarificationAttachment> ClarificationAttachments => Set<ClarificationAttachment>();

    // BOQ
    public DbSet<BoqSection> BoqSections => Set<BoqSection>();
    public DbSet<BoqItem> BoqItems => Set<BoqItem>();
    public DbSet<UomMaster> UomMasters => Set<UomMaster>();
    public DbSet<UnitOfMeasure> UnitsOfMeasure => Set<UnitOfMeasure>();

    // Bid Submissions
    public DbSet<BidSubmission> BidSubmissions => Set<BidSubmission>();
    public DbSet<BidDocument> BidDocuments => Set<BidDocument>();
    public DbSet<BidPricing> BidPricings => Set<BidPricing>();

    // Vendor Pricing
    public DbSet<VendorPricingSnapshot> VendorPricingSnapshots => Set<VendorPricingSnapshot>();
    public DbSet<VendorItemRate> VendorItemRates => Set<VendorItemRate>();

    // Evaluation
    public DbSet<EvaluationPanel> EvaluationPanels => Set<EvaluationPanel>();
    public DbSet<TechnicalScore> TechnicalScores => Set<TechnicalScore>();
    public DbSet<EvaluationState> EvaluationStates => Set<EvaluationState>();
    public DbSet<CommercialScore> CommercialScores => Set<CommercialScore>();
    public DbSet<CombinedScorecard> CombinedScorecards => Set<CombinedScorecard>();
    public DbSet<BidException> BidExceptions => Set<BidException>();

    // Approval
    public DbSet<ApprovalWorkflow> ApprovalWorkflows => Set<ApprovalWorkflow>();
    public DbSet<ApprovalLevel> ApprovalLevels => Set<ApprovalLevel>();

    // Audit & Logs
    public DbSet<AuditLog> AuditLogs => Set<AuditLog>();
    public DbSet<EmailLog> EmailLogs => Set<EmailLog>();

    // Settings
    public DbSet<NotificationPreference> NotificationPreferences => Set<NotificationPreference>();
    public DbSet<SystemSetting> SystemSettings => Set<SystemSetting>();

    public override async Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        foreach (var entry in ChangeTracker.Entries<IAuditableEntity>())
        {
            switch (entry.State)
            {
                case EntityState.Added:
                    entry.Entity.CreatedBy = _currentUserService.UserId;
                    entry.Entity.CreatedAt = DateTime.UtcNow;
                    break;

                case EntityState.Modified:
                    entry.Entity.LastModifiedBy = _currentUserService.UserId;
                    entry.Entity.LastModifiedAt = DateTime.UtcNow;
                    break;
            }
        }

        foreach (var entry in ChangeTracker.Entries<BaseEntity>())
        {
            switch (entry.State)
            {
                case EntityState.Added:
                    if (entry.Entity.Id == Guid.Empty)
                    {
                        entry.Entity.Id = Guid.NewGuid();
                    }
                    entry.Entity.CreatedAt = DateTime.UtcNow;
                    break;

                case EntityState.Modified:
                    entry.Entity.UpdatedAt = DateTime.UtcNow;
                    break;
            }
        }

        return await base.SaveChangesAsync(cancellationToken);
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Apply all configurations from the Data/Configurations folder
        modelBuilder.ApplyConfigurationsFromAssembly(Assembly.GetExecutingAssembly());
    }
}
