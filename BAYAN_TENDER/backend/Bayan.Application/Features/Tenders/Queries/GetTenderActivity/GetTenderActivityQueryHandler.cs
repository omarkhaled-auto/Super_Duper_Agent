using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Tenders.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Queries.GetTenderActivity;

/// <summary>
/// Handler for the GetTenderActivityQuery.
/// Aggregates recent activity from various related entities.
/// </summary>
public class GetTenderActivityQueryHandler : IRequestHandler<GetTenderActivityQuery, List<TenderActivityDto>>
{
    private readonly IApplicationDbContext _context;

    public GetTenderActivityQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<List<TenderActivityDto>> Handle(
        GetTenderActivityQuery request,
        CancellationToken cancellationToken)
    {
        var activities = new List<TenderActivityDto>();

        // Get tender details for creation/update activities
        var tender = await _context.Tenders
            .Include(t => t.Creator)
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            return activities;
        }

        // Add tender creation activity
        activities.Add(new TenderActivityDto
        {
            ActivityType = "TenderCreated",
            Description = "Tender was created",
            PerformedBy = tender.Creator?.FullName,
            PerformedById = tender.CreatedBy,
            OccurredAt = tender.CreatedAt
        });

        // Add published activity if applicable
        if (tender.PublishedAt.HasValue)
        {
            activities.Add(new TenderActivityDto
            {
                ActivityType = "TenderPublished",
                Description = "Tender was published and opened for bidding",
                PerformedBy = tender.Creator?.FullName,
                PerformedById = tender.CreatedBy,
                OccurredAt = tender.PublishedAt.Value
            });
        }

        // Add awarded activity if applicable
        if (tender.AwardedAt.HasValue)
        {
            activities.Add(new TenderActivityDto
            {
                ActivityType = "TenderAwarded",
                Description = "Tender was awarded",
                OccurredAt = tender.AwardedAt.Value
            });
        }

        // Get bidder invitation activities
        var bidderActivities = await _context.TenderBidders
            .Where(tb => tb.TenderId == request.TenderId && tb.InvitationSentAt.HasValue)
            .Include(tb => tb.Bidder)
            .AsNoTracking()
            .Select(tb => new TenderActivityDto
            {
                ActivityType = "BidderInvited",
                Description = $"Invitation sent to {tb.Bidder.CompanyName}",
                OccurredAt = tb.InvitationSentAt!.Value,
                Details = tb.Bidder.Email
            })
            .ToListAsync(cancellationToken);

        activities.AddRange(bidderActivities);

        // Get bidder registration activities
        var registrationActivities = await _context.TenderBidders
            .Where(tb => tb.TenderId == request.TenderId && tb.RegisteredAt.HasValue)
            .Include(tb => tb.Bidder)
            .AsNoTracking()
            .Select(tb => new TenderActivityDto
            {
                ActivityType = "BidderRegistered",
                Description = $"{tb.Bidder.CompanyName} registered for the tender",
                OccurredAt = tb.RegisteredAt!.Value
            })
            .ToListAsync(cancellationToken);

        activities.AddRange(registrationActivities);

        // Get bid submission activities
        var bidActivities = await _context.BidSubmissions
            .Where(bs => bs.TenderId == request.TenderId)
            .Include(bs => bs.Bidder)
            .AsNoTracking()
            .Select(bs => new TenderActivityDto
            {
                ActivityType = "BidSubmitted",
                Description = $"Bid submitted by {bs.Bidder.CompanyName}",
                OccurredAt = bs.SubmissionTime
            })
            .ToListAsync(cancellationToken);

        activities.AddRange(bidActivities);

        // Get clarification activities
        var clarificationActivities = await _context.Clarifications
            .Where(c => c.TenderId == request.TenderId && c.SubmittedByBidderId.HasValue)
            .Include(c => c.SubmittedByBidder)
            .AsNoTracking()
            .Select(c => new TenderActivityDto
            {
                ActivityType = "ClarificationSubmitted",
                Description = $"Clarification submitted by {c.SubmittedByBidder!.CompanyName}",
                OccurredAt = c.SubmittedAt,
                Details = c.Subject
            })
            .ToListAsync(cancellationToken);

        activities.AddRange(clarificationActivities);

        // Get addendum activities
        var addendumActivities = await _context.Addenda
            .Where(a => a.TenderId == request.TenderId)
            .AsNoTracking()
            .Select(a => new TenderActivityDto
            {
                ActivityType = "AddendumIssued",
                Description = $"Addendum #{a.AddendumNumber} issued: {a.Summary}",
                OccurredAt = a.IssuedAt ?? a.CreatedAt
            })
            .ToListAsync(cancellationToken);

        activities.AddRange(addendumActivities);

        // Sort by occurrence date descending and limit
        return activities
            .OrderByDescending(a => a.OccurredAt)
            .Take(request.Limit)
            .ToList();
    }
}
