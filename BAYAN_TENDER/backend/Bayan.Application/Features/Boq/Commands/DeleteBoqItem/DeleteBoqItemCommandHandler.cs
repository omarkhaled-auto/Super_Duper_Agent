using Bayan.Application.Common.Interfaces;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Boq.Commands.DeleteBoqItem;

/// <summary>
/// Handler for the DeleteBoqItemCommand.
/// </summary>
public class DeleteBoqItemCommandHandler : IRequestHandler<DeleteBoqItemCommand, bool>
{
    private readonly IApplicationDbContext _context;

    public DeleteBoqItemCommandHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<bool> Handle(
        DeleteBoqItemCommand request,
        CancellationToken cancellationToken)
    {
        var item = await _context.BoqItems
            .FirstOrDefaultAsync(i => i.Id == request.ItemId && i.TenderId == request.TenderId, cancellationToken);

        if (item == null)
        {
            return false;
        }

        _context.BoqItems.Remove(item);
        await _context.SaveChangesAsync(cancellationToken);

        return true;
    }
}
