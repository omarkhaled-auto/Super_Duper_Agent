using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Portal.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Portal.Documents;

/// <summary>
/// Handler for GetPortalAddendaQuery.
/// </summary>
public class GetPortalAddendaQueryHandler : IRequestHandler<GetPortalAddendaQuery, List<PortalAddendumDto>>
{
    private readonly IApplicationDbContext _context;

    public GetPortalAddendaQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<List<PortalAddendumDto>> Handle(GetPortalAddendaQuery request, CancellationToken cancellationToken)
    {
        // Validate bidder access to tender
        var tenderBidder = await _context.TenderBidders
            .FirstOrDefaultAsync(tb => tb.TenderId == request.TenderId && tb.BidderId == request.BidderId, cancellationToken);

        if (tenderBidder == null)
        {
            throw new UnauthorizedAccessException("You do not have access to this tender.");
        }

        if (tenderBidder.QualificationStatus == QualificationStatus.Removed)
        {
            throw new UnauthorizedAccessException("You have been removed from this tender.");
        }

        // Get issued addenda with acknowledgment status
        var addenda = await _context.Addenda
            .Where(a => a.TenderId == request.TenderId && a.Status == AddendumStatus.Issued)
            .Select(a => new
            {
                Addendum = a,
                Acknowledgment = a.Acknowledgments.FirstOrDefault(ack => ack.BidderId == request.BidderId)
            })
            .OrderByDescending(x => x.Addendum.AddendumNumber)
            .ToListAsync(cancellationToken);

        return addenda.Select(x => new PortalAddendumDto
        {
            Id = x.Addendum.Id,
            AddendumNumber = x.Addendum.AddendumNumber,
            IssueDate = x.Addendum.IssueDate,
            Summary = x.Addendum.Summary,
            ExtendsDeadline = x.Addendum.ExtendsDeadline,
            NewDeadline = x.Addendum.NewDeadline,
            Status = x.Addendum.Status,
            IsAcknowledged = x.Acknowledgment?.AcknowledgedAt != null,
            AcknowledgedAt = x.Acknowledgment?.AcknowledgedAt
        }).ToList();
    }
}
