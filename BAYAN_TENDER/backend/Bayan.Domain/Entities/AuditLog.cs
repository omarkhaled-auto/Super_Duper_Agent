using Bayan.Domain.Common;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents an audit log entry.
/// </summary>
public class AuditLog : BaseEntity
{
    /// <summary>
    /// User who performed the action.
    /// </summary>
    public Guid? UserId { get; set; }

    /// <summary>
    /// Email of the user (denormalized).
    /// </summary>
    public string? UserEmail { get; set; }

    /// <summary>
    /// Action performed (e.g., "Tender.Created").
    /// </summary>
    public string Action { get; set; } = string.Empty;

    /// <summary>
    /// Type of entity affected.
    /// </summary>
    public string EntityType { get; set; } = string.Empty;

    /// <summary>
    /// ID of the entity affected.
    /// </summary>
    public Guid? EntityId { get; set; }

    /// <summary>
    /// Previous values as JSON.
    /// </summary>
    public string? OldValues { get; set; }

    /// <summary>
    /// New values as JSON.
    /// </summary>
    public string? NewValues { get; set; }

    /// <summary>
    /// IP address of the request.
    /// </summary>
    public string? IpAddress { get; set; }

    /// <summary>
    /// User agent of the request.
    /// </summary>
    public string? UserAgent { get; set; }

    // Navigation properties
    /// <summary>
    /// User who performed the action.
    /// </summary>
    public virtual User? User { get; set; }
}
