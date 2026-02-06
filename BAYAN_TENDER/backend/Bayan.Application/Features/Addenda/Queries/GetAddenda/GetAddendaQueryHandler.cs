using AutoMapper;
using AutoMapper.QueryableExtensions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Addenda.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Addenda.Queries.GetAddenda;

/// <summary>
/// Handler for the GetAddendaQuery.
/// </summary>
public class GetAddendaQueryHandler : IRequestHandler<GetAddendaQuery, List<AddendumDto>>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public GetAddendaQueryHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<List<AddendumDto>> Handle(
        GetAddendaQuery request,
        CancellationToken cancellationToken)
    {
        return await _context.Addenda
            .AsNoTracking()
            .Where(a => a.TenderId == request.TenderId)
            .OrderBy(a => a.AddendumNumber)
            .ProjectTo<AddendumDto>(_mapper.ConfigurationProvider)
            .ToListAsync(cancellationToken);
    }
}
