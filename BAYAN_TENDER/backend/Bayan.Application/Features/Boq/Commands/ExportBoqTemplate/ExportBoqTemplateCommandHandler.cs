using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Boq.Commands.ExportBoqTemplate;

/// <summary>
/// Handler for ExportBoqTemplateCommand.
/// </summary>
public class ExportBoqTemplateCommandHandler : IRequestHandler<ExportBoqTemplateCommand, ExportResultDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ITemplateExportService _templateExportService;
    private readonly ILogger<ExportBoqTemplateCommandHandler> _logger;

    public ExportBoqTemplateCommandHandler(
        IApplicationDbContext context,
        ITemplateExportService templateExportService,
        ILogger<ExportBoqTemplateCommandHandler> logger)
    {
        _context = context;
        _templateExportService = templateExportService;
        _logger = logger;
    }

    public async Task<ExportResultDto> Handle(
        ExportBoqTemplateCommand request,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation("Exporting BOQ template for tender {TenderId}", request.TenderId);

        // Fetch tender with BOQ data including child items for hierarchy
        var tender = await _context.Tenders
            .AsNoTracking()
            .Include(t => t.BoqSections.OrderBy(s => s.SortOrder))
            .Include(t => t.BoqItems.OrderBy(i => i.SortOrder))
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new KeyNotFoundException($"Tender with ID {request.TenderId} not found.");
        }

        // Fetch available UOMs for dropdown
        var uoms = await _context.UomMasters
            .AsNoTracking()
            .OrderBy(u => u.Category)
            .ThenBy(u => u.Name)
            .Select(u => u.Code)
            .ToListAsync(cancellationToken);

        // Build section hierarchy with items (now includes hierarchy metadata)
        var sections = BuildSectionHierarchy(tender.BoqSections.ToList(), tender.BoqItems.ToList());

        // Ensure the "Level" column is included for hierarchy-aware exports
        var includeColumns = new List<string>(request.IncludeColumns);
        if (!includeColumns.Contains("Level"))
        {
            // Insert "Level" column after "Section" if present, otherwise at position 0
            int sectionIdx = includeColumns.IndexOf("Section");
            includeColumns.Insert(sectionIdx >= 0 ? sectionIdx + 1 : 0, "Level");
        }

        // Build generation request
        var generationRequest = new BoqTemplateGenerationRequest
        {
            TenderId = tender.Id,
            TenderTitle = tender.Title,
            TenderReference = tender.Reference,
            SubmissionDeadline = tender.SubmissionDeadline,
            Currency = tender.BaseCurrency,
            PricingLevel = tender.PricingLevel,
            Sections = sections,
            AvailableUoms = uoms,
            IncludeColumns = includeColumns,
            LockColumns = request.LockColumns,
            IncludeInstructions = request.IncludeInstructions,
            Language = request.Language
        };

        // Generate Excel file
        var result = await _templateExportService.GenerateBoqTemplateAsync(generationRequest, cancellationToken);

        _logger.LogInformation(
            "BOQ template exported successfully for tender {TenderId} at pricing level {PricingLevel}. File size: {FileSize} bytes",
            request.TenderId,
            tender.PricingLevel,
            result.FileSize);

        return result;
    }

    private static List<BoqSectionExportDto> BuildSectionHierarchy(
        List<Domain.Entities.BoqSection> sections,
        List<Domain.Entities.BoqItem> items)
    {
        var itemsBySection = items
            .GroupBy(i => i.SectionId)
            .ToDictionary(g => g.Key, g => g.OrderBy(i => i.SortOrder).ToList());

        return sections
            .Where(s => s.ParentSectionId == null) // Root sections only
            .OrderBy(s => s.SortOrder)
            .Select(s => MapSection(s, sections, itemsBySection, items))
            .ToList();
    }

    private static BoqSectionExportDto MapSection(
        Domain.Entities.BoqSection section,
        List<Domain.Entities.BoqSection> allSections,
        Dictionary<Guid, List<Domain.Entities.BoqItem>> itemsBySection,
        List<Domain.Entities.BoqItem> allItems)
    {
        var sectionDto = new BoqSectionExportDto
        {
            SectionNumber = section.SectionNumber,
            Title = section.Title,
            Items = new List<BoqItemExportDto>()
        };

        // Add items for this section with hierarchy metadata
        if (itemsBySection.TryGetValue(section.Id, out var sectionItems))
        {
            foreach (var item in sectionItems)
            {
                var hierarchyLevel = DetermineHierarchyLevel(item);
                sectionDto.Items.Add(new BoqItemExportDto
                {
                    ItemNumber = item.ItemNumber,
                    Description = item.Description,
                    Quantity = item.Quantity,
                    Uom = item.Uom,
                    Notes = item.Notes,
                    IsGroup = item.IsGroup,
                    HasParent = item.ParentItemId.HasValue,
                    HierarchyLevel = hierarchyLevel
                });
            }
        }

        // Recursively add child sections' items
        var childSections = allSections
            .Where(s => s.ParentSectionId == section.Id)
            .OrderBy(s => s.SortOrder);

        foreach (var child in childSections)
        {
            var childDto = MapSection(child, allSections, itemsBySection, allItems);
            // Flatten child items into parent for simplicity in export
            sectionDto.Items.AddRange(childDto.Items);
        }

        return sectionDto;
    }

    /// <summary>
    /// Determines the hierarchy level string for an item.
    /// - Group items (IsGroup=true) → "Item" (item group header)
    /// - Items with a parent → "Sub-Item"
    /// - Standalone items → "Item"
    /// </summary>
    private static string DetermineHierarchyLevel(Domain.Entities.BoqItem item)
    {
        if (item.IsGroup)
            return "Item";

        if (item.ParentItemId.HasValue)
            return "Sub-Item";

        return "Item";
    }
}
