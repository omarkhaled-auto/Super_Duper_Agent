using Bayan.Application.Features.Bids.DTOs;
using MediatR;

namespace Bayan.Application.Features.Bids.Commands.DownloadAllBids;

/// <summary>
/// Command for downloading all bid documents as a ZIP file.
/// Structure: {BidderName}/Commercial/..., {BidderName}/Technical/...
/// </summary>
public class DownloadAllBidsCommand : IRequest<DownloadAllBidsResultDto>
{
    /// <summary>
    /// ID of the tender.
    /// </summary>
    public Guid TenderId { get; }

    public DownloadAllBidsCommand(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
