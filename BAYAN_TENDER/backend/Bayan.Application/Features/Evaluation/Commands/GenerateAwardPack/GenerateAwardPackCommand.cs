using Bayan.Application.Features.Evaluation.DTOs;
using MediatR;

namespace Bayan.Application.Features.Evaluation.Commands.GenerateAwardPack;

/// <summary>
/// Command to generate an award pack PDF for a tender.
/// </summary>
public class GenerateAwardPackCommand : IRequest<AwardPackDto>
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Whether to include technical evaluation details.
    /// </summary>
    public bool IncludeTechnicalDetails { get; set; } = true;

    /// <summary>
    /// Whether to include commercial evaluation details.
    /// </summary>
    public bool IncludeCommercialDetails { get; set; } = true;

    /// <summary>
    /// Whether to include sensitivity analysis.
    /// </summary>
    public bool IncludeSensitivityAnalysis { get; set; } = true;

    /// <summary>
    /// Whether to include bid exceptions.
    /// </summary>
    public bool IncludeExceptions { get; set; } = true;

    /// <summary>
    /// Custom executive summary (optional).
    /// </summary>
    public string? ExecutiveSummary { get; set; }

    /// <summary>
    /// Custom recommendation notes (optional).
    /// </summary>
    public string? RecommendationNotes { get; set; }

    public GenerateAwardPackCommand()
    {
    }

    public GenerateAwardPackCommand(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
