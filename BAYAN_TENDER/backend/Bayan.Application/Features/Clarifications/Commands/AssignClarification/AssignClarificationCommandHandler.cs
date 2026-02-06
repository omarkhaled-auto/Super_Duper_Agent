using AutoMapper;
using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Clarifications.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Clarifications.Commands.AssignClarification;

/// <summary>
/// Handler for the AssignClarificationCommand.
/// </summary>
public class AssignClarificationCommandHandler : IRequestHandler<AssignClarificationCommand, ClarificationDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public AssignClarificationCommandHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<ClarificationDto> Handle(
        AssignClarificationCommand request,
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

        // Verify user to assign to exists
        var assignToUser = await _context.Users
            .FirstOrDefaultAsync(u => u.Id == request.AssignToUserId, cancellationToken);

        if (assignToUser == null)
        {
            throw new NotFoundException("User", request.AssignToUserId);
        }

        // Verify clarification is in a valid state for assignment
        var terminalStatuses = new[]
        {
            ClarificationStatus.Published,
            ClarificationStatus.Duplicate,
            ClarificationStatus.Rejected
        };

        if (terminalStatuses.Contains(clarification.Status))
        {
            throw new InvalidOperationException(
                $"Cannot assign clarification when in '{clarification.Status}' status.");
        }

        // Update status to Pending if it was Submitted
        if (clarification.Status == ClarificationStatus.Submitted)
        {
            clarification.Status = ClarificationStatus.Pending;
        }

        clarification.AssignedToId = request.AssignToUserId;
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
