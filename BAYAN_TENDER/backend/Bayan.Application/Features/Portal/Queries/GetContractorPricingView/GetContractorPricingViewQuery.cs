using Bayan.Application.Features.Portal.DTOs;
using MediatR;

namespace Bayan.Application.Features.Portal.Queries.GetContractorPricingView;

/// <summary>
/// Query to retrieve the contractor pricing view for a tender.
/// Builds a tree of priceable nodes based on the tender's pricing level
/// and includes any existing draft pricing data for the bidder.
/// </summary>
public class GetContractorPricingViewQuery : IRequest<ContractorPricingViewDto?>
{
    /// <summary>
    /// The tender ID to retrieve pricing for.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// The bidder ID requesting the pricing view.
    /// </summary>
    public Guid BidderId { get; set; }
}
