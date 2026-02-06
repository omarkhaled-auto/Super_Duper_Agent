using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Portal.DTOs;

/// <summary>
/// Data transfer object for addenda displayed in the bidder portal.
/// </summary>
public class PortalAddendumDto
{
    /// <summary>
    /// Addendum unique identifier.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Addendum number (sequential within tender).
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
    /// Whether this addendum extends the submission deadline.
    /// </summary>
    public bool ExtendsDeadline { get; set; }

    /// <summary>
    /// New submission deadline (if extended).
    /// </summary>
    public DateTime? NewDeadline { get; set; }

    /// <summary>
    /// Current status of the addendum.
    /// </summary>
    public AddendumStatus Status { get; set; }

    /// <summary>
    /// Whether the current bidder has acknowledged this addendum.
    /// </summary>
    public bool IsAcknowledged { get; set; }

    /// <summary>
    /// When the bidder acknowledged the addendum.
    /// </summary>
    public DateTime? AcknowledgedAt { get; set; }
}
