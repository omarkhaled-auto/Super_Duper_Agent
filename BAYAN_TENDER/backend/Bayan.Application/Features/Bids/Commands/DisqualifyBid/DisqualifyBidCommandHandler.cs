using System.Text.Json;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Bids.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bids.Commands.DisqualifyBid;

/// <summary>
/// Handler for the DisqualifyBidCommand.
/// </summary>
public class DisqualifyBidCommandHandler : IRequestHandler<DisqualifyBidCommand, DisqualifyBidResultDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;

    public DisqualifyBidCommandHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _currentUserService = currentUserService;
    }

    public async Task<DisqualifyBidResultDto> Handle(
        DisqualifyBidCommand request,
        CancellationToken cancellationToken)
    {
        var bid = await _context.BidSubmissions
            .Include(b => b.Bidder)
            .FirstOrDefaultAsync(b => b.Id == request.BidId && b.TenderId == request.TenderId, cancellationToken);

        if (bid == null)
        {
            throw new InvalidOperationException($"Bid with ID {request.BidId} not found for tender {request.TenderId}.");
        }

        var disqualifiedAt = DateTime.UtcNow;
        var disqualifiedBy = _currentUserService.UserId ?? Guid.Empty;

        // Get user info
        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.Id == disqualifiedBy, cancellationToken);

        var disqualifiedByName = user != null ? $"{user.FirstName} {user.LastName}" : "System";

        var previousStatus = bid.Status;

        // Disqualify the bid
        bid.Status = BidSubmissionStatus.Disqualified;
        bid.UpdatedAt = disqualifiedAt;

        // Create audit log entry
        var auditLog = new AuditLog
        {
            Id = Guid.NewGuid(),
            UserId = disqualifiedBy,
            UserEmail = _currentUserService.Email,
            Action = "Bid.Disqualified",
            EntityType = "BidSubmission",
            EntityId = request.BidId,
            OldValues = JsonSerializer.Serialize(new
            {
                Status = previousStatus.ToString()
            }),
            NewValues = JsonSerializer.Serialize(new
            {
                Status = BidSubmissionStatus.Disqualified.ToString(),
                DisqualifiedBy = disqualifiedByName,
                DisqualifiedAt = disqualifiedAt,
                Reason = request.Reason
            }),
            CreatedAt = disqualifiedAt
        };

        _context.AuditLogs.Add(auditLog);

        await _context.SaveChangesAsync(cancellationToken);

        return new DisqualifyBidResultDto
        {
            BidId = bid.Id,
            Reason = request.Reason,
            DisqualifiedBy = disqualifiedBy,
            DisqualifiedByName = disqualifiedByName,
            DisqualifiedAt = disqualifiedAt,
            BidderName = bid.Bidder.CompanyName
        };
    }
}
