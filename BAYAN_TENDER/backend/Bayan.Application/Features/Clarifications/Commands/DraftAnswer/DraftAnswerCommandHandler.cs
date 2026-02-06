using AutoMapper;
using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Clarifications.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Clarifications.Commands.DraftAnswer;

/// <summary>
/// Handler for the DraftAnswerCommand.
/// </summary>
public class DraftAnswerCommandHandler : IRequestHandler<DraftAnswerCommand, ClarificationDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public DraftAnswerCommandHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<ClarificationDto> Handle(
        DraftAnswerCommand request,
        CancellationToken cancellationToken)
    {
        var clarification = await _context.Clarifications
            .Include(c => c.SubmittedByBidder)
            .Include(c => c.SubmittedByUser)
            .Include(c => c.Answerer)
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

        // Verify clarification is in a valid state for drafting answer
        var validStatuses = new[]
        {
            ClarificationStatus.Submitted,
            ClarificationStatus.Pending,
            ClarificationStatus.DraftAnswer
        };

        if (!validStatuses.Contains(clarification.Status))
        {
            throw new InvalidOperationException(
                $"Cannot draft answer for clarification in '{clarification.Status}' status. " +
                "Clarification must be in Submitted, Pending, or DraftAnswer status.");
        }

        // Update the clarification
        clarification.Answer = request.Answer;
        clarification.AnsweredBy = request.UserId;
        clarification.Status = ClarificationStatus.DraftAnswer;
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
