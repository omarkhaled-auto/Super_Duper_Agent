using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Portal.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Portal.Clarifications;

/// <summary>
/// Handler for SubmitBidderQuestionCommand.
/// </summary>
public class SubmitBidderQuestionCommandHandler : IRequestHandler<SubmitBidderQuestionCommand, BidderQuestionDto>
{
    private readonly IApplicationDbContext _context;

    public SubmitBidderQuestionCommandHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<BidderQuestionDto> Handle(SubmitBidderQuestionCommand request, CancellationToken cancellationToken)
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

        // Get tender to check clarification deadline
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new NotFoundException("Tender", request.TenderId);
        }

        // Validate clarification deadline
        if (DateTime.UtcNow > tender.ClarificationDeadline)
        {
            throw new InvalidOperationException(
                $"The clarification deadline has passed. Deadline was: {tender.ClarificationDeadline:yyyy-MM-dd HH:mm} UTC");
        }

        // Generate reference number (CL-XXX format)
        var referenceNumber = await GenerateReferenceNumberAsync(request.TenderId, cancellationToken);

        // Create clarification
        var clarification = new Clarification
        {
            Id = Guid.NewGuid(),
            TenderId = request.TenderId,
            ReferenceNumber = referenceNumber,
            Subject = request.Subject,
            Question = request.Question,
            SubmittedByBidderId = request.BidderId,
            RelatedBoqSection = request.RelatedBoqSection,
            IsAnonymous = request.IsAnonymous,
            ClarificationType = ClarificationType.BidderQuestion,
            Status = ClarificationStatus.Submitted,
            Priority = ClarificationPriority.Normal,
            SubmittedAt = DateTime.UtcNow,
            CreatedAt = DateTime.UtcNow
        };

        _context.Clarifications.Add(clarification);
        await _context.SaveChangesAsync(cancellationToken);

        return new BidderQuestionDto
        {
            Id = clarification.Id,
            ReferenceNumber = clarification.ReferenceNumber,
            Subject = clarification.Subject,
            Question = clarification.Question,
            RelatedBoqSection = clarification.RelatedBoqSection,
            IsAnonymous = clarification.IsAnonymous,
            SubmittedAt = clarification.SubmittedAt,
            StatusDisplay = "Submitted"
        };
    }

    private async Task<string> GenerateReferenceNumberAsync(Guid tenderId, CancellationToken cancellationToken)
    {
        // Get the count of existing clarifications for this tender
        var count = await _context.Clarifications
            .CountAsync(c => c.TenderId == tenderId, cancellationToken);

        // Generate reference in CL-XXX format (3-digit padded)
        return $"CL-{(count + 1):D3}";
    }
}
