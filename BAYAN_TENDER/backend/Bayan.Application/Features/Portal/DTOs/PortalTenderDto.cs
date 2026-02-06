using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Portal.DTOs;

/// <summary>
/// Data transfer object for tender information displayed in the bidder portal.
/// </summary>
public class PortalTenderDto
{
    /// <summary>
    /// Tender unique identifier.
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
    /// Current status of the tender.
    /// </summary>
    public TenderStatus Status { get; set; }

    /// <summary>
    /// Display name for the status.
    /// </summary>
    public string StatusDisplay { get; set; } = string.Empty;

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
    /// Days remaining until submission deadline.
    /// </summary>
    public int DaysUntilSubmission { get; set; }

    /// <summary>
    /// Hours remaining until submission deadline (within last day).
    /// </summary>
    public int HoursUntilSubmission { get; set; }

    /// <summary>
    /// Whether the clarification deadline has passed.
    /// </summary>
    public bool IsClarificationClosed { get; set; }

    /// <summary>
    /// Whether the submission deadline has passed.
    /// </summary>
    public bool IsSubmissionClosed { get; set; }

    /// <summary>
    /// Base currency for the tender (ISO 4217 code).
    /// </summary>
    public string BaseCurrency { get; set; } = "AED";

    /// <summary>
    /// Number of days the bid is valid.
    /// </summary>
    public int BidValidityDays { get; set; }

    /// <summary>
    /// Tender description.
    /// </summary>
    public string? Description { get; set; }
}
