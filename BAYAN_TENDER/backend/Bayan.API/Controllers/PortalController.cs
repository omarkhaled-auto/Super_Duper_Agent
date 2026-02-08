using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using Bayan.Application.Features.Auth.DTOs;
using Bayan.Application.Features.Bids.Commands.SubmitBid;
using Bayan.Application.Features.Bids.Commands.UploadBidFile;
using Bayan.Application.Features.Bids.DTOs;
using Bayan.Application.Features.Bids.Queries.GetBidReceipt;
using Bayan.Application.Features.Portal.Auth;
using Bayan.Application.Features.Portal.Clarifications;
using Bayan.Application.Features.Portal.Documents;
using Bayan.Application.Features.Portal.DTOs;
using Bayan.Application.Features.Portal.Queries;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Security.Claims;

namespace Bayan.API.Controllers;

/// <summary>
/// Controller for the bidder portal - handles authentication, documents, clarifications, and bid submissions.
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class PortalController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly IFileStorageService _fileStorage;
    private readonly IApplicationDbContext _context;

    public PortalController(
        IMediator mediator,
        IFileStorageService fileStorage,
        IApplicationDbContext context)
    {
        _mediator = mediator;
        _fileStorage = fileStorage;
        _context = context;
    }

    /// <summary>
    /// Gets the current bidder's ID from the claims.
    /// </summary>
    private Guid GetBidderId()
    {
        // Try multiple claim types for bidder ID
        var bidderIdClaim = User.FindFirst("BidderId")?.Value
            ?? User.FindFirst(ClaimTypes.NameIdentifier)?.Value;

        if (string.IsNullOrEmpty(bidderIdClaim) || !Guid.TryParse(bidderIdClaim, out var bidderId))
        {
            throw new UnauthorizedAccessException("Invalid bidder credentials.");
        }
        return bidderId;
    }

    /// <summary>
    /// Gets the client IP address from the request.
    /// </summary>
    private string? GetClientIpAddress()
    {
        var forwardedFor = HttpContext.Request.Headers["X-Forwarded-For"].FirstOrDefault();
        if (!string.IsNullOrEmpty(forwardedFor))
        {
            return forwardedFor.Split(',').First().Trim();
        }

        var realIp = HttpContext.Request.Headers["X-Real-IP"].FirstOrDefault();
        if (!string.IsNullOrEmpty(realIp))
        {
            return realIp;
        }

        return HttpContext.Connection.RemoteIpAddress?.ToString();
    }

    #region Authentication

    /// <summary>
    /// Authenticates a bidder and returns JWT tokens.
    /// </summary>
    /// <param name="request">Login credentials.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Login response with tokens and bidder info.</returns>
    [HttpPost("auth/login")]
    [AllowAnonymous]
    [ProducesResponseType(typeof(BidderLoginResponseDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<ActionResult<BidderLoginResponseDto>> Login(
        [FromBody] BidderLoginRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new BidderLoginCommand
        {
            Email = request.Email,
            Password = request.Password,
            TenderId = request.TenderId,
            RememberMe = request.RememberMe,
            IpAddress = GetClientIpAddress()
        };

        try
        {
            var result = await _mediator.Send(command, cancellationToken);
            return Ok(ApiResponse<BidderLoginResponseDto>.SuccessResponse(result));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    /// <summary>
    /// Refreshes JWT tokens using a valid refresh token.
    /// </summary>
    /// <param name="request">Refresh token request.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>New tokens.</returns>
    [HttpPost("auth/refresh-token")]
    [AllowAnonymous]
    [ProducesResponseType(typeof(TokenDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<TokenDto>> RefreshToken(
        [FromBody] BidderRefreshTokenRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new BidderRefreshTokenCommand
        {
            RefreshToken = request.RefreshToken,
            IpAddress = GetClientIpAddress()
        };

        try
        {
            var result = await _mediator.Send(command, cancellationToken);
            return Ok(ApiResponse<TokenDto>.SuccessResponse(result));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    /// <summary>
    /// Activates a bidder account by setting the password.
    /// </summary>
    /// <param name="request">Activation request with token and new password.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Success response if activated.</returns>
    [HttpPost("auth/activate")]
    [AllowAnonymous]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> ActivateAccount(
        [FromBody] ActivateAccountRequest request,
        CancellationToken cancellationToken = default)
    {
        var command = new ActivateBidderAccountCommand
        {
            Email = request.Email,
            ActivationToken = request.ActivationToken,
            Password = request.Password,
            ConfirmPassword = request.ConfirmPassword
        };

        try
        {
            await _mediator.Send(command, cancellationToken);
            return Ok(ApiResponse<object>.SuccessResponse(new { message = "Account activated successfully." }));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    #endregion

    #region Tender Information

    /// <summary>
    /// Gets tender information for the portal header.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Tender information.</returns>
    [HttpGet("tenders/{tenderId:guid}")]
    [Authorize(Roles = "Bidder")]
    [ProducesResponseType(typeof(PortalTenderDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<PortalTenderDto>> GetTenderInfo(
        Guid tenderId,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var bidderId = GetBidderId();
            var query = new GetPortalTenderInfoQuery
            {
                TenderId = tenderId,
                BidderId = bidderId
            };

            var result = await _mediator.Send(query, cancellationToken);
            return Ok(ApiResponse<PortalTenderDto>.SuccessResponse(result));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    #endregion

    #region Documents

    /// <summary>
    /// Gets documents accessible to the bidder for a tender.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="folderPath">Optional folder path filter.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of documents.</returns>
    [HttpGet("tenders/{tenderId:guid}/documents")]
    [Authorize(Roles = "Bidder")]
    [ProducesResponseType(typeof(List<PortalDocumentDto>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<List<PortalDocumentDto>>> GetDocuments(
        Guid tenderId,
        [FromQuery] string? folderPath = null,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var bidderId = GetBidderId();
            var query = new GetPortalDocumentsQuery
            {
                TenderId = tenderId,
                BidderId = bidderId,
                FolderPath = folderPath
            };

            var result = await _mediator.Send(query, cancellationToken);
            return Ok(ApiResponse<List<PortalDocumentDto>>.SuccessResponse(result));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    /// <summary>
    /// Downloads a document.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="documentId">The document ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The document download URL.</returns>
    [HttpGet("tenders/{tenderId:guid}/documents/{documentId:guid}/download")]
    [Authorize(Roles = "Bidder")]
    [ProducesResponseType(typeof(DocumentDownloadResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<DocumentDownloadResponse>> DownloadDocument(
        Guid tenderId,
        Guid documentId,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var bidderId = GetBidderId();

            // Validate bidder access
            var tenderBidder = await _context.TenderBidders
                .FirstOrDefaultAsync(tb => tb.TenderId == tenderId && tb.BidderId == bidderId, cancellationToken);

            if (tenderBidder == null || tenderBidder.QualificationStatus != QualificationStatus.Qualified)
            {
                return Unauthorized(ApiResponse<object>.FailureResponse("You do not have access to this tender."));
            }

            // Get document
            var document = await _context.Documents
                .FirstOrDefaultAsync(d => d.Id == documentId && d.TenderId == tenderId, cancellationToken);

            if (document == null)
            {
                return NotFound(ApiResponse<object>.FailureResponse("Document not found."));
            }

            // Generate presigned URL
            var downloadUrl = await _fileStorage.GetPresignedUrlAsync(
                document.FilePath,
                TimeSpan.FromMinutes(15),
                cancellationToken);

            return Ok(ApiResponse<DocumentDownloadResponse>.SuccessResponse(new DocumentDownloadResponse
            {
                DocumentId = document.Id,
                FileName = document.FileName,
                ContentType = document.ContentType,
                DownloadUrl = downloadUrl,
                ExpiresAt = DateTime.UtcNow.AddMinutes(15)
            }));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    #endregion

    #region Addenda

    /// <summary>
    /// Gets addenda with acknowledgment status for the current bidder.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of addenda.</returns>
    [HttpGet("tenders/{tenderId:guid}/addenda")]
    [Authorize(Roles = "Bidder")]
    [ProducesResponseType(typeof(List<PortalAddendumDto>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<List<PortalAddendumDto>>> GetAddenda(
        Guid tenderId,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var bidderId = GetBidderId();
            var query = new GetPortalAddendaQuery
            {
                TenderId = tenderId,
                BidderId = bidderId
            };

            var result = await _mediator.Send(query, cancellationToken);
            return Ok(ApiResponse<List<PortalAddendumDto>>.SuccessResponse(result));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    /// <summary>
    /// Acknowledges an addendum.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="addendumId">The addendum ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Success status.</returns>
    [HttpPost("tenders/{tenderId:guid}/addenda/{addendumId:guid}/acknowledge")]
    [Authorize(Roles = "Bidder")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> AcknowledgeAddendum(
        Guid tenderId,
        Guid addendumId,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var bidderId = GetBidderId();
            var command = new AcknowledgeAddendumCommand
            {
                TenderId = tenderId,
                AddendumId = addendumId,
                BidderId = bidderId
            };

            await _mediator.Send(command, cancellationToken);
            return Ok(ApiResponse<object>.SuccessResponse(new { message = "Addendum acknowledged successfully." }));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    #endregion

    #region Clarifications

    /// <summary>
    /// Gets published clarifications (Q&A) for a tender.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of published clarifications.</returns>
    [HttpGet("tenders/{tenderId:guid}/clarifications")]
    [Authorize(Roles = "Bidder")]
    [ProducesResponseType(typeof(List<PortalClarificationDto>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<List<PortalClarificationDto>>> GetClarifications(
        Guid tenderId,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var bidderId = GetBidderId();
            var query = new GetPublishedClarificationsQuery
            {
                TenderId = tenderId,
                BidderId = bidderId
            };

            var result = await _mediator.Send(query, cancellationToken);
            return Ok(ApiResponse<List<PortalClarificationDto>>.SuccessResponse(result));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    /// <summary>
    /// Submits a question/clarification request.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="request">The question details.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The submitted question.</returns>
    [HttpPost("tenders/{tenderId:guid}/clarifications")]
    [Authorize(Roles = "Bidder")]
    [ProducesResponseType(typeof(BidderQuestionDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<BidderQuestionDto>> SubmitQuestion(
        Guid tenderId,
        [FromBody] SubmitQuestionRequest request,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var bidderId = GetBidderId();
            var command = new SubmitBidderQuestionCommand
            {
                TenderId = tenderId,
                BidderId = bidderId,
                Subject = request.Subject,
                Question = request.Question,
                RelatedBoqSection = request.RelatedBoqSection,
                IsAnonymous = request.IsAnonymous
            };

            var result = await _mediator.Send(command, cancellationToken);
            return Ok(ApiResponse<BidderQuestionDto>.SuccessResponse(result));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
        catch (InvalidOperationException ex)
        {
            return BadRequest(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    #endregion

    #region Bulletins

    /// <summary>
    /// Gets published clarification bulletins for a tender.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of bulletins.</returns>
    [HttpGet("tenders/{tenderId:guid}/bulletins")]
    [Authorize(Roles = "Bidder")]
    [ProducesResponseType(typeof(List<PortalBulletinDto>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<ActionResult<List<PortalBulletinDto>>> GetBulletins(
        Guid tenderId,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var bidderId = GetBidderId();
            var query = new GetPublishedBulletinsQuery
            {
                TenderId = tenderId,
                BidderId = bidderId
            };

            var result = await _mediator.Send(query, cancellationToken);
            return Ok(ApiResponse<List<PortalBulletinDto>>.SuccessResponse(result));
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    /// <summary>
    /// Downloads a bulletin PDF.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="bulletinId">The bulletin ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The bulletin PDF file.</returns>
    [HttpGet("tenders/{tenderId:guid}/bulletins/{bulletinId:guid}/download")]
    [Authorize(Roles = "Bidder")]
    [ProducesResponseType(typeof(FileStreamResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> DownloadBulletin(
        Guid tenderId,
        Guid bulletinId,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var bidderId = GetBidderId();

            // Validate bidder access
            var tenderBidder = await _context.TenderBidders
                .FirstOrDefaultAsync(tb => tb.TenderId == tenderId && tb.BidderId == bidderId, cancellationToken);

            if (tenderBidder == null || tenderBidder.QualificationStatus != QualificationStatus.Qualified)
            {
                return Unauthorized(ApiResponse<object>.FailureResponse("You do not have access to this tender."));
            }

            // Get bulletin
            var bulletin = await _context.ClarificationBulletins
                .FirstOrDefaultAsync(b => b.Id == bulletinId && b.TenderId == tenderId, cancellationToken);

            if (bulletin == null)
            {
                return NotFound(ApiResponse<object>.FailureResponse("Bulletin not found."));
            }

            if (string.IsNullOrEmpty(bulletin.PdfPath))
            {
                return NotFound(ApiResponse<object>.FailureResponse("Bulletin PDF is not available."));
            }

            var stream = await _fileStorage.DownloadFileAsync(bulletin.PdfPath, cancellationToken);
            return File(stream, "application/pdf", $"Bulletin-{bulletin.BulletinNumber}.pdf");
        }
        catch (UnauthorizedAccessException ex)
        {
            return Unauthorized(ApiResponse<object>.FailureResponse(ex.Message));
        }
    }

    #endregion

    #region Bid Submissions

    /// <summary>
    /// Uploads a file for a bid submission.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="file">The file to upload.</param>
    /// <param name="documentType">The type of document (PricedBOQ, Methodology, TeamCVs, Program, HSEPlan, Supporting).</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The upload result with file ID.</returns>
    [HttpPost("tenders/{tenderId:guid}/bids/upload")]
    [Authorize(Roles = "Bidder")]
    [ProducesResponseType(typeof(UploadBidFileResultDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [RequestSizeLimit(100 * 1024 * 1024)] // 100 MB limit
    public async Task<ActionResult<UploadBidFileResultDto>> UploadBidFile(
        Guid tenderId,
        IFormFile file,
        [FromQuery] BidDocumentType documentType,
        CancellationToken cancellationToken = default)
    {
        if (file == null || file.Length == 0)
        {
            return BadRequest(ApiResponse<object>.FailureResponse("No file provided."));
        }

        var bidderId = GetBidderId();

        using var stream = file.OpenReadStream();
        var command = new UploadBidFileCommand
        {
            TenderId = tenderId,
            BidderId = bidderId,
            DocumentType = documentType,
            FileStream = stream,
            FileName = file.FileName,
            ContentType = file.ContentType,
            FileSize = file.Length
        };

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<UploadBidFileResultDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Submits a bid for a tender.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="dto">The submission details.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The submission result with receipt.</returns>
    [HttpPost("tenders/{tenderId:guid}/bids/submit")]
    [Authorize(Roles = "Bidder")]
    [ProducesResponseType(typeof(SubmitBidResultDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<SubmitBidResultDto>> SubmitBid(
        Guid tenderId,
        [FromBody] SubmitBidRequestDto dto,
        CancellationToken cancellationToken = default)
    {
        var bidderId = GetBidderId();

        var command = new SubmitBidCommand
        {
            TenderId = tenderId,
            BidderId = bidderId,
            BidValidityDays = dto.BidValidityDays
        };

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<SubmitBidResultDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets the receipt for a submitted bid.
    /// </summary>
    /// <param name="bidId">The bid submission ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The bid receipt.</returns>
    [HttpGet("bids/{bidId:guid}/receipt")]
    [Authorize(Roles = "Bidder")]
    [ProducesResponseType(typeof(BidReceiptDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<BidReceiptDto>> GetBidReceipt(
        Guid bidId,
        CancellationToken cancellationToken = default)
    {
        var bidderId = GetBidderId();

        var query = new GetBidReceiptQuery(bidId, bidderId);
        var result = await _mediator.Send(query, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Resource not found"));
        }

        return Ok(ApiResponse<BidReceiptDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Downloads the PDF receipt for a submitted bid.
    /// </summary>
    /// <param name="bidId">The bid submission ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The PDF file.</returns>
    [HttpGet("bids/{bidId:guid}/receipt/download")]
    [Authorize(Roles = "Bidder")]
    [ProducesResponseType(typeof(FileStreamResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> DownloadBidReceipt(
        Guid bidId,
        CancellationToken cancellationToken = default)
    {
        var bidderId = GetBidderId();

        // Get the bid submission to verify ownership and get PDF path
        var bidSubmission = await _context.BidSubmissions
            .Where(b => b.Id == bidId && b.BidderId == bidderId)
            .Select(b => new { b.ReceiptPdfPath, b.ReceiptNumber })
            .FirstOrDefaultAsync(cancellationToken);

        if (bidSubmission == null || string.IsNullOrEmpty(bidSubmission.ReceiptPdfPath))
        {
            return NotFound(ApiResponse<object>.FailureResponse("Resource not found"));
        }

        var stream = await _fileStorage.DownloadFileAsync(
            bidSubmission.ReceiptPdfPath,
            cancellationToken);

        return File(stream, "application/pdf", $"BidReceipt-{bidSubmission.ReceiptNumber}.pdf");
    }

    #endregion
}

#region Request DTOs

/// <summary>
/// Request DTO for bidder login.
/// </summary>
public class BidderLoginRequest
{
    /// <summary>
    /// Bidder's email address.
    /// </summary>
    public string Email { get; set; } = string.Empty;

    /// <summary>
    /// Bidder's password.
    /// </summary>
    public string Password { get; set; } = string.Empty;

    /// <summary>
    /// Optional tender ID to validate access to.
    /// </summary>
    public Guid? TenderId { get; set; }

    /// <summary>
    /// Whether to extend the refresh token validity period.
    /// </summary>
    public bool RememberMe { get; set; }
}

/// <summary>
/// Request DTO for bidder refresh token.
/// </summary>
public class BidderRefreshTokenRequest
{
    /// <summary>
    /// The refresh token.
    /// </summary>
    public string RefreshToken { get; set; } = string.Empty;
}

/// <summary>
/// Request DTO for submitting a question.
/// </summary>
public class SubmitQuestionRequest
{
    /// <summary>
    /// Subject of the question.
    /// </summary>
    public string Subject { get; set; } = string.Empty;

    /// <summary>
    /// The question content.
    /// </summary>
    public string Question { get; set; } = string.Empty;

    /// <summary>
    /// Related BOQ section reference (optional).
    /// </summary>
    public string? RelatedBoqSection { get; set; }

    /// <summary>
    /// Whether the submitter identity should be hidden.
    /// </summary>
    public bool IsAnonymous { get; set; }
}

/// <summary>
/// Response DTO for document download.
/// </summary>
public class DocumentDownloadResponse
{
    /// <summary>
    /// Document unique identifier.
    /// </summary>
    public Guid DocumentId { get; set; }

    /// <summary>
    /// Original file name.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// MIME content type.
    /// </summary>
    public string ContentType { get; set; } = string.Empty;

    /// <summary>
    /// Presigned download URL.
    /// </summary>
    public string DownloadUrl { get; set; } = string.Empty;

    /// <summary>
    /// When the download URL expires.
    /// </summary>
    public DateTime ExpiresAt { get; set; }
}

/// <summary>
/// Request DTO for submitting a bid.
/// </summary>
public class SubmitBidRequestDto
{
    /// <summary>
    /// Bid validity period in days.
    /// </summary>
    public int BidValidityDays { get; set; } = 90;
}

/// <summary>
/// Request DTO for bidder account activation.
/// </summary>
public class ActivateAccountRequest
{
    /// <summary>
    /// Bidder's email address.
    /// </summary>
    public string Email { get; set; } = string.Empty;

    /// <summary>
    /// The activation token from the invitation email.
    /// </summary>
    public string ActivationToken { get; set; } = string.Empty;

    /// <summary>
    /// The new password.
    /// </summary>
    public string Password { get; set; } = string.Empty;

    /// <summary>
    /// Confirmation of the new password.
    /// </summary>
    public string ConfirmPassword { get; set; } = string.Empty;
}

#endregion
