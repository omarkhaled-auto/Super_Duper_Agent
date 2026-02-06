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

        // Fetch tender with BOQ data
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

        // Build section hierarchy with items
        var sections = BuildSectionHierarchy(tender.BoqSections.ToList(), tender.BoqItems.ToList());

        // Build generation request
        var generationRequest = new BoqTemplateGenerationRequest
        {
            TenderId = tender.Id,
            TenderTitle = tender.Title,
            TenderReference = tender.Reference,
            SubmissionDeadline = tender.SubmissionDeadline,
            Currency = tender.BaseCurrency,
            Sections = sections,
            AvailableUoms = uoms,
            IncludeColumns = request.IncludeColumns,
            LockColumns = request.LockColumns,
            IncludeInstructions = request.IncludeInstructions,
            Language = request.Language
        };

        // Generate Excel file
        var result = await _templateExportService.GenerateBoqTemplateAsync(generationRequest, cancellationToken);

        _logger.LogInformation(
            "BOQ template exported successfully for tender {TenderId}. File size: {FileSize} bytes",
            request.TenderId,
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
            .Select(s => MapSection(s, sections, itemsBySection))
            .ToList();
    }

    private static BoqSectionExportDto MapSection(
        Domain.Entities.BoqSection section,
        List<Domain.Entities.BoqSection> allSections,
        Dictionary<Guid, List<Domain.Entities.BoqItem>> itemsBySection)
    {
        var sectionDto = new BoqSectionExportDto
        {
            SectionNumber = section.SectionNumber,
            Title = section.Title,
            Items = new List<BoqItemExportDto>()
        };

        // Add items for this section
        if (itemsBySection.TryGetValue(section.Id, out var sectionItems))
        {
            sectionDto.Items.AddRange(sectionItems.Select(i => new BoqItemExportDto
            {
                ItemNumber = i.ItemNumber,
                Description = i.Description,
                Quantity = i.Quantity,
                Uom = i.Uom,
                Notes = i.Notes
            }));
        }

        // Recursively add child sections' items
        var childSections = allSections
            .Where(s => s.ParentSectionId == section.Id)
            .OrderBy(s => s.SortOrder);

        foreach (var child in childSections)
        {
            var childDto = MapSection(child, allSections, itemsBySection);
            // Flatten child items into parent for simplicity in export
            sectionDto.Items.AddRange(childDto.Items);
        }

        return sectionDto;
    }
}
