using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Portal.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Portal.Clarifications;

/// <summary>
/// Handler for GetMyQuestionsQuery — returns the bidder's own questions (any status).
/// </summary>
public class GetMyQuestionsQueryHandler : IRequestHandler<GetMyQuestionsQuery, List<PortalClarificationDto>>
{
    private readonly IApplicationDbContext _context;

    public GetMyQuestionsQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<List<PortalClarificationDto>> Handle(GetMyQuestionsQuery request, CancellationToken cancellationToken)
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

        // Get all questions submitted by this bidder (any status, BidderQuestion type only)
        var clarifications = await _context.Clarifications
            .Where(c => c.TenderId == request.TenderId
                     && c.SubmittedByBidderId == request.BidderId
                     && c.ClarificationType == ClarificationType.BidderQuestion)
            .OrderByDescending(c => c.SubmittedAt)
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
