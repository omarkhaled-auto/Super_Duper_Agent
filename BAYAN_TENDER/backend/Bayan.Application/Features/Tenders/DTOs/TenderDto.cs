using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Tenders.DTOs;

/// <summary>
/// Data transfer object for Tender entity (list view).
/// </summary>
public class TenderDto
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
    /// Base currency for the tender.
    /// </summary>
    public string BaseCurrency { get; set; } = string.Empty;

    /// <summary>
    /// Estimated value of the tender.
    /// </summary>
    public decimal? EstimatedValue { get; set; }

    /// <summary>
    /// Current status of the tender.
    /// </summary>
    public TenderStatus Status { get; set; }

    /// <summary>
    /// Pricing level for the BOQ hierarchy.
    /// </summary>
    public PricingLevel PricingLevel { get; set; }

    /// <summary>
    /// Deadline for bid submissions.
    /// </summary>
    public DateTime SubmissionDeadline { get; set; }

    /// <summary>
    /// Number of invited bidders.
    /// </summary>
    public int BidderCount { get; set; }

    /// <summary>
    /// Number of bids received.
    /// </summary>
    public int BidCount { get; set; }

    /// <summary>
    /// Timestamp when the tender was created.
    /// </summary>
    public DateTime CreatedAt { get; set; }
}
