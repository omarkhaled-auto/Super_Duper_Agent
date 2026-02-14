using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using Bayan.Application.Features.Evaluation.Commands.AddBidException;
using Bayan.Application.Features.Evaluation.Commands.CalculateCommercialScores;
using Bayan.Application.Features.Evaluation.Commands.CalculateCombinedScores;
using Bayan.Application.Features.Evaluation.Commands.ExportComparableSheet;
using Bayan.Application.Features.Evaluation.Commands.GenerateAwardPack;
using Bayan.Application.Features.Evaluation.Commands.UpdateOutlierStatus;
using Bayan.Application.Features.Evaluation.DTOs;
using Bayan.Application.Features.Evaluation.Queries.GetBidExceptions;
using Bayan.Application.Features.Evaluation.Queries.GetComparableSheet;
using Bayan.Application.Features.Evaluation.Queries.GetCombinedScorecard;
using Bayan.Application.Features.Evaluation.Queries.GetSensitivityAnalysis;
using Bayan.API.Authorization;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bayan.API.Controllers;

/// <summary>
/// Controller for evaluation operations including comparable sheets,
/// outlier detection, commercial scoring, combined scorecard, and award pack generation.
/// </summary>
[ApiController]
[Route("api/tenders/{tenderId:guid}/evaluation")]
[Authorize(Roles = BayanRoles.EvaluationViewers)]
public class EvaluationController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<EvaluationController> _logger;
    private readonly IFileStorageService _fileStorageService;

    public EvaluationController(
        IMediator mediator,
        ILogger<EvaluationController> logger,
        IFileStorageService fileStorageService)
    {
        _mediator = mediator;
        _logger = logger;
        _fileStorageService = fileStorageService;
    }

    /// <summary>
    /// Gets the comparable sheet for a tender.
    /// Returns all BOQ items with bidder rates and outlier detection.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="includeProvisionalSums">Include provisional sum items (default: true).</param>
    /// <param name="includeAlternates">Include alternate items (default: true).</param>
    /// <param name="includeDaywork">Include daywork items (default: true).</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The comparable sheet data.</returns>
    [HttpGet("comparable-sheet")]
    [ProducesResponseType(typeof(ComparableSheetDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ComparableSheetDto>> GetComparableSheet(
        Guid tenderId,
        [FromQuery] bool includeProvisionalSums = true,
        [FromQuery] bool includeAlternates = true,
        [FromQuery] bool includeDaywork = true,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Getting comparable sheet for tender {TenderId} " +
            "(IncludePS: {IncludePS}, IncludeAlt: {IncludeAlt}, IncludeDW: {IncludeDW})",
            tenderId, includeProvisionalSums, includeAlternates, includeDaywork);

        try
        {
            var query = new GetComparableSheetQuery
            {
                TenderId = tenderId,
                IncludeProvisionalSums = includeProvisionalSums,
                IncludeAlternates = includeAlternates,
                IncludeDaywork = includeDaywork
            };

            var result = await _mediator.Send(query, cancellationToken);
            return Ok(ApiResponse<ComparableSheetDto>.SuccessResponse(result));
        }
        catch (KeyNotFoundException ex)
        {
            return NotFound(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    /// <summary>
    /// Exports the comparable sheet to an Excel file.
    /// Features:
    /// - Frozen panes for Item #, Description, Qty, UOM columns
    /// - Color-coded cells matching outlier severity (Red=High, Yellow=Medium, Green=Low)
    /// - Section totals and grand totals
    /// - Auto-filter on header row
    /// - Currency formatting
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="includeProvisionalSums">Include provisional sum items (default: true).</param>
    /// <param name="includeAlternates">Include alternate items (default: true).</param>
    /// <param name="includeDaywork">Include daywork items (default: true).</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Excel file containing the comparable sheet.</returns>
    [HttpGet("comparable-sheet/export-excel")]
    [ProducesResponseType(typeof(FileContentResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> ExportComparableSheet(
        Guid tenderId,
        [FromQuery] bool includeProvisionalSums = true,
        [FromQuery] bool includeAlternates = true,
        [FromQuery] bool includeDaywork = true,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Exporting comparable sheet to Excel for tender {TenderId}", tenderId);

        try
        {
            var command = new ExportComparableSheetCommand
            {
                TenderId = tenderId,
                IncludeProvisionalSums = includeProvisionalSums,
                IncludeAlternates = includeAlternates,
                IncludeDaywork = includeDaywork
            };

            var result = await _mediator.Send(command, cancellationToken);

            return File(
                result.FileContent,
                result.ContentType,
                result.FileName);
        }
        catch (KeyNotFoundException ex)
        {
            return NotFound(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    /// <summary>
    /// Calculates commercial scores for all bidders in a tender.
    /// Formula: (Lowest Total / This Total) x 100
    /// Lowest bidder gets 100 points, others get proportionally lower scores.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="request">Calculation options.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The calculated commercial scores for all bidders.</returns>
    [HttpPost("calculate-commercial-scores")]
    [Authorize(Roles = BayanRoles.EvaluationEditors)]
    [ProducesResponseType(typeof(CalculateCommercialScoresResultDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<CalculateCommercialScoresResultDto>> CalculateCommercialScores(
        Guid tenderId,
        [FromBody] CalculateCommercialScoresRequest? request = null,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Calculating commercial scores for tender {TenderId} " +
            "(IncludePS: {IncludePS}, IncludeAlt: {IncludeAlt})",
            tenderId,
            request?.IncludeProvisionalSums ?? true,
            request?.IncludeAlternates ?? true);

        try
        {
            var command = new CalculateCommercialScoresCommand
            {
                TenderId = tenderId,
                IncludeProvisionalSums = request?.IncludeProvisionalSums ?? true,
                IncludeAlternates = request?.IncludeAlternates ?? true
            };

            var result = await _mediator.Send(command, cancellationToken);
            return Ok(ApiResponse<CalculateCommercialScoresResultDto>.SuccessResponse(result));
        }
        catch (KeyNotFoundException ex)
        {
            return NotFound(ApiResponse<object>.FailureResponse(ex.Message));
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    /// <summary>
    /// Recalculates outlier status for all bid pricing in a tender.
    /// For each BOQ item:
    /// - Collects all bidder rates (excludes NoBid, NonComparable)
    /// - Calculates the average rate
    /// - For each rate, calculates deviation percentage
    /// - Assigns severity: >20% = High (red), >10% = Medium (yellow), else Low (green)
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="request">Outlier detection thresholds.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Summary of outlier detection results.</returns>
    [HttpPost("recalculate-outliers")]
    [Authorize(Roles = BayanRoles.EvaluationEditors)]
    [ProducesResponseType(typeof(OutlierRecalculationResultDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<OutlierRecalculationResultDto>> RecalculateOutliers(
        Guid tenderId,
        [FromBody] RecalculateOutliersRequest? request = null,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Recalculating outliers for tender {TenderId} " +
            "(HighThreshold: {High}%, MediumThreshold: {Medium}%)",
            tenderId,
            request?.HighThreshold ?? 20m,
            request?.MediumThreshold ?? 10m);

        try
        {
            var command = new UpdateOutlierStatusCommand
            {
                TenderId = tenderId,
                HighThreshold = request?.HighThreshold ?? 20m,
                MediumThreshold = request?.MediumThreshold ?? 10m
            };

            var result = await _mediator.Send(command, cancellationToken);
            return Ok(ApiResponse<OutlierRecalculationResultDto>.SuccessResponse(result));
        }
        catch (KeyNotFoundException ex)
        {
            return NotFound(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    #region Combined Scorecard

    /// <summary>
    /// Gets the combined scorecard for a tender.
    /// Returns technical, commercial, and combined scores with rankings.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="techWeight">Technical weight percentage (optional, uses tender defaults).</param>
    /// <param name="commWeight">Commercial weight percentage (optional, uses tender defaults).</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The combined scorecard data.</returns>
    [HttpGet("combined-scorecard")]
    [ProducesResponseType(typeof(CombinedScorecardDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<CombinedScorecardDto>> GetCombinedScorecard(
        Guid tenderId,
        [FromQuery] int? techWeight = null,
        [FromQuery] int? commWeight = null,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Getting combined scorecard for tender {TenderId} (TechWeight: {TechWeight}, CommWeight: {CommWeight})",
            tenderId, techWeight, commWeight);

        try
        {
            var query = new GetCombinedScorecardQuery
            {
                TenderId = tenderId,
                TechnicalWeight = techWeight,
                CommercialWeight = commWeight
            };

            var result = await _mediator.Send(query, cancellationToken);
            return Ok(ApiResponse<CombinedScorecardDto>.SuccessResponse(result));
        }
        catch (KeyNotFoundException ex)
        {
            return NotFound(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    /// <summary>
    /// Calculates combined scores for all bidders in a tender.
    /// Formula: (TechWeight/100 x TechScore) + (CommWeight/100 x CommScore)
    /// Highest combined score bidder is marked as recommended.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="request">Calculation options.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The calculated combined scores for all bidders.</returns>
    [HttpPost("calculate-combined")]
    [Authorize(Roles = BayanRoles.EvaluationEditors)]
    [ProducesResponseType(typeof(CombinedScorecardDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<CombinedScorecardDto>> CalculateCombinedScores(
        Guid tenderId,
        [FromBody] CalculateCombinedScoresRequestDto? request = null,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Calculating combined scores for tender {TenderId} (TechWeight: {TechWeight}, CommWeight: {CommWeight})",
            tenderId, request?.TechnicalWeight, request?.CommercialWeight);

        try
        {
            var command = new CalculateCombinedScoresCommand
            {
                TenderId = tenderId,
                TechnicalWeight = request?.TechnicalWeight,
                CommercialWeight = request?.CommercialWeight
            };

            var result = await _mediator.Send(command, cancellationToken);
            return Ok(ApiResponse<CombinedScorecardDto>.SuccessResponse(result));
        }
        catch (KeyNotFoundException ex)
        {
            return NotFound(ApiResponse<object>.FailureResponse(ex.Message));
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    #endregion

    #region Sensitivity Analysis

    /// <summary>
    /// Gets sensitivity analysis showing how rankings change at different weight splits.
    /// Analyzes: 30/70, 40/60, 50/50, 60/40, 70/30 (Tech/Comm).
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Sensitivity analysis data.</returns>
    [HttpGet("sensitivity-analysis")]
    [ProducesResponseType(typeof(SensitivityAnalysisDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<SensitivityAnalysisDto>> GetSensitivityAnalysis(
        Guid tenderId,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Getting sensitivity analysis for tender {TenderId}", tenderId);

        try
        {
            var query = new GetSensitivityAnalysisQuery(tenderId);
            var result = await _mediator.Send(query, cancellationToken);
            return Ok(ApiResponse<SensitivityAnalysisDto>.SuccessResponse(result));
        }
        catch (KeyNotFoundException ex)
        {
            return NotFound(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    #endregion

    #region Bid Exceptions

    /// <summary>
    /// Gets all bid exceptions for a tender.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of bid exceptions with summaries.</returns>
    [HttpGet("~/api/tenders/{tenderId:guid}/exceptions")]
    [ProducesResponseType(typeof(BidExceptionListDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<BidExceptionListDto>> GetBidExceptions(
        Guid tenderId,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Getting bid exceptions for tender {TenderId}", tenderId);

        try
        {
            var query = new GetBidExceptionsQuery(tenderId);
            var result = await _mediator.Send(query, cancellationToken);
            return Ok(ApiResponse<BidExceptionListDto>.SuccessResponse(result));
        }
        catch (KeyNotFoundException ex)
        {
            return NotFound(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    /// <summary>
    /// Adds a new bid exception for a tender.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="request">Exception details.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created bid exception.</returns>
    [HttpPost("~/api/tenders/{tenderId:guid}/exceptions")]
    [Authorize(Roles = BayanRoles.EvaluationEditors)]
    [ProducesResponseType(typeof(BidExceptionDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<BidExceptionDto>> AddBidException(
        Guid tenderId,
        [FromBody] CreateBidExceptionDto request,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Adding bid exception for tender {TenderId}, bidder {BidderId}, type {ExceptionType}",
            tenderId, request.BidderId, request.ExceptionType);

        try
        {
            var command = new AddBidExceptionCommand
            {
                TenderId = tenderId,
                BidderId = request.BidderId,
                ExceptionType = request.ExceptionType,
                Description = request.Description,
                CostImpact = request.CostImpact,
                TimeImpactDays = request.TimeImpactDays,
                RiskLevel = request.RiskLevel,
                Mitigation = request.Mitigation
            };

            var result = await _mediator.Send(command, cancellationToken);
            return CreatedAtAction(nameof(GetBidExceptions), new { tenderId }, ApiResponse<BidExceptionDto>.SuccessResponse(result));
        }
        catch (KeyNotFoundException ex)
        {
            return NotFound(ApiResponse<object>.FailureResponse(ex.Message));
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(ApiResponse<object>.FailureResponse(ex.Message));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    #endregion

    #region Award Pack

    /// <summary>
    /// Generates an award pack PDF for a tender.
    /// Includes: cover page, executive summary, evaluation methodology,
    /// technical/commercial results, combined scorecard, recommendation,
    /// exceptions, and appendices.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="request">Generation options.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Award pack metadata with download URL.</returns>
    [HttpPost("generate-award-pack")]
    [Authorize(Roles = BayanRoles.TenderLifecycleManagers)]
    [ProducesResponseType(typeof(AwardPackDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<AwardPackDto>> GenerateAwardPack(
        Guid tenderId,
        [FromBody] GenerateAwardPackRequestDto? request = null,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Generating award pack for tender {TenderId}", tenderId);

        try
        {
            var command = new GenerateAwardPackCommand
            {
                TenderId = tenderId,
                IncludeTechnicalDetails = request?.IncludeTechnicalDetails ?? true,
                IncludeCommercialDetails = request?.IncludeCommercialDetails ?? true,
                IncludeSensitivityAnalysis = request?.IncludeSensitivityAnalysis ?? true,
                IncludeExceptions = request?.IncludeExceptions ?? true,
                ExecutiveSummary = request?.ExecutiveSummary,
                RecommendationNotes = request?.RecommendationNotes
            };

            var result = await _mediator.Send(command, cancellationToken);
            return Ok(ApiResponse<AwardPackDto>.SuccessResponse(result));
        }
        catch (KeyNotFoundException ex)
        {
            return NotFound(ApiResponse<object>.FailureResponse(ex.Message));
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(ApiResponse<object>.FailureResponse(ex.Message));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    /// <summary>
    /// Downloads the award pack PDF for a tender.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The award pack PDF file.</returns>
    [HttpGet("award-pack/download")]
    [ProducesResponseType(typeof(FileContentResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> DownloadAwardPack(
        Guid tenderId,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Downloading award pack for tender {TenderId}", tenderId);

        try
        {
            // Find the latest award pack file for this tender
            var storagePath = $"tenders/{tenderId}/award-packs";
            var files = await _fileStorageService.ListFilesAsync(storagePath, cancellationToken);

            if (!files.Any())
            {
                return NotFound(ApiResponse<object>.FailureResponse("No award pack found for this tender. Please generate one first."));
            }

            // Get the most recent file
            var latestFile = files.OrderByDescending(f => f.LastModified).First();

            // Download the file
            var stream = await _fileStorageService.DownloadFileAsync(latestFile.FilePath, cancellationToken);

            using var memoryStream = new MemoryStream();
            await stream.CopyToAsync(memoryStream, cancellationToken);

            return File(
                memoryStream.ToArray(),
                "application/pdf",
                latestFile.FileName);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error downloading award pack for tender {TenderId}", tenderId);
            return NotFound(ApiResponse<object>.FailureResponse("Award pack not found or could not be downloaded."));
        }
    }

    #endregion
}

/// <summary>
/// Request model for calculating commercial scores.
/// </summary>
public class CalculateCommercialScoresRequest
{
    /// <summary>
    /// Whether to include provisional sums in the total calculation (default: true).
    /// </summary>
    public bool IncludeProvisionalSums { get; set; } = true;

    /// <summary>
    /// Whether to include alternates in the total calculation (default: true).
    /// </summary>
    public bool IncludeAlternates { get; set; } = true;
}

/// <summary>
/// Request model for recalculating outliers.
/// </summary>
public class RecalculateOutliersRequest
{
    /// <summary>
    /// High threshold percentage. Deviations above this are marked as High severity (default: 20%).
    /// </summary>
    public decimal HighThreshold { get; set; } = 20m;

    /// <summary>
    /// Medium threshold percentage. Deviations above this (but below high) are marked as Medium severity (default: 10%).
    /// </summary>
    public decimal MediumThreshold { get; set; } = 10m;
}
