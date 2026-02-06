using AutoMapper;
using AutoMapper.QueryableExtensions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Admin.Users.Queries.GetUsers;

/// <summary>
/// Handler for GetUsersQuery.
/// </summary>
public class GetUsersQueryHandler : IRequestHandler<GetUsersQuery, PaginatedList<UserDto>>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public GetUsersQueryHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<PaginatedList<UserDto>> Handle(GetUsersQuery request, CancellationToken cancellationToken)
    {
        var query = _context.Users.AsNoTracking();

        // Apply search filter
        if (!string.IsNullOrWhiteSpace(request.Search))
        {
            var searchTerm = request.Search.ToLower();
            query = query.Where(u =>
                u.FirstName.ToLower().Contains(searchTerm) ||
                u.LastName.ToLower().Contains(searchTerm) ||
                u.Email.ToLower().Contains(searchTerm) ||
                (u.CompanyName != null && u.CompanyName.ToLower().Contains(searchTerm)));
        }

        // Apply role filter
        if (request.Role.HasValue)
        {
            query = query.Where(u => u.Role == request.Role.Value);
        }

        // Apply active status filter
        if (request.IsActive.HasValue)
        {
            query = query.Where(u => u.IsActive == request.IsActive.Value);
        }

        // Order by creation date (newest first)
        query = query.OrderByDescending(u => u.CreatedAt);

        // Project to DTO and paginate
        var projectedQuery = query.ProjectTo<UserDto>(_mapper.ConfigurationProvider);

        return await PaginatedList<UserDto>.CreateAsync(
            projectedQuery,
            request.Page,
            request.PageSize,
            cancellationToken);
    }
}
