using Bayan.Application.Features.Evaluation.DTOs;
using MediatR;

namespace Bayan.Application.Features.Evaluation.Queries.GetBidExceptions;

/// <summary>
/// Query to get all bid exceptions for a tender.
/// </summary>
public class GetBidExceptionsQuery : IRequest<BidExceptionListDto>
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    public GetBidExceptionsQuery()
    {
    }

    public GetBidExceptionsQuery(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
