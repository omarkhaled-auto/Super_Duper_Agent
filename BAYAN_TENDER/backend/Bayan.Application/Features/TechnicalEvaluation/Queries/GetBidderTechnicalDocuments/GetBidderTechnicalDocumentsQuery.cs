using Bayan.Application.Features.TechnicalEvaluation.DTOs;
using MediatR;

namespace Bayan.Application.Features.TechnicalEvaluation.Queries.GetBidderTechnicalDocuments;

/// <summary>
/// Query to get a bidder's technical documents for evaluation.
/// Enforces blind mode by hiding bidder identity if enabled.
/// </summary>
public class GetBidderTechnicalDocumentsQuery : IRequest<BidderTechnicalDocumentsDto?>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; }

    /// <summary>
    /// The bidder's unique identifier.
    /// </summary>
    public Guid BidderId { get; }

    public GetBidderTechnicalDocumentsQuery(Guid tenderId, Guid bidderId)
    {
        TenderId = tenderId;
        BidderId = bidderId;
    }
}
