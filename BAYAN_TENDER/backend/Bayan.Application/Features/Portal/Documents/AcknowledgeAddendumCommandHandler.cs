using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Portal.Documents;

/// <summary>
/// Handler for AcknowledgeAddendumCommand.
/// </summary>
public class AcknowledgeAddendumCommandHandler : IRequestHandler<AcknowledgeAddendumCommand, bool>
{
    private readonly IApplicationDbContext _context;

    public AcknowledgeAddendumCommandHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<bool> Handle(AcknowledgeAddendumCommand request, CancellationToken cancellationToken)
    {
        // Validate bidder access to tender
        var tenderBidder = await _context.TenderBidders
            .FirstOrDefaultAsync(tb => tb.TenderId == request.TenderId && tb.BidderId == request.BidderId, cancellationToken);

        if (tenderBidder == null)
        {
            throw new UnauthorizedAccessException("You do not have access to this tender.");
        }

        if (tenderBidder.QualificationStatus == QualificationStatus.Removed)
        {
            throw new UnauthorizedAccessException("You have been removed from this tender.");
        }

        // Get the addendum
        var addendum = await _context.Addenda
            .FirstOrDefaultAsync(a => a.Id == request.AddendumId && a.TenderId == request.TenderId, cancellationToken);

        if (addendum == null)
        {
            throw new NotFoundException("Addendum", request.AddendumId);
        }

        if (addendum.Status != AddendumStatus.Issued)
        {
            throw new InvalidOperationException("This addendum has not been issued yet.");
        }

        // Check if already acknowledged
        var existingAck = await _context.AddendumAcknowledgments
            .FirstOrDefaultAsync(ack => ack.AddendumId == request.AddendumId && ack.BidderId == request.BidderId, cancellationToken);

        if (existingAck != null)
        {
            if (existingAck.AcknowledgedAt != null)
            {
                // Already acknowledged, return success
                return true;
            }

            // Update existing acknowledgment
            existingAck.AcknowledgedAt = DateTime.UtcNow;
        }
        else
        {
            // Create new acknowledgment
            var acknowledgment = new AddendumAcknowledgment
            {
                Id = Guid.NewGuid(),
                AddendumId = request.AddendumId,
                BidderId = request.BidderId,
                AcknowledgedAt = DateTime.UtcNow,
                CreatedAt = DateTime.UtcNow
            };

            _context.AddendumAcknowledgments.Add(acknowledgment);
        }

        await _context.SaveChangesAsync(cancellationToken);
        return true;
    }
}
