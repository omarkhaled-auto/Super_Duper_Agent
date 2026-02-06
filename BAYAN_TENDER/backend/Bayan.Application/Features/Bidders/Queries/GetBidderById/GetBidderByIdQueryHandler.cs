using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Bidders.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bidders.Queries.GetBidderById;

/// <summary>
/// Handler for the GetBidderByIdQuery.
/// </summary>
public class GetBidderByIdQueryHandler : IRequestHandler<GetBidderByIdQuery, BidderDetailDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public GetBidderByIdQueryHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<BidderDetailDto?> Handle(
        GetBidderByIdQuery request,
        CancellationToken cancellationToken)
    {
        var bidder = await _context.Bidders
            .AsNoTracking()
            .Include(b => b.TenderBidders)
            .Where(b => b.Id == request.Id)
            .FirstOrDefaultAsync(cancellationToken);

        if (bidder == null)
        {
            return null;
        }

        var dto = _mapper.Map<BidderDetailDto>(bidder);
        dto.TenderCount = bidder.TenderBidders.Count;

        return dto;
    }
}
