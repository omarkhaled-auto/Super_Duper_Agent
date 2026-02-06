using Bayan.Application.Features.Bidders.DTOs;
using MediatR;

namespace Bayan.Application.Features.Bidders.Queries.GetBidderById;

/// <summary>
/// Query for retrieving a single bidder by ID with full details.
/// </summary>
public class GetBidderByIdQuery : IRequest<BidderDetailDto?>
{
    /// <summary>
    /// The unique identifier of the bidder to retrieve.
    /// </summary>
    public Guid Id { get; set; }

    public GetBidderByIdQuery(Guid id)
    {
        Id = id;
    }
}
