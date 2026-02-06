using Bayan.Application.Features.Tenders.DTOs;
using MediatR;

namespace Bayan.Application.Features.Tenders.Commands.PublishTender;

/// <summary>
/// Command for publishing a tender (transitioning from Draft to Active status).
/// </summary>
public class PublishTenderCommand : IRequest<TenderDto?>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid Id { get; }

    public PublishTenderCommand(Guid id)
    {
        Id = id;
    }
}
