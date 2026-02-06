using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Addenda.Commands.AcknowledgeAddendum;

/// <summary>
/// Handler for the AcknowledgeAddendumCommand.
/// </summary>
public class AcknowledgeAddendumCommandHandler : IRequestHandler<AcknowledgeAddendumCommand, bool>
{
    private readonly IApplicationDbContext _context;
    private readonly ILogger<AcknowledgeAddendumCommandHandler> _logger;

    public AcknowledgeAddendumCommandHandler(
        IApplicationDbContext context,
        ILogger<AcknowledgeAddendumCommandHandler> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task<bool> Handle(
        AcknowledgeAddendumCommand request,
        CancellationToken cancellationToken)
    {
        // Verify the addendum exists and is issued
        var addendum = await _context.Addenda
            .FirstOrDefaultAsync(a => a.Id == request.AddendumId && a.TenderId == request.TenderId,
                cancellationToken);

        if (addendum == null)
        {
            throw new NotFoundException("Addendum", request.AddendumId);
        }

        if (addendum.Status != AddendumStatus.Issued)
        {
            throw new InvalidOperationException(
                $"Cannot acknowledge addendum in '{addendum.Status}' status. Addendum must be issued.");
        }

        // Verify the bidder is qualified for this tender
        var tenderBidder = await _context.TenderBidders
            .FirstOrDefaultAsync(tb => tb.TenderId == request.TenderId &&
                                       tb.BidderId == request.BidderId &&
                                       tb.QualificationStatus == QualificationStatus.Qualified,
                cancellationToken);

        if (tenderBidder == null)
        {
            throw new InvalidOperationException(
                "Bidder is not qualified for this tender or does not exist.");
        }

        // Find the acknowledgment record
        var acknowledgment = await _context.AddendumAcknowledgments
            .FirstOrDefaultAsync(ack => ack.AddendumId == request.AddendumId &&
                                        ack.BidderId == request.BidderId,
                cancellationToken);

        if (acknowledgment == null)
        {
            throw new NotFoundException(
                $"No acknowledgment record found for Bidder {request.BidderId} on Addendum {request.AddendumId}");
        }

        // Check if already acknowledged
        if (acknowledgment.AcknowledgedAt.HasValue)
        {
            _logger.LogInformation(
                "Bidder {BidderId} has already acknowledged Addendum #{AddendumId} at {AcknowledgedAt}",
                request.BidderId, request.AddendumId, acknowledgment.AcknowledgedAt);
            return true; // Already acknowledged, return success
        }

        // Update acknowledgment
        acknowledgment.AcknowledgedAt = DateTime.UtcNow;
        acknowledgment.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation(
            "Bidder {BidderId} acknowledged Addendum #{AddendumNumber} for Tender {TenderId}",
            request.BidderId, addendum.AddendumNumber, request.TenderId);

        return true;
    }
}
