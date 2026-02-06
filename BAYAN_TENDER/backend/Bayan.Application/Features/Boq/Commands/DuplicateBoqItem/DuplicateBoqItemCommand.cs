using Bayan.Application.Features.Boq.DTOs;
using MediatR;

namespace Bayan.Application.Features.Boq.Commands.DuplicateBoqItem;

/// <summary>
/// Command for duplicating a BOQ item.
/// Creates a copy with a new item number.
/// </summary>
public class DuplicateBoqItemCommand : IRequest<BoqItemDto?>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; }

    /// <summary>
    /// The item's unique identifier to duplicate.
    /// </summary>
    public Guid ItemId { get; }

    /// <summary>
    /// Optional new item number for the duplicate.
    /// If not provided, will be auto-generated.
    /// </summary>
    public string? NewItemNumber { get; set; }

    public DuplicateBoqItemCommand(Guid tenderId, Guid itemId)
    {
        TenderId = tenderId;
        ItemId = itemId;
    }
}
