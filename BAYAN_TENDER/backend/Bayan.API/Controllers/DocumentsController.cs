using Bayan.Application.Common.Models;
using Bayan.Application.Features.Documents.Commands.CreateFolder;
using Bayan.Application.Features.Documents.Commands.DeleteDocument;
using Bayan.Application.Features.Documents.Commands.UploadDocument;
using Bayan.Application.Features.Documents.DTOs;
using Bayan.Application.Features.Documents.Queries.GetDocumentDownload;
using Bayan.Application.Features.Documents.Queries.GetDocuments;
using Bayan.Application.Features.Documents.Queries.GetDocumentVersions;
using Bayan.Application.Features.Documents.Queries.GetFolders;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bayan.API.Controllers;

/// <summary>
/// Controller for managing tender documents.
/// </summary>
[ApiController]
[Route("api/tenders/{tenderId:guid}/documents")]
[Authorize(Roles = "Admin,TenderManager")]
public class DocumentsController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<DocumentsController> _logger;

    public DocumentsController(IMediator mediator, ILogger<DocumentsController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Gets a paginated list of documents for a tender.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="folder">Optional folder path to filter documents.</param>
    /// <param name="search">Optional search term for file names.</param>
    /// <param name="latestOnly">Whether to return only latest versions (default: true).</param>
    /// <param name="page">Page number (1-based).</param>
    /// <param name="pageSize">Number of items per page.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A paginated list of documents.</returns>
    [HttpGet]
    [ProducesResponseType(typeof(PaginatedList<DocumentDto>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<PaginatedList<DocumentDto>>> GetDocuments(
        Guid tenderId,
        [FromQuery] string? folder = null,
        [FromQuery] string? search = null,
        [FromQuery] bool latestOnly = true,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        CancellationToken cancellationToken = default)
    {
        var query = new GetDocumentsQuery
        {
            TenderId = tenderId,
            FolderPath = folder,
            Search = search,
            LatestOnly = latestOnly,
            Page = page,
            PageSize = pageSize
        };

        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<PaginatedList<DocumentDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets all folders for a tender.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of folders.</returns>
    [HttpGet("folders")]
    [ProducesResponseType(typeof(IReadOnlyList<FolderDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<IReadOnlyList<FolderDto>>> GetFolders(
        Guid tenderId,
        CancellationToken cancellationToken = default)
    {
        var query = new GetFoldersQuery(tenderId);
        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<IReadOnlyList<FolderDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Uploads a document to a tender.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="dto">Upload document data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The uploaded document.</returns>
    [HttpPost("upload")]
    [ProducesResponseType(typeof(DocumentDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [RequestSizeLimit(104857600)] // 100 MB
    public async Task<ActionResult<DocumentDto>> UploadDocument(
        Guid tenderId,
        [FromForm] UploadDocumentDto dto,
        CancellationToken cancellationToken = default)
    {
        if (dto.File == null || dto.File.Length == 0)
        {
            return BadRequest(ApiResponse<object>.FailureResponse("No file uploaded."));
        }

        _logger.LogInformation(
            "Uploading document {FileName} ({Size} bytes) to tender {TenderId}, folder {Folder}",
            dto.File.FileName, dto.File.Length, tenderId, dto.FolderPath);

        await using var stream = dto.File.OpenReadStream();

        var command = new UploadDocumentCommand
        {
            TenderId = tenderId,
            FileStream = stream,
            FileName = dto.File.FileName,
            ContentType = dto.File.ContentType,
            FileSize = dto.File.Length,
            FolderPath = dto.FolderPath
        };

        var result = await _mediator.Send(command, cancellationToken);
        return CreatedAtAction(
            nameof(GetDocumentDownload),
            new { tenderId, docId = result.Id },
            ApiResponse<DocumentDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets a presigned download URL for a document.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="docId">The document ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Download URL information.</returns>
    [HttpGet("{docId:guid}/download")]
    [ProducesResponseType(typeof(DocumentDownloadDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<DocumentDownloadDto>> GetDocumentDownload(
        Guid tenderId,
        Guid docId,
        CancellationToken cancellationToken = default)
    {
        var query = new GetDocumentDownloadQuery(tenderId, docId);
        var result = await _mediator.Send(query, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Document not found."));
        }

        return Ok(ApiResponse<DocumentDownloadDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Gets all versions of a document.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="docId">The document ID.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of document versions.</returns>
    [HttpGet("{docId:guid}/versions")]
    [ProducesResponseType(typeof(IReadOnlyList<DocumentDto>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<IReadOnlyList<DocumentDto>>> GetDocumentVersions(
        Guid tenderId,
        Guid docId,
        CancellationToken cancellationToken = default)
    {
        var query = new GetDocumentVersionsQuery(tenderId, docId);
        var result = await _mediator.Send(query, cancellationToken);

        if (!result.Any())
        {
            return NotFound(ApiResponse<object>.FailureResponse("Document not found."));
        }

        return Ok(ApiResponse<IReadOnlyList<DocumentDto>>.SuccessResponse(result));
    }

    /// <summary>
    /// Deletes a document.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="docId">The document ID.</param>
    /// <param name="deleteAllVersions">Whether to delete all versions.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>No content if successful.</returns>
    [HttpDelete("{docId:guid}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> DeleteDocument(
        Guid tenderId,
        Guid docId,
        [FromQuery] bool deleteAllVersions = false,
        CancellationToken cancellationToken = default)
    {
        var command = new DeleteDocumentCommand(tenderId, docId, deleteAllVersions);
        var result = await _mediator.Send(command, cancellationToken);

        if (!result)
        {
            return NotFound(ApiResponse<object>.FailureResponse("Document not found."));
        }

        return NoContent();
    }

    /// <summary>
    /// Creates a new folder for document organization.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <param name="dto">Create folder data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created folder information.</returns>
    [HttpPost("folders")]
    [ProducesResponseType(typeof(FolderDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<FolderDto>> CreateFolder(
        Guid tenderId,
        [FromBody] CreateFolderDto dto,
        CancellationToken cancellationToken = default)
    {
        var command = new CreateFolderCommand
        {
            TenderId = tenderId,
            FolderName = dto.FolderName,
            ParentPath = dto.ParentPath
        };

        var result = await _mediator.Send(command, cancellationToken);
        return CreatedAtAction(
            nameof(GetFolders),
            new { tenderId },
            ApiResponse<FolderDto>.SuccessResponse(result));
    }
}
