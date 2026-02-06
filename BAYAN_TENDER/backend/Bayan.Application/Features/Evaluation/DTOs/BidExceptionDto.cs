using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Evaluation.DTOs;

/// <summary>
/// DTO for a bid exception.
/// </summary>
public class BidExceptionDto
{
    /// <summary>
    /// Exception ID.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bidder ID.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Bidder company name.
    /// </summary>
    public string BidderCompanyName { get; set; } = string.Empty;

    /// <summary>
    /// Type of exception.
    /// </summary>
    public ExceptionType ExceptionType { get; set; }

    /// <summary>
    /// Type of exception as string.
    /// </summary>
    public string ExceptionTypeName => ExceptionType.ToString();

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
    /// Risk level as string.
    /// </summary>
    public string RiskLevelName => RiskLevel.ToString();

    /// <summary>
    /// Mitigation strategy.
    /// </summary>
    public string? Mitigation { get; set; }

    /// <summary>
    /// User who logged the exception.
    /// </summary>
    public Guid LoggedBy { get; set; }

    /// <summary>
    /// Name of user who logged the exception.
    /// </summary>
    public string LoggedByName { get; set; } = string.Empty;

    /// <summary>
    /// When the exception was created.
    /// </summary>
    public DateTime CreatedAt { get; set; }
}

/// <summary>
/// DTO for creating a new bid exception.
/// </summary>
public class CreateBidExceptionDto
{
    /// <summary>
    /// Bidder ID the exception is for.
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
    /// Cost impact of the exception (optional).
    /// </summary>
    public decimal? CostImpact { get; set; }

    /// <summary>
    /// Time impact in days (optional).
    /// </summary>
    public int? TimeImpactDays { get; set; }

    /// <summary>
    /// Risk level.
    /// </summary>
    public RiskLevel RiskLevel { get; set; }

    /// <summary>
    /// Mitigation strategy (optional).
    /// </summary>
    public string? Mitigation { get; set; }
}

/// <summary>
/// DTO for the list of bid exceptions.
/// </summary>
public class BidExceptionListDto
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// List of exceptions.
    /// </summary>
    public List<BidExceptionDto> Exceptions { get; set; } = new();

    /// <summary>
    /// Summary by risk level.
    /// </summary>
    public Dictionary<string, int> CountByRiskLevel { get; set; } = new();

    /// <summary>
    /// Summary by exception type.
    /// </summary>
    public Dictionary<string, int> CountByType { get; set; } = new();

    /// <summary>
    /// Total cost impact.
    /// </summary>
    public decimal TotalCostImpact { get; set; }
}
