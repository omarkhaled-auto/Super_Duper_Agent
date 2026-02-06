using Bayan.Application.Features.BidAnalysis.DTOs;
using MediatR;

namespace Bayan.Application.Features.BidAnalysis.Commands.ParseBidFile;

/// <summary>
/// Command to parse a bid file and return column information and preview.
/// </summary>
public class ParseBidFileCommand : IRequest<ParseBidResultDto>
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
    /// Number of preview rows to return.
    /// </summary>
    public int PreviewRowCount { get; set; } = 10;

    public ParseBidFileCommand(Guid tenderId, Guid bidId, int previewRowCount = 10)
    {
        TenderId = tenderId;
        BidId = bidId;
        PreviewRowCount = previewRowCount;
    }
}
