using Bayan.Domain.Common;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a clarification bulletin published for a tender.
/// </summary>
public class ClarificationBulletin : BaseEntity
{
    /// <summary>
    /// Tender this bulletin belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bulletin number (sequential within tender).
    /// </summary>
    public int BulletinNumber { get; set; }

    /// <summary>
    /// Date the bulletin was issued.
    /// </summary>
    public DateTime IssueDate { get; set; }

    /// <summary>
    /// Introduction text for the bulletin.
    /// </summary>
    public string? Introduction { get; set; }

    /// <summary>
    /// Closing notes for the bulletin.
    /// </summary>
    public string? ClosingNotes { get; set; }

    /// <summary>
    /// Path to generated PDF in MinIO.
    /// </summary>
    public string? PdfPath { get; set; }

    /// <summary>
    /// User who published the bulletin.
    /// </summary>
    public Guid PublishedBy { get; set; }

    /// <summary>
    /// When the bulletin was published.
    /// </summary>
    public DateTime PublishedAt { get; set; }

    // Navigation properties
    /// <summary>
    /// Tender associated with this bulletin.
    /// </summary>
    public virtual Tender Tender { get; set; } = null!;

    /// <summary>
    /// User who published the bulletin.
    /// </summary>
    public virtual User Publisher { get; set; } = null!;

    /// <summary>
    /// Clarifications included in this bulletin.
    /// </summary>
    public virtual ICollection<Clarification> Clarifications { get; set; } = new List<Clarification>();
}
