using Bayan.Application.Features.Evaluation.DTOs;
using MediatR;

namespace Bayan.Application.Features.Evaluation.Queries.GetSensitivityAnalysis;

/// <summary>
/// Query to get sensitivity analysis showing rank changes at different weight splits.
/// </summary>
public class GetSensitivityAnalysisQuery : IRequest<SensitivityAnalysisDto>
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    public GetSensitivityAnalysisQuery()
    {
    }

    public GetSensitivityAnalysisQuery(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
