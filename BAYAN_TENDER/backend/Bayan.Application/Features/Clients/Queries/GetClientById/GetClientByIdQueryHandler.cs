using AutoMapper;
using AutoMapper.QueryableExtensions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Clients.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Clients.Queries.GetClientById;

/// <summary>
/// Handler for the GetClientByIdQuery.
/// </summary>
public class GetClientByIdQueryHandler : IRequestHandler<GetClientByIdQuery, ClientDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public GetClientByIdQueryHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<ClientDto?> Handle(
        GetClientByIdQuery request,
        CancellationToken cancellationToken)
    {
        return await _context.Clients
            .AsNoTracking()
            .Where(c => c.Id == request.Id)
            .ProjectTo<ClientDto>(_mapper.ConfigurationProvider)
            .FirstOrDefaultAsync(cancellationToken);
    }
}
