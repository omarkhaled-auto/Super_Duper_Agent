using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Portal.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Portal.Queries;

/// <summary>
/// Handler for GetPortalTenderInfoQuery.
/// </summary>
public class GetPortalTenderInfoQueryHandler : IRequestHandler<GetPortalTenderInfoQuery, PortalTenderDto>
{
    private readonly IApplicationDbContext _context;

    public GetPortalTenderInfoQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<PortalTenderDto> Handle(GetPortalTenderInfoQuery request, CancellationToken cancellationToken)
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

        // Get tender with client
        var tender = await _context.Tenders
            .Include(t => t.Client)
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new NotFoundException("Tender", request.TenderId);
        }

        var now = DateTime.UtcNow;
        var timeUntilSubmission = tender.SubmissionDeadline - now;

        return new PortalTenderDto
        {
            Id = tender.Id,
            Title = tender.Title,
            Reference = tender.Reference,
            ClientName = tender.Client.Name,
            Status = tender.Status,
            StatusDisplay = GetStatusDisplay(tender.Status),
            IssueDate = tender.IssueDate,
            ClarificationDeadline = tender.ClarificationDeadline,
            SubmissionDeadline = tender.SubmissionDeadline,
            OpeningDate = tender.OpeningDate,
            DaysUntilSubmission = Math.Max(0, (int)timeUntilSubmission.TotalDays),
            HoursUntilSubmission = Math.Max(0, (int)(timeUntilSubmission.TotalHours % 24)),
            IsClarificationClosed = now > tender.ClarificationDeadline,
            IsSubmissionClosed = now > tender.SubmissionDeadline,
            BaseCurrency = tender.BaseCurrency,
            BidValidityDays = tender.BidValidityDays,
            Description = tender.Description
        };
    }

    private static string GetStatusDisplay(TenderStatus status)
    {
        return status switch
        {
            TenderStatus.Draft => "Draft",
            TenderStatus.Active => "Open for Bidding",
            TenderStatus.Evaluation => "Under Evaluation",
            TenderStatus.Awarded => "Awarded",
            TenderStatus.Cancelled => "Cancelled",
            _ => status.ToString()
        };
    }
}
