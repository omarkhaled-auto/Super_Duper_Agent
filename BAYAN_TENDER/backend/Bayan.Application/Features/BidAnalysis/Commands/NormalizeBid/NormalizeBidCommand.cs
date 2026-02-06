using Bayan.Application.Features.BidAnalysis.DTOs;
using MediatR;

namespace Bayan.Application.Features.BidAnalysis.Commands.NormalizeBid;

/// <summary>
/// Command to normalize bid pricing by applying FX rate and UOM conversions.
/// </summary>
public record NormalizeBidCommand : IRequest<NormalizationResultDto>
{
    /// <summary>
    /// Tender identifier.
    /// </summary>
    public Guid TenderId { get; init; }

    /// <summary>
    /// Bid submission identifier.
    /// </summary>
    public Guid BidSubmissionId { get; init; }

    /// <summary>
    /// Optional FX rate to use. If not provided, uses the rate stored in bid submission.
    /// </summary>
    public decimal? FxRate { get; init; }

    /// <summary>
    /// Source of the FX rate (e.g., "Manual", "API").
    /// </summary>
    public string? FxRateSource { get; init; }

    /// <summary>
    /// Whether to persist the normalization results to the database.
    /// If false, returns preview only.
    /// </summary>
    public bool PersistResults { get; init; } = false;
}
