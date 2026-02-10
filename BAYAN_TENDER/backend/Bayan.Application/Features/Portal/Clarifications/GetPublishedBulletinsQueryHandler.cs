using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Portal.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Portal.Clarifications;

/// <summary>
/// Handler for GetPublishedBulletinsQuery.
/// </summary>
public class GetPublishedBulletinsQueryHandler : IRequestHandler<GetPublishedBulletinsQuery, List<PortalBulletinDto>>
{
    private readonly IApplicationDbContext _context;

    public GetPublishedBulletinsQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<List<PortalBulletinDto>> Handle(GetPublishedBulletinsQuery request, CancellationToken cancellationToken)
    {
        // Validate bidder access to tender
        var tenderBidder = await _context.TenderBidders
            .FirstOrDefaultAsync(tb => tb.TenderId == request.TenderId && tb.BidderId == request.BidderId, cancellationToken);

        if (tenderBidder == null)
        {
            throw new UnauthorizedAccessException("You do not have access to this tender.");
        }

        if (tenderBidder.QualificationStatus != QualificationStatus.Qualified)
        {
            throw new UnauthorizedAccessException($"You are not qualified for this tender. Current status: {tenderBidder.QualificationStatus}");
        }

        // Get bulletins with their published Q&A items
        var bulletins = await _context.ClarificationBulletins
            .Where(b => b.TenderId == request.TenderId)
            .Select(b => new PortalBulletinDto
            {
                Id = b.Id,
                BulletinNumber = b.BulletinNumber,
                IssueDate = b.IssueDate,
                Introduction = b.Introduction,
                ClosingNotes = b.ClosingNotes,
                HasPdf = !string.IsNullOrEmpty(b.PdfPath),
                PublishedAt = b.PublishedAt,
                ClarificationCount = b.Clarifications.Count,
                Clarifications = b.Clarifications
                    .OrderBy(c => c.ReferenceNumber)
                    .Select(c => new PortalBulletinClarificationDto
                    {
                        Id = c.Id,
                        ReferenceNumber = c.ReferenceNumber,
                        Subject = c.Subject,
                        Question = c.Question,
                        Answer = c.Answer ?? string.Empty,
                        RelatedBoqSection = c.RelatedBoqSection,
                        AnsweredAt = c.AnsweredAt
                    })
                    .ToList()
            })
            .OrderByDescending(b => b.BulletinNumber)
            .ToListAsync(cancellationToken);

        return bulletins;
    }
}
