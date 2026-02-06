using AutoMapper;
using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Clarifications.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Clarifications.Commands.MarkDuplicate;

/// <summary>
/// Handler for the MarkDuplicateCommand.
/// </summary>
public class MarkDuplicateCommandHandler : IRequestHandler<MarkDuplicateCommand, ClarificationDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public MarkDuplicateCommandHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<ClarificationDto> Handle(
        MarkDuplicateCommand request,
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

        // Verify original clarification exists and belongs to the same tender
        var originalClarification = await _context.Clarifications
            .FirstOrDefaultAsync(c => c.TenderId == request.TenderId &&
                                      c.Id == request.OriginalClarificationId, cancellationToken);

        if (originalClarification == null)
        {
            throw new NotFoundException("Original Clarification", request.OriginalClarificationId);
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
                $"Cannot mark clarification as duplicate when in '{clarification.Status}' status.");
        }

        // Prevent marking as duplicate of a duplicate
        if (originalClarification.Status == ClarificationStatus.Duplicate)
        {
            throw new InvalidOperationException(
                "Cannot mark as duplicate of a clarification that is itself a duplicate. " +
                "Please reference the original clarification.");
        }

        // Update the clarification
        clarification.Status = ClarificationStatus.Duplicate;
        clarification.DuplicateOfId = request.OriginalClarificationId;
        clarification.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync(cancellationToken);

        // Reload for mapping
        clarification = await _context.Clarifications
            .Include(c => c.SubmittedByBidder)
            .Include(c => c.SubmittedByUser)
            .Include(c => c.DuplicateOf)
            .FirstAsync(c => c.Id == clarification.Id, cancellationToken);

        return _mapper.Map<ClarificationDto>(clarification);
    }
}
