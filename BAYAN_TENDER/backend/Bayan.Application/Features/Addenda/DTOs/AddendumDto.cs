using Bayan.Domain.Enums;

namespace Bayan.Application.Features.Addenda.DTOs;

/// <summary>
/// Data transfer object for addendum summary information.
/// </summary>
public class AddendumDto
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
}
