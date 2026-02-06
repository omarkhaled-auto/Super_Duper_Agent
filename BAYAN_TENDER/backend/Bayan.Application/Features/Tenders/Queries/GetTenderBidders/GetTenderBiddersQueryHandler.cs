using AutoMapper;
using AutoMapper.QueryableExtensions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using Bayan.Application.Features.Tenders.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Queries.GetTenderBidders;

/// <summary>
/// Handler for the GetTenderBiddersQuery.
/// </summary>
public class GetTenderBiddersQueryHandler : IRequestHandler<GetTenderBiddersQuery, PaginatedList<TenderBidderDto>>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public GetTenderBiddersQueryHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<PaginatedList<TenderBidderDto>> Handle(
        GetTenderBiddersQuery request,
        CancellationToken cancellationToken)
    {
        var query = _context.TenderBidders
            .AsNoTracking()
            .Include(tb => tb.Bidder)
            .Where(tb => tb.TenderId == request.TenderId)
            .OrderBy(tb => tb.Bidder.CompanyName);

        var projectedQuery = query.ProjectTo<TenderBidderDto>(_mapper.ConfigurationProvider);

        return await PaginatedList<TenderBidderDto>.CreateAsync(
            projectedQuery,
            request.Page,
            request.PageSize,
            cancellationToken);
    }
}
