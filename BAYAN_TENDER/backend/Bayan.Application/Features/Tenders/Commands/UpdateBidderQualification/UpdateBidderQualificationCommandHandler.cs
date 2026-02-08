using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Commands.UpdateBidderQualification;

/// <summary>
/// Handler for UpdateBidderQualificationCommand.
/// </summary>
public class UpdateBidderQualificationCommandHandler : IRequestHandler<UpdateBidderQualificationCommand, Unit>
{
    private readonly IApplicationDbContext _context;

    public UpdateBidderQualificationCommandHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<Unit> Handle(UpdateBidderQualificationCommand request, CancellationToken cancellationToken)
    {
        // Verify tender exists
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new NotFoundException(nameof(Tender), request.TenderId);
        }

        // Find the tender-bidder relationship
        var tenderBidder = await _context.TenderBidders
            .FirstOrDefaultAsync(tb => tb.TenderId == request.TenderId && tb.BidderId == request.BidderId, cancellationToken);

        if (tenderBidder == null)
        {
            throw new NotFoundException(nameof(TenderBidder), new { request.TenderId, request.BidderId });
        }

        // Parse and set qualification status
        if (!Enum.TryParse<QualificationStatus>(request.QualificationStatus, true, out var status))
        {
            throw new InvalidOperationException($"Invalid qualification status: {request.QualificationStatus}. Valid values are: Qualified, Rejected.");
        }

        tenderBidder.QualificationStatus = status;
        tenderBidder.QualifiedAt = status == QualificationStatus.Qualified ? DateTime.UtcNow : null;
        tenderBidder.QualificationReason = request.Reason;
        tenderBidder.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync(cancellationToken);

        return Unit.Value;
    }
}
