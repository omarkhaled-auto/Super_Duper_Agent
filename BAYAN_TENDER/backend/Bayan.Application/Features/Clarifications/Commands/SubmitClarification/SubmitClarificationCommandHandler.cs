using AutoMapper;
using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Clarifications.DTOs;
using Bayan.Application.Features.Clarifications.Queries.GetNextClarificationRef;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Clarifications.Commands.SubmitClarification;

/// <summary>
/// Handler for the SubmitClarificationCommand.
/// </summary>
public class SubmitClarificationCommandHandler : IRequestHandler<SubmitClarificationCommand, ClarificationDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;
    private readonly IMediator _mediator;

    public SubmitClarificationCommandHandler(
        IApplicationDbContext context,
        IMapper mapper,
        IMediator mediator)
    {
        _context = context;
        _mapper = mapper;
        _mediator = mediator;
    }

    public async Task<ClarificationDto> Handle(
        SubmitClarificationCommand request,
        CancellationToken cancellationToken)
    {
        // Verify tender exists and is in a valid state
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new NotFoundException("Tender", request.TenderId);
        }

        // Ensure tender is in Active status and within clarification deadline
        if (tender.Status != TenderStatus.Active)
        {
            throw new InvalidOperationException(
                $"Cannot submit clarification for tender in '{tender.Status}' status. " +
                "Tender must be in Active status.");
        }

        if (DateTime.UtcNow > tender.ClarificationDeadline)
        {
            throw new InvalidOperationException(
                "The clarification submission deadline has passed.");
        }

        // Verify bidder exists and is invited to this tender
        var tenderBidder = await _context.TenderBidders
            .FirstOrDefaultAsync(tb => tb.TenderId == request.TenderId &&
                                       tb.BidderId == request.BidderId, cancellationToken);

        if (tenderBidder == null)
        {
            throw new InvalidOperationException(
                "Bidder is not invited to this tender.");
        }

        // Generate reference number
        var referenceNumber = await _mediator.Send(
            new GetNextClarificationRefQuery(request.TenderId), cancellationToken);

        var clarification = new Clarification
        {
            Id = Guid.NewGuid(),
            TenderId = request.TenderId,
            ReferenceNumber = referenceNumber,
            Subject = request.Subject,
            Question = request.Question,
            SubmittedByBidderId = request.BidderId,
            RelatedBoqSection = request.RelatedBoqSection,
            RelatedDocumentId = request.RelatedDocumentId,
            IsAnonymous = request.IsAnonymous,
            ClarificationType = ClarificationType.BidderQuestion,
            Status = ClarificationStatus.Submitted,
            Priority = ClarificationPriority.Normal,
            SubmittedAt = DateTime.UtcNow,
            CreatedAt = DateTime.UtcNow
        };

        _context.Clarifications.Add(clarification);
        await _context.SaveChangesAsync(cancellationToken);

        // Reload with navigation properties for mapping
        clarification = await _context.Clarifications
            .Include(c => c.SubmittedByBidder)
            .FirstAsync(c => c.Id == clarification.Id, cancellationToken);

        return _mapper.Map<ClarificationDto>(clarification);
    }
}
