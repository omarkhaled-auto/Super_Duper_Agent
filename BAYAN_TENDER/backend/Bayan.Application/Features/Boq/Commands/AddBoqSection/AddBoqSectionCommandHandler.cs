using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.DTOs;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Boq.Commands.AddBoqSection;

/// <summary>
/// Handler for the AddBoqSectionCommand.
/// </summary>
public class AddBoqSectionCommandHandler : IRequestHandler<AddBoqSectionCommand, BoqSectionDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public AddBoqSectionCommandHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<BoqSectionDto> Handle(
        AddBoqSectionCommand request,
        CancellationToken cancellationToken)
    {
        var section = new BoqSection
        {
            Id = Guid.NewGuid(),
            TenderId = request.TenderId,
            SectionNumber = request.SectionNumber,
            Title = request.Title,
            SortOrder = request.SortOrder,
            ParentSectionId = request.ParentSectionId,
            CreatedAt = DateTime.UtcNow
        };

        _context.BoqSections.Add(section);
        await _context.SaveChangesAsync(cancellationToken);

        // Load the section with items for the response
        var createdSection = await _context.BoqSections
            .Include(s => s.Items.OrderBy(i => i.SortOrder))
            .AsNoTracking()
            .FirstAsync(s => s.Id == section.Id, cancellationToken);

        return _mapper.Map<BoqSectionDto>(createdSection);
    }
}
