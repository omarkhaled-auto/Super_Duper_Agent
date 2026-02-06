using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Addenda.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Addenda.Queries.GetAddendumById;

/// <summary>
/// Handler for the GetAddendumByIdQuery.
/// </summary>
public class GetAddendumByIdQueryHandler : IRequestHandler<GetAddendumByIdQuery, AddendumDetailDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public GetAddendumByIdQueryHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<AddendumDetailDto?> Handle(
        GetAddendumByIdQuery request,
        CancellationToken cancellationToken)
    {
        var addendum = await _context.Addenda
            .AsNoTracking()
            .Include(a => a.Tender)
            .Include(a => a.Issuer)
            .Include(a => a.Acknowledgments)
                .ThenInclude(ack => ack.Bidder)
            .Where(a => a.TenderId == request.TenderId && a.Id == request.AddendumId)
            .FirstOrDefaultAsync(cancellationToken);

        if (addendum == null)
        {
            return null;
        }

        var dto = _mapper.Map<AddendumDetailDto>(addendum);

        // Get the total number of qualified bidders for this tender
        var totalBidders = await _context.TenderBidders
            .AsNoTracking()
            .Where(tb => tb.TenderId == request.TenderId &&
                         tb.QualificationStatus == QualificationStatus.Qualified)
            .CountAsync(cancellationToken);

        dto.TotalBidders = totalBidders;
        dto.AcknowledgedCount = addendum.Acknowledgments.Count(a => a.AcknowledgedAt.HasValue);
        dto.Acknowledgments = _mapper.Map<List<AddendumAcknowledgmentDto>>(addendum.Acknowledgments);

        return dto;
    }
}
