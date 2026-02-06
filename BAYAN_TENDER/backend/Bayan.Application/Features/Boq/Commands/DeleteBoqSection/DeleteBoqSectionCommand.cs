using MediatR;

namespace Bayan.Application.Features.Boq.Commands.DeleteBoqSection;

/// <summary>
/// Command for deleting a BOQ section.
/// Cascade deletes all items in the section.
/// </summary>
public class DeleteBoqSectionCommand : IRequest<bool>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; }

    /// <summary>
    /// The section's unique identifier.
    /// </summary>
    public Guid SectionId { get; }

    public DeleteBoqSectionCommand(Guid tenderId, Guid sectionId)
    {
        TenderId = tenderId;
        SectionId = sectionId;
    }
}
