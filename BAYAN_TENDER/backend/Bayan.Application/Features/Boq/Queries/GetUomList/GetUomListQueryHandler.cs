using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Boq.Queries.GetUomList;

/// <summary>
/// Handler for the GetUomListQuery.
/// Returns list of active units of measurement from uom_master.
/// </summary>
public class GetUomListQueryHandler : IRequestHandler<GetUomListQuery, List<UomDto>>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public GetUomListQueryHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<List<UomDto>> Handle(
        GetUomListQuery request,
        CancellationToken cancellationToken)
    {
        var query = _context.UnitsOfMeasure
            .Where(u => u.IsActive)
            .AsNoTracking();

        // Apply category filter if provided
        if (!string.IsNullOrWhiteSpace(request.Category))
        {
            query = query.Where(u => u.Category == request.Category);
        }

        var units = await query
            .OrderBy(u => u.DisplayOrder)
            .ThenBy(u => u.Name)
            .Select(u => new UomDto
            {
                Id = u.Id,
                Code = u.Code,
                Name = u.Name,
                Category = u.Category
            })
            .ToListAsync(cancellationToken);

        return units;
    }
}
