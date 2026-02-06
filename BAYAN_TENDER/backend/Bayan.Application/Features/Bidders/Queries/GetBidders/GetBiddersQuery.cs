using Bayan.Application.Common.Models;
using Bayan.Application.Features.Bidders.DTOs;
using Bayan.Domain.Enums;
using MediatR;

namespace Bayan.Application.Features.Bidders.Queries.GetBidders;

/// <summary>
/// Query for retrieving a paginated list of bidders with filtering options.
/// </summary>
public class GetBiddersQuery : IRequest<PaginatedList<BidderDto>>
{
    /// <summary>
    /// Page number (1-based).
    /// </summary>
    public int Page { get; set; } = 1;

    /// <summary>
    /// Number of items per page.
    /// </summary>
    public int PageSize { get; set; } = 10;

    /// <summary>
    /// Optional search term for filtering by company name, contact person, or email.
    /// </summary>
    public string? Search { get; set; }

    /// <summary>
    /// Optional filter by trade specialization.
    /// </summary>
    public string? TradeSpecialization { get; set; }

    /// <summary>
    /// Optional filter by prequalification status.
    /// </summary>
    public PrequalificationStatus? PrequalificationStatus { get; set; }

    /// <summary>
    /// Optional filter for active status. If null, returns all bidders.
    /// </summary>
    public bool? IsActive { get; set; }
}
