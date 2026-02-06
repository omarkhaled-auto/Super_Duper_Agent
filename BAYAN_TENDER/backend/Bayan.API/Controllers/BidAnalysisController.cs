using Bayan.Application.Common.Models;
using Bayan.Application.Features.BidAnalysis.Commands.ExecuteBidImport;
using Bayan.Application.Features.BidAnalysis.Commands.MapBidColumns;
using Bayan.Application.Features.BidAnalysis.Commands.MatchBidItems;
using Bayan.Application.Features.BidAnalysis.Commands.NormalizeBid;
using Bayan.Application.Features.BidAnalysis.Commands.ParseBidFile;
using Bayan.Application.Features.BidAnalysis.Commands.ValidateBidImport;
using Bayan.Application.Features.BidAnalysis.DTOs;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bayan.API.Controllers;

/// <summary>
/// Controller for bid analysis operations including normalization, validation, and import execution.
/// </summary>
[ApiController]
[Route("api/tenders/{tenderId:guid}/bids/{bidId:guid}/import")]
[Authorize(Roles = "Admin,TenderManager,CommercialAnalyst")]
public class BidAnalysisController : ControllerBase
{
    private readonly IMediator _mediator;

    public BidAnalysisController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Normalizes bid pricing by applying FX rate and UOM conversions.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="bidId">The bid submission's unique identifier.</param>
    /// <param name="request">Normalization parameters.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Normalization result with converted values and UOM mismatches.</returns>
    /// <remarks>
    /// This endpoint performs the following:
    /// - Applies FX rate conversion from bid currency to tender base currency
    /// - Applies UOM conversion factors using the uom_master table
    /// - Calculates normalized rates and amounts
    /// - Identifies non-comparable items (e.g., LS to m2 cannot be converted)
    ///
    /// Set `persistResults` to true to save normalization results to the database.
    /// </remarks>
    [HttpPost("normalize")]
    [ProducesResponseType(typeof(NormalizationResultDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<NormalizationResultDto>> NormalizeBid(
        Guid tenderId,
        Guid bidId,
        [FromBody] NormalizeBidRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new NormalizeBidCommand
        {
            TenderId = tenderId,
            BidSubmissionId = bidId,
            FxRate = request.FxRate,
            FxRateSource = request.FxRateSource,
            PersistResults = request.PersistResults
        };

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<NormalizationResultDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Validates bid data before import.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="bidId">The bid submission's unique identifier.</param>
    /// <param name="request">Validation parameters.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Validation result with issues, formula checks, and coverage analysis.</returns>
    /// <remarks>
    /// This endpoint performs the following validations:
    /// - Formula check: Verifies Amount approximately equals Qty x Rate (within tolerance)
    /// - Data validation: Checks for negative values, zero rates, missing fields
    /// - Coverage check: Ensures all master BOQ items are matched
    /// - Outlier detection: Pre-detects pricing outliers if other bids are already imported
    /// </remarks>
    [HttpPost("validate")]
    [ProducesResponseType(typeof(ValidationResultDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ValidationResultDto>> ValidateBidImport(
        Guid tenderId,
        Guid bidId,
        [FromBody] ValidateBidImportRequest? request = null,
        CancellationToken cancellationToken = default)
    {
        var command = new ValidateBidImportCommand
        {
            TenderId = tenderId,
            BidSubmissionId = bidId,
            FormulaTolerancePercent = request?.FormulaTolerancePercent ?? 1.0m,
            DetectOutliers = request?.DetectOutliers ?? true,
            OutlierThresholdPercent = request?.OutlierThresholdPercent ?? 30.0m
        };

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<ValidationResultDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Executes the final import of a bid submission.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="bidId">The bid submission's unique identifier.</param>
    /// <param name="request">Import execution parameters.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Import result with statistics and vendor snapshot ID.</returns>
    /// <remarks>
    /// This endpoint performs the following:
    /// - Validates the bid (blocks if errors exist)
    /// - Normalizes all pricing items (FX and UOM conversion)
    /// - Stores bid_pricing records with native and normalized values
    /// - Updates bid_submissions.import_status to Imported
    /// - Calculates total amounts
    /// - Creates vendor pricing snapshot for historical tracking
    ///
    /// Set `forceImport` to true to proceed even with validation warnings (errors still block).
    /// </remarks>
    [HttpPost("execute")]
    [ProducesResponseType(typeof(ImportResultDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ImportResultDto>> ExecuteBidImport(
        Guid tenderId,
        Guid bidId,
        [FromBody] ExecuteBidImportRequest? request = null,
        CancellationToken cancellationToken = default)
    {
        var command = new ExecuteBidImportCommand
        {
            TenderId = tenderId,
            BidSubmissionId = bidId,
            ForceImport = request?.ForceImport ?? false,
            CreateVendorSnapshot = request?.CreateVendorSnapshot ?? true,
            FxRate = request?.FxRate
        };

        var result = await _mediator.Send(command, cancellationToken);

        // Return appropriate status code based on import result
        if (result.Status == ImportStatus.Failed)
        {
            return BadRequest(ApiResponse<object>.FailureResponse("Bid import failed"));
        }

        return Ok(ApiResponse<ImportResultDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Parses a bid file and returns column information and data preview.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="bidId">The bid submission's unique identifier.</param>
    /// <param name="request">Parse parameters.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Parse result with detected columns and preview rows.</returns>
    [HttpPost("parse")]
    [ProducesResponseType(typeof(ApiResponse<ParseBidResultDto>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ParseBidResultDto>> ParseBidFile(
        Guid tenderId,
        Guid bidId,
        [FromBody] ParseBidFileRequest? request = null,
        CancellationToken cancellationToken = default)
    {
        var command = new ParseBidFileCommand(
            tenderId,
            bidId,
            request?.PreviewRowCount ?? 10);

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<ParseBidResultDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Applies column mappings and extracts bid items from the parsed file.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="bidId">The bid submission's unique identifier.</param>
    /// <param name="request">Column mapping configuration.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Extracted bid items ready for matching.</returns>
    [HttpPost("map-columns")]
    [ProducesResponseType(typeof(ApiResponse<ImportBidDto>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ImportBidDto>> MapBidColumns(
        Guid tenderId,
        Guid bidId,
        [FromBody] MapBidColumnsRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new MapBidColumnsCommand(
            tenderId,
            bidId,
            request.ColumnMappings);

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<ImportBidDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Matches bid items with BOQ items using exact and fuzzy matching.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="bidId">The bid submission's unique identifier.</param>
    /// <param name="request">Match parameters including items and thresholds.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Match result with matched/unmatched items and confidence scores.</returns>
    [HttpPost("match")]
    [ProducesResponseType(typeof(ApiResponse<MatchResultDto>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<MatchResultDto>> MatchBidItems(
        Guid tenderId,
        Guid bidId,
        [FromBody] MatchBidItemsRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new MatchBidItemsCommand(
            tenderId,
            bidId,
            request.Items)
        {
            FuzzyMatchThreshold = request.FuzzyMatchThreshold,
            AlternativeMatchCount = request.AlternativeMatchCount
        };

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<MatchResultDto>.SuccessResponse(result));
    }
}

/// <summary>
/// Request model for parsing a bid file.
/// </summary>
public class ParseBidFileRequest
{
    /// <summary>
    /// Number of preview rows to return (default: 10).
    /// </summary>
    public int PreviewRowCount { get; set; } = 10;
}

/// <summary>
/// Request model for mapping bid columns.
/// </summary>
public class MapBidColumnsRequest
{
    /// <summary>
    /// Column mapping configuration.
    /// </summary>
    public ColumnMappingsDto ColumnMappings { get; set; } = new();
}

/// <summary>
/// Request model for matching bid items.
/// </summary>
public class MatchBidItemsRequest
{
    /// <summary>
    /// Bid items to match (from mapping step).
    /// </summary>
    public List<ImportBidItemDto> Items { get; set; } = new();

    /// <summary>
    /// Minimum confidence threshold for fuzzy matching (default 80%).
    /// </summary>
    public double FuzzyMatchThreshold { get; set; } = 80.0;

    /// <summary>
    /// Number of alternative matches to return (default: 3).
    /// </summary>
    public int AlternativeMatchCount { get; set; } = 3;
}

/// <summary>
/// Request model for bid normalization.
/// </summary>
public class NormalizeBidRequest
{
    /// <summary>
    /// Optional FX rate to use. If not provided, uses the rate stored in bid submission.
    /// </summary>
    public decimal? FxRate { get; set; }

    /// <summary>
    /// Source of the FX rate (e.g., "Manual", "API").
    /// </summary>
    public string? FxRateSource { get; set; }

    /// <summary>
    /// Whether to persist the normalization results to the database.
    /// If false, returns preview only.
    /// </summary>
    public bool PersistResults { get; set; } = false;
}

/// <summary>
/// Request model for bid validation.
/// </summary>
public class ValidateBidImportRequest
{
    /// <summary>
    /// Tolerance percentage for formula validation (Amount = Qty x Rate).
    /// Default is 1% tolerance.
    /// </summary>
    public decimal FormulaTolerancePercent { get; set; } = 1.0m;

    /// <summary>
    /// Whether to perform outlier detection against other imported bids.
    /// </summary>
    public bool DetectOutliers { get; set; } = true;

    /// <summary>
    /// Threshold percentage for outlier detection.
    /// Items with deviation above this threshold are flagged.
    /// </summary>
    public decimal OutlierThresholdPercent { get; set; } = 30.0m;
}

/// <summary>
/// Request model for bid import execution.
/// </summary>
public class ExecuteBidImportRequest
{
    /// <summary>
    /// Whether to force import even with validation warnings.
    /// Errors will still block import.
    /// </summary>
    public bool ForceImport { get; set; } = false;

    /// <summary>
    /// Whether to create a vendor pricing snapshot for historical tracking.
    /// </summary>
    public bool CreateVendorSnapshot { get; set; } = true;

    /// <summary>
    /// FX rate to use for normalization. If not provided, uses existing rate.
    /// </summary>
    public decimal? FxRate { get; set; }
}
