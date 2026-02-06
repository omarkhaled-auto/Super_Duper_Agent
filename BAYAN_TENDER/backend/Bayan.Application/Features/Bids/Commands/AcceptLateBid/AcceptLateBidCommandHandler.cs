using System.Text.Json;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Bids.DTOs;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bids.Commands.AcceptLateBid;

/// <summary>
/// Handler for the AcceptLateBidCommand.
/// </summary>
public class AcceptLateBidCommandHandler : IRequestHandler<AcceptLateBidCommand, LateBidDecisionDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;

    public AcceptLateBidCommandHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _currentUserService = currentUserService;
    }

    public async Task<LateBidDecisionDto> Handle(
        AcceptLateBidCommand request,
        CancellationToken cancellationToken)
    {
        var bid = await _context.BidSubmissions
            .Include(b => b.Bidder)
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

        // Accept the late bid
        bid.LateAccepted = true;
        bid.LateAcceptedBy = decisionBy;
        bid.UpdatedAt = decisionAt;

        // Create audit log entry
        var auditLog = new AuditLog
        {
            Id = Guid.NewGuid(),
            UserId = decisionBy,
            UserEmail = _currentUserService.Email,
            Action = "Bid.LateBidAccepted",
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
                LateAccepted = true,
                AcceptedBy = decisionByName,
                AcceptedAt = decisionAt
            }),
            CreatedAt = decisionAt
        };

        _context.AuditLogs.Add(auditLog);

        await _context.SaveChangesAsync(cancellationToken);

        return new LateBidDecisionDto
        {
            BidId = bid.Id,
            Accepted = true,
            Reason = null,
            DecisionBy = decisionBy,
            DecisionByName = decisionByName,
            DecisionAt = decisionAt,
            BidderName = bid.Bidder.CompanyName,
            BidderEmail = bid.Bidder.Email,
            NotificationSent = false // No notification needed for acceptance
        };
    }
}
