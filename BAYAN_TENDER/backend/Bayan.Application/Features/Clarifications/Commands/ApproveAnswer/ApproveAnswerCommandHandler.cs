using AutoMapper;
using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Clarifications.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Clarifications.Commands.ApproveAnswer;

/// <summary>
/// Handler for the ApproveAnswerCommand.
/// </summary>
public class ApproveAnswerCommandHandler : IRequestHandler<ApproveAnswerCommand, ClarificationDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public ApproveAnswerCommandHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<ClarificationDto> Handle(
        ApproveAnswerCommand request,
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

        // Verify clarification has a draft answer
        if (clarification.Status != ClarificationStatus.DraftAnswer)
        {
            throw new InvalidOperationException(
                $"Cannot approve answer for clarification in '{clarification.Status}' status. " +
                "Clarification must be in DraftAnswer status.");
        }

        if (string.IsNullOrWhiteSpace(clarification.Answer))
        {
            throw new InvalidOperationException(
                "Cannot approve clarification without an answer.");
        }

        // Update the clarification
        clarification.Status = ClarificationStatus.Answered;
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
