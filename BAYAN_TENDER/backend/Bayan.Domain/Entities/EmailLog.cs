using Bayan.Domain.Common;
using Bayan.Domain.Enums;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents an email log entry.
/// </summary>
public class EmailLog : BaseEntity
{
    /// <summary>
    /// Related tender (if applicable).
    /// </summary>
    public Guid? TenderId { get; set; }

    /// <summary>
    /// Recipient email address.
    /// </summary>
    public string RecipientEmail { get; set; } = string.Empty;

    /// <summary>
    /// Recipient name.
    /// </summary>
    public string? RecipientName { get; set; }

    /// <summary>
    /// Type of email.
    /// </summary>
    public EmailType EmailType { get; set; }

    /// <summary>
    /// Email subject.
    /// </summary>
    public string Subject { get; set; } = string.Empty;

    /// <summary>
    /// Email body.
    /// </summary>
    public string? Body { get; set; }

    /// <summary>
    /// Email status.
    /// </summary>
    public EmailStatus Status { get; set; } = EmailStatus.Pending;

    /// <summary>
    /// When the email was sent.
    /// </summary>
    public DateTime? SentAt { get; set; }

    /// <summary>
    /// Error message if failed.
    /// </summary>
    public string? ErrorMessage { get; set; }

    // Navigation properties
    /// <summary>
    /// Tender associated with this email.
    /// </summary>
    public virtual Tender? Tender { get; set; }
}
