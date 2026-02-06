using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.DTOs;
using Bayan.Application.Features.Boq.Services;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Boq.Commands.ValidateBoqImport;

/// <summary>
/// Handler for ValidateBoqImportCommand.
/// </summary>
public class ValidateBoqImportCommandHandler : IRequestHandler<ValidateBoqImportCommand, ImportValidationResultDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IBoqImportSessionService _sessionService;
    private readonly IBoqSectionDetectionService _sectionDetectionService;
    private readonly ILogger<ValidateBoqImportCommandHandler> _logger;

    public ValidateBoqImportCommandHandler(
        IApplicationDbContext context,
        IBoqImportSessionService sessionService,
        IBoqSectionDetectionService sectionDetectionService,
        ILogger<ValidateBoqImportCommandHandler> logger)
    {
        _context = context;
        _sessionService = sessionService;
        _sectionDetectionService = sectionDetectionService;
        _logger = logger;
    }

    public async Task<ImportValidationResultDto> Handle(
        ValidateBoqImportCommand request,
        CancellationToken cancellationToken)
    {
        // Get the import session
        var session = await _sessionService.GetSessionAsync(request.ImportSessionId, cancellationToken);
        if (session == null)
        {
            throw new NotFoundException("Import session", request.ImportSessionId);
        }

        if (session.TenderId != request.TenderId)
        {
            throw new ApplicationException("Import session does not belong to the specified tender.");
        }

        // Get UOM codes from database for validation
        var validUomCodes = await _context.UomMasters
            .Select(u => u.Code.ToLower())
            .ToListAsync(cancellationToken);

        // Get the sheet to process
        var sheetIndex = request.SheetIndex;
        if (sheetIndex >= session.ParseResult.Sheets.Count)
        {
            throw new ApplicationException($"Sheet index {sheetIndex} is out of range.");
        }

        var sheet = session.ParseResult.Sheets[sheetIndex];

        // Build column mapping dictionary
        var mappings = request.Mappings.ToDictionary(m => m.BoqField, m => m.ExcelColumn);

        // Update session with mappings
        await _sessionService.UpdateMappingsAsync(request.ImportSessionId, request.Mappings, cancellationToken);

        // Validate all rows
        var issues = new List<ImportValidationIssue>();
        var itemNumbers = new List<string>();
        var uomCodes = new HashSet<string>();
        var seenItemNumbers = new HashSet<string>();
        var validRowCount = 0;
        var skippedRowCount = 0;

        for (var rowIndex = 0; rowIndex < sheet.Rows.Count; rowIndex++)
        {
            var row = sheet.Rows[rowIndex];
            var rowNumber = rowIndex + sheet.HeaderRowIndex + 2; // 1-based, after header

            // Get mapped values
            var itemNumber = GetMappedValue(row, mappings, BoqField.ItemNumber);
            var description = GetMappedValue(row, mappings, BoqField.Description);
            var quantityStr = GetMappedValue(row, mappings, BoqField.Quantity);
            var uom = GetMappedValue(row, mappings, BoqField.Uom);

            // Check if row is empty
            if (string.IsNullOrWhiteSpace(itemNumber) && string.IsNullOrWhiteSpace(description))
            {
                skippedRowCount++;
                issues.Add(new ImportValidationIssue
                {
                    RowNumber = rowNumber,
                    Severity = ValidationSeverity.Info,
                    IssueCode = ValidationIssueCodes.EmptyRow,
                    Message = "Row is empty and will be skipped."
                });
                continue;
            }

            var rowHasError = false;

            // Validate item number
            if (string.IsNullOrWhiteSpace(itemNumber))
            {
                issues.Add(new ImportValidationIssue
                {
                    RowNumber = rowNumber,
                    ColumnName = mappings.GetValueOrDefault(BoqField.ItemNumber),
                    Severity = ValidationSeverity.Error,
                    IssueCode = ValidationIssueCodes.MissingItemNumber,
                    Message = "Item number is required.",
                    SuggestedFix = "Provide an item number for this row."
                });
                rowHasError = true;
            }
            else
            {
                // Validate item number format
                var parseResult = _sectionDetectionService.ParseItemNumber(itemNumber);
                if (!parseResult.Success)
                {
                    issues.Add(new ImportValidationIssue
                    {
                        RowNumber = rowNumber,
                        ColumnName = mappings.GetValueOrDefault(BoqField.ItemNumber),
                        Value = itemNumber,
                        Severity = ValidationSeverity.Warning,
                        IssueCode = ValidationIssueCodes.InvalidItemNumber,
                        Message = $"Item number '{itemNumber}' has non-standard format.",
                        SuggestedFix = "Use format like 1.1, 1.2.1, etc."
                    });
                }

                // Check for duplicates
                if (seenItemNumbers.Contains(itemNumber.ToLower()))
                {
                    issues.Add(new ImportValidationIssue
                    {
                        RowNumber = rowNumber,
                        ColumnName = mappings.GetValueOrDefault(BoqField.ItemNumber),
                        Value = itemNumber,
                        Severity = ValidationSeverity.Error,
                        IssueCode = ValidationIssueCodes.DuplicateItemNumber,
                        Message = $"Duplicate item number '{itemNumber}'.",
                        SuggestedFix = "Ensure each item has a unique item number."
                    });
                    rowHasError = true;
                }
                else
                {
                    seenItemNumbers.Add(itemNumber.ToLower());
                    itemNumbers.Add(itemNumber);
                }
            }

            // Validate description
            if (string.IsNullOrWhiteSpace(description))
            {
                issues.Add(new ImportValidationIssue
                {
                    RowNumber = rowNumber,
                    ColumnName = mappings.GetValueOrDefault(BoqField.Description),
                    Severity = ValidationSeverity.Error,
                    IssueCode = ValidationIssueCodes.MissingDescription,
                    Message = "Description is required.",
                    SuggestedFix = "Provide a description for this item."
                });
                rowHasError = true;
            }

            // Validate quantity
            if (!string.IsNullOrWhiteSpace(quantityStr))
            {
                if (!decimal.TryParse(quantityStr, out var quantity))
                {
                    issues.Add(new ImportValidationIssue
                    {
                        RowNumber = rowNumber,
                        ColumnName = mappings.GetValueOrDefault(BoqField.Quantity),
                        Value = quantityStr,
                        Severity = ValidationSeverity.Warning,
                        IssueCode = ValidationIssueCodes.InvalidQuantity,
                        Message = $"Invalid quantity value '{quantityStr}'.",
                        SuggestedFix = "Provide a numeric quantity value."
                    });
                }
                else if (quantity < 0)
                {
                    issues.Add(new ImportValidationIssue
                    {
                        RowNumber = rowNumber,
                        ColumnName = mappings.GetValueOrDefault(BoqField.Quantity),
                        Value = quantityStr,
                        Severity = ValidationSeverity.Warning,
                        IssueCode = ValidationIssueCodes.NegativeQuantity,
                        Message = "Quantity is negative.",
                        SuggestedFix = "Use a positive quantity value."
                    });
                }
            }

            // Validate UOM
            if (!string.IsNullOrWhiteSpace(uom))
            {
                uomCodes.Add(uom);
                if (!validUomCodes.Contains(uom.ToLower()))
                {
                    issues.Add(new ImportValidationIssue
                    {
                        RowNumber = rowNumber,
                        ColumnName = mappings.GetValueOrDefault(BoqField.Uom),
                        Value = uom,
                        Severity = ValidationSeverity.Warning,
                        IssueCode = ValidationIssueCodes.UnknownUom,
                        Message = $"Unknown UOM code '{uom}'.",
                        SuggestedFix = "Use a valid UOM code from the master list."
                    });
                }
            }

            if (!rowHasError)
            {
                validRowCount++;
            }
        }

        // Detect sections from item numbers
        var detectedSections = _sectionDetectionService.DetectSections(itemNumbers);

        // Find unknown UOM codes
        var unknownUomCodes = uomCodes
            .Where(code => !validUomCodes.Contains(code.ToLower()))
            .ToList();

        // Build summary
        var summary = new ImportDataSummary
        {
            TotalSections = detectedSections.Count,
            TotalItems = validRowCount,
            UniqueUomCount = uomCodes.Count,
            UomCodes = uomCodes.ToList(),
            UnknownUomCodes = unknownUomCodes,
            SkippedRows = skippedRowCount
        };

        var warningCount = issues.Count(i => i.Severity == ValidationSeverity.Warning);
        var errorCount = issues.Count(i => i.Severity == ValidationSeverity.Error);

        var result = new ImportValidationResultDto
        {
            ImportSessionId = request.ImportSessionId,
            ValidCount = validRowCount,
            WarningCount = warningCount,
            ErrorCount = errorCount,
            TotalRows = sheet.Rows.Count,
            Issues = issues.OrderBy(i => i.RowNumber).ThenByDescending(i => i.Severity).ToList(),
            DetectedSections = detectedSections,
            Summary = summary
        };

        // Update session with validation result
        await _sessionService.UpdateValidationResultAsync(request.ImportSessionId, result, cancellationToken);

        _logger.LogInformation(
            "Validated BOQ import session {SessionId}: {ValidCount} valid, {WarningCount} warnings, {ErrorCount} errors, {SectionCount} sections detected",
            request.ImportSessionId,
            validRowCount,
            warningCount,
            errorCount,
            detectedSections.Count);

        return result;
    }

    private static string? GetMappedValue(
        Dictionary<string, object?> row,
        Dictionary<BoqField, string> mappings,
        BoqField field)
    {
        if (!mappings.TryGetValue(field, out var columnName) || string.IsNullOrWhiteSpace(columnName))
        {
            return null;
        }

        if (row.TryGetValue(columnName, out var value) && value != null)
        {
            return value.ToString()?.Trim();
        }

        return null;
    }
}
