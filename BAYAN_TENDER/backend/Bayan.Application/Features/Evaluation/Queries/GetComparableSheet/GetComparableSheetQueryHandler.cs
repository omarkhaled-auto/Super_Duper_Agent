using System.Data;
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
/// Supports pricing-level-aware queries: Bill, Item, and SubItem levels.
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

        // Get tender info (includes PricingLevel)
        var tender = await _context.Tenders
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new KeyNotFoundException($"Tender with ID {request.TenderId} not found.");
        }

        var pricingLevel = tender.PricingLevel;
        _logger.LogInformation(
            "Tender {TenderId} pricing level: {PricingLevel}",
            request.TenderId, pricingLevel);

        using var connection = _dapperContext.CreateConnection();

        // Build item type filter (only applicable for Item and SubItem levels)
        var itemTypeFilter = BuildItemTypeFilter(request);

        // Get all bidders with imported bids for this tender
        var bidders = await GetBidders(connection, request.TenderId);

        // Assign ranks
        for (int i = 0; i < bidders.Count; i++)
        {
            bidders[i].Rank = i + 1;
        }

        // Fetch items and pricing based on pricing level
        List<ComparableSheetItemDto> items;
        List<BidderRateWithItemDto> pricingData;

        switch (pricingLevel)
        {
            case PricingLevel.Bill:
                items = await GetItemsForBillLevel(connection, request.TenderId);
                pricingData = await GetPricingForBillLevel(connection, request.TenderId);
                break;

            case PricingLevel.Item:
                items = await GetItemsForItemLevel(connection, request.TenderId, itemTypeFilter);
                pricingData = await GetPricingForItemLevel(connection, request.TenderId);
                break;

            case PricingLevel.SubItem:
            default:
                items = await GetItemsForSubItemLevel(connection, request.TenderId, itemTypeFilter);
                pricingData = await GetPricingForItemLevel(connection, request.TenderId);
                break;
        }

        // Group pricing data by BOQ item (or section for Bill level)
        var pricingByItem = pricingData
            .GroupBy(p => p.BoqItemId)
            .ToDictionary(g => g.Key, g => g.ToList());

        // Populate bidder rates for each priceable item
        PopulateBidderRates(items, pricingByItem, bidders);

        // Insert subtotal rows based on pricing level
        if (pricingLevel == PricingLevel.SubItem)
        {
            items = await InsertSubItemLevelSubtotals(items, bidders, connection, request.TenderId);
        }
        else if (pricingLevel == PricingLevel.Item)
        {
            items = InsertBillSubtotals(items, bidders);
        }
        // Bill level: no subtotals needed (each row IS a bill total)

        // Calculate section totals (only for priceable "item" rows)
        var priceableItems = items.Where(i => i.RowType == "item").ToList();
        var sectionTotals = CalculateSectionTotals(priceableItems, bidders);

        // Calculate grand totals
        var grandTotals = bidders.Select(b => new BidderGrandTotalDto
        {
            BidderId = b.Id,
            GrandTotal = b.TotalNormalizedAmount
        }).ToList();

        // Calculate summary statistics (from priceable items only)
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
            PricingLevel = pricingLevel,
            Summary = new ComparableSheetSummaryDto
            {
                TotalItems = priceableItems.Count,
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
            "Generated comparable sheet for tender {TenderId} at {PricingLevel} level: {ItemCount} priceable items, {TotalRows} total rows, {BidderCount} bidders, {OutlierCount} outliers",
            request.TenderId, pricingLevel, priceableItems.Count, items.Count, bidders.Count, outlierCount);

        return result;
    }

    #region Bidders

    private async Task<List<ComparableSheetBidderDto>> GetBidders(
        IDbConnection connection, Guid tenderId)
    {
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

        return (await connection.QueryAsync<ComparableSheetBidderDto>(
            biddersSql,
            new
            {
                TenderId = tenderId,
                ImportedStatus = BidImportStatus.Imported.ToString(),
                DisqualifiedStatus = BidSubmissionStatus.Disqualified.ToString()
            })).ToList();
    }

    #endregion

    #region Items Queries by Pricing Level

    /// <summary>
    /// SubItem level: Fetch leaf items only (is_group = false).
    /// Includes standalone items (parent_item_id IS NULL, is_group = false)
    /// and sub-items (parent_item_id IS NOT NULL).
    /// </summary>
    private async Task<List<ComparableSheetItemDto>> GetItemsForSubItemLevel(
        IDbConnection connection, Guid tenderId, string itemTypeFilter)
    {
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
                bi.sort_order AS SortOrder,
                bi.parent_item_id AS ParentItemId,
                bi.is_group AS IsGroup
            FROM boq_items bi
            INNER JOIN boq_sections bs ON bi.section_id = bs.id
            WHERE bi.tender_id = @TenderId
            AND bi.is_group = false
            {itemTypeFilter}
            ORDER BY bs.sort_order, bi.sort_order, bi.item_number";

        var items = (await connection.QueryAsync<ComparableSheetItemDto>(
            itemsSql,
            new { TenderId = tenderId })).ToList();

        // All leaf items are priceable rows
        foreach (var item in items)
        {
            item.RowType = "item";
        }

        return items;
    }

    /// <summary>
    /// Item level: Fetch top-level items only (parent_item_id IS NULL).
    /// Includes both standalone items and group headers at the top level.
    /// </summary>
    private async Task<List<ComparableSheetItemDto>> GetItemsForItemLevel(
        IDbConnection connection, Guid tenderId, string itemTypeFilter)
    {
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
                bi.sort_order AS SortOrder,
                bi.parent_item_id AS ParentItemId,
                bi.is_group AS IsGroup
            FROM boq_items bi
            INNER JOIN boq_sections bs ON bi.section_id = bs.id
            WHERE bi.tender_id = @TenderId
            AND bi.parent_item_id IS NULL
            {itemTypeFilter}
            ORDER BY bs.sort_order, bi.sort_order, bi.item_number";

        var items = (await connection.QueryAsync<ComparableSheetItemDto>(
            itemsSql,
            new { TenderId = tenderId })).ToList();

        foreach (var item in items)
        {
            item.RowType = "item";
        }

        return items;
    }

    /// <summary>
    /// Bill level: Query boq_sections instead of boq_items.
    /// Each row represents a bill (top-level section) with lump-sum pricing.
    /// </summary>
    private async Task<List<ComparableSheetItemDto>> GetItemsForBillLevel(
        IDbConnection connection, Guid tenderId)
    {
        var sectionsSql = @"
            SELECT
                bsec.id AS BoqItemId,
                bsec.section_number AS ItemNumber,
                bsec.title AS Description,
                0 AS Quantity,
                '' AS Uom,
                bsec.id AS SectionId,
                bsec.title AS SectionName,
                bsec.sort_order AS SortOrder
            FROM boq_sections bsec
            WHERE bsec.tender_id = @TenderId
            AND bsec.parent_section_id IS NULL
            ORDER BY bsec.sort_order";

        var items = (await connection.QueryAsync<ComparableSheetItemDto>(
            sectionsSql,
            new { TenderId = tenderId })).ToList();

        foreach (var item in items)
        {
            item.RowType = "item";
        }

        return items;
    }

    #endregion

    #region Pricing Queries by Pricing Level

    /// <summary>
    /// Pricing for Item and SubItem levels: join on boq_item_id.
    /// </summary>
    private async Task<List<BidderRateWithItemDto>> GetPricingForItemLevel(
        IDbConnection connection, Guid tenderId)
    {
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

        return (await connection.QueryAsync<BidderRateWithItemDto>(
            pricingSql,
            new
            {
                TenderId = tenderId,
                ImportedStatus = BidImportStatus.Imported.ToString(),
                DisqualifiedStatus = BidSubmissionStatus.Disqualified.ToString()
            })).ToList();
    }

    /// <summary>
    /// Pricing for Bill level: join on boq_section_id instead of boq_item_id.
    /// Maps boq_section_id to BoqItemId for consistent downstream processing.
    /// </summary>
    private async Task<List<BidderRateWithItemDto>> GetPricingForBillLevel(
        IDbConnection connection, Guid tenderId)
    {
        var pricingSql = @"
            SELECT
                bp.boq_section_id AS BoqItemId,
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
            AND bp.boq_section_id IS NOT NULL";

        return (await connection.QueryAsync<BidderRateWithItemDto>(
            pricingSql,
            new
            {
                TenderId = tenderId,
                ImportedStatus = BidImportStatus.Imported.ToString(),
                DisqualifiedStatus = BidSubmissionStatus.Disqualified.ToString()
            })).ToList();
    }

    #endregion

    #region Rate Population

    /// <summary>
    /// Populates bidder rates on each priceable item from the pricing lookup.
    /// </summary>
    private void PopulateBidderRates(
        List<ComparableSheetItemDto> items,
        Dictionary<Guid, List<BidderRateWithItemDto>> pricingByItem,
        List<ComparableSheetBidderDto> bidders)
    {
        foreach (var item in items)
        {
            if (item.RowType != "item")
                continue;

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

                // Calculate average amount (excluding NoBid and NonComparable)
                // Use Amount (rate * qty) for a meaningful comparable average
                var validAmounts = item.BidderRates
                    .Where(r => !r.IsNoBid && !r.IsNonComparable && r.Amount.HasValue)
                    .Select(r => r.Amount!.Value)
                    .ToList();

                if (validAmounts.Any())
                {
                    item.AverageRate = validAmounts.Average();
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
    }

    #endregion

    #region Subtotals

    /// <summary>
    /// For SubItem level: inserts group headers, item subtotals, and bill subtotals.
    /// Group headers appear before their children; item subtotals appear after.
    /// Bill subtotals appear at the end of each section.
    /// </summary>
    private async Task<List<ComparableSheetItemDto>> InsertSubItemLevelSubtotals(
        List<ComparableSheetItemDto> leafItems,
        List<ComparableSheetBidderDto> bidders,
        IDbConnection connection,
        Guid tenderId)
    {
        // Fetch group headers (is_group = true) for this tender
        var groupsSql = @"
            SELECT
                bi.id AS BoqItemId,
                bi.item_number AS ItemNumber,
                bi.description AS Description,
                0 AS Quantity,
                '' AS Uom,
                bi.section_id AS SectionId,
                bs.title AS SectionName,
                bi.item_type AS ItemType,
                bi.sort_order AS SortOrder,
                bi.parent_item_id AS ParentItemId,
                bi.is_group AS IsGroup
            FROM boq_items bi
            INNER JOIN boq_sections bs ON bi.section_id = bs.id
            WHERE bi.tender_id = @TenderId
            AND bi.is_group = true
            ORDER BY bs.sort_order, bi.sort_order";

        var groupItems = (await connection.QueryAsync<ComparableSheetItemDto>(
            groupsSql,
            new { TenderId = tenderId })).ToList();

        // Build a lookup: group ID -> its child leaf items
        var childrenByParent = leafItems
            .Where(i => i.ParentItemId.HasValue)
            .GroupBy(i => i.ParentItemId!.Value)
            .ToDictionary(g => g.Key, g => g.OrderBy(c => c.SortOrder).ToList());

        // Build the final ordered list section by section
        var result = new List<ComparableSheetItemDto>();

        // Group all items and groups by section
        var sectionIds = leafItems.Select(i => i.SectionId)
            .Union(groupItems.Select(g => g.SectionId))
            .Distinct()
            .ToList();

        // Derive section ordering from first appearance in leafItems (which are already
        // sorted by bs.sort_order from the SQL query). This preserves the database section
        // sort_order rather than using item sort_order (which is 0-based within each section).
        var sectionOrderIndex = new Dictionary<Guid, int>();
        int orderIdx = 0;
        foreach (var item in leafItems)
        {
            if (!sectionOrderIndex.ContainsKey(item.SectionId))
            {
                sectionOrderIndex[item.SectionId] = orderIdx++;
            }
        }

        // Include sections from groups that might not have leaf items directly
        foreach (var group in groupItems)
        {
            if (!sectionOrderIndex.ContainsKey(group.SectionId))
            {
                sectionOrderIndex[group.SectionId] = orderIdx++;
            }
        }

        var orderedSections = sectionOrderIndex.OrderBy(kv => kv.Value).Select(kv => kv.Key).ToList();

        foreach (var sectionId in orderedSections)
        {
            var sectionLeafItems = leafItems
                .Where(i => i.SectionId == sectionId)
                .OrderBy(i => i.SortOrder)
                .ToList();

            var sectionGroups = groupItems
                .Where(g => g.SectionId == sectionId)
                .OrderBy(g => g.SortOrder)
                .ToList();

            // Standalone items (no parent) in this section
            var standaloneItems = sectionLeafItems
                .Where(i => !i.ParentItemId.HasValue)
                .ToList();

            // Build an interleaved list: groups (with children + subtotal) and standalone items
            // sorted by sort_order
            var sectionRows = new List<(int sortOrder, List<ComparableSheetItemDto> rows)>();

            // Add group blocks
            foreach (var group in sectionGroups)
            {
                var block = new List<ComparableSheetItemDto>();

                // Group header row
                var groupHeader = new ComparableSheetItemDto
                {
                    BoqItemId = group.BoqItemId,
                    ItemNumber = group.ItemNumber,
                    Description = group.Description,
                    Quantity = 0,
                    Uom = string.Empty,
                    SectionId = group.SectionId,
                    SectionName = group.SectionName,
                    ItemType = group.ItemType,
                    SortOrder = group.SortOrder,
                    RowType = "item_group_header",
                    ParentItemId = group.ParentItemId,
                    IsGroup = true,
                    BidderRates = new List<BidderRateDto>()
                };
                block.Add(groupHeader);

                // Children of this group
                if (childrenByParent.TryGetValue(group.BoqItemId, out var children))
                {
                    block.AddRange(children);

                    // Item subtotal row
                    var subtotalRow = CreateSubtotalRow(
                        group.BoqItemId,
                        $"Subtotal: {group.Description}",
                        "item_subtotal",
                        group.SectionId,
                        group.SectionName,
                        group.SortOrder,
                        children,
                        bidders);
                    block.Add(subtotalRow);
                }

                sectionRows.Add((group.SortOrder, block));
            }

            // Add standalone items
            foreach (var standalone in standaloneItems)
            {
                sectionRows.Add((standalone.SortOrder, new List<ComparableSheetItemDto> { standalone }));
            }

            // Sort by the sort_order of the first element in each block
            sectionRows.Sort((a, b) => a.sortOrder.CompareTo(b.sortOrder));

            // Flatten into result
            foreach (var (_, rows) in sectionRows)
            {
                result.AddRange(rows);
            }

            // Bill subtotal row for this section
            var allSectionPriceableItems = result
                .Where(i => i.SectionId == sectionId && i.RowType == "item")
                .ToList();

            if (allSectionPriceableItems.Any())
            {
                var sectionName = allSectionPriceableItems.First().SectionName;
                var billSubtotal = CreateSubtotalRow(
                    sectionId,
                    $"Bill Subtotal: {sectionName}",
                    "bill_subtotal",
                    sectionId,
                    sectionName,
                    int.MaxValue,
                    allSectionPriceableItems,
                    bidders);
                result.Add(billSubtotal);
            }
        }

        return result;
    }

    /// <summary>
    /// For Item level: inserts bill subtotals at the end of each section.
    /// </summary>
    private List<ComparableSheetItemDto> InsertBillSubtotals(
        List<ComparableSheetItemDto> items,
        List<ComparableSheetBidderDto> bidders)
    {
        var result = new List<ComparableSheetItemDto>();

        // Derive section ordering from first appearance in items list (which is already
        // sorted by bs.sort_order from the SQL query) to preserve database section order.
        var sectionFirstAppearance = new Dictionary<Guid, int>();
        for (int idx = 0; idx < items.Count; idx++)
        {
            if (!sectionFirstAppearance.ContainsKey(items[idx].SectionId))
            {
                sectionFirstAppearance[items[idx].SectionId] = idx;
            }
        }

        var itemsBySection = items
            .GroupBy(i => new { i.SectionId, i.SectionName })
            .OrderBy(g => sectionFirstAppearance.GetValueOrDefault(g.Key.SectionId, int.MaxValue));

        foreach (var section in itemsBySection)
        {
            var sectionItems = section.OrderBy(i => i.SortOrder).ToList();
            result.AddRange(sectionItems);

            // Bill subtotal for this section
            var priceableItems = sectionItems.Where(i => i.RowType == "item").ToList();
            if (priceableItems.Any())
            {
                var billSubtotal = CreateSubtotalRow(
                    section.Key.SectionId,
                    $"Bill Subtotal: {section.Key.SectionName}",
                    "bill_subtotal",
                    section.Key.SectionId,
                    section.Key.SectionName,
                    int.MaxValue,
                    priceableItems,
                    bidders);
                result.Add(billSubtotal);
            }
        }

        return result;
    }

    /// <summary>
    /// Creates a subtotal row by summing bidder amounts from the given items.
    /// </summary>
    private ComparableSheetItemDto CreateSubtotalRow(
        Guid id,
        string description,
        string rowType,
        Guid sectionId,
        string sectionName,
        int sortOrder,
        List<ComparableSheetItemDto> itemsToSum,
        List<ComparableSheetBidderDto> bidders)
    {
        var subtotalRow = new ComparableSheetItemDto
        {
            BoqItemId = id,
            ItemNumber = string.Empty,
            Description = description,
            Quantity = 0,
            Uom = string.Empty,
            SectionId = sectionId,
            SectionName = sectionName,
            SortOrder = sortOrder,
            RowType = rowType,
            IsGroup = false,
            BidderRates = new List<BidderRateDto>()
        };

        foreach (var bidder in bidders)
        {
            var totalAmount = itemsToSum
                .SelectMany(i => i.BidderRates ?? new List<BidderRateDto>())
                .Where(r => r.BidderId == bidder.Id && r.Amount.HasValue)
                .Sum(r => r.Amount ?? 0);

            subtotalRow.BidderRates.Add(new BidderRateDto
            {
                BidderId = bidder.Id,
                BidSubmissionId = bidder.BidSubmissionId,
                Rate = null,
                Amount = totalAmount
            });
        }

        // Average of bidder subtotals
        var validAmounts = subtotalRow.BidderRates
            .Where(r => r.Amount.HasValue && r.Amount.Value != 0)
            .Select(r => r.Amount!.Value)
            .ToList();

        if (validAmounts.Any())
        {
            subtotalRow.AverageRate = validAmounts.Average();
        }

        return subtotalRow;
    }

    #endregion

    #region Filters and Totals

    private string BuildItemTypeFilter(GetComparableSheetQuery request)
    {
        var excludedTypes = new List<string>();

        if (!request.IncludeProvisionalSums)
        {
            excludedTypes.Add($"'{BoqItemType.ProvisionalSum}'");
        }

        if (!request.IncludeAlternates)
        {
            excludedTypes.Add($"'{BoqItemType.Alternate}'");
        }

        if (!request.IncludeDaywork)
        {
            excludedTypes.Add($"'{BoqItemType.Daywork}'");
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
                    .SelectMany(item => item.BidderRates ?? new List<BidderRateDto>())
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

    #endregion

    #region Internal DTOs

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

    #endregion
}
