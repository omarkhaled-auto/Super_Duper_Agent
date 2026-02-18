using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Tenders.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Queries.GetTenderById;

/// <summary>
/// Handler for the GetTenderByIdQuery.
/// </summary>
public class GetTenderByIdQueryHandler : IRequestHandler<GetTenderByIdQuery, TenderDetailDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public GetTenderByIdQueryHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<TenderDetailDto?> Handle(
        GetTenderByIdQuery request,
        CancellationToken cancellationToken)
    {
        var tender = await _context.Tenders
            .Include(t => t.Client)
            .Include(t => t.Creator)
            .Include(t => t.EvaluationCriteria.OrderBy(c => c.SortOrder))
            .Include(t => t.TenderBidders)
                .ThenInclude(tb => tb.Bidder)
            .Include(t => t.BidSubmissions)
            .Include(t => t.Documents)
            .Include(t => t.Clarifications)
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == request.Id, cancellationToken);

        if (tender == null)
        {
            return null;
        }

        var dto = new TenderDetailDto
        {
            Id = tender.Id,
            Title = tender.Title,
            Reference = tender.Reference,
            Description = tender.Description,
            ClientId = tender.ClientId,
            ClientName = tender.Client.Name,
            TenderType = tender.TenderType,
            BaseCurrency = tender.BaseCurrency,
            EstimatedValue = tender.EstimatedValue,
            BidValidityDays = tender.BidValidityDays,
            IssueDate = tender.IssueDate,
            ClarificationDeadline = tender.ClarificationDeadline,
            SubmissionDeadline = tender.SubmissionDeadline,
            OpeningDate = tender.OpeningDate,
            TechnicalWeight = tender.TechnicalWeight,
            CommercialWeight = tender.CommercialWeight,
            PricingLevel = tender.PricingLevel,
            Status = tender.Status,
            PublishedAt = tender.PublishedAt,
            AwardedAt = tender.AwardedAt,
            CreatedBy = tender.CreatedBy,
            CreatedByName = tender.Creator?.FullName,
            CreatedAt = tender.CreatedAt,
            UpdatedAt = tender.UpdatedAt,
            EvaluationCriteria = tender.EvaluationCriteria
                .Select(c => new EvaluationCriterionDto
                {
                    Id = c.Id,
                    Name = c.Name,
                    WeightPercentage = c.WeightPercentage,
                    GuidanceNotes = c.GuidanceNotes,
                    SortOrder = c.SortOrder
                }).ToList(),
            Bidders = tender.TenderBidders
                .Select(tb => new TenderBidderDto
                {
                    Id = tb.Id,
                    BidderId = tb.BidderId,
                    CompanyName = tb.Bidder.CompanyName,
                    ContactPerson = tb.Bidder.ContactPerson,
                    Email = tb.Bidder.Email,
                    InvitationSentAt = tb.InvitationSentAt,
                    RegisteredAt = tb.RegisteredAt,
                    NdaStatus = tb.NdaStatus,
                    QualificationStatus = tb.QualificationStatus
                }).ToList(),
            BidCount = tender.BidSubmissions.Count,
            DocumentCount = tender.Documents.Count,
            ClarificationCount = tender.Clarifications.Count
        };

        return dto;
    }
}
