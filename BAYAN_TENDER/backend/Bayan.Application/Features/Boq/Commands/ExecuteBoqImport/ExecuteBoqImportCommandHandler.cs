using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.DTOs;
using Bayan.Application.Features.Boq.Services;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Boq.Commands.ExecuteBoqImport;

/// <summary>
/// Handler for ExecuteBoqImportCommand.
/// </summary>
public class ExecuteBoqImportCommandHandler : IRequestHandler<ExecuteBoqImportCommand, ImportResultDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IBoqImportSessionService _sessionService;
    private readonly IBoqSectionDetectionService _sectionDetectionService;
    private readonly IFileStorageService _fileStorageService;
    private readonly ICurrentUserService _currentUserService;
    private readonly ILogger<ExecuteBoqImportCommandHandler> _logger;

    public ExecuteBoqImportCommandHandler(
        IApplicationDbContext context,
        IBoqImportSessionService sessionService,
        IBoqSectionDetectionService sectionDetectionService,
        IFileStorageService fileStorageService,
        ICurrentUserService currentUserService,
        ILogger<ExecuteBoqImportCommandHandler> logger)
    {
        _context = context;
        _sessionService = sessionService;
        _sectionDetectionService = sectionDetectionService;
        _fileStorageService = fileStorageService;
        _currentUserService = currentUserService;
        _logger = logger;
    }

    public async Task<ImportResultDto> Handle(
        ExecuteBoqImportCommand request,
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

        if (session.ValidationResult == null)
        {
            throw new ApplicationException("Import must be validated before execution.");
        }

        if (!session.ValidationResult.CanProceed)
        {
            throw new ApplicationException("Import cannot proceed due to validation errors.");
        }

        // Verify tender exists
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new NotFoundException("Tender", request.TenderId);
        }

        var warnings = new List<string>();
        string? originalFilePath = null;

        try
        {
            // Clear existing BOQ data if requested
            if (request.ClearExisting)
            {
                await ClearExistingBoqDataAsync(request.TenderId, cancellationToken);
                _logger.LogInformation("Cleared existing BOQ data for tender {TenderId}", request.TenderId);
            }

            // Get the sheet data
            var sheet = session.ParseResult.Sheets[0];

            // Build column mapping dictionary
            var mappings = session.ColumnMappings.ToDictionary(m => m.BoqField, m => m.ExcelColumn);

            // Create sections
            var createdSections = await CreateSectionsAsync(
                request.TenderId,
                session.ValidationResult.DetectedSections,
                request.DefaultSectionTitle ?? "General",
                cancellationToken);

            // Create items
            var itemResults = await CreateItemsAsync(
                request.TenderId,
                sheet,
                mappings,
                createdSections,
                request.SkipWarnings,
                session.ValidationResult.Issues,
                warnings,
                cancellationToken);

            // Store original file in MinIO if stream provided
            if (request.OriginalFileStream != null && !string.IsNullOrEmpty(request.OriginalFileName))
            {
                try
                {
                    originalFilePath = await _fileStorageService.UploadFileAsync(
                        request.OriginalFileStream,
                        request.OriginalFileName,
                        request.ContentType ?? "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        $"tender-boq/{request.TenderId}/imports",
                        cancellationToken);

                    _logger.LogInformation("Stored original BOQ file at {FilePath}", originalFilePath);
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Failed to store original BOQ file, continuing import");
                    warnings.Add("Original file could not be stored for reference.");
                }
            }

            // Save all changes
            await _context.SaveChangesAsync(cancellationToken);

            // Mark session as completed
            await _sessionService.CompleteSessionAsync(request.ImportSessionId, cancellationToken);

            // Build result
            var result = new ImportResultDto
            {
                Success = true,
                ImportedSections = createdSections.Count,
                ImportedItems = itemResults.ItemCount,
                SkippedRows = itemResults.SkippedRows,
                TenderId = request.TenderId,
                OriginalFilePath = originalFilePath,
                Sections = BuildSectionResults(createdSections, itemResults.ItemsPerSection),
                ImportedAt = DateTime.UtcNow,
                ImportedBy = _currentUserService.UserId,
                Warnings = warnings
            };

            _logger.LogInformation(
                "Successfully imported BOQ for tender {TenderId}: {SectionCount} sections, {ItemCount} items",
                request.TenderId,
                result.ImportedSections,
                result.ImportedItems);

            return result;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to execute BOQ import for tender {TenderId}", request.TenderId);

            return new ImportResultDto
            {
                Success = false,
                TenderId = request.TenderId,
                ImportedAt = DateTime.UtcNow,
                ImportedBy = _currentUserService.UserId,
                ErrorMessage = $"Import failed: {ex.Message}",
                Warnings = warnings
            };
        }
    }

    private async Task ClearExistingBoqDataAsync(Guid tenderId, CancellationToken cancellationToken)
    {
        // Delete existing items
        var existingItems = await _context.BoqItems
            .Where(i => i.TenderId == tenderId)
            .ToListAsync(cancellationToken);

        _context.BoqItems.RemoveRange(existingItems);

        // Delete existing sections
        var existingSections = await _context.BoqSections
            .Where(s => s.TenderId == tenderId)
            .ToListAsync(cancellationToken);

        _context.BoqSections.RemoveRange(existingSections);

        await _context.SaveChangesAsync(cancellationToken);
    }

    private async Task<Dictionary<string, BoqSection>> CreateSectionsAsync(
        Guid tenderId,
        List<DetectedSectionDto> detectedSections,
        string defaultTitle,
        CancellationToken cancellationToken)
    {
        var createdSections = new Dictionary<string, BoqSection>();

        // First pass: create all sections without parent references
        var sortOrder = 0;
        foreach (var sectionDto in detectedSections.OrderBy(s => s.Level).ThenBy(s => s.SectionNumber))
        {
            var section = new BoqSection
            {
                Id = Guid.NewGuid(),
                TenderId = tenderId,
                SectionNumber = sectionDto.SectionNumber,
                Title = sectionDto.Title ?? $"Section {sectionDto.SectionNumber}",
                SortOrder = sortOrder++
            };

            _context.BoqSections.Add(section);
            createdSections[sectionDto.SectionNumber] = section;
        }

        // Ensure there's at least a default section
        if (createdSections.Count == 0)
        {
            var defaultSection = new BoqSection
            {
                Id = Guid.NewGuid(),
                TenderId = tenderId,
                SectionNumber = "1",
                Title = defaultTitle,
                SortOrder = 0
            };

            _context.BoqSections.Add(defaultSection);
            createdSections["1"] = defaultSection;
        }

        // Second pass: set parent references
        foreach (var sectionDto in detectedSections)
        {
            if (!string.IsNullOrEmpty(sectionDto.ParentSectionNumber) &&
                createdSections.TryGetValue(sectionDto.SectionNumber, out var section) &&
                createdSections.TryGetValue(sectionDto.ParentSectionNumber, out var parentSection))
            {
                section.ParentSectionId = parentSection.Id;
            }
        }

        await _context.SaveChangesAsync(cancellationToken);

        return createdSections;
    }

    private Task<(int ItemCount, int SkippedRows, Dictionary<string, int> ItemsPerSection)> CreateItemsAsync(
        Guid tenderId,
        ExcelSheetData sheet,
        Dictionary<BoqField, string> mappings,
        Dictionary<string, BoqSection> sections,
        bool skipWarnings,
        List<ImportValidationIssue> issues,
        List<string> warnings,
        CancellationToken cancellationToken)
    {
        var itemCount = 0;
        var skippedRows = 0;
        var itemsPerSection = new Dictionary<string, int>();
        var sortOrderBySection = new Dictionary<string, int>();

        // Get row numbers with errors or warnings
        var errorRows = issues
            .Where(i => i.Severity == ValidationSeverity.Error)
            .Select(i => i.RowNumber)
            .ToHashSet();

        var warningRows = issues
            .Where(i => i.Severity == ValidationSeverity.Warning)
            .Select(i => i.RowNumber)
            .ToHashSet();

        // Get default section
        var defaultSection = sections.Values.FirstOrDefault();
        if (defaultSection == null)
        {
            throw new ApplicationException("No sections available for import.");
        }

        // Build set of known section numbers for best-section lookup
        var knownSectionNumbers = new HashSet<string>(sections.Keys, StringComparer.OrdinalIgnoreCase);

        for (var rowIndex = 0; rowIndex < sheet.Rows.Count; rowIndex++)
        {
            var row = sheet.Rows[rowIndex];
            var rowNumber = rowIndex + sheet.HeaderRowIndex + 2;

            // Skip error rows
            if (errorRows.Contains(rowNumber))
            {
                skippedRows++;
                continue;
            }

            // Skip warning rows if requested
            if (skipWarnings && warningRows.Contains(rowNumber))
            {
                skippedRows++;
                continue;
            }

            // Get mapped values
            var itemNumber = GetMappedValue(row, mappings, BoqField.ItemNumber);
            var description = GetMappedValue(row, mappings, BoqField.Description);
            var quantityStr = GetMappedValue(row, mappings, BoqField.Quantity);
            var uom = GetMappedValue(row, mappings, BoqField.Uom);
            var notes = GetMappedValue(row, mappings, BoqField.Notes);

            // Skip empty rows
            if (string.IsNullOrWhiteSpace(itemNumber) && string.IsNullOrWhiteSpace(description))
            {
                skippedRows++;
                continue;
            }

            // Skip section header rows (they were already created as sections)
            if (_sectionDetectionService.IsSectionHeaderRow(itemNumber, quantityStr, uom))
            {
                skippedRows++;
                continue;
            }

            // Determine best section for this item using context-aware lookup
            BoqSection section;
            if (!string.IsNullOrWhiteSpace(itemNumber))
            {
                var sectionNumber = _sectionDetectionService.FindBestSection(itemNumber, knownSectionNumbers);
                if (!sections.TryGetValue(sectionNumber, out section!))
                {
                    // Try parent sections
                    var parentNumber = _sectionDetectionService.GetParentSectionNumber(sectionNumber);
                    while (!string.IsNullOrEmpty(parentNumber))
                    {
                        if (sections.TryGetValue(parentNumber, out section!))
                        {
                            break;
                        }
                        parentNumber = _sectionDetectionService.GetParentSectionNumber(parentNumber);
                    }

                    section ??= defaultSection;
                }
            }
            else
            {
                section = defaultSection;
            }

            // Parse quantity
            decimal quantity = 0;
            if (!string.IsNullOrWhiteSpace(quantityStr) && decimal.TryParse(quantityStr, out var parsedQty))
            {
                quantity = parsedQty;
            }

            // Get sort order for this section
            if (!sortOrderBySection.ContainsKey(section.SectionNumber))
            {
                sortOrderBySection[section.SectionNumber] = 0;
            }
            var sortOrder = sortOrderBySection[section.SectionNumber]++;

            // Create BOQ item
            var boqItem = new BoqItem
            {
                Id = Guid.NewGuid(),
                TenderId = tenderId,
                SectionId = section.Id,
                ItemNumber = itemNumber ?? $"ITEM-{rowNumber}",
                Description = description ?? string.Empty,
                Quantity = quantity,
                Uom = uom ?? string.Empty,
                ItemType = BoqItemType.Base,
                Notes = notes,
                SortOrder = sortOrder
            };

            _context.BoqItems.Add(boqItem);
            itemCount++;

            // Track items per section
            if (!itemsPerSection.ContainsKey(section.SectionNumber))
            {
                itemsPerSection[section.SectionNumber] = 0;
            }
            itemsPerSection[section.SectionNumber]++;
        }

        return Task.FromResult((itemCount, skippedRows, itemsPerSection));
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

    private static List<ImportedSectionResult> BuildSectionResults(
        Dictionary<string, BoqSection> sections,
        Dictionary<string, int> itemsPerSection)
    {
        var results = new List<ImportedSectionResult>();

        // Group sections by parent - use a lookup which handles null keys better
        var sectionsByParent = sections.Values.ToLookup(s => s.ParentSectionId);

        // Build root sections (those with null ParentSectionId)
        foreach (var section in sectionsByParent[null])
        {
            results.Add(BuildSectionResult(section, sectionsByParent, itemsPerSection));
        }

        return results.OrderBy(s => s.SectionNumber).ToList();
    }

    private static ImportedSectionResult BuildSectionResult(
        BoqSection section,
        ILookup<Guid?, BoqSection> sectionsByParent,
        Dictionary<string, int> itemsPerSection)
    {
        var childSections = sectionsByParent[section.Id];

        return new ImportedSectionResult
        {
            SectionId = section.Id,
            SectionNumber = section.SectionNumber,
            Title = section.Title,
            ItemCount = itemsPerSection.GetValueOrDefault(section.SectionNumber),
            ChildSections = childSections
                .Select(child => BuildSectionResult(child, sectionsByParent, itemsPerSection))
                .OrderBy(s => s.SectionNumber)
                .ToList()
        };
    }
}
