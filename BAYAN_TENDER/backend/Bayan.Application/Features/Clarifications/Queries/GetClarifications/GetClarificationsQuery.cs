using Bayan.Application.Common.Models;
using Bayan.Application.Features.Clarifications.DTOs;
using Bayan.Domain.Enums;
using MediatR;

namespace Bayan.Application.Features.Clarifications.Queries.GetClarifications;

/// <summary>
/// Query for retrieving a paginated list of clarifications for a tender with optional filtering.
/// </summary>
public class GetClarificationsQuery : IRequest<PaginatedList<ClarificationDto>>
{
    /// <summary>
    /// ID of the tender to get clarifications for.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Page number (1-based).
    /// </summary>
    public int Page { get; set; } = 1;

    /// <summary>
    /// Number of items per page.
    /// </summary>
    public int PageSize { get; set; } = 10;

    /// <summary>
    /// Optional filter by status.
    /// </summary>
    public ClarificationStatus? Status { get; set; }

    /// <summary>
    /// Optional filter by type.
    /// </summary>
    public ClarificationType? Type { get; set; }

    /// <summary>
    /// Optional filter by BOQ section.
    /// </summary>
    public string? Section { get; set; }

    /// <summary>
    /// Optional filter by priority.
    /// </summary>
    public ClarificationPriority? Priority { get; set; }

    /// <summary>
    /// Optional filter by bidder ID.
    /// </summary>
    public Guid? BidderId { get; set; }

    /// <summary>
    /// Optional filter by assigned user ID.
    /// </summary>
    public Guid? AssignedToId { get; set; }

    /// <summary>
    /// Optional search term for subject or question.
    /// </summary>
    public string? Search { get; set; }

    /// <summary>
    /// Sort field (default: SubmittedAt).
    /// </summary>
    public string SortBy { get; set; } = "SubmittedAt";

    /// <summary>
    /// Sort direction (default: descending).
    /// </summary>
    public bool SortDescending { get; set; } = true;

    public GetClarificationsQuery()
    {
    }

    public GetClarificationsQuery(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
