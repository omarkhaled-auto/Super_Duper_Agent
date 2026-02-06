using Bayan.Application.Common.Interfaces;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Boq.Commands.DeleteBoqSection;

/// <summary>
/// Handler for the DeleteBoqSectionCommand.
/// Cascade deletes all items and child sections.
/// </summary>
public class DeleteBoqSectionCommandHandler : IRequestHandler<DeleteBoqSectionCommand, bool>
{
    private readonly IApplicationDbContext _context;

    public DeleteBoqSectionCommandHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<bool> Handle(
        DeleteBoqSectionCommand request,
        CancellationToken cancellationToken)
    {
        var section = await _context.BoqSections
            .Include(s => s.Items)
            .Include(s => s.ChildSections)
                .ThenInclude(cs => cs.Items)
            .FirstOrDefaultAsync(s => s.Id == request.SectionId && s.TenderId == request.TenderId, cancellationToken);

        if (section == null)
        {
            return false;
        }

        // Recursively delete child sections and their items
        await DeleteSectionRecursivelyAsync(section, cancellationToken);

        await _context.SaveChangesAsync(cancellationToken);

        return true;
    }

    private async Task DeleteSectionRecursivelyAsync(
        Bayan.Domain.Entities.BoqSection section,
        CancellationToken cancellationToken)
    {
        // Load child sections if not already loaded
        var childSections = await _context.BoqSections
            .Include(s => s.Items)
            .Where(s => s.ParentSectionId == section.Id)
            .ToListAsync(cancellationToken);

        // Recursively delete child sections
        foreach (var childSection in childSections)
        {
            await DeleteSectionRecursivelyAsync(childSection, cancellationToken);
        }

        // Delete items in this section
        _context.BoqItems.RemoveRange(section.Items);

        // Delete the section
        _context.BoqSections.Remove(section);
    }
}
