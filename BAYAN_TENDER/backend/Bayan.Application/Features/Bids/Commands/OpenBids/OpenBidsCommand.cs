using Bayan.Application.Features.Bids.DTOs;
using MediatR;

namespace Bayan.Application.Features.Bids.Commands.OpenBids;

/// <summary>
/// Command for opening all bids for a tender.
/// WARNING: This is an IRREVERSIBLE action.
/// All bid amounts will be revealed and the action will be logged.
/// </summary>
public class OpenBidsCommand : IRequest<OpenBidsResultDto>
{
    /// <summary>
    /// ID of the tender to open bids for.
    /// </summary>
    public Guid TenderId { get; }

    public OpenBidsCommand(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
