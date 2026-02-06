using Bayan.Application.Features.BidAnalysis.DTOs;
using MediatR;

namespace Bayan.Application.Features.BidAnalysis.Commands.ExecuteBidImport;

/// <summary>
/// Command to execute the final import of a bid submission.
/// Stores bid pricing records and creates vendor pricing snapshot.
/// </summary>
public record ExecuteBidImportCommand : IRequest<ImportResultDto>
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
    /// Whether to force import even with validation warnings.
    /// Errors will still block import.
    /// </summary>
    public bool ForceImport { get; init; } = false;

    /// <summary>
    /// Whether to create a vendor pricing snapshot for historical tracking.
    /// </summary>
    public bool CreateVendorSnapshot { get; init; } = true;

    /// <summary>
    /// FX rate to use for normalization. If not provided, uses existing rate.
    /// </summary>
    public decimal? FxRate { get; init; }
}
