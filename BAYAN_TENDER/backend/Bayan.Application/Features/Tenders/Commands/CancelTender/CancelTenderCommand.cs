using Bayan.Application.Features.Tenders.DTOs;
using MediatR;

namespace Bayan.Application.Features.Tenders.Commands.CancelTender;

/// <summary>
/// Command for cancelling a tender.
/// </summary>
public class CancelTenderCommand : IRequest<TenderDto?>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid Id { get; }

    /// <summary>
    /// Reason for cancellation.
    /// </summary>
    public string? Reason { get; set; }

    public CancelTenderCommand(Guid id)
    {
        Id = id;
    }
}
