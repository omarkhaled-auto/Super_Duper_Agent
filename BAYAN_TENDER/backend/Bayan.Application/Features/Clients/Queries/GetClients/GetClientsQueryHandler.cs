using AutoMapper;
using AutoMapper.QueryableExtensions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using Bayan.Application.Features.Clients.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Clients.Queries.GetClients;

/// <summary>
/// Handler for the GetClientsQuery.
/// </summary>
public class GetClientsQueryHandler : IRequestHandler<GetClientsQuery, PaginatedList<ClientDto>>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public GetClientsQueryHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<PaginatedList<ClientDto>> Handle(
        GetClientsQuery request,
        CancellationToken cancellationToken)
    {
        var query = _context.Clients.AsNoTracking();

        // Apply search filter
        if (!string.IsNullOrWhiteSpace(request.Search))
        {
            var searchTerm = request.Search.ToLower();
            query = query.Where(c =>
                c.Name.ToLower().Contains(searchTerm) ||
                (c.ContactPerson != null && c.ContactPerson.ToLower().Contains(searchTerm)) ||
                (c.Email != null && c.Email.ToLower().Contains(searchTerm)));
        }

        // Apply active status filter
        if (request.IsActive.HasValue)
        {
            query = query.Where(c => c.IsActive == request.IsActive.Value);
        }

        // Order by name
        query = query.OrderBy(c => c.Name);

        // Project to DTO and paginate
        var projectedQuery = query.ProjectTo<ClientDto>(_mapper.ConfigurationProvider);

        return await PaginatedList<ClientDto>.CreateAsync(
            projectedQuery,
            request.Page,
            request.PageSize,
            cancellationToken);
    }
}
