using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Tenders.DTOs;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Commands.UpdateTender;

/// <summary>
/// Handler for the UpdateTenderCommand.
/// </summary>
public class UpdateTenderCommandHandler : IRequestHandler<UpdateTenderCommand, TenderDto?>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;
    private readonly ICurrentUserService _currentUserService;

    public UpdateTenderCommandHandler(
        IApplicationDbContext context,
        IMapper mapper,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _mapper = mapper;
        _currentUserService = currentUserService;
    }

    public async Task<TenderDto?> Handle(
        UpdateTenderCommand request,
        CancellationToken cancellationToken)
    {
        var tender = await _context.Tenders
            .Include(t => t.EvaluationCriteria)
            .Include(t => t.Client)
            .Include(t => t.TenderBidders)
            .FirstOrDefaultAsync(t => t.Id == request.Id, cancellationToken);

        if (tender == null)
        {
            return null;
        }

        // Update tender properties
        tender.Title = request.Title;
        tender.Description = request.Description;
        tender.ClientId = request.ClientId;
        tender.TenderType = request.TenderType;
        tender.BaseCurrency = request.BaseCurrency;
        tender.EstimatedValue = request.EstimatedValue;
        tender.BidValidityDays = request.BidValidityDays;
        tender.IssueDate = request.IssueDate;
        tender.ClarificationDeadline = request.ClarificationDeadline;
        tender.SubmissionDeadline = request.SubmissionDeadline;
        tender.OpeningDate = request.OpeningDate;
        tender.TechnicalWeight = request.TechnicalWeight;
        tender.CommercialWeight = request.CommercialWeight;
        tender.LastModifiedBy = _currentUserService.UserId;
        tender.LastModifiedAt = DateTime.UtcNow;
        tender.UpdatedAt = DateTime.UtcNow;

        // Handle evaluation criteria updates
        if (request.EvaluationCriteria != null)
        {
            // Get IDs of criteria in the request
            var requestCriteriaIds = request.EvaluationCriteria
                .Where(c => c.Id.HasValue)
                .Select(c => c.Id!.Value)
                .ToHashSet();

            // Remove criteria that are not in the request
            var criteriaToRemove = tender.EvaluationCriteria
                .Where(c => !requestCriteriaIds.Contains(c.Id))
                .ToList();

            foreach (var criterion in criteriaToRemove)
            {
                _context.EvaluationCriteria.Remove(criterion);
            }

            // Update or add criteria
            foreach (var criterionDto in request.EvaluationCriteria)
            {
                if (criterionDto.Id.HasValue)
                {
                    // Update existing criterion
                    var existingCriterion = tender.EvaluationCriteria
                        .FirstOrDefault(c => c.Id == criterionDto.Id.Value);

                    if (existingCriterion != null)
                    {
                        existingCriterion.Name = criterionDto.Name;
                        existingCriterion.WeightPercentage = criterionDto.WeightPercentage;
                        existingCriterion.GuidanceNotes = criterionDto.GuidanceNotes;
                        existingCriterion.SortOrder = criterionDto.SortOrder;
                        existingCriterion.UpdatedAt = DateTime.UtcNow;
                    }
                }
                else
                {
                    // Add new criterion
                    var newCriterion = new EvaluationCriteria
                    {
                        Id = Guid.NewGuid(),
                        TenderId = tender.Id,
                        Name = criterionDto.Name,
                        WeightPercentage = criterionDto.WeightPercentage,
                        GuidanceNotes = criterionDto.GuidanceNotes,
                        SortOrder = criterionDto.SortOrder,
                        CreatedAt = DateTime.UtcNow
                    };

                    tender.EvaluationCriteria.Add(newCriterion);
                }
            }
        }

        await _context.SaveChangesAsync(cancellationToken);

        // Reload client if changed
        if (tender.Client == null || tender.Client.Id != request.ClientId)
        {
            tender.Client = await _context.Clients
                .AsNoTracking()
                .FirstAsync(c => c.Id == request.ClientId, cancellationToken);
        }

        return new TenderDto
        {
            Id = tender.Id,
            Title = tender.Title,
            Reference = tender.Reference,
            ClientId = tender.ClientId,
            ClientName = tender.Client.Name,
            TenderType = tender.TenderType,
            BaseCurrency = tender.BaseCurrency,
            EstimatedValue = tender.EstimatedValue,
            Status = tender.Status,
            SubmissionDeadline = tender.SubmissionDeadline,
            BidderCount = tender.TenderBidders.Count,
            BidCount = 0, // Would need to load BidSubmissions if needed
            CreatedAt = tender.CreatedAt
        };
    }
}
