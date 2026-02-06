using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Portal.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Portal.Clarifications;

/// <summary>
/// Handler for GetPublishedClarificationsQuery.
/// </summary>
public class GetPublishedClarificationsQueryHandler : IRequestHandler<GetPublishedClarificationsQuery, List<PortalClarificationDto>>
{
    private readonly IApplicationDbContext _context;

    public GetPublishedClarificationsQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<List<PortalClarificationDto>> Handle(GetPublishedClarificationsQuery request, CancellationToken cancellationToken)
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

        // Get published clarifications only
        var clarifications = await _context.Clarifications
            .Where(c => c.TenderId == request.TenderId && c.Status == ClarificationStatus.Published)
            .OrderByDescending(c => c.PublishedAt)
            .ThenBy(c => c.ReferenceNumber)
            .Select(c => new PortalClarificationDto
            {
                Id = c.Id,
                ReferenceNumber = c.ReferenceNumber,
                Subject = c.Subject,
                Question = c.Question,
                Answer = c.Answer,
                RelatedBoqSection = c.RelatedBoqSection,
                SubmittedAt = c.SubmittedAt,
                AnsweredAt = c.AnsweredAt,
                PublishedAt = c.PublishedAt,
                ClarificationType = c.ClarificationType,
                Priority = c.Priority,
                Status = c.Status
            })
            .ToListAsync(cancellationToken);

        return clarifications;
    }
}
