using System.Text.Json;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Bids.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Bids.Commands.OpenBids;

/// <summary>
/// Handler for the OpenBidsCommand.
/// This is an IRREVERSIBLE action.
/// </summary>
public class OpenBidsCommandHandler : IRequestHandler<OpenBidsCommand, OpenBidsResultDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;

    public OpenBidsCommandHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _currentUserService = currentUserService;
    }

    public async Task<OpenBidsResultDto> Handle(
        OpenBidsCommand request,
        CancellationToken cancellationToken)
    {
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new InvalidOperationException($"Tender with ID {request.TenderId} not found.");
        }

        // Get all bids for the tender that have status Submitted
        var bidsToOpen = await _context.BidSubmissions
            .Include(b => b.Bidder)
            .Where(b => b.TenderId == request.TenderId && b.Status == BidSubmissionStatus.Submitted)
            .ToListAsync(cancellationToken);

        var openedAt = DateTime.UtcNow;
        var openedBy = _currentUserService.UserId ?? Guid.Empty;

        // Get user info for audit
        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.Id == openedBy, cancellationToken);

        var openedByName = user != null ? $"{user.FirstName} {user.LastName}" : "System";

        // Open all bids
        foreach (var bid in bidsToOpen)
        {
            bid.Status = BidSubmissionStatus.Opened;
            bid.UpdatedAt = openedAt;
        }

        // Update tender status to Evaluation if it was Active
        if (tender.Status == TenderStatus.Active)
        {
            tender.Status = TenderStatus.Evaluation;
            tender.LastModifiedBy = openedBy;
            tender.LastModifiedAt = openedAt;
            tender.UpdatedAt = openedAt;
        }

        // Create audit log entry for this IRREVERSIBLE action
        var auditLog = new AuditLog
        {
            Id = Guid.NewGuid(),
            UserId = openedBy,
            UserEmail = _currentUserService.Email,
            Action = "Bids.Opened",
            EntityType = "Tender",
            EntityId = request.TenderId,
            OldValues = JsonSerializer.Serialize(new
            {
                BidCount = bidsToOpen.Count,
                PreviousTenderStatus = tender.Status.ToString()
            }),
            NewValues = JsonSerializer.Serialize(new
            {
                BidsOpened = bidsToOpen.Select(b => new
                {
                    b.Id,
                    BidderName = b.Bidder.CompanyName,
                    b.NativeCurrency,
                    b.NativeTotalAmount,
                    b.NormalizedTotalAmount,
                    b.IsLate,
                    b.LateAccepted
                }).ToList(),
                NewTenderStatus = TenderStatus.Evaluation.ToString(),
                OpenedAt = openedAt
            }),
            CreatedAt = openedAt
        };

        _context.AuditLogs.Add(auditLog);

        await _context.SaveChangesAsync(cancellationToken);

        return new OpenBidsResultDto
        {
            TenderId = request.TenderId,
            TenderReference = tender.Reference,
            BidsOpenedCount = bidsToOpen.Count,
            OpenedAt = openedAt,
            OpenedBy = openedBy,
            OpenedByName = openedByName,
            AuditLogId = auditLog.Id,
            OpenedBids = bidsToOpen.Select(b => new OpenedBidSummaryDto
            {
                BidId = b.Id,
                BidderName = b.Bidder.CompanyName,
                NativeCurrency = b.NativeCurrency,
                NativeTotalAmount = b.NativeTotalAmount,
                NormalizedTotalAmount = b.NormalizedTotalAmount,
                IsLate = b.IsLate,
                LateAccepted = b.LateAccepted
            }).OrderBy(b => b.NormalizedTotalAmount ?? decimal.MaxValue).ToList()
        };
    }
}
