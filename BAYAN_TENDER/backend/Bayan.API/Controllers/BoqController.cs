using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using Bayan.Application.Features.Boq.Commands.AddBoqItem;
using Bayan.Application.Features.Boq.Commands.AddBoqSection;
using Bayan.Application.Features.Boq.Commands.DeleteBoqItem;
using Bayan.Application.Features.Boq.Commands.DeleteBoqSection;
using Bayan.Application.Features.Boq.Commands.DuplicateBoqItem;
using Bayan.Application.Features.Boq.Commands.ExecuteBoqImport;
using Bayan.Application.Features.Boq.Commands.ExportBoqTemplate;
using Bayan.Application.Features.Boq.Commands.UpdateBoqItem;
using Bayan.Application.Features.Boq.Commands.UpdateBoqSection;
using Bayan.Application.Features.Boq.Commands.UploadBoqImportFile;
using Bayan.Application.Features.Boq.Commands.ValidateBoqImport;
using Bayan.Application.Features.Boq.DTOs;
using Bayan.Application.Features.Boq.Queries.GetBoqStructure;
using Bayan.Application.Features.Boq.Queries.GetUomList;
using Bayan.API.Authorization;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Bayan.API.Controllers;

/// <summary>
/// Controller for managing Bill of Quantities (BOQ) sections and items.
/// </summary>
[ApiController]
[Route("api")]
[Authorize(Roles = BayanRoles.BoqManagers)]
public class BoqController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<BoqController> _logger;

    public BoqController(IMediator mediator, ILogger<BoqController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    #region BOQ Structure

    /// <summary>
    /// Gets the hierarchical BOQ structure for a tender.
    /// Returns sections with nested child sections and items.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Hierarchical tree of BOQ sections with items.</returns>
    [HttpGet("tenders/{tenderId:guid}/boq")]
    [ProducesResponseType(typeof(List<BoqTreeNodeDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<List<BoqTreeNodeDto>>> GetBoqStructure(
        Guid tenderId,
        CancellationToken cancellationToken = default)
    {
        var query = new GetBoqStructureQuery(tenderId);
        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<List<BoqTreeNodeDto>>.SuccessResponse(result));
    }

    #endregion

    #region Sections

    /// <summary>
    /// Creates a new BOQ section for a tender.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="dto">The section data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created section.</returns>
    [HttpPost("tenders/{tenderId:guid}/boq/sections")]
    [ProducesResponseType(typeof(BoqSectionDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<BoqSectionDto>> CreateSection(
        Guid tenderId,
        [FromBody] CreateBoqSectionDto dto,
        CancellationToken cancellationToken = default)
    {
        var command = new AddBoqSectionCommand
        {
            TenderId = tenderId,
            SectionNumber = dto.SectionNumber,
            Title = dto.Title,
            SortOrder = dto.SortOrder,
            ParentSectionId = dto.ParentSectionId
        };

        var result = await _mediator.Send(command, cancellationToken);
        return CreatedAtAction(nameof(GetBoqStructure), new { tenderId }, ApiResponse<BoqSectionDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Updates an existing BOQ section.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="sectionId">The section's unique identifier.</param>
    /// <param name="dto">The updated section data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The updated section if found.</returns>
    [HttpPut("tenders/{tenderId:guid}/boq/sections/{sectionId:guid}")]
    [ProducesResponseType(typeof(BoqSectionDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<BoqSectionDto>> UpdateSection(
        Guid tenderId,
        Guid sectionId,
        [FromBody] UpdateBoqSectionDto dto,
        CancellationToken cancellationToken = default)
    {
        var command = new UpdateBoqSectionCommand
        {
            TenderId = tenderId,
            SectionId = sectionId,
            SectionNumber = dto.SectionNumber,
            Title = dto.Title,
            SortOrder = dto.SortOrder,
            ParentSectionId = dto.ParentSectionId
        };

        var result = await _mediator.Send(command, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("BOQ section not found"));
        }

        return Ok(ApiResponse<BoqSectionDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Deletes a BOQ section and all its items.
    /// Also deletes child sections recursively.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="sectionId">The section's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>No content if successful.</returns>
    [HttpDelete("tenders/{tenderId:guid}/boq/sections/{sectionId:guid}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> DeleteSection(
        Guid tenderId,
        Guid sectionId,
        CancellationToken cancellationToken = default)
    {
        var command = new DeleteBoqSectionCommand(tenderId, sectionId);
        var result = await _mediator.Send(command, cancellationToken);

        if (!result)
        {
            return NotFound(ApiResponse<object>.FailureResponse("BOQ section not found"));
        }

        return NoContent();
    }

    #endregion

    #region Items

    /// <summary>
    /// Creates a new BOQ item for a tender.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="dto">The item data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The created item.</returns>
    [HttpPost("tenders/{tenderId:guid}/boq/items")]
    [ProducesResponseType(typeof(BoqItemDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<BoqItemDto>> CreateItem(
        Guid tenderId,
        [FromBody] CreateBoqItemDto dto,
        CancellationToken cancellationToken = default)
    {
        var command = new AddBoqItemCommand
        {
            TenderId = tenderId,
            SectionId = dto.SectionId,
            ItemNumber = dto.ItemNumber,
            Description = dto.Description,
            Quantity = dto.Quantity,
            Uom = dto.Uom,
            ItemType = dto.ItemType,
            Notes = dto.Notes,
            SortOrder = dto.SortOrder
        };

        var result = await _mediator.Send(command, cancellationToken);
        return CreatedAtAction(nameof(GetBoqStructure), new { tenderId }, ApiResponse<BoqItemDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Updates an existing BOQ item.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="itemId">The item's unique identifier.</param>
    /// <param name="dto">The updated item data.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The updated item if found.</returns>
    [HttpPut("tenders/{tenderId:guid}/boq/items/{itemId:guid}")]
    [ProducesResponseType(typeof(BoqItemDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<BoqItemDto>> UpdateItem(
        Guid tenderId,
        Guid itemId,
        [FromBody] UpdateBoqItemDto dto,
        CancellationToken cancellationToken = default)
    {
        var command = new UpdateBoqItemCommand
        {
            TenderId = tenderId,
            ItemId = itemId,
            SectionId = dto.SectionId,
            ItemNumber = dto.ItemNumber,
            Description = dto.Description,
            Quantity = dto.Quantity,
            Uom = dto.Uom,
            ItemType = dto.ItemType,
            Notes = dto.Notes,
            SortOrder = dto.SortOrder
        };

        var result = await _mediator.Send(command, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("BOQ item not found"));
        }

        return Ok(ApiResponse<BoqItemDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Deletes a BOQ item.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="itemId">The item's unique identifier.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>No content if successful.</returns>
    [HttpDelete("tenders/{tenderId:guid}/boq/items/{itemId:guid}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> DeleteItem(
        Guid tenderId,
        Guid itemId,
        CancellationToken cancellationToken = default)
    {
        var command = new DeleteBoqItemCommand(tenderId, itemId);
        var result = await _mediator.Send(command, cancellationToken);

        if (!result)
        {
            return NotFound(ApiResponse<object>.FailureResponse("BOQ item not found"));
        }

        return NoContent();
    }

    /// <summary>
    /// Duplicates an existing BOQ item.
    /// Creates a copy with a new auto-generated item number.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="itemId">The item's unique identifier to duplicate.</param>
    /// <param name="request">Optional request with new item number.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The duplicated item if found.</returns>
    [HttpPost("tenders/{tenderId:guid}/boq/items/{itemId:guid}/duplicate")]
    [ProducesResponseType(typeof(BoqItemDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<BoqItemDto>> DuplicateItem(
        Guid tenderId,
        Guid itemId,
        [FromBody] DuplicateBoqItemRequest? request = null,
        CancellationToken cancellationToken = default)
    {
        var command = new DuplicateBoqItemCommand(tenderId, itemId)
        {
            NewItemNumber = request?.NewItemNumber
        };

        var result = await _mediator.Send(command, cancellationToken);

        if (result == null)
        {
            return NotFound(ApiResponse<object>.FailureResponse("BOQ item not found"));
        }

        return CreatedAtAction(nameof(GetBoqStructure), new { tenderId }, ApiResponse<BoqItemDto>.SuccessResponse(result));
    }

    #endregion

    #region Units of Measurement

    /// <summary>
    /// Gets the list of available units of measurement.
    /// </summary>
    /// <param name="category">Optional filter by category (Area, Volume, Length, Weight, etc.).</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of available units of measurement.</returns>
    [HttpGet("uoms")]
    [ProducesResponseType(typeof(List<UomDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<List<UomDto>>> GetUoms(
        [FromQuery] string? category = null,
        CancellationToken cancellationToken = default)
    {
        var query = new GetUomListQuery { Category = category };
        var result = await _mediator.Send(query, cancellationToken);
        return Ok(ApiResponse<List<UomDto>>.SuccessResponse(result));
    }

    #endregion

    #region Excel Import

    /// <summary>
    /// Uploads an Excel file for BOQ import and returns a preview with detected columns.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="file">The Excel file to upload (.xlsx or .xls).</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Preview of the Excel file with detected columns and suggested mappings.</returns>
    [HttpPost("tenders/{tenderId:guid}/boq/import/upload")]
    [ProducesResponseType(typeof(ExcelPreviewDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [RequestSizeLimit(50 * 1024 * 1024)] // 50MB limit
    public async Task<ActionResult<ExcelPreviewDto>> UploadBoqImportFile(
        Guid tenderId,
        IFormFile file,
        CancellationToken cancellationToken = default)
    {
        if (file == null || file.Length == 0)
        {
            return BadRequest(ApiResponse<object>.FailureResponse("No file was uploaded."));
        }

        var allowedExtensions = new[] { ".xlsx", ".xls" };
        var fileExtension = Path.GetExtension(file.FileName).ToLowerInvariant();
        if (!allowedExtensions.Contains(fileExtension))
        {
            return BadRequest(ApiResponse<object>.FailureResponse("Only Excel files (.xlsx, .xls) are allowed."));
        }

        _logger.LogInformation(
            "Uploading BOQ import file '{FileName}' ({FileSize} bytes) for tender {TenderId}",
            file.FileName,
            file.Length,
            tenderId);

        using var stream = file.OpenReadStream();

        var command = new UploadBoqImportFileCommand
        {
            TenderId = tenderId,
            FileStream = stream,
            FileName = file.FileName,
            ContentType = file.ContentType,
            FileSize = file.Length
        };

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<ExcelPreviewDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Validates the BOQ import data with the provided column mappings.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="request">The validation request with column mappings.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Validation results including any issues found.</returns>
    [HttpPost("tenders/{tenderId:guid}/boq/import/validate")]
    [ProducesResponseType(typeof(ImportValidationResultDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ImportValidationResultDto>> ValidateBoqImport(
        Guid tenderId,
        [FromBody] ValidateBoqImportRequest request,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Validating BOQ import session {SessionId} for tender {TenderId}",
            request.ImportSessionId,
            tenderId);

        var command = new ValidateBoqImportCommand
        {
            TenderId = tenderId,
            ImportSessionId = request.ImportSessionId,
            Mappings = request.Mappings,
            SheetIndex = request.SheetIndex ?? 0,
            HeaderRowOverride = request.HeaderRowOverride
        };

        var result = await _mediator.Send(command, cancellationToken);
        return Ok(ApiResponse<ImportValidationResultDto>.SuccessResponse(result));
    }

    /// <summary>
    /// Executes the BOQ import after validation.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="request">The import execution request.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Import results including created sections and items.</returns>
    [HttpPost("tenders/{tenderId:guid}/boq/import/execute")]
    [ProducesResponseType(typeof(ImportResultDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ImportResultDto>> ExecuteBoqImport(
        Guid tenderId,
        [FromBody] ExecuteBoqImportRequest request,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Executing BOQ import session {SessionId} for tender {TenderId}",
            request.ImportSessionId,
            tenderId);

        var command = new ExecuteBoqImportCommand
        {
            TenderId = tenderId,
            ImportSessionId = request.ImportSessionId,
            ClearExisting = request.ClearExisting,
            DefaultSectionTitle = request.DefaultSectionTitle,
            SkipWarnings = request.SkipWarnings
        };

        var result = await _mediator.Send(command, cancellationToken);

        if (!result.Success)
        {
            return BadRequest(ApiResponse<ImportResultDto>.FailureResponse("Import validation failed"));
        }

        return Ok(ApiResponse<ImportResultDto>.SuccessResponse(result));
    }

    #endregion

    #region Template Export

    /// <summary>
    /// Exports a BOQ template as an Excel file for bidders to fill in unit rates.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="dto">Export options including columns to include/lock and language.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Excel file containing the BOQ template.</returns>
    /// <response code="200">Returns the Excel file.</response>
    /// <response code="400">If the request is invalid.</response>
    /// <response code="404">If the tender is not found.</response>
    [HttpPost("tenders/{tenderId:guid}/boq/export-template")]
    [ProducesResponseType(typeof(FileContentResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> ExportTemplate(
        Guid tenderId,
        [FromBody] ExportBoqTemplateDto? dto = null,
        CancellationToken cancellationToken = default)
    {
        // Use defaults if no DTO provided
        dto ??= new ExportBoqTemplateDto();

        var command = new ExportBoqTemplateCommand
        {
            TenderId = tenderId,
            IncludeColumns = dto.IncludeColumns,
            LockColumns = dto.LockColumns,
            IncludeInstructions = dto.IncludeInstructions,
            Language = dto.Language
        };

        try
        {
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
    /// Exports a BOQ template with default settings using GET for convenience.
    /// </summary>
    /// <param name="tenderId">The tender's unique identifier.</param>
    /// <param name="language">Template language (0=English, 1=Arabic, 2=Both).</param>
    /// <param name="includeInstructions">Whether to include instructions sheet.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Excel file containing the BOQ template.</returns>
    [HttpGet("tenders/{tenderId:guid}/boq/export-template")]
    [ProducesResponseType(typeof(FileContentResult), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> ExportTemplateGet(
        Guid tenderId,
        [FromQuery] TemplateLanguage language = TemplateLanguage.English,
        [FromQuery] bool includeInstructions = true,
        CancellationToken cancellationToken = default)
    {
        var command = new ExportBoqTemplateCommand
        {
            TenderId = tenderId,
            Language = language,
            IncludeInstructions = includeInstructions
        };

        try
        {
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

    #endregion
}

/// <summary>
/// Request model for duplicating a BOQ item.
/// </summary>
public class DuplicateBoqItemRequest
{
    /// <summary>
    /// Optional new item number for the duplicate.
    /// If not provided, will be auto-generated.
    /// </summary>
    public string? NewItemNumber { get; set; }
}

/// <summary>
/// Request model for BOQ import validation.
/// </summary>
public class ValidateBoqImportRequest
{
    /// <summary>
    /// The import session ID from the upload step.
    /// </summary>
    public Guid ImportSessionId { get; set; }

    /// <summary>
    /// The column mappings to use for import.
    /// </summary>
    public List<ColumnMappingDto> Mappings { get; set; } = new();

    /// <summary>
    /// Optional: Sheet index to import from (default: 0).
    /// </summary>
    public int? SheetIndex { get; set; }

    /// <summary>
    /// Optional: Override the detected header row.
    /// </summary>
    public int? HeaderRowOverride { get; set; }
}
