using Bayan.Domain.Common;
using Bayan.Domain.Enums;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents an exception/deviation logged for a bid.
/// </summary>
public class BidException : BaseEntity
{
    /// <summary>
    /// Tender this exception is for.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bidder this exception is for.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Type of exception.
    /// </summary>
    public ExceptionType ExceptionType { get; set; }

    /// <summary>
    /// Description of the exception.
    /// </summary>
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Cost impact of the exception.
    /// </summary>
    public decimal? CostImpact { get; set; }

    /// <summary>
    /// Time impact in days.
    /// </summary>
    public int? TimeImpactDays { get; set; }

    /// <summary>
    /// Risk level.
    /// </summary>
    public RiskLevel RiskLevel { get; set; }

    /// <summary>
    /// Mitigation strategy.
    /// </summary>
    public string? Mitigation { get; set; }

    /// <summary>
    /// User who logged the exception.
    /// </summary>
    public Guid LoggedBy { get; set; }

    // Navigation properties
    /// <summary>
    /// Tender associated with this exception.
    /// </summary>
    public virtual Tender Tender { get; set; } = null!;

    /// <summary>
    /// Bidder associated with this exception.
    /// </summary>
    public virtual Bidder Bidder { get; set; } = null!;

    /// <summary>
    /// User who logged the exception.
    /// </summary>
    public virtual User LoggedByUser { get; set; } = null!;
}
