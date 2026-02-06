using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Tenders.DTOs;

/// <summary>
/// Optimized data transfer object for tender list queries.
/// Contains only essential fields for list display.
/// </summary>
public class TenderListDto
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
    /// Client name.
    /// </summary>
    public string ClientName { get; set; } = string.Empty;

    /// <summary>
    /// Type of tender procedure.
    /// </summary>
    public TenderType TenderType { get; set; }

    /// <summary>
    /// Current status of the tender.
    /// </summary>
    public TenderStatus Status { get; set; }

    /// <summary>
    /// Deadline for bid submissions.
    /// </summary>
    public DateTime SubmissionDeadline { get; set; }

    /// <summary>
    /// Number of invited bidders.
    /// </summary>
    public int BidderCount { get; set; }

    /// <summary>
    /// Days remaining until submission deadline.
    /// Negative values indicate the deadline has passed.
    /// </summary>
    public int DaysRemaining { get; set; }

    /// <summary>
    /// Timestamp when the tender was created.
    /// </summary>
    public DateTime CreatedAt { get; set; }
}
