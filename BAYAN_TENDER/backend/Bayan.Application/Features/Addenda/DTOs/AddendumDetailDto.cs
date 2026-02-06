using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Addenda.DTOs;

/// <summary>
/// Data transfer object for detailed addendum information including acknowledgments.
/// </summary>
public class AddendumDetailDto
{
    /// <summary>
    /// Unique identifier of the addendum.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// ID of the tender this addendum belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Title of the tender.
    /// </summary>
    public string TenderTitle { get; set; } = string.Empty;

    /// <summary>
    /// Reference number of the tender.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;

    /// <summary>
    /// Sequential addendum number within the tender.
    /// </summary>
    public int AddendumNumber { get; set; }

    /// <summary>
    /// Date the addendum was issued.
    /// </summary>
    public DateTime IssueDate { get; set; }

    /// <summary>
    /// Summary of changes in this addendum.
    /// </summary>
    public string Summary { get; set; } = string.Empty;

    /// <summary>
    /// Current status of the addendum.
    /// </summary>
    public AddendumStatus Status { get; set; }

    /// <summary>
    /// Status display name.
    /// </summary>
    public string StatusName => Status.ToString();

    /// <summary>
    /// Whether this addendum extends the submission deadline.
    /// </summary>
    public bool ExtendsDeadline { get; set; }

    /// <summary>
    /// New submission deadline (if extended).
    /// </summary>
    public DateTime? NewDeadline { get; set; }

    /// <summary>
    /// When the addendum was created.
    /// </summary>
    public DateTime CreatedAt { get; set; }

    /// <summary>
    /// When the addendum was issued.
    /// </summary>
    public DateTime? IssuedAt { get; set; }

    /// <summary>
    /// Name of the user who issued the addendum.
    /// </summary>
    public string? IssuedByName { get; set; }

    /// <summary>
    /// List of acknowledgments from bidders.
    /// </summary>
    public List<AddendumAcknowledgmentDto> Acknowledgments { get; set; } = new();

    /// <summary>
    /// Total number of bidders who should acknowledge.
    /// </summary>
    public int TotalBidders { get; set; }

    /// <summary>
    /// Number of bidders who have acknowledged.
    /// </summary>
    public int AcknowledgedCount { get; set; }

    /// <summary>
    /// Percentage of bidders who have acknowledged.
    /// </summary>
    public double AcknowledgmentPercentage =>
        TotalBidders > 0 ? (double)AcknowledgedCount / TotalBidders * 100 : 0;
}
