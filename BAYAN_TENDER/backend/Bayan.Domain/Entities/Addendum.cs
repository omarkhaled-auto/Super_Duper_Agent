using Bayan.Domain.Common;
using Bayan.Domain.Enums;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents an addendum to a tender.
/// </summary>
public class Addendum : BaseEntity
{
    /// <summary>
    /// Tender this addendum belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

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
    public AddendumStatus Status { get; set; } = AddendumStatus.Draft;

    /// <summary>
    /// User who issued the addendum.
    /// </summary>
    public Guid? IssuedBy { get; set; }

    /// <summary>
    /// When the addendum was issued.
    /// </summary>
    public DateTime? IssuedAt { get; set; }

    // Navigation properties
    /// <summary>
    /// Tender associated with this addendum.
    /// </summary>
    public virtual Tender Tender { get; set; } = null!;

    /// <summary>
    /// User who issued the addendum.
    /// </summary>
    public virtual User? Issuer { get; set; }

    /// <summary>
    /// Acknowledgments from bidders.
    /// </summary>
    public virtual ICollection<AddendumAcknowledgment> Acknowledgments { get; set; } = new List<AddendumAcknowledgment>();
}
