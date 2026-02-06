using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Evaluation.DTOs;
using Bayan.Domain.Enums;
using Dapper;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Evaluation.Queries.GetComparableSheet;

/// <summary>
/// Handler for GetComparableSheetQuery using Dapper for optimized performance.
/// </summary>
public class GetComparableSheetQueryHandler : IRequestHandler<GetComparableSheetQuery, ComparableSheetDto>
{
    private readonly IDapperContext _dapperContext;
    private readonly IApplicationDbContext _context;
    private readonly ILogger<GetComparableSheetQueryHandler> _logger;

    public GetComparableSheetQueryHandler(
        IDapperContext dapperContext,
        IApplicationDbContext context,
        ILogger<GetComparableSheetQueryHandler> logger)
    {
        _dapperContext = dapperContext;
        _context = context;
        _logger = logger;
    }

    public async Task<ComparableSheetDto> Handle(
        GetComparableSheetQuery request,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation("Generating comparable sheet for tender {TenderId}", request.TenderId);

        // Get tender info
        var tender = await _context.Tenders
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new KeyNotFoundException($"Tender with ID {request.TenderId} not found.");
        }

        using var connection = _dapperContext.CreateConnection();

        // Build item type filter
        var itemTypeFilter = BuildItemTypeFilter(request);

        // Get all bidders with imported bids for this tender
        var biddersSql = @"
            SELECT
                b.id AS Id,
                bs.id AS BidSubmissionId,
                b.company_name AS CompanyName,
                COALESCE(bs.normalized_total_amount, 0) AS TotalNormalizedAmount
            FROM bid_submissions bs
            INNER JOIN bidders b ON bs.bidder_id = b.id
            WHERE bs.tender_id = @TenderId
            AND bs.import_status = @ImportedStatus
            AND bs.status NOT IN (@DisqualifiedStatus)
            ORDER BY bs.normalized_total_amount ASC";

        var bidders = (await connection.QueryAsync<ComparableSheetBidderDto>(
            biddersSql,
            new
            {
                TenderId = request.TenderId,
                ImportedStatus = (int)BidImportStatus.Imported,
                DisqualifiedStatus = (int)BidSubmissionStatus.Disqualified
            })).ToList();

        // Assign ranks
        for (int i = 0; i < bidders.Count; i++)
        {
            bidders[i].Rank = i + 1;
        }

        // Get all BOQ items with their sections
        var itemsSql = $@"
            SELECT
                bi.id AS BoqItemId,
                bi.item_number AS ItemNumber,
                bi.description AS Description,
                bi.quantity AS Quantity,
                bi.uom AS Uom,
                bi.section_id AS SectionId,
                bs.title AS SectionName,
                bi.item_type AS ItemType,
                bi.sort_order AS SortOrder
            FROM boq_items bi
            INNER JOIN boq_sections bs ON bi.section_id = bs.id
            WHERE bi.tender_id = @TenderId
            {itemTypeFilter}
            ORDER BY bs.sort_order, bi.sort_order, bi.item_number";

        var items = (await connection.QueryAsync<ComparableSheetItemDto>(
            itemsSql,
            new { TenderId = request.TenderId })).ToList();

        // Get all bid pricing data
        var pricingSql = @"
            SELECT
                bp.boq_item_id AS BoqItemId,
                bs.bidder_id AS BidderId,
                bs.id AS BidSubmissionId,
                bp.normalized_unit_rate AS Rate,
                bp.normalized_amount AS Amount,
                bp.is_outlier AS IsOutlier,
                bp.outlier_severity AS Severity,
                bp.deviation_from_average AS Deviation,
                bp.is_no_bid AS IsNoBid,
                bp.is_non_comparable AS IsNonComparable
            FROM bid_pricing bp
            INNER JOIN bid_submissions bs ON bp.bid_submission_id = bs.id
            WHERE bs.tender_id = @TenderId
            AND bs.import_status = @ImportedStatus
            AND bs.status NOT IN (@DisqualifiedStatus)
            AND bp.boq_item_id IS NOT NULL";

        var pricingData = (await connection.QueryAsync<BidderRateWithItemDto>(
            pricingSql,
            new
            {
                TenderId = request.TenderId,
                ImportedStatus = (int)BidImportStatus.Imported,
                DisqualifiedStatus = (int)BidSubmissionStatus.Disqualified
            })).ToList();

        // Group pricing data by BOQ item
        var pricingByItem = pricingData
            .GroupBy(p => p.BoqItemId)
            .ToDictionary(g => g.Key, g => g.ToList());

