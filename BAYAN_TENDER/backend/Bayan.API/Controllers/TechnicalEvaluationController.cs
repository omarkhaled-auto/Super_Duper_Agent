using Bayan.Application.Common.Models;
using Bayan.Application.Features.TechnicalEvaluation.Commands.LockTechnicalScores;
using Bayan.Application.Features.TechnicalEvaluation.Commands.SaveTechnicalScores;
using Bayan.Application.Features.TechnicalEvaluation.Commands.SetupTechnicalEvaluation;
using Bayan.Application.Features.TechnicalEvaluation.DTOs;
using Bayan.Application.Features.TechnicalEvaluation.Queries.GetBidderTechnicalDocuments;
using Bayan.Application.Features.TechnicalEvaluation.Queries.GetEvaluationSetup;
using Bayan.Application.Features.TechnicalEvaluation.Queries.GetPanelistAssignments;
using Bayan.Application.Features.TechnicalEvaluation.Queries.GetPanelists;
using Bayan.Application.Features.TechnicalEvaluation.Queries.GetPanelistScores;
using Bayan.Application.Features.TechnicalEvaluation.Queries.GetTechnicalScoresSummary;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bayan.API.Controllers;

/// <summary>
/// Controller for technical evaluation operations including setup, scoring, and summary.
/// </summary>
[ApiController]
[Route("api/tenders/{tenderId:guid}/evaluation")]
[Authorize]
public class TechnicalEvaluationController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<TechnicalEvaluationController> _logger;

    public TechnicalEvaluationController(IMediator mediator, ILogger<TechnicalEvaluationController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Gets the technical evaluation setup for a tender.
    /// Returns configuration, panelists, criteria, and progress information.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The evaluation setup data.</returns>
    [HttpGet("setup")]
    [ProducesResponseType(typeof(EvaluationSetupDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<EvaluationSetupDto>> GetEvaluationSetup(
        Guid tenderId,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Getting evaluation setup for tender {TenderId}", tenderId);

        var result = await _mediator.Send(new GetEvaluationSetupQuery(tenderId), cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse($"Tender with ID {tenderId} not found."));
        }

        return Ok(ApiResponse<EvaluationSetupDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Sets up or updates the technical evaluation for a tender.
    /// Creates EvaluationState record and assigns panelists.
    /// Sends notification emails to newly assigned panelists.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="request">The setup configuration.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The setup result.</returns>
    [HttpPost("setup")]
    [ProducesResponseType(typeof(SetupTechnicalEvaluationResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<SetupTechnicalEvaluationResult>> SetupTechnicalEvaluation(
        Guid tenderId,
        [FromBody] SetupTechnicalEvaluationRequest request,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Setting up technical evaluation for tender {TenderId} with {PanelistCount} panelists",
            tenderId, request.PanelistUserIds?.Count ?? 0);

        var command = new SetupTechnicalEvaluationCommand
        {
            TenderId = tenderId,
            ScoringMethod = request.ScoringMethod,
            BlindMode = request.BlindMode,
            TechnicalEvaluationDeadline = request.TechnicalEvaluationDeadline,
            PanelistUserIds = request.PanelistUserIds ?? new List<Guid>(),
            SendNotificationEmails = request.SendNotificationEmails
        };

        var result = await _mediator.Send(command, cancellationToken);

        if (!result.Success)
        {
            return BadRequest(ApiResponse<object>.FailureResponse(result.ErrorMessage));
        }

        return Ok(ApiResponse<SetupTechnicalEvaluationResult>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets all panelists assigned to a tender.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of panelists with progress information.</returns>
    [HttpGet("panelists")]
    [ProducesResponseType(typeof(List<PanelistDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<List<PanelistDto>>> GetPanelists(
        Guid tenderId,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Getting panelists for tender {TenderId}", tenderId);

        var result = await _mediator.Send(new GetPanelistsQuery(tenderId), cancellationToken);
        return Ok(ApiResponse<List<PanelistDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets the current panelist's assignments for a tender.
    /// Returns bidders to score and progress information.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The panelist's assignment data.</returns>
    [HttpGet("my-assignments")]
    [ProducesResponseType(typeof(PanelistAssignmentDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<PanelistAssignmentDto>> GetMyAssignments(
        Guid tenderId,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Getting panelist assignments for tender {TenderId}", tenderId);

        var result = await _mediator.Send(new GetPanelistAssignmentsQuery(tenderId), cancellationToken);

        if (result == null)
        {
            return Forbid();
        }

        return Ok(ApiResponse<PanelistAssignmentDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets a bidder's technical documents for evaluation.
    /// Enforces blind mode by hiding bidder identity if enabled.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="bidderId">The bidder's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The bidder's technical documents.</returns>
    [HttpGet("bidders/{bidderId:guid}/documents")]
    [ProducesResponseType(typeof(BidderTechnicalDocumentsDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status403Forbidden)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<BidderTechnicalDocumentsDto>> GetBidderTechnicalDocuments(
        Guid tenderId,
        Guid bidderId,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Getting technical documents for bidder {BidderId} in tender {TenderId}",
            bidderId, tenderId);

        var result = await _mediator.Send(
            new GetBidderTechnicalDocumentsQuery(tenderId, bidderId),
            cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Bidder documents not found or you are not authorized."));
        }

        return Ok(ApiResponse<BidderTechnicalDocumentsDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets the current panelist's scores for a specific bidder.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="bidderId">The bidder's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of scores for the bidder.</returns>
    [HttpGet("scores/{bidderId:guid}")]
    [ProducesResponseType(typeof(List<TechnicalScoreDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<List<TechnicalScoreDto>>> GetPanelistScores(
        Guid tenderId,
        Guid bidderId,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Getting scores for bidder {BidderId} in tender {TenderId}",
            bidderId, tenderId);

        var result = await _mediator.Send(
            new GetPanelistScoresQuery(tenderId, bidderId),
            cancellationToken);

        return Ok(ApiResponse<List<TechnicalScoreDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Saves technical scores for bidders.
    /// Can save as draft or submit as final.
    /// Requires comment for scores below 3 or above 8.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="request">The scores to save.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The save result.</returns>
    [HttpPost("scores")]
    [Authorize(Roles = "Admin,TenderManager,TechnicalPanelist")]
    [ProducesResponseType(typeof(SaveTechnicalScoresResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<SaveTechnicalScoresResult>> SaveTechnicalScores(
        Guid tenderId,
        [FromBody] SaveTechnicalScoresRequest request,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Saving {Count} scores for tender {TenderId}. Final: {IsFinal}",
            request.Scores?.Count ?? 0, tenderId, request.IsFinalSubmission);

        var command = new SaveTechnicalScoresCommand
        {
            TenderId = tenderId,
            Scores = request.Scores ?? new List<SaveTechnicalScoreDto>(),
            IsFinalSubmission = request.IsFinalSubmission
        };

        var result = await _mediator.Send(command, cancellationToken);

        if (!result.Success)
        {
            return BadRequest(ApiResponse<object>.FailureResponse(result.ErrorMessage));
        }

        return Ok(ApiResponse<SaveTechnicalScoresResult>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets the technical scores summary with matrix view, averages, variance, and ranks.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The scores summary.</returns>
    [HttpGet("summary")]
    [ProducesResponseType(typeof(TechnicalScoresSummaryDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<TechnicalScoresSummaryDto>> GetTechnicalScoresSummary(
        Guid tenderId,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Getting technical scores summary for tender {TenderId}", tenderId);

        var result = await _mediator.Send(
            new GetTechnicalScoresSummaryQuery(tenderId),
            cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse($"Tender with ID {tenderId} not found."));
        }

        return Ok(ApiResponse<TechnicalScoresSummaryDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Locks technical scores for a tender.
    /// This is an irreversible action that prevents further score modifications.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="request">Lock confirmation.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The lock result.</returns>
    [HttpPost("lock-scores")]
    [Authorize(Roles = "Admin,TenderManager")]
    [ProducesResponseType(typeof(LockTechnicalScoresResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<LockTechnicalScoresResult>> LockTechnicalScores(
        Guid tenderId,
        [FromBody] LockTechnicalScoresRequest request,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Locking technical scores for tender {TenderId}. Confirm: {Confirm}",
            tenderId, request.Confirm);

        var command = new LockTechnicalScoresCommand
        {
            TenderId = tenderId,
            Confirm = request.Confirm
        };

        var result = await _mediator.Send(command, cancellationToken);

        if (!result.Success)
        {
            return BadRequest(ApiResponse<object>.FailureResponse(result.ErrorMessage));
        }

        return Ok(ApiResponse<LockTechnicalScoresResult>.SuccessResponse(result));
    }
}

/// <summary>
/// Request model for setting up technical evaluation.
/// </summary>
public class SetupTechnicalEvaluationRequest
{
    /// <summary>
    /// The scoring method to use.
    /// </summary>
    public ScoringMethod ScoringMethod { get; set; } = ScoringMethod.Numeric;

    /// <summary>
    /// Whether blind evaluation mode is enabled.
    /// </summary>
    public bool BlindMode { get; set; } = true;

    /// <summary>
    /// Deadline for completing technical evaluation.
    /// </summary>
    public DateTime? TechnicalEvaluationDeadline { get; set; }

    /// <summary>
    /// List of user IDs to assign as panelists.
    /// </summary>
    public List<Guid>? PanelistUserIds { get; set; }

    /// <summary>
    /// Whether to send notification emails to panelists.
    /// </summary>
    public bool SendNotificationEmails { get; set; } = true;
}

/// <summary>
/// Request model for saving technical scores.
/// </summary>
public class SaveTechnicalScoresRequest
{
    /// <summary>
    /// List of scores to save.
    /// </summary>
    public List<SaveTechnicalScoreDto>? Scores { get; set; }

    /// <summary>
    /// Whether to submit final scores (true) or save as draft (false).
    /// </summary>
    public bool IsFinalSubmission { get; set; }
}

/// <summary>
/// Request model for locking technical scores.
/// </summary>
public class LockTechnicalScoresRequest
{
    /// <summary>
    /// Confirmation flag. Must be true to proceed with locking.
    /// </summary>
    public bool Confirm { get; set; }
}
