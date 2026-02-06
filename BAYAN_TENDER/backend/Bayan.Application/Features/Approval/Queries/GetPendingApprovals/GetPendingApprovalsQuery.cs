using Bayan.Application.Common.Models;
using Bayan.Application.Features.Approval.DTOs;
using MediatR;

namespace Bayan.Application.Features.Approval.Queries.GetPendingApprovals;

/// <summary>
/// Query to get pending approvals for the current user (for dashboard).
/// </summary>
public record GetPendingApprovalsQuery : IRequest<PaginatedList<PendingApprovalDto>>
{
    /// <summary>
    /// Page number (1-based). Default is 1.
    /// </summary>
    public int Page { get; init; } = 1;

    /// <summary>
    /// Number of items per page. Default is 10.
    /// </summary>
    public int PageSize { get; init; } = 10;

    /// <summary>
    /// Optional: Get pending approvals for a specific user ID.
    /// If null, returns pending approvals for the current authenticated user.
    /// </summary>
    public Guid? UserId { get; init; }

    /// <summary>
    /// Optional: Search term to filter by tender reference or title.
    /// </summary>
    public string? Search { get; init; }

    /// <summary>
    /// Optional: Filter to show only overdue items.
    /// </summary>
    public bool? OverdueOnly { get; init; }
}
