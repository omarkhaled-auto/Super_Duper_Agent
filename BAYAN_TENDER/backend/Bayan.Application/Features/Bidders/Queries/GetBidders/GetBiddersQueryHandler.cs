using AutoMapper;
using AutoMapper.QueryableExtensions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using Bayan.Application.Features.Bidders.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bidders.Queries.GetBidders;

/// <summary>
/// Handler for the GetBiddersQuery.
/// </summary>
public class GetBiddersQueryHandler : IRequestHandler<GetBiddersQuery, PaginatedList<BidderDto>>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public GetBiddersQueryHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<PaginatedList<BidderDto>> Handle(
        GetBiddersQuery request,
        CancellationToken cancellationToken)
    {
        var query = _context.Bidders.AsNoTracking();

        // Apply search filter
        if (!string.IsNullOrWhiteSpace(request.Search))
        {
            var searchTerm = request.Search.ToLower();
            query = query.Where(b =>
                b.CompanyName.ToLower().Contains(searchTerm) ||
                b.ContactPerson.ToLower().Contains(searchTerm) ||
                b.Email.ToLower().Contains(searchTerm) ||
                (b.CRNumber != null && b.CRNumber.ToLower().Contains(searchTerm)));
        }

        // Apply trade specialization filter
        if (!string.IsNullOrWhiteSpace(request.TradeSpecialization))
        {
            var tradeTerm = request.TradeSpecialization.ToLower();
            query = query.Where(b =>
                b.TradeSpecialization != null &&
                b.TradeSpecialization.ToLower().Contains(tradeTerm));
        }

        // Apply prequalification status filter
        if (request.PrequalificationStatus.HasValue)
        {
            query = query.Where(b => b.PrequalificationStatus == request.PrequalificationStatus.Value);
        }

        // Apply active status filter
        if (request.IsActive.HasValue)
        {
            query = query.Where(b => b.IsActive == request.IsActive.Value);
        }

        // Order by company name
        query = query.OrderBy(b => b.CompanyName);

        // Project to DTO and paginate
        var projectedQuery = query.ProjectTo<BidderDto>(_mapper.ConfigurationProvider);

        return await PaginatedList<BidderDto>.CreateAsync(
            projectedQuery,
            request.Page,
            request.PageSize,
            cancellationToken);
    }
}
