using AutoMapper;
using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Tenders.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Commands.InviteBidders;

/// <summary>
/// Handler for the InviteBiddersCommand.
/// </summary>
public class InviteBiddersCommandHandler : IRequestHandler<InviteBiddersCommand, InviteBiddersResult>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;
    private readonly IEmailService _emailService;

    public InviteBiddersCommandHandler(
        IApplicationDbContext context,
        IMapper mapper,
        IEmailService emailService)
    {
        _context = context;
        _mapper = mapper;
        _emailService = emailService;
    }

    public async Task<InviteBiddersResult> Handle(
        InviteBiddersCommand request,
        CancellationToken cancellationToken)
    {
        // Verify tender exists
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new NotFoundException(nameof(Tender), request.TenderId);
        }

        // Get existing invitations for this tender
        var existingBidderIds = await _context.TenderBidders
            .Where(tb => tb.TenderId == request.TenderId)
            .Select(tb => tb.BidderId)
            .ToListAsync(cancellationToken);

        // Get bidders to invite (excluding already invited)
        var newBidderIds = request.BidderIds
            .Except(existingBidderIds)
            .ToList();

        // Verify all bidder IDs exist
        var bidders = await _context.Bidders
            .Where(b => newBidderIds.Contains(b.Id) && b.IsActive)
            .ToListAsync(cancellationToken);

        var result = new InviteBiddersResult
        {
            AlreadyInvitedCount = request.BidderIds.Count - newBidderIds.Count
        };

        var invitedTenderBidders = new List<TenderBidder>();

        foreach (var bidder in bidders)
        {
            var tenderBidder = new TenderBidder
            {
                Id = Guid.NewGuid(),
                TenderId = request.TenderId,
                BidderId = bidder.Id,
                InvitationSentAt = DateTime.UtcNow,
                NdaStatus = NdaStatus.Pending,
                QualificationStatus = QualificationStatus.Pending,
                CreatedAt = DateTime.UtcNow
            };

            _context.TenderBidders.Add(tenderBidder);
            invitedTenderBidders.Add(tenderBidder);

            // Send invitation email
            try
            {
                await _emailService.SendTenderInvitationEmailAsync(
                    bidder.Email,
                    bidder.ContactPerson,
                    tender.Title,
                    tender.Reference,
                    tender.SubmissionDeadline,
                    cancellationToken);
            }
            catch
            {
                // Log error but don't fail the operation
                // Email sending failures should not prevent invitation creation
            }
        }

        await _context.SaveChangesAsync(cancellationToken);

        // Reload with bidder information for mapping
        var invitedIds = invitedTenderBidders.Select(tb => tb.Id).ToList();
        var reloadedTenderBidders = await _context.TenderBidders
            .Include(tb => tb.Bidder)
            .Where(tb => invitedIds.Contains(tb.Id))
            .ToListAsync(cancellationToken);

        result.InvitedCount = reloadedTenderBidders.Count;
        result.InvitedBidders = _mapper.Map<List<TenderBidderDto>>(reloadedTenderBidders);

        return result;
    }
}
