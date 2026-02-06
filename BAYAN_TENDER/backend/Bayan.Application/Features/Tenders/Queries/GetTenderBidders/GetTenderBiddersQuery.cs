using Bayan.Application.Common.Models;
using Bayan.Application.Features.Tenders.DTOs;
using MediatR;

namespace Bayan.Application.Features.Tenders.Queries.GetTenderBidders;

/// <summary>
/// Query for retrieving bidders invited to a specific tender.
/// </summary>
public class GetTenderBiddersQuery : IRequest<PaginatedList<TenderBidderDto>>
{
    /// <summary>
    /// The tender ID.
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

    public GetTenderBiddersQuery(Guid tenderId, int page = 1, int pageSize = 10)
    {
        TenderId = tenderId;
        Page = page;
        PageSize = pageSize;
    }
}
