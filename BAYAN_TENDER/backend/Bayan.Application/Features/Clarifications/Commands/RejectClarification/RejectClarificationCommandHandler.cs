using AutoMapper;
using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Clarifications.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Clarifications.Commands.RejectClarification;

/// <summary>
/// Handler for the RejectClarificationCommand.
/// </summary>
public class RejectClarificationCommandHandler : IRequestHandler<RejectClarificationCommand, ClarificationDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public RejectClarificationCommandHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<ClarificationDto> Handle(
        RejectClarificationCommand request,
        CancellationToken cancellationToken)
    {
        var clarification = await _context.Clarifications
            .Include(c => c.SubmittedByBidder)
            .Include(c => c.SubmittedByUser)
            .FirstOrDefaultAsync(c => c.TenderId == request.TenderId &&
                                      c.Id == request.ClarificationId, cancellationToken);

        if (clarification == null)
        {
            throw new NotFoundException("Clarification", request.ClarificationId);
        }

        // Verify user exists
        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.Id == request.UserId, cancellationToken);

        if (user == null)
        {
            throw new NotFoundException("User", request.UserId);
        }

        // Verify clarification is in a valid state
        var terminalStatuses = new[]
        {
            ClarificationStatus.Published,
            ClarificationStatus.Duplicate,
            ClarificationStatus.Rejected
        };

        if (terminalStatuses.Contains(clarification.Status))
        {
            throw new InvalidOperationException(
                $"Cannot reject clarification when in '{clarification.Status}' status.");
        }

        // Update the clarification
        clarification.Status = ClarificationStatus.Rejected;
        // Store rejection reason in Answer field for simplicity
        // In a production system, you might want a separate RejectionReason field
        clarification.Answer = $"[REJECTED] {request.Reason}";
        clarification.AnsweredBy = request.UserId;
        clarification.AnsweredAt = DateTime.UtcNow;
        clarification.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync(cancellationToken);

        // Reload for mapping
        clarification = await _context.Clarifications
            .Include(c => c.SubmittedByBidder)
            .Include(c => c.SubmittedByUser)
            .Include(c => c.Answerer)
            .FirstAsync(c => c.Id == clarification.Id, cancellationToken);

        return _mapper.Map<ClarificationDto>(clarification);
    }
}
