using System.Text.Json;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Bids.DTOs;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bids.Commands.RejectLateBid;

/// <summary>
/// Handler for the RejectLateBidCommand.
/// </summary>
public class RejectLateBidCommandHandler : IRequestHandler<RejectLateBidCommand, LateBidDecisionDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;
    private readonly IEmailService _emailService;

    public RejectLateBidCommandHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService,
        IEmailService emailService)
    {
        _context = context;
        _currentUserService = currentUserService;
        _emailService = emailService;
    }

    public async Task<LateBidDecisionDto> Handle(
        RejectLateBidCommand request,
        CancellationToken cancellationToken)
    {
        var bid = await _context.BidSubmissions
            .Include(b => b.Bidder)
            .Include(b => b.Tender)
            .FirstOrDefaultAsync(b => b.Id == request.BidId && b.TenderId == request.TenderId, cancellationToken);

        if (bid == null)
        {
            throw new InvalidOperationException($"Bid with ID {request.BidId} not found for tender {request.TenderId}.");
        }

        var decisionAt = DateTime.UtcNow;
        var decisionBy = _currentUserService.UserId ?? Guid.Empty;

        // Get user info
        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.Id == decisionBy, cancellationToken);

        var decisionByName = user != null ? $"{user.FirstName} {user.LastName}" : "System";

        // Reject the late bid
        bid.LateAccepted = false;
        bid.UpdatedAt = decisionAt;

        // Create audit log entry
        var auditLog = new AuditLog
        {
            Id = Guid.NewGuid(),
            UserId = decisionBy,
            UserEmail = _currentUserService.Email,
            Action = "Bid.LateBidRejected",
            EntityType = "BidSubmission",
            EntityId = request.BidId,
            OldValues = JsonSerializer.Serialize(new
            {
                bid.IsLate,
                LateAccepted = (bool?)null
            }),
            NewValues = JsonSerializer.Serialize(new
            {
                bid.IsLate,
                LateAccepted = false,
                RejectedBy = decisionByName,
                RejectedAt = decisionAt,
                Reason = request.Reason
            }),
            CreatedAt = decisionAt
        };

        _context.AuditLogs.Add(auditLog);

        await _context.SaveChangesAsync(cancellationToken);

        // Send notification to bidder
        var notificationSent = false;
        try
        {
            var mergeFields = new Dictionary<string, string>
            {
                { "BidderName", bid.Bidder.ContactPerson },
                { "CompanyName", bid.Bidder.CompanyName },
                { "TenderTitle", bid.Tender.Title },
                { "TenderReference", bid.Tender.Reference },
                { "SubmissionTime", bid.SubmissionTime.ToString("yyyy-MM-dd HH:mm:ss UTC") },
                { "RejectionReason", request.Reason },
                { "DecisionDate", decisionAt.ToString("yyyy-MM-dd HH:mm:ss UTC") }
            };

            await _emailService.SendTemplatedEmailAsync(
                bid.Bidder.Email,
                "LateBidRejectedTemplate",
                mergeFields,
                cancellationToken);

            notificationSent = true;
        }
        catch
        {
            // Log email failure but don't fail the command
            // The rejection is still valid even if email fails
        }

        return new LateBidDecisionDto
        {
            BidId = bid.Id,
            Accepted = false,
            Reason = request.Reason,
            DecisionBy = decisionBy,
            DecisionByName = decisionByName,
            DecisionAt = decisionAt,
            BidderName = bid.Bidder.CompanyName,
            BidderEmail = bid.Bidder.Email,
            NotificationSent = notificationSent
        };
    }
}
