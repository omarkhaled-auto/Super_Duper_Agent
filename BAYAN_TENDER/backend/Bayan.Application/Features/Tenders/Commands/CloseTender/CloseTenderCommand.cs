using Bayan.Application.Features.Tenders.DTOs;
using MediatR;

namespace Bayan.Application.Features.Tenders.Commands.CloseTender;

/// <summary>
/// Command for closing a tender (transitioning from Active to Evaluation).
/// Closing a tender stops accepting bids and begins the evaluation phase.
/// </summary>
public class CloseTenderCommand : IRequest<TenderDto?>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid Id { get; }

    public CloseTenderCommand(Guid id)
    {
        Id = id;
    }
}
