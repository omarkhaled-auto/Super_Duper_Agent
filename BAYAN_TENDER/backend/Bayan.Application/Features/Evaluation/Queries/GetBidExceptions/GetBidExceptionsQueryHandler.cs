using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Evaluation.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Evaluation.Queries.GetBidExceptions;

/// <summary>
/// Handler for GetBidExceptionsQuery.
/// </summary>
public class GetBidExceptionsQueryHandler : IRequestHandler<GetBidExceptionsQuery, BidExceptionListDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ILogger<GetBidExceptionsQueryHandler> _logger;

    public GetBidExceptionsQueryHandler(
        IApplicationDbContext context,
        ILogger<GetBidExceptionsQueryHandler> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task<BidExceptionListDto> Handle(
        GetBidExceptionsQuery request,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation("Getting bid exceptions for tender {TenderId}", request.TenderId);

        // Verify tender exists
        var tenderExists = await _context.Tenders
            .AnyAsync(t => t.Id == request.TenderId, cancellationToken);

        if (!tenderExists)
        {
            throw new KeyNotFoundException($"Tender with ID {request.TenderId} not found.");
        }

        // Get exceptions with related entities
        var exceptions = await _context.BidExceptions
            .Include(be => be.Bidder)
            .Include(be => be.LoggedByUser)
            .Where(be => be.TenderId == request.TenderId)
            .OrderByDescending(be => be.CreatedAt)
            .ToListAsync(cancellationToken);

        var exceptionDtos = exceptions.Select(e => new BidExceptionDto
        {
            Id = e.Id,
            TenderId = e.TenderId,
            BidderId = e.BidderId,
            BidderCompanyName = e.Bidder.CompanyName,
            ExceptionType = e.ExceptionType,
            Description = e.Description,
            CostImpact = e.CostImpact,
            TimeImpactDays = e.TimeImpactDays,
            RiskLevel = e.RiskLevel,
            Mitigation = e.Mitigation,
            LoggedBy = e.LoggedBy,
            LoggedByName = e.LoggedByUser != null
                ? $"{e.LoggedByUser.FirstName} {e.LoggedByUser.LastName}".Trim()
                : "Unknown",
            CreatedAt = e.CreatedAt
        }).ToList();

        // Calculate summaries
        var countByRiskLevel = exceptionDtos
            .GroupBy(e => e.RiskLevelName)
            .ToDictionary(g => g.Key, g => g.Count());

        var countByType = exceptionDtos
            .GroupBy(e => e.ExceptionTypeName)
            .ToDictionary(g => g.Key, g => g.Count());

        var totalCostImpact = exceptionDtos
            .Where(e => e.CostImpact.HasValue)
            .Sum(e => e.CostImpact!.Value);

        _logger.LogInformation(
            "Found {Count} bid exceptions for tender {TenderId}",
            exceptionDtos.Count, request.TenderId);

        return new BidExceptionListDto
        {
            TenderId = request.TenderId,
            Exceptions = exceptionDtos,
            CountByRiskLevel = countByRiskLevel,
            CountByType = countByType,
            TotalCostImpact = totalCostImpact
        };
    }
}
