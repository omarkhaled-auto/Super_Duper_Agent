using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.DTOs;
using Bayan.Domain.Entities;
using MediatR;

namespace Bayan.Application.Features.Boq.Commands.AddBoqItem;

/// <summary>
/// Handler for the AddBoqItemCommand.
/// </summary>
public class AddBoqItemCommandHandler : IRequestHandler<AddBoqItemCommand, BoqItemDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public AddBoqItemCommandHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<BoqItemDto> Handle(
        AddBoqItemCommand request,
        CancellationToken cancellationToken)
    {
        var item = new BoqItem
        {
            Id = Guid.NewGuid(),
            TenderId = request.TenderId,
            SectionId = request.SectionId,
            ItemNumber = request.ItemNumber,
            Description = request.Description,
            Quantity = request.Quantity,
            Uom = request.Uom,
            ItemType = request.ItemType,
            Notes = request.Notes,
            SortOrder = request.SortOrder,
            ParentItemId = request.ParentItemId,
            IsGroup = request.IsGroup,
            CreatedAt = DateTime.UtcNow
        };

        _context.BoqItems.Add(item);
        await _context.SaveChangesAsync(cancellationToken);

        return _mapper.Map<BoqItemDto>(item);
    }
}
