using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.DTOs;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Boq.Commands.DuplicateBoqItem;

/// <summary>
/// Handler for the DuplicateBoqItemCommand.
/// Creates a copy of an existing item with a new item number.
/// </summary>
public class DuplicateBoqItemCommandHandler : IRequestHandler<DuplicateBoqItemCommand, BoqItemDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public DuplicateBoqItemCommandHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<BoqItemDto?> Handle(
        DuplicateBoqItemCommand request,
        CancellationToken cancellationToken)
    {
        var originalItem = await _context.BoqItems
            .AsNoTracking()
            .FirstOrDefaultAsync(i => i.Id == request.ItemId && i.TenderId == request.TenderId, cancellationToken);

        if (originalItem == null)
        {
            return null;
        }

        // Generate new item number if not provided
        var newItemNumber = request.NewItemNumber;
        if (string.IsNullOrWhiteSpace(newItemNumber))
        {
            newItemNumber = await GenerateNewItemNumberAsync(originalItem.ItemNumber, request.TenderId, cancellationToken);
        }

        // Create duplicate item
        var duplicateItem = new BoqItem
        {
            Id = Guid.NewGuid(),
            TenderId = originalItem.TenderId,
            SectionId = originalItem.SectionId,
            ItemNumber = newItemNumber,
            Description = originalItem.Description,
            Quantity = originalItem.Quantity,
            Uom = originalItem.Uom,
            ItemType = originalItem.ItemType,
            Notes = originalItem.Notes,
            SortOrder = originalItem.SortOrder + 1,
            CreatedAt = DateTime.UtcNow
        };

        _context.BoqItems.Add(duplicateItem);
        await _context.SaveChangesAsync(cancellationToken);

        return _mapper.Map<BoqItemDto>(duplicateItem);
    }

    /// <summary>
    /// Generates a new unique item number based on the original.
    /// Appends a suffix like "-COPY" or "-COPY2" if needed.
    /// </summary>
    private async Task<string> GenerateNewItemNumberAsync(
        string originalItemNumber,
        Guid tenderId,
        CancellationToken cancellationToken)
    {
        var baseNumber = originalItemNumber;
        var suffix = "-COPY";
        var counter = 1;

        // Check if original already has a copy suffix
        if (originalItemNumber.Contains("-COPY"))
        {
            var lastDashIndex = originalItemNumber.LastIndexOf("-COPY");
            baseNumber = originalItemNumber.Substring(0, lastDashIndex);
        }

        var newItemNumber = baseNumber + suffix;

        // Check for uniqueness and increment counter if necessary
        while (await _context.BoqItems.AnyAsync(
            i => i.TenderId == tenderId && i.ItemNumber == newItemNumber, cancellationToken))
        {
            counter++;
            newItemNumber = baseNumber + suffix + counter;
        }

        return newItemNumber;
    }
}
