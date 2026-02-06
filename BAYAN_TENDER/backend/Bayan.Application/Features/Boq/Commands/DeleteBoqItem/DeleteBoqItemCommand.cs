using MediatR;

namespace Bayan.Application.Features.Boq.Commands.DeleteBoqItem;

/// <summary>
/// Command for deleting a BOQ item.
/// </summary>
public class DeleteBoqItemCommand : IRequest<bool>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; }

    /// <summary>
    /// The item's unique identifier.
    /// </summary>
    public Guid ItemId { get; }

    public DeleteBoqItemCommand(Guid tenderId, Guid itemId)
    {
        TenderId = tenderId;
        ItemId = itemId;
    }
}
