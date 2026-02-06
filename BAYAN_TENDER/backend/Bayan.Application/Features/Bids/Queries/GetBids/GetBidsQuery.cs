using Bayan.Application.Common.Models;
using Bayan.Application.Features.Bids.DTOs;
using Bayan.Domain.Enums;
using MediatR;

namespace Bayan.Application.Features.Bids.Queries.GetBids;

/// <summary>
/// Query for retrieving a paginated list of bids for a tender.
/// </summary>
public class GetBidsQuery : IRequest<PaginatedList<BidListDto>>
{
    /// <summary>
    /// ID of the tender to get bids for.
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
    /// Optional filter by bid status.
    /// </summary>
    public BidSubmissionStatus? Status { get; set; }

    /// <summary>
    /// Optional filter by late submissions.
    /// </summary>
    public bool? IsLate { get; set; }

    /// <summary>
    /// Optional filter by late acceptance status.
    /// </summary>
    public bool? LateAccepted { get; set; }

    /// <summary>
    /// Optional search term for filtering by bidder name.
    /// </summary>
    public string? Search { get; set; }

    /// <summary>
    /// Sort field (default: SubmissionTime).
    /// </summary>
    public string SortBy { get; set; } = "SubmissionTime";

    /// <summary>
    /// Sort direction (default: descending).
    /// </summary>
    public bool SortDescending { get; set; } = true;
}
