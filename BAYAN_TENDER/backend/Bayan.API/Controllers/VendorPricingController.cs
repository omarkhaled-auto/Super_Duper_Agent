using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using Bayan.Application.Features.VendorPricing.Commands.CreateVendorPricingSnapshot;
using Bayan.Application.Features.VendorPricing.Commands.ExportVendorPricing;
using Bayan.Application.Features.VendorPricing.DTOs;
using Bayan.Application.Features.VendorPricing.Queries.CompareVendorRates;
using Bayan.Application.Features.VendorPricing.Queries.GetVendorAnalytics;
using Bayan.Application.Features.VendorPricing.Queries.GetVendorList;
using Bayan.Application.Features.VendorPricing.Queries.GetVendorPricingDashboard;
using Bayan.Application.Features.VendorPricing.Queries.GetVendorPricingHistory;
using Bayan.Application.Features.VendorPricing.Queries.GetVendorRates;
using Bayan.Application.Features.VendorPricing.Queries.GetVendorTrends;
using Bayan.Infrastructure.Caching;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bayan.API.Controllers;

/// <summary>
/// Controller for vendor pricing management and analysis.
/// </summary>
[ApiController]
[Route("api/vendor-pricing")]
[Authorize(Roles = "Admin,TenderManager,CommercialAnalyst,Auditor")]
public class VendorPricingController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ICacheService _cacheService;
    private readonly ILogger<VendorPricingController> _logger;

    public VendorPricingController(
        IMediator mediator,
        ICacheService cacheService,
        ILogger<VendorPricingController> logger)
    {
        _mediator = mediator;
        _cacheService = cacheService;
        _logger = logger;
    }

    /// <summary>
    /// Gets dashboard data for vendor pricing.
    /// </summary>
    /// <param name="fromDate">Optional start date for filtering data.</param>
    /// <param name="toDate">Optional end date for filtering data.</param>
    /// <param name="tradeSpecialization">Optional trade specialization filter.</param>
    /// <param name="topVendorsLimit">Maximum number of top vendors to return.</param>
    /// <param name="recentSnapshotsLimit">Maximum number of recent snapshots to return.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Dashboard data including summary, top vendors, and trends.</returns>
    [HttpGet("dashboard")]
    [ProducesResponseType(typeof(VendorPricingDashboardDto), StatusCodes.Status200OK)]
    public async Task<ActionResult<VendorPricingDashboardDto>> GetDashboard(
        [FromQuery] DateTime? fromDate = null,
        [FromQuery] DateTime? toDate = null,
        [FromQuery] string? tradeSpecialization = null,
        [FromQuery] int topVendorsLimit = 10,
        [FromQuery] int recentSnapshotsLimit = 10,
        CancellationToken cancellationToken = default)
    {
        var query = new GetVendorPricingDashboardQuery
        {
            FromDate = fromDate,
            ToDate = toDate,
            TradeSpecialization = tradeSpecialization,
            TopVendorsLimit = topVendorsLimit,
            RecentSnapshotsLimit = recentSnapshotsLimit
        };

        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<VendorPricingDashboardDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets rate trends for a specific vendor over time.
    /// </summary>
    /// <param name="bidderId">The bidder's unique identifier.</param>
    /// <param name="fromDate">Optional start date for trends period.</param>
    /// <param name="toDate">Optional end date for trends period.</param>
    /// <param name="maxItemTrends">Maximum number of item trends to return.</param>
    /// <param name="includeItemHistory">Include item-level rate history.</param>
    /// <param name="includeTenderParticipation">Include tender participation details.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Vendor trends data if found.</returns>
    [HttpGet("trends/{bidderId:guid}")]
    [ProducesResponseType(typeof(VendorTrendsDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<VendorTrendsDto>> GetVendorTrends(
        Guid bidderId,
        [FromQuery] DateTime? fromDate = null,
        [FromQuery] DateTime? toDate = null,
        [FromQuery] int maxItemTrends = 50,
        [FromQuery] bool includeItemHistory = true,
        [FromQuery] bool includeTenderParticipation = true,
        CancellationToken cancellationToken = default)
    {
        var query = new GetVendorTrendsQuery
        {
            BidderId = bidderId,
            FromDate = fromDate,
            ToDate = toDate,
            MaxItemTrends = maxItemTrends,
            IncludeItemHistory = includeItemHistory,
            IncludeTenderParticipation = includeTenderParticipation
        };

        var result = await _mediator.Send(query, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Vendor trends not found"));
        }

        return Ok(ApiResponse<VendorTrendsDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Exports vendor pricing data to Excel.
    /// </summary>
    /// <param name="bidderIds">Optional list of bidder IDs to export.</param>
    /// <param name="fromDate">Optional start date for filtering data.</param>
    /// <param name="toDate">Optional end date for filtering data.</param>
    /// <param name="tradeSpecialization">Optional trade specialization filter.</param>
    /// <param name="tenderId">Optional tender ID filter.</param>
    /// <param name="includeItemDetails">Include item-level details.</param>
    /// <param name="includeSummary">Include summary sheet.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Excel file with vendor pricing data.</returns>
    [HttpGet("export")]
    [ProducesResponseType(typeof(FileContentResult), StatusCodes.Status200OK)]
    public async Task<IActionResult> ExportVendorPricing(
        [FromQuery] List<Guid>? bidderIds = null,
        [FromQuery] DateTime? fromDate = null,
        [FromQuery] DateTime? toDate = null,
        [FromQuery] string? tradeSpecialization = null,
        [FromQuery] Guid? tenderId = null,
        [FromQuery] bool includeItemDetails = true,
        [FromQuery] bool includeSummary = true,
        CancellationToken cancellationToken = default)
    {
        var command = new ExportVendorPricingCommand
        {
            BidderIds = bidderIds,
            FromDate = fromDate,
            ToDate = toDate,
            TradeSpecialization = tradeSpecialization,
            TenderId = tenderId,
            IncludeItemDetails = includeItemDetails,
            IncludeSummary = includeSummary
        };

        var result = await _mediator.Send(command, cancellationToken);

        _logger.LogInformation(
            "Exported vendor pricing data: {RecordCount} records, file: {FileName}",
            result.RecordCount,
            result.FileName);

        return File(result.Content, result.ContentType, result.FileName);
    }

    /// <summary>
    /// Gets a paginated list of vendors with pricing data.
    /// </summary>
    /// <param name="page">Page number (1-based).</param>
    /// <param name="pageSize">Number of items per page.</param>
    /// <param name="search">Optional search term for filtering by company name.</param>
    /// <param name="tradeSpecialization">Optional filter by trade specialization.</param>
    /// <param name="onlyWithPricingData">If true, only return vendors with pricing data.</param>
    /// <param name="isActive">Optional filter for active status.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A paginated list of vendors.</returns>
    [HttpGet("vendors")]
    [ProducesResponseType(typeof(PaginatedList<VendorListItemDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PaginatedList<VendorListItemDto>>> GetVendors(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 10,
        [FromQuery] string? search = null,
        [FromQuery] string? tradeSpecialization = null,
        [FromQuery] bool onlyWithPricingData = false,
        [FromQuery] bool? isActive = null,
        CancellationToken cancellationToken = default)
    {
        var query = new GetVendorListQuery
        {
            Page = page,
            PageSize = pageSize,
            Search = search,
            TradeSpecialization = tradeSpecialization,
            OnlyWithPricingData = onlyWithPricingData,
            IsActive = isActive
        };

        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<PaginatedList<VendorListItemDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets detailed analytics for a specific vendor.
    /// </summary>
    /// <param name="bidderId">The bidder's unique identifier.</param>
    /// <param name="fromDate">Optional start date for analytics period.</param>
    /// <param name="toDate">Optional end date for analytics period.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Vendor analytics if found.</returns>
    [HttpGet("vendors/{bidderId:guid}")]
    [ProducesResponseType(typeof(VendorAnalyticsDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<VendorAnalyticsDto>> GetVendor(
        Guid bidderId,
        [FromQuery] DateTime? fromDate = null,
        [FromQuery] DateTime? toDate = null,
        CancellationToken cancellationToken = default)
    {
        // Try to get from cache first
        var cacheKey = CacheKeys.GetVendorAnalyticsKey(bidderId);
        var cached = await _cacheService.GetAsync<VendorAnalyticsDto>(cacheKey, cancellationToken);

        if (cached != null)
        {
            _logger.LogDebug("Returning cached vendor analytics for bidder {BidderId}", bidderId);
            return Ok(ApiResponse<VendorAnalyticsDto>.SuccessResponse(cached));
        }

        var query = new GetVendorAnalyticsQuery
        {
            BidderId = bidderId,
            FromDate = fromDate,
            ToDate = toDate
        };

        var result = await _mediator.Send(query, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Vendor not found"));
        }

        // Cache the result
        await _cacheService.SetAsync(cacheKey, result, CacheKeys.VendorAnalyticsTtl, cancellationToken);

        return Ok(ApiResponse<VendorAnalyticsDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets pricing history for a specific vendor.
    /// </summary>
    /// <param name="bidderId">The bidder's unique identifier.</param>
    /// <param name="itemDescription">Optional filter by item description (partial match).</param>
    /// <param name="uom">Optional filter by unit of measurement.</param>
    /// <param name="fromDate">Optional start date for history range.</param>
    /// <param name="toDate">Optional end date for history range.</param>
    /// <param name="maxItems">Maximum number of items to return.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of vendor history items.</returns>
    [HttpGet("vendors/{bidderId:guid}/history")]
    [ProducesResponseType(typeof(List<VendorHistoryDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<List<VendorHistoryDto>>> GetVendorHistory(
        Guid bidderId,
        [FromQuery] string? itemDescription = null,
        [FromQuery] string? uom = null,
        [FromQuery] DateTime? fromDate = null,
        [FromQuery] DateTime? toDate = null,
        [FromQuery] int maxItems = 50,
        CancellationToken cancellationToken = default)
    {
        var query = new GetVendorPricingHistoryQuery
        {
            BidderId = bidderId,
            ItemDescription = itemDescription,
            Uom = uom,
            FromDate = fromDate,
            ToDate = toDate,
            MaxItems = maxItems
        };

        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<List<VendorHistoryDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets current/latest rates for a vendor by item.
    /// </summary>
    /// <param name="bidderId">The bidder's unique identifier.</param>
    /// <param name="page">Page number (1-based).</param>
    /// <param name="pageSize">Number of items per page.</param>
    /// <param name="itemDescription">Optional filter by item description (partial match).</param>
    /// <param name="uom">Optional filter by unit of measurement.</param>
    /// <param name="tenderId">Optional filter by tender ID.</param>
    /// <param name="latestOnly">If true, only return the latest rate for each item.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Paginated list of vendor item rates.</returns>
    [HttpGet("vendors/{bidderId:guid}/rates")]
    [ProducesResponseType(typeof(PaginatedList<VendorItemRateDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PaginatedList<VendorItemRateDto>>> GetVendorRates(
        Guid bidderId,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        [FromQuery] string? itemDescription = null,
        [FromQuery] string? uom = null,
        [FromQuery] Guid? tenderId = null,
        [FromQuery] bool latestOnly = true,
        CancellationToken cancellationToken = default)
    {
        // Try to get from cache for simple requests (no filters, latest only)
        if (latestOnly && string.IsNullOrEmpty(itemDescription) && string.IsNullOrEmpty(uom) && !tenderId.HasValue && page == 1)
        {
            var cacheKey = CacheKeys.GetVendorPricingKey(bidderId);
            var cached = await _cacheService.GetAsync<PaginatedList<VendorItemRateDto>>(cacheKey, cancellationToken);

            if (cached != null)
            {
                _logger.LogDebug("Returning cached vendor rates for bidder {BidderId}", bidderId);
                return Ok(ApiResponse<PaginatedList<VendorItemRateDto>>.SuccessResponse(cached));
            }
        }

        var query = new GetVendorRatesQuery
        {
            BidderId = bidderId,
            Page = page,
            PageSize = pageSize,
            ItemDescription = itemDescription,
            Uom = uom,
            TenderId = tenderId,
            LatestOnly = latestOnly
        };

        var result = await _mediator.Send(query, cancellationToken);

        // Cache simple requests
        if (latestOnly && string.IsNullOrEmpty(itemDescription) && string.IsNullOrEmpty(uom) && !tenderId.HasValue && page == 1)
        {
            var cacheKey = CacheKeys.GetVendorPricingKey(bidderId);
            await _cacheService.SetAsync(cacheKey, result, CacheKeys.VendorPricingTtl, cancellationToken);
        }

        return Ok(ApiResponse<PaginatedList<VendorItemRateDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Compares rates between multiple vendors.
    /// </summary>
    /// <param name="request">Comparison request with bidder IDs and optional filters.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Vendor comparison result.</returns>
    [HttpPost("compare")]
    [ProducesResponseType(typeof(VendorComparisonDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<VendorComparisonDto>> CompareVendors(
        [FromBody] CompareVendorsRequest request,
        CancellationToken cancellationToken = default)
    {
        if (request.BidderIds == null || request.BidderIds.Count < 2)
        {
            return BadRequest(ApiResponse<object>.FailureResponse("At least 2 bidder IDs are required for comparison."));
        }

        if (request.BidderIds.Count > 5)
        {
            return BadRequest(ApiResponse<object>.FailureResponse("Maximum 5 vendors can be compared at once."));
        }

        // Try to get from cache
        var cacheKey = CacheKeys.GetVendorComparisonKey(request.BidderIds);
        var cached = await _cacheService.GetAsync<VendorComparisonDto>(cacheKey, cancellationToken);

        if (cached != null && request.ItemDescriptions == null && string.IsNullOrEmpty(request.Uom))
        {
            _logger.LogDebug("Returning cached vendor comparison");
            return Ok(ApiResponse<VendorComparisonDto>.SuccessResponse(cached));
        }

        var query = new CompareVendorRatesQuery
        {
            BidderIds = request.BidderIds,
            ItemDescriptions = request.ItemDescriptions,
            Uom = request.Uom,
            LatestRatesOnly = request.LatestRatesOnly,
            MaxItems = request.MaxItems
        };

        var result = await _mediator.Send(query, cancellationToken);

        // Cache the result if no specific filters
        if (request.ItemDescriptions == null && string.IsNullOrEmpty(request.Uom))
        {
            await _cacheService.SetAsync(cacheKey, result, CacheKeys.VendorComparisonTtl, cancellationToken);
        }

        return Ok(ApiResponse<VendorComparisonDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Creates a vendor pricing snapshot from a bid submission.
    /// Typically triggered after successful bid import.
    /// </summary>
    /// <param name="request">The snapshot creation request.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created snapshot.</returns>
    [HttpPost("snapshots")]
    [ProducesResponseType(typeof(VendorPricingSnapshotDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<VendorPricingSnapshotDto>> CreateSnapshot(
        [FromBody] CreateSnapshotRequest request,
        CancellationToken cancellationToken = default)
    {
        if (request.BidSubmissionId == Guid.Empty)
        {
            return BadRequest(ApiResponse<object>.FailureResponse("Bid submission ID is required."));
        }

        var command = new CreateVendorPricingSnapshotCommand
        {
            BidSubmissionId = request.BidSubmissionId,
            SnapshotDate = request.SnapshotDate
        };

        var result = await _mediator.Send(command, cancellationToken);

        // Invalidate vendor pricing cache for this bidder
        var vendorPricingKey = CacheKeys.GetVendorPricingKey(result.BidderId);
        var vendorAnalyticsKey = CacheKeys.GetVendorAnalyticsKey(result.BidderId);

        await _cacheService.RemoveAsync(vendorPricingKey, cancellationToken);
        await _cacheService.RemoveAsync(vendorAnalyticsKey, cancellationToken);

        // Invalidate comparable sheet cache for this tender
        var comparableSheetKey = CacheKeys.GetComparableSheetKey(result.TenderId);
        await _cacheService.RemoveAsync(comparableSheetKey, cancellationToken);

        _logger.LogInformation(
            "Created vendor pricing snapshot for bidder {BidderId}, invalidated cache keys",
            result.BidderId);

        return CreatedAtAction(nameof(GetVendor), new { bidderId = result.BidderId }, ApiResponse<VendorPricingSnapshotDto>.SuccessResponse(result));
    }
}

/// <summary>
/// Request model for comparing vendors.
/// </summary>
public class CompareVendorsRequest
{
    /// <summary>
    /// List of bidder IDs to compare (2-5 vendors).
    /// </summary>
    public List<Guid> BidderIds { get; set; } = new();

    /// <summary>
    /// Optional list of item descriptions to compare.
    /// </summary>
    public List<string>? ItemDescriptions { get; set; }

    /// <summary>
    /// Optional filter by unit of measurement.
    /// </summary>
    public string? Uom { get; set; }

    /// <summary>
    /// Use latest rates only (default: true).
    /// </summary>
    public bool LatestRatesOnly { get; set; } = true;

    /// <summary>
    /// Maximum number of items to compare (default: 100).
    /// </summary>
    public int MaxItems { get; set; } = 100;
}

/// <summary>
/// Request model for creating a snapshot.
/// </summary>
public class CreateSnapshotRequest
{
    /// <summary>
    /// Bid submission ID to create snapshot from.
    /// </summary>
    public Guid BidSubmissionId { get; set; }

    /// <summary>
    /// Optional override for snapshot date.
    /// </summary>
    public DateTime? SnapshotDate { get; set; }
}
