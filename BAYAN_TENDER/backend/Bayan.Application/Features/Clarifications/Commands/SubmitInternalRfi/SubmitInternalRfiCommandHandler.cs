using AutoMapper;
using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Clarifications.DTOs;
using Bayan.Application.Features.Clarifications.Queries.GetNextClarificationRef;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Clarifications.Commands.SubmitInternalRfi;

/// <summary>
/// Handler for the SubmitInternalRfiCommand.
/// </summary>
public class SubmitInternalRfiCommandHandler : IRequestHandler<SubmitInternalRfiCommand, ClarificationDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;
    private readonly IMediator _mediator;

    public SubmitInternalRfiCommandHandler(
        IApplicationDbContext context,
        IMapper mapper,
        IMediator mediator)
    {
        _context = context;
        _mapper = mapper;
        _mediator = mediator;
    }

    public async Task<ClarificationDto> Handle(
        SubmitInternalRfiCommand request,
        CancellationToken cancellationToken)
    {
        // Verify tender exists
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new NotFoundException("Tender", request.TenderId);
        }

        // Verify user exists
        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.Id == request.UserId, cancellationToken);

        if (user == null)
        {
            throw new NotFoundException("User", request.UserId);
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
            SubmittedByUserId = request.UserId,
            RelatedBoqSection = request.RelatedBoqSection,
            RelatedDocumentId = request.RelatedDocumentId,
            IsAnonymous = false,
            ClarificationType = ClarificationType.InternalRFI,
            Status = ClarificationStatus.Submitted,
            Priority = request.Priority,
            SubmittedAt = DateTime.UtcNow,
            CreatedAt = DateTime.UtcNow
        };

        _context.Clarifications.Add(clarification);
        await _context.SaveChangesAsync(cancellationToken);

        // Reload with navigation properties for mapping
        clarification = await _context.Clarifications
            .Include(c => c.SubmittedByUser)
            .FirstAsync(c => c.Id == clarification.Id, cancellationToken);

        return _mapper.Map<ClarificationDto>(clarification);
    }
}
