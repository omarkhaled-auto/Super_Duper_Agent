namespace Bayan.Application.Features.Admin.AuditLogs.DTOs;

/// <summary>
/// Data transfer object for audit log entries.
/// </summary>
public record AuditLogDto
{
    /// <summary>
    /// Unique identifier.
    /// </summary>
    public Guid Id { get; init; }

    /// <summary>
    /// Timestamp when the action occurred.
    /// </summary>
    public DateTime Timestamp { get; init; }

    /// <summary>
    /// User ID who performed the action.
    /// </summary>
    public Guid? UserId { get; init; }

    /// <summary>
    /// Email of the user who performed the action.
    /// </summary>
    public string? UserEmail { get; init; }

    /// <summary>
    /// Full name of the user who performed the action.
    /// </summary>
    public string? UserFullName { get; init; }

    /// <summary>
    /// Action performed (e.g., "Tender.Created", "Bid.Submitted").
    /// </summary>
    public string Action { get; init; } = string.Empty;

    /// <summary>
    /// Type of entity affected.
    /// </summary>
    public string EntityType { get; init; } = string.Empty;

    /// <summary>
    /// ID of the entity affected.
    /// </summary>
    public Guid? EntityId { get; init; }

    /// <summary>
    /// Previous values as JSON.
    /// </summary>
    public string? OldValues { get; init; }

    /// <summary>
    /// New values as JSON.
    /// </summary>
    public string? NewValues { get; init; }

    /// <summary>
    /// IP address of the request.
    /// </summary>
    public string? IpAddress { get; init; }

    /// <summary>
    /// User agent of the request.
    /// </summary>
    public string? UserAgent { get; init; }
}
