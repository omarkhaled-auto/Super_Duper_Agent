using Bayan.Application.Features.Addenda.DTOs;
using MediatR;

namespace Bayan.Application.Features.Addenda.Commands.CreateAddendum;

/// <summary>
/// Command for creating a new addendum for a tender.
/// </summary>
public class CreateAddendumCommand : IRequest<AddendumDto>
{
    /// <summary>
    /// ID of the tender to add the addendum to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Summary of changes in this addendum.
    /// </summary>
    public string Summary { get; set; } = string.Empty;

    /// <summary>
    /// Whether this addendum extends the submission deadline.
    /// </summary>
    public bool ExtendsDeadline { get; set; }

    /// <summary>
    /// New submission deadline (required if ExtendsDeadline is true).
    /// </summary>
    public DateTime? NewDeadline { get; set; }
}
