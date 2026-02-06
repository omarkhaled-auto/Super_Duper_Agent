using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Boq.Commands.UpdateBoqItem;

/// <summary>
/// Handler for the UpdateBoqItemCommand.
/// </summary>
public class UpdateBoqItemCommandHandler : IRequestHandler<UpdateBoqItemCommand, BoqItemDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public UpdateBoqItemCommandHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<BoqItemDto?> Handle(
        UpdateBoqItemCommand request,
        CancellationToken cancellationToken)
    {
        var item = await _context.BoqItems
            .FirstOrDefaultAsync(i => i.Id == request.ItemId && i.TenderId == request.TenderId, cancellationToken);

        if (item == null)
        {
            return null;
        }

        item.SectionId = request.SectionId;
        item.ItemNumber = request.ItemNumber;
        item.Description = request.Description;
        item.Quantity = request.Quantity;
        item.Uom = request.Uom;
        item.ItemType = request.ItemType;
        item.Notes = request.Notes;
        item.SortOrder = request.SortOrder;
        item.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync(cancellationToken);

        return _mapper.Map<BoqItemDto>(item);
    }
}
