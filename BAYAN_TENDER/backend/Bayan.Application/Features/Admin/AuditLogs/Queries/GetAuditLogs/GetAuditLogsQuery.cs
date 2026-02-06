namespace Bayan.Application.Features.Admin.AuditLogs.Queries.GetAuditLogs;

using Bayan.Application.Common.Models;
using Bayan.Application.Features.Admin.AuditLogs.DTOs;
using MediatR;

/// <summary>
/// Query to retrieve paginated and filtered audit logs.
/// </summary>
public record GetAuditLogsQuery : IRequest<PaginatedList<AuditLogDto>>
{
    /// <summary>
    /// Page number (1-based). Default is 1.
    /// </summary>
    public int Page { get; init; } = 1;

    /// <summary>
    /// Number of items per page. Default is 20.
    /// </summary>
    public int PageSize { get; init; } = 20;

    /// <summary>
    /// Filter by user ID.
    /// </summary>
    public Guid? UserId { get; init; }

    /// <summary>
    /// Filter by action type (e.g., "Created", "Updated", "Deleted").
    /// </summary>
    public string? Action { get; init; }

    /// <summary>
    /// Filter by entity type (e.g., "Tender", "Bid", "User").
    /// </summary>
    public string? EntityType { get; init; }

    /// <summary>
    /// Filter by specific entity ID.
    /// </summary>
    public Guid? EntityId { get; init; }

    /// <summary>
    /// Filter by start date (inclusive).
    /// </summary>
    public DateTime? StartDate { get; init; }

    /// <summary>
    /// Filter by end date (inclusive).
    /// </summary>
    public DateTime? EndDate { get; init; }

    /// <summary>
    /// Search term for filtering by user email or action.
    /// </summary>
    public string? Search { get; init; }
}
