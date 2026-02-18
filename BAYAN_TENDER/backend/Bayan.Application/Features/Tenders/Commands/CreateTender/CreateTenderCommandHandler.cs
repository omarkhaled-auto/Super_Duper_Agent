using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Tenders.DTOs;
using Bayan.Application.Features.Tenders.Queries.GetNextTenderReference;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Commands.CreateTender;

/// <summary>
/// Handler for the CreateTenderCommand.
/// </summary>
public class CreateTenderCommandHandler : IRequestHandler<CreateTenderCommand, TenderDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;
    private readonly IMediator _mediator;
    private readonly ICurrentUserService _currentUserService;

    public CreateTenderCommandHandler(
        IApplicationDbContext context,
        IMapper mapper,
        IMediator mediator,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _mapper = mapper;
        _mediator = mediator;
        _currentUserService = currentUserService;
    }

    public async Task<TenderDto> Handle(
        CreateTenderCommand request,
        CancellationToken cancellationToken)
    {
        // Generate the next reference number
        var reference = await _mediator.Send(new GetNextTenderReferenceQuery(), cancellationToken);

        // Create the tender entity
        var tender = new Tender
        {
            Id = Guid.NewGuid(),
            Title = request.Title,
            Reference = reference,
            Description = request.Description,
            ClientId = request.ClientId,
            TenderType = request.TenderType,
            BaseCurrency = request.BaseCurrency,
            EstimatedValue = request.EstimatedValue,
            BidValidityDays = request.BidValidityDays,
            IssueDate = request.IssueDate,
            ClarificationDeadline = request.ClarificationDeadline,
            SubmissionDeadline = request.SubmissionDeadline,
            OpeningDate = request.OpeningDate,
            TechnicalWeight = request.TechnicalWeight,
            CommercialWeight = request.CommercialWeight,
            PricingLevel = request.PricingLevel,
            Status = TenderStatus.Draft,
            CreatedBy = _currentUserService.UserId,
            CreatedAt = DateTime.UtcNow
        };

        // Add evaluation criteria if provided
        if (request.EvaluationCriteria?.Any() == true)
        {
            foreach (var criterionDto in request.EvaluationCriteria)
            {
                var criterion = new EvaluationCriteria
                {
                    Id = Guid.NewGuid(),
                    TenderId = tender.Id,
                    Name = criterionDto.Name,
                    WeightPercentage = criterionDto.WeightPercentage,
                    GuidanceNotes = criterionDto.GuidanceNotes,
                    SortOrder = criterionDto.SortOrder,
                    CreatedAt = DateTime.UtcNow
                };

                tender.EvaluationCriteria.Add(criterion);
            }
        }

        _context.Tenders.Add(tender);
        await _context.SaveChangesAsync(cancellationToken);

        // Load the client for the DTO
        var client = await _context.Clients
            .AsNoTracking()
            .FirstOrDefaultAsync(c => c.Id == tender.ClientId, cancellationToken);

        return new TenderDto
        {
            Id = tender.Id,
            Title = tender.Title,
            Reference = tender.Reference,
            ClientId = tender.ClientId,
            ClientName = client?.Name ?? string.Empty,
            TenderType = tender.TenderType,
            BaseCurrency = tender.BaseCurrency,
            EstimatedValue = tender.EstimatedValue,
            Status = tender.Status,
            SubmissionDeadline = tender.SubmissionDeadline,
            BidderCount = 0,
            BidCount = 0,
            CreatedAt = tender.CreatedAt,
            PricingLevel = tender.PricingLevel
        };
    }
}
