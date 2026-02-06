using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Boq.Commands.UpdateBoqSection;

/// <summary>
/// Handler for the UpdateBoqSectionCommand.
/// </summary>
public class UpdateBoqSectionCommandHandler : IRequestHandler<UpdateBoqSectionCommand, BoqSectionDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public UpdateBoqSectionCommandHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<BoqSectionDto?> Handle(
        UpdateBoqSectionCommand request,
        CancellationToken cancellationToken)
    {
        var section = await _context.BoqSections
            .Include(s => s.Items.OrderBy(i => i.SortOrder))
            .FirstOrDefaultAsync(s => s.Id == request.SectionId && s.TenderId == request.TenderId, cancellationToken);

        if (section == null)
        {
            return null;
        }

        section.SectionNumber = request.SectionNumber;
        section.Title = request.Title;
        section.SortOrder = request.SortOrder;
        section.ParentSectionId = request.ParentSectionId;
        section.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync(cancellationToken);

        return _mapper.Map<BoqSectionDto>(section);
    }
}
