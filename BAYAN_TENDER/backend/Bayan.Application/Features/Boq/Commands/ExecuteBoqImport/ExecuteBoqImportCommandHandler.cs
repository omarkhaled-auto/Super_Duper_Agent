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

        // Check if BillNumber or SubItemLabel columns are mapped
        var hasBillNumberMapping = mappings.ContainsKey(BoqField.BillNumber);
        var hasSubItemLabelMapping = mappings.ContainsKey(BoqField.SubItemLabel);

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

        // ── Pre-scan: Create sections from BillNumber column if mapped ──
        if (hasBillNumberMapping)
        {
            var billSortOrder = sections.Count;
            for (var rowIndex = 0; rowIndex < sheet.Rows.Count; rowIndex++)
            {
                var row = sheet.Rows[rowIndex];
                var billNumber = GetMappedValue(row, mappings, BoqField.BillNumber);
                var itemNumber = GetMappedValue(row, mappings, BoqField.ItemNumber);
                var description = GetMappedValue(row, mappings, BoqField.Description);

                if (string.IsNullOrWhiteSpace(billNumber))
                    continue;

                // Only create a section from a bill row if it doesn't have a regular item number
                // (rows with both BillNumber and ItemNumber are items that belong to a bill)
                var isItemRow = !string.IsNullOrWhiteSpace(itemNumber);
                var sectionKey = $"BILL-{billNumber.Trim()}";

                if (!sections.ContainsKey(sectionKey))
                {
                    var billTitle = !string.IsNullOrWhiteSpace(description) && !isItemRow
                        ? description
                        : $"Bill No. {billNumber.Trim()}";

                    var billSection = new BoqSection
                    {
                        Id = Guid.NewGuid(),
                        TenderId = tenderId,
                        SectionNumber = sectionKey,
                        Title = billTitle,
                        SortOrder = billSortOrder++
                    };

                    _context.BoqSections.Add(billSection);
                    sections[sectionKey] = billSection;
                    knownSectionNumbers.Add(sectionKey);

                    _logger.LogInformation(
                        "Created bill section '{SectionKey}' with title '{Title}' from BillNumber column",
                        sectionKey, billTitle);
                }
            }
        }

        // ── Hierarchy detection ──
        // Build BoqRowContext list from sheet rows for hierarchy analysis
        var rowContexts = new List<BoqRowContext>(sheet.Rows.Count);
        for (var rowIndex = 0; rowIndex < sheet.Rows.Count; rowIndex++)
        {
            var row = sheet.Rows[rowIndex];
            rowContexts.Add(new BoqRowContext
            {
                ItemNumber = GetMappedValue(row, mappings, BoqField.ItemNumber) ?? string.Empty,
                Description = GetMappedValue(row, mappings, BoqField.Description),
                Quantity = GetMappedValue(row, mappings, BoqField.Quantity),
                Uom = GetMappedValue(row, mappings, BoqField.Uom)
            });
        }

        var hierarchyInfos = _sectionDetectionService.DetectItemHierarchy(rowContexts);

        // Build a lookup from item number → hierarchy role for quick access
        var hierarchyByIndex = new Dictionary<int, ItemHierarchyInfo>();
        foreach (var hi in hierarchyInfos)
        {
            hierarchyByIndex[hi.RowIndex] = hi;
        }

        // ── Two-pass item creation ──
        // Pass 1: Create groups and standalone items (ParentItemId = null)
        // Pass 2: Create sub-items with ParentItemId pointing to their group

        // Dictionary: item number → created BoqItem ID (for parent lookup in Pass 2)
        var createdItemsByNumber = new Dictionary<string, Guid>(StringComparer.OrdinalIgnoreCase);

        // Collect sub-item row indices for Pass 2
        var subItemRows = new List<int>();

        // Track the last created group item ID (for SubItemLabel-based parenting)
        Guid? lastGroupItemId = null;
        string? lastGroupItemNumber = null;
        string? lastGroupSectionNumber = null;

        // Map sub-item row index → parent group info captured at deferral time
        var subItemParentMap = new Dictionary<int, (Guid GroupId, string GroupNumber, string SectionNumber)>();

        // ── Pass 1: Groups + Standalone items ──
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

            // Get hierarchy info for this row
            var hasHierarchy = hierarchyByIndex.TryGetValue(rowIndex, out var hi);

            // Get mapped values
            var itemNumber = GetMappedValue(row, mappings, BoqField.ItemNumber);
            var description = GetMappedValue(row, mappings, BoqField.Description);
            var quantityStr = GetMappedValue(row, mappings, BoqField.Quantity);
            var uom = GetMappedValue(row, mappings, BoqField.Uom);
            var notes = GetMappedValue(row, mappings, BoqField.Notes);
            var billNumber = GetMappedValue(row, mappings, BoqField.BillNumber);
            var subItemLabel = GetMappedValue(row, mappings, BoqField.SubItemLabel);

            // Check if this row is a bill-only row (BillNumber mapped, has value, no item number)
            var isBillOnlyRow = hasBillNumberMapping &&
                                !string.IsNullOrWhiteSpace(billNumber) &&
                                string.IsNullOrWhiteSpace(itemNumber);
            if (isBillOnlyRow)
            {
                // Bill-only rows were already handled by section creation above
                skippedRows++;
                continue;
            }

            // Check if this row should be treated as a sub-item via SubItemLabel column
            var isExplicitSubItem = hasSubItemLabelMapping && !string.IsNullOrWhiteSpace(subItemLabel);

            // Skip empty rows
            if (string.IsNullOrWhiteSpace(itemNumber) && string.IsNullOrWhiteSpace(description) && !isExplicitSubItem)
            {
                skippedRows++;
                continue;
            }

            // Skip bill header rows (detected by hierarchy analysis)
            if (hasHierarchy && hi!.Role == ItemHierarchyRole.BillHeader)
            {
                skippedRows++;
                continue;
            }

            // Skip section header rows (they were already created as sections)
            if (_sectionDetectionService.IsSectionHeaderRow(itemNumber, quantityStr, uom) && !isExplicitSubItem)
            {
                // But not if it was detected as a Group — groups should be created as items
                var isDetectedGroup = hasHierarchy && hi!.Role == ItemHierarchyRole.Group;

                // When SubItemLabel mapping is present, items with ItemNumber but no qty/uom
                // should be treated as group items (parents of sub-items), not section headers
                var isImpliedGroup = hasSubItemLabelMapping && !string.IsNullOrWhiteSpace(itemNumber);

                if (!isDetectedGroup && !isImpliedGroup)
                {
                    skippedRows++;
                    continue;
                }
            }

            // Defer sub-items to Pass 2 (both hierarchy-detected and explicit SubItemLabel)
            if (hasHierarchy && hi!.Role == ItemHierarchyRole.SubItem)
            {
                subItemRows.Add(rowIndex);
                if (lastGroupItemId != null && lastGroupItemNumber != null && lastGroupSectionNumber != null)
                    subItemParentMap[rowIndex] = (lastGroupItemId.Value, lastGroupItemNumber, lastGroupSectionNumber);
                continue;
            }
            if (isExplicitSubItem && !(hasHierarchy && hi!.Role == ItemHierarchyRole.Group))
            {
                // Explicit sub-item (has SubItemLabel value) — defer to Pass 2
                subItemRows.Add(rowIndex);
                if (lastGroupItemId != null && lastGroupItemNumber != null && lastGroupSectionNumber != null)
                    subItemParentMap[rowIndex] = (lastGroupItemId.Value, lastGroupItemNumber, lastGroupSectionNumber);
                continue;
            }

            // Determine section — use bill section if BillNumber is mapped and present
            BoqSection section;
            if (hasBillNumberMapping && !string.IsNullOrWhiteSpace(billNumber))
            {
                var billSectionKey = $"BILL-{billNumber.Trim()}";
                section = sections.GetValueOrDefault(billSectionKey) ?? defaultSection;
            }
            else
            {
                section = ResolveSection(itemNumber, knownSectionNumbers, sections, defaultSection);
            }

            // Parse quantity
            decimal quantity = 0;
            if (!string.IsNullOrWhiteSpace(quantityStr) && decimal.TryParse(quantityStr, out var parsedQty))
            {
                quantity = parsedQty;
            }

            // Get sort order
            if (!sortOrderBySection.ContainsKey(section.SectionNumber))
                sortOrderBySection[section.SectionNumber] = 0;
            var sortOrder = sortOrderBySection[section.SectionNumber]++;

            var isGroup = hasHierarchy && hi!.Role == ItemHierarchyRole.Group;

            // If an item has ItemNumber but no Quantity and no UOM, mark as group
            // (applies when hierarchy detection didn't explicitly classify it)
            if (!isGroup && !string.IsNullOrWhiteSpace(itemNumber))
            {
                var hasQty = !string.IsNullOrWhiteSpace(quantityStr) &&
                             decimal.TryParse(quantityStr, out var q) && q != 0;
                var hasUom = !string.IsNullOrWhiteSpace(uom);
                if (!hasQty && !hasUom)
                {
                    isGroup = true;
                }
            }

            var boqItem = new BoqItem
            {
                Id = Guid.NewGuid(),
                TenderId = tenderId,
                SectionId = section.Id,
                ItemNumber = itemNumber,
                Description = description ?? string.Empty,
                Quantity = quantity,
                Uom = uom ?? string.Empty,
                ItemType = BoqItemType.Base,
                Notes = notes,
                SortOrder = sortOrder,
                IsGroup = isGroup,
                ParentItemId = null
            };

            _context.BoqItems.Add(boqItem);
            itemCount++;

            // Store for sub-item parent lookup
            if (!string.IsNullOrWhiteSpace(itemNumber))
            {
                createdItemsByNumber[itemNumber] = boqItem.Id;
            }

            // Track last group for SubItemLabel-based parenting
            if (isGroup)
            {
                lastGroupItemId = boqItem.Id;
                lastGroupItemNumber = boqItem.ItemNumber;
                lastGroupSectionNumber = section.SectionNumber;
            }

            // Track items per section
            if (!itemsPerSection.ContainsKey(section.SectionNumber))
                itemsPerSection[section.SectionNumber] = 0;
            itemsPerSection[section.SectionNumber]++;
        }

        // ── Pass 2: Sub-items (with ParentItemId) ──
        foreach (var rowIndex in subItemRows)
        {
            var row = sheet.Rows[rowIndex];
            var rowNumber = rowIndex + sheet.HeaderRowIndex + 2;
            var hasHi = hierarchyByIndex.TryGetValue(rowIndex, out var hi);

            var itemNumber = GetMappedValue(row, mappings, BoqField.ItemNumber);
            var description = GetMappedValue(row, mappings, BoqField.Description);
            var quantityStr = GetMappedValue(row, mappings, BoqField.Quantity);
            var uom = GetMappedValue(row, mappings, BoqField.Uom);
            var notes = GetMappedValue(row, mappings, BoqField.Notes);
            var billNumber = GetMappedValue(row, mappings, BoqField.BillNumber);
            var subItemLabel = GetMappedValue(row, mappings, BoqField.SubItemLabel);

            // Resolve parent item ID
            Guid? parentItemId = null;
            string? parentSectionNumber = null;

            if (hasHi && hi!.ParentItemNumber != null &&
                createdItemsByNumber.TryGetValue(hi.ParentItemNumber, out var parentId))
            {
                // Hierarchy-detected parent
                parentItemId = parentId;
                parentSectionNumber = hi.ParentItemNumber;
            }
            else if (hasSubItemLabelMapping && !string.IsNullOrWhiteSpace(subItemLabel) &&
                     subItemParentMap.TryGetValue(rowIndex, out var capturedParent))
            {
                // SubItemLabel-based parent: use the group item captured at deferral time
                parentItemId = capturedParent.GroupId;
                parentSectionNumber = capturedParent.SectionNumber;
            }
            else if (hasHi && hi!.ParentItemNumber != null)
            {
                // Parent wasn't created (possibly filtered) — create as standalone instead
                _logger.LogWarning(
                    "Sub-item '{ItemNumber}' at row {RowNumber} has parent '{ParentItemNumber}' which was not found. Creating as standalone.",
                    itemNumber, rowNumber, hi.ParentItemNumber);
            }

            // Determine section — use bill section, parent's section, or resolve from item number
            BoqSection section;
            if (hasBillNumberMapping && !string.IsNullOrWhiteSpace(billNumber))
            {
                var billSectionKey = $"BILL-{billNumber.Trim()}";
                section = sections.GetValueOrDefault(billSectionKey) ?? defaultSection;
            }
            else if (parentItemId != null && parentSectionNumber != null)
            {
                // Find parent's section by looking up the parent item number
                section = ResolveSection(parentSectionNumber, knownSectionNumbers, sections, defaultSection);
            }
            else
            {
                section = ResolveSection(itemNumber, knownSectionNumbers, sections, defaultSection);
            }

            // Parse quantity
            decimal quantity = 0;
            if (!string.IsNullOrWhiteSpace(quantityStr) && decimal.TryParse(quantityStr, out var parsedQty))
            {
                quantity = parsedQty;
            }

            // Get sort order
            if (!sortOrderBySection.ContainsKey(section.SectionNumber))
                sortOrderBySection[section.SectionNumber] = 0;
            var sortOrder = sortOrderBySection[section.SectionNumber]++;

            // Use SubItemLabel as the item number if no explicit item number is provided
            // Prefix with parent item number to ensure uniqueness across groups (e.g., "1.01.a" instead of just "a")
            var effectiveItemNumber = itemNumber;
            if (string.IsNullOrWhiteSpace(effectiveItemNumber) && !string.IsNullOrWhiteSpace(subItemLabel))
            {
                // Try to get parent's item number for composite key
                string? parentNum = null;
                if (hasHi && hi?.ParentItemNumber != null)
                    parentNum = hi.ParentItemNumber;
                else if (subItemParentMap.TryGetValue(rowIndex, out var pInfo))
                    parentNum = pInfo.GroupNumber;

                effectiveItemNumber = !string.IsNullOrWhiteSpace(parentNum)
                    ? $"{parentNum}.{subItemLabel.Trim()}"
                    : subItemLabel;
            }

            var boqItem = new BoqItem
            {
                Id = Guid.NewGuid(),
                TenderId = tenderId,
                SectionId = section.Id,
                ItemNumber = effectiveItemNumber ?? $"ITEM-{rowNumber}",
                Description = description ?? string.Empty,
                Quantity = quantity,
                Uom = uom ?? string.Empty,
                ItemType = BoqItemType.Base,
                Notes = notes,
                SortOrder = sortOrder,
                IsGroup = false,
                ParentItemId = parentItemId
            };

            _context.BoqItems.Add(boqItem);
            itemCount++;

            // Store in lookup (sub-items can theoretically be parents too)
            if (!string.IsNullOrWhiteSpace(effectiveItemNumber))
            {
                createdItemsByNumber[effectiveItemNumber] = boqItem.Id;
            }

            // Track items per section
            if (!itemsPerSection.ContainsKey(section.SectionNumber))
                itemsPerSection[section.SectionNumber] = 0;
            itemsPerSection[section.SectionNumber]++;
        }

        var groupCount = hierarchyInfos.Count(h => h.Role == ItemHierarchyRole.Group);
        var subItemCount = subItemRows.Count;
        if (groupCount > 0 || subItemCount > 0)
        {
            _logger.LogInformation(
                "Hierarchy detection: {GroupCount} group items, {SubItemCount} sub-items, {StandaloneCount} standalone items",
                groupCount, subItemCount, itemCount - groupCount - subItemCount);
        }

        if (hasBillNumberMapping)
        {
            var billSectionCount = sections.Keys.Count(k => k.StartsWith("BILL-", StringComparison.OrdinalIgnoreCase));
            _logger.LogInformation(
                "BillNumber column mapping: created {BillSectionCount} bill sections",
                billSectionCount);
        }

        return Task.FromResult((itemCount, skippedRows, itemsPerSection));
    }

    /// <summary>
    /// Resolves the best section for an item number using section detection service.
    /// </summary>
    private BoqSection ResolveSection(
        string? itemNumber,
        HashSet<string> knownSectionNumbers,
        Dictionary<string, BoqSection> sections,
        BoqSection defaultSection)
    {
        if (!string.IsNullOrWhiteSpace(itemNumber))
        {
            var sectionNumber = _sectionDetectionService.FindBestSection(itemNumber, knownSectionNumbers);
            if (sections.TryGetValue(sectionNumber, out var section))
            {
                return section;
            }

            // Try parent sections
            var parentNumber = _sectionDetectionService.GetParentSectionNumber(sectionNumber);
            while (!string.IsNullOrEmpty(parentNumber))
            {
                if (sections.TryGetValue(parentNumber, out section))
                {
                    return section;
                }
                parentNumber = _sectionDetectionService.GetParentSectionNumber(parentNumber);
            }
        }

        return defaultSection;
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
