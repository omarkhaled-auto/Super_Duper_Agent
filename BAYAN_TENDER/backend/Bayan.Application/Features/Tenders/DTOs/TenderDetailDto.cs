using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Tenders.DTOs;

/// <summary>
/// Data transfer object for Tender entity with full details including bidders and criteria.
/// </summary>
public class TenderDetailDto
{
    /// <summary>
    /// Unique identifier for the tender.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Tender title.
    /// </summary>
    public string Title { get; set; } = string.Empty;

    /// <summary>
    /// Unique tender reference number.
    /// </summary>
    public string Reference { get; set; } = string.Empty;

    /// <summary>
    /// Tender description.
    /// </summary>
    public string? Description { get; set; }

    /// <summary>
    /// Client ID.
    /// </summary>
    public Guid ClientId { get; set; }

    /// <summary>
    /// Client name.
    /// </summary>
    public string ClientName { get; set; } = string.Empty;

    /// <summary>
    /// Type of tender procedure.
    /// </summary>
    public TenderType TenderType { get; set; }

    /// <summary>
    /// Base currency for the tender (ISO 4217 code).
    /// </summary>
    public string BaseCurrency { get; set; } = string.Empty;

    /// <summary>
    /// Estimated value of the tender.
    /// </summary>
    public decimal? EstimatedValue { get; set; }

    /// <summary>
    /// Number of days the bid is valid.
    /// </summary>
    public int BidValidityDays { get; set; }

    /// <summary>
    /// Date the tender was issued.
    /// </summary>
    public DateTime IssueDate { get; set; }

    /// <summary>
    /// Deadline for clarification questions.
    /// </summary>
    public DateTime ClarificationDeadline { get; set; }

    /// <summary>
    /// Deadline for bid submissions.
    /// </summary>
    public DateTime SubmissionDeadline { get; set; }

    /// <summary>
    /// Date when bids will be opened.
    /// </summary>
    public DateTime OpeningDate { get; set; }

    /// <summary>
    /// Weight for technical evaluation (percentage).
    /// </summary>
    public int TechnicalWeight { get; set; }

    /// <summary>
    /// Weight for commercial evaluation (percentage).
    /// </summary>
    public int CommercialWeight { get; set; }

    /// <summary>
    /// Pricing level for the BOQ hierarchy.
    /// </summary>
    public PricingLevel PricingLevel { get; set; }

    /// <summary>
    /// Current status of the tender.
    /// </summary>
    public TenderStatus Status { get; set; }

    /// <summary>
    /// When the tender was published.
    /// </summary>
    public DateTime? PublishedAt { get; set; }

    /// <summary>
    /// When the tender was awarded.
    /// </summary>
    public DateTime? AwardedAt { get; set; }

    /// <summary>
    /// User who created the tender.
    /// </summary>
    public Guid? CreatedBy { get; set; }

    /// <summary>
    /// Name of user who created the tender.
    /// </summary>
    public string? CreatedByName { get; set; }

    /// <summary>
    /// Timestamp when the tender was created.
    /// </summary>
    public DateTime CreatedAt { get; set; }

    /// <summary>
    /// Timestamp when the tender was last updated.
    /// </summary>
    public DateTime? UpdatedAt { get; set; }

    /// <summary>
    /// Evaluation criteria for this tender.
    /// </summary>
    public List<EvaluationCriterionDto> EvaluationCriteria { get; set; } = new();

    /// <summary>
    /// Bidders invited to this tender.
    /// </summary>
    public List<TenderBidderDto> Bidders { get; set; } = new();

    /// <summary>
    /// Number of bid submissions received.
    /// </summary>
    public int BidCount { get; set; }

    /// <summary>
    /// Number of documents attached.
    /// </summary>
    public int DocumentCount { get; set; }

    /// <summary>
    /// Number of clarifications.
    /// </summary>
    public int ClarificationCount { get; set; }
}
