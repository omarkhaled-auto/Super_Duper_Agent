using Bayan.Application.Features.TechnicalEvaluation.DTOs;
using MediatR;

namespace Bayan.Application.Features.TechnicalEvaluation.Queries.GetEvaluationSetup;

/// <summary>
/// Query to get the technical evaluation setup for a tender.
/// </summary>
public class GetEvaluationSetupQuery : IRequest<EvaluationSetupDto?>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; }

    public GetEvaluationSetupQuery(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