        // Populate bidder rates for each item
        foreach (var item in items)
        {
            if (pricingByItem.TryGetValue(item.BoqItemId, out var itemPricing))
            {
                item.BidderRates = itemPricing.Select(p => new BidderRateDto
                {
                    BidderId = p.BidderId,
                    BidSubmissionId = p.BidSubmissionId,
                    Rate = p.Rate,
                    Amount = p.Amount,
                    IsOutlier = p.IsOutlier,
                    Severity = p.Severity,
                    Deviation = p.Deviation,
                    IsNoBid = p.IsNoBid,
                    IsNonComparable = p.IsNonComparable
                }).ToList();

                // Calculate average rate (excluding NoBid and NonComparable)
                var validRates = item.BidderRates
                    .Where(r => !r.IsNoBid && !r.IsNonComparable && r.Rate.HasValue)
                    .Select(r => r.Rate!.Value)
                    .ToList();

                if (validRates.Any())
                {
                    item.AverageRate = validRates.Average();
                }
            }
            else
            {
                // No pricing data - add empty rates for all bidders
                item.BidderRates = bidders.Select(b => new BidderRateDto
                {
                    BidderId = b.Id,
                    BidSubmissionId = b.BidSubmissionId,
                    Rate = null,
                    Amount = null,
                    IsNoBid = true
                }).ToList();
            }
        }

        // Calculate section totals
        var sectionTotals = CalculateSectionTotals(items, bidders);

        // Calculate grand totals
        var grandTotals = bidders.Select(b => new BidderGrandTotalDto
        {
            BidderId = b.Id,
            GrandTotal = b.TotalNormalizedAmount
        }).ToList();

        // Calculate summary statistics
        var outlierCount = pricingData.Count(p => p.IsOutlier);
        var maxDeviation = pricingData
            .Where(p => p.Deviation.HasValue)
            .Select(p => Math.Abs(p.Deviation!.Value))
            .DefaultIfEmpty(0)
            .Max();

        // Generate minimum bidders warning if fewer than 3
        string? minimumBiddersWarning = null;
        if (bidders.Count < 3)
        {
            minimumBiddersWarning = $"Warning: Only {bidders.Count} bidder(s) submitted. Minimum 3 bidders are required for a valid commercial evaluation.";
            _logger.LogWarning(
                "Tender {TenderId} has only {BidderCount} bidders, minimum 3 required",
                request.TenderId, bidders.Count);
        }

        var result = new ComparableSheetDto
        {
            TenderId = request.TenderId,
            TenderName = tender.Title,
            Summary = new ComparableSheetSummaryDto
            {
                TotalItems = items.Count,
                BidderCount = bidders.Count,
                OutlierCount = outlierCount,
                MaxDeviation = maxDeviation
            },
            Bidders = bidders,
            Items = items,
            SectionTotals = sectionTotals,
            GrandTotals = grandTotals,
            GeneratedAt = DateTime.UtcNow,
            MinimumBiddersWarning = minimumBiddersWarning
        };

        _logger.LogInformation(
            "Generated comparable sheet for tender {TenderId}: {ItemCount} items, {BidderCount} bidders, {OutlierCount} outliers",
            request.TenderId, items.Count, bidders.Count, outlierCount);

        return result;
    }

    private string BuildItemTypeFilter(GetComparableSheetQuery request)
    {
        var excludedTypes = new List<int>();

        if (!request.IncludeProvisionalSums)
        {
            excludedTypes.Add((int)BoqItemType.ProvisionalSum);
        }

        if (!request.IncludeAlternates)
        {
            excludedTypes.Add((int)BoqItemType.Alternate);
        }

        if (!request.IncludeDaywork)
        {
            excludedTypes.Add((int)BoqItemType.Daywork);
        }

        if (excludedTypes.Count == 0)
        {
            return string.Empty;
        }

        return $"AND bi.item_type NOT IN ({string.Join(",", excludedTypes)})";
    }

    private List<ComparableSheetSectionTotalDto> CalculateSectionTotals(
        List<ComparableSheetItemDto> items,
        List<ComparableSheetBidderDto> bidders)
    {
        var sectionTotals = new List<ComparableSheetSectionTotalDto>();

        var itemsBySection = items.GroupBy(i => new { i.SectionId, i.SectionName });

        foreach (var section in itemsBySection)
        {
            var sectionTotal = new ComparableSheetSectionTotalDto
            {
                SectionId = section.Key.SectionId,
                SectionName = section.Key.SectionName,
                SortOrder = section.Min(i => i.SortOrder),
                BidderTotals = new List<BidderSectionTotalDto>()
            };

            foreach (var bidder in bidders)
            {
                var bidderTotal = section
                    .SelectMany(item => item.BidderRates)
                    .Where(r => r.BidderId == bidder.Id && r.Amount.HasValue)
                    .Sum(r => r.Amount ?? 0);

                sectionTotal.BidderTotals.Add(new BidderSectionTotalDto
                {
                    BidderId = bidder.Id,
                    Total = bidderTotal
                });
            }

            sectionTotals.Add(sectionTotal);
        }

        return sectionTotals.OrderBy(s => s.SortOrder).ToList();
    }

    /// <summary>
    /// Internal DTO for Dapper query result.
    /// </summary>
    private class BidderRateWithItemDto
    {
        public Guid BoqItemId { get; set; }
        public Guid BidderId { get; set; }
        public Guid BidSubmissionId { get; set; }
        public decimal? Rate { get; set; }
        public decimal? Amount { get; set; }
        public bool IsOutlier { get; set; }
        public OutlierSeverity? Severity { get; set; }
        public decimal? Deviation { get; set; }
        public bool IsNoBid { get; set; }
        public bool IsNonComparable { get; set; }
    }
}
