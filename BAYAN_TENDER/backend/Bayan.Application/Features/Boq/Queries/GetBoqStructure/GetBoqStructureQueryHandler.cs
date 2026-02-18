using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.DTOs;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Boq.Queries.GetBoqStructure;

/// <summary>
/// Handler for the GetBoqStructureQuery.
/// Builds a hierarchical tree structure of sections with nested items.
/// </summary>
public class GetBoqStructureQueryHandler : IRequestHandler<GetBoqStructureQuery, List<BoqTreeNodeDto>>
{
    private readonly IApplicationDbContext _context;
    private readonly IMapper _mapper;

    public GetBoqStructureQueryHandler(IApplicationDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    public async Task<List<BoqTreeNodeDto>> Handle(
        GetBoqStructureQuery request,
        CancellationToken cancellationToken)
    {
        // Fetch all sections for this tender with their items (including child items)
        var sections = await _context.BoqSections
            .Where(s => s.TenderId == request.TenderId)
            .Include(s => s.Items.OrderBy(i => i.SortOrder))
                .ThenInclude(i => i.ChildItems.OrderBy(c => c.SortOrder))
            .AsNoTracking()
            .OrderBy(s => s.SortOrder)
            .ToListAsync(cancellationToken);

        // Build hierarchical tree from flat list
        return BuildTree(sections);
    }

    /// <summary>
    /// Builds a hierarchical tree structure from a flat list of sections.
    /// </summary>
    private List<BoqTreeNodeDto> BuildTree(List<BoqSection> sections)
    {
        // Create a dictionary for fast lookup
        var sectionDict = sections.ToDictionary(s => s.Id, s => new BoqTreeNodeDto
        {
            Id = s.Id,
            SectionNumber = s.SectionNumber,
            Title = s.Title,
            SortOrder = s.SortOrder,
            ParentSectionId = s.ParentSectionId,
            Items = MapItemsHierarchically(s.Items),
            Children = new List<BoqTreeNodeDto>()
        });

        var rootNodes = new List<BoqTreeNodeDto>();

        foreach (var section in sections)
        {
            var node = sectionDict[section.Id];

            if (section.ParentSectionId.HasValue && sectionDict.TryGetValue(section.ParentSectionId.Value, out var parent))
            {
                // Add as child to parent
                parent.Children.Add(node);
            }
            else
            {
                // Root-level section
                rootNodes.Add(node);
            }
        }

        // Sort children at each level
        SortChildrenRecursive(rootNodes);

        return rootNodes;
    }

    /// <summary>
    /// Recursively sorts children by SortOrder.
    /// </summary>
    private void SortChildrenRecursive(List<BoqTreeNodeDto> nodes)
    {
        nodes.Sort((a, b) => a.SortOrder.CompareTo(b.SortOrder));

        foreach (var node in nodes)
        {
            if (node.Children.Count > 0)
            {
                SortChildrenRecursive(node.Children);
            }
        }
    }

    /// <summary>
    /// Maps items hierarchically — only top-level items (no parent) at root level,
    /// with child items nested inside their group parents.
    /// </summary>
    private List<BoqItemDto> MapItemsHierarchically(ICollection<BoqItem> items)
    {
        // Only return top-level items (ParentItemId == null)
        // Child items are included via the ChildItems navigation property
        var topLevelItems = items
            .Where(i => i.ParentItemId == null)
            .OrderBy(i => i.SortOrder)
            .ToList();

        return topLevelItems.Select(MapItemRecursive).ToList();
    }

    /// <summary>
    /// Recursively maps a BoqItem entity to DTO including its child items.
    /// </summary>
    private BoqItemDto MapItemRecursive(BoqItem item)
    {
        var dto = _mapper.Map<BoqItemDto>(item);

        if (item.IsGroup && item.ChildItems?.Any() == true)
        {
            dto.ChildItems = item.ChildItems
                .OrderBy(c => c.SortOrder)
                .Select(MapItemRecursive)
                .ToList();
        }
        else
        {
            dto.ChildItems = new List<BoqItemDto>();
        }

        return dto;
    }
}
