using Bayan.Application.Features.BidAnalysis.DTOs;
using MediatR;

namespace Bayan.Application.Features.BidAnalysis.Commands.MapBidColumns;

/// <summary>
/// Command to apply column mappings and extract bid items from the parsed file.
/// </summary>
public class MapBidColumnsCommand : IRequest<ImportBidDto>
{
    /// <summary>
    /// Tender ID the bid belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bid submission ID.
    /// </summary>
    public Guid BidId { get; set; }

    /// <summary>
    /// Column mappings to apply.
    /// </summary>
    public ColumnMappingsDto ColumnMappings { get; set; } = new();

    public MapBidColumnsCommand()
    {
    }

    public MapBidColumnsCommand(Guid tenderId, Guid bidId, ColumnMappingsDto columnMappings)
    {
        TenderId = tenderId;
        BidId = bidId;
        ColumnMappings = columnMappings;
    }
}
