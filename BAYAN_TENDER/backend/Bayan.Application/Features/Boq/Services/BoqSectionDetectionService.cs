using System.Text.RegularExpressions;
using Bayan.Application.Features.Boq.DTOs;

namespace Bayan.Application.Features.Boq.Services;

/// <summary>
/// Row context for section detection with full row data.
/// </summary>
public class BoqRowContext
{
    public string ItemNumber { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? Quantity { get; set; }
    public string? Uom { get; set; }
}

/// <summary>
/// Service for detecting sections from BOQ item numbers.
/// </summary>
public interface IBoqSectionDetectionService
{
    /// <summary>
    /// Parses an item number and returns section information.
    /// </summary>
    ItemNumberParseResult ParseItemNumber(string itemNumber);

    /// <summary>
    /// Detects all sections from a list of item numbers.
    /// </summary>
    List<DetectedSectionDto> DetectSections(IEnumerable<string> itemNumbers);

    /// <summary>
    /// Detects sections using full row context (item number, description, quantity, uom).
    /// Section header rows are identified by having no quantity/uom, and their descriptions become section titles.
    /// </summary>
    List<DetectedSectionDto> DetectSectionsFromRows(IEnumerable<BoqRowContext> rows);

    /// <summary>
    /// Checks if a row is a section header based on its data.
    /// </summary>
    bool IsSectionHeaderRow(string? itemNumber, string? quantity, string? uom);

    /// <summary>
    /// Finds the best matching section for an item number given known sections.
    /// Handles dash-to-dot conversion (E-001 → section E.001).
    /// </summary>
    string FindBestSection(string itemNumber, ISet<string> knownSectionNumbers);

    /// <summary>
    /// Gets the parent section number for a given section number.
    /// </summary>
    string? GetParentSectionNumber(string sectionNumber);
}

/// <summary>
/// Result of parsing an item number.
/// </summary>
public class ItemNumberParseResult
{
    /// <summary>
    /// Whether the item number was successfully parsed.
    /// </summary>
    public bool Success { get; set; }

    /// <summary>
    /// The original item number.
    /// </summary>
    public string OriginalValue { get; set; } = string.Empty;

    /// <summary>
    /// Normalized item number.
    /// </summary>
    public string NormalizedValue { get; set; } = string.Empty;

    /// <summary>
    /// The section number this item belongs to.
    /// </summary>
    public string SectionNumber { get; set; } = string.Empty;

    /// <summary>
    /// Whether this is a section header row (not an item).
    /// </summary>
    public bool IsSectionHeader { get; set; }

    /// <summary>
    /// The hierarchy level (number of parts).
    /// </summary>
    public int Level { get; set; }

    /// <summary>
    /// Individual parts of the item number.
    /// </summary>
    public List<string> Parts { get; set; } = new();

    /// <summary>
    /// Error message if parsing failed.
    /// </summary>
    public string? ErrorMessage { get; set; }
}

/// <summary>
/// Implementation of section detection from item numbers.
/// </summary>
public class BoqSectionDetectionService : IBoqSectionDetectionService
{
    // Pattern to match item numbers like "1", "1.1", "1.1.1", "1-1", "E-001", "F-004", "A.1", etc.
    private static readonly Regex ItemNumberPattern = new(
        @"^([A-Za-z0-9]+)([.\-/]([A-Za-z0-9]+))*$",
        RegexOptions.Compiled);

    // Pattern to split item numbers
    private static readonly Regex SplitPattern = new(
        @"[.\-/]",
        RegexOptions.Compiled);

    public ItemNumberParseResult ParseItemNumber(string itemNumber)
    {
        var result = new ItemNumberParseResult
        {
            OriginalValue = itemNumber ?? string.Empty
        };

        if (string.IsNullOrWhiteSpace(itemNumber))
        {
            result.ErrorMessage = "Item number is empty";
            return result;
        }

        // Normalize whitespace and common variations
        var normalized = itemNumber.Trim()
            .Replace(" ", "")
            .Replace(",", ".")
            .Replace("_", ".");

        result.NormalizedValue = normalized;

        // Check if it matches the expected pattern
        if (!ItemNumberPattern.IsMatch(normalized))
        {
            result.ErrorMessage = "Item number does not match expected format";
            return result;
        }

        // Split into parts
        var parts = SplitPattern.Split(normalized).ToList();
        result.Parts = parts;
        result.Level = parts.Count;
        result.Success = true;

        // Determine section number
        // For "1.1.3", section is "1.1"
        // For "1.1", section is "1"
        // For "1", it's a top-level section itself
        if (parts.Count == 1)
        {
            // This could be a section header (just "1") or a single-level item
            result.SectionNumber = parts[0];
            result.IsSectionHeader = true;
        }
        else
        {
            // Take all parts except the last one as the section
            result.SectionNumber = string.Join(".", parts.Take(parts.Count - 1));
            result.IsSectionHeader = false;
        }

        return result;
    }

    public List<DetectedSectionDto> DetectSections(IEnumerable<string> itemNumbers)
    {
        var sectionDict = new Dictionary<string, DetectedSectionDto>();
        var itemCounts = new Dictionary<string, int>();

        foreach (var itemNumber in itemNumbers.Where(n => !string.IsNullOrWhiteSpace(n)))
        {
            var parseResult = ParseItemNumber(itemNumber);
            if (!parseResult.Success)
            {
                continue;
            }

            // Build section hierarchy
            var parts = parseResult.Parts;
            for (var i = 1; i <= parts.Count; i++)
            {
                var sectionNumber = string.Join(".", parts.Take(i));
                var parentSectionNumber = i > 1 ? string.Join(".", parts.Take(i - 1)) : null;

                if (!sectionDict.ContainsKey(sectionNumber))
                {
                    sectionDict[sectionNumber] = new DetectedSectionDto
                    {
                        SectionNumber = sectionNumber,
                        Title = $"Section {sectionNumber}",
                        ParentSectionNumber = parentSectionNumber,
                        Level = i - 1,
                        ItemCount = 0
                    };
                }
            }

            // Count items per section
            if (!parseResult.IsSectionHeader)
            {
                var section = parseResult.SectionNumber;
                if (!itemCounts.ContainsKey(section))
                {
                    itemCounts[section] = 0;
                }
                itemCounts[section]++;
            }
        }

        // Update item counts
        foreach (var (section, count) in itemCounts)
        {
            if (sectionDict.TryGetValue(section, out var sectionDto))
            {
                sectionDict[section] = sectionDto with { ItemCount = count };
            }
        }

        // Sort by section number (natural sort)
        return sectionDict.Values
            .OrderBy(s => s.Level)
            .ThenBy(s => s.SectionNumber, new NaturalSortComparer())
            .ToList();
    }

    public bool IsSectionHeaderRow(string? itemNumber, string? quantity, string? uom)
    {
        if (string.IsNullOrWhiteSpace(itemNumber))
            return false;

        // A row is a section header if it has an item number but no quantity and no UOM
        var hasQuantity = !string.IsNullOrWhiteSpace(quantity) &&
                          decimal.TryParse(quantity, out var qty) && qty != 0;
        var hasUom = !string.IsNullOrWhiteSpace(uom);

        return !hasQuantity && !hasUom;
    }

    public List<DetectedSectionDto> DetectSectionsFromRows(IEnumerable<BoqRowContext> rows)
    {
        var sectionDict = new Dictionary<string, DetectedSectionDto>(StringComparer.OrdinalIgnoreCase);

        // Pass 1: Identify section header rows and build section hierarchy
        foreach (var row in rows.Where(r => !string.IsNullOrWhiteSpace(r.ItemNumber)))
        {
            var parseResult = ParseItemNumber(row.ItemNumber);
            if (!parseResult.Success)
                continue;

            var isSectionHeader = IsSectionHeaderRow(row.ItemNumber, row.Quantity, row.Uom);

            if (isSectionHeader)
            {
                // This row is a section header — use its description as the title
                var sectionNumber = string.Join(".", parseResult.Parts);
                var parentNumber = parseResult.Parts.Count > 1
                    ? string.Join(".", parseResult.Parts.Take(parseResult.Parts.Count - 1))
                    : null;

                sectionDict[sectionNumber] = new DetectedSectionDto
                {
                    SectionNumber = sectionNumber,
                    Title = !string.IsNullOrWhiteSpace(row.Description)
                        ? row.Description
                        : $"Section {sectionNumber}",
                    ParentSectionNumber = parentNumber,
                    Level = parseResult.Parts.Count - 1,
                    ItemCount = 0
                };

                // Also ensure parent sections exist in the hierarchy
                for (var i = 1; i < parseResult.Parts.Count; i++)
                {
                    var ancestorNumber = string.Join(".", parseResult.Parts.Take(i));
                    var ancestorParent = i > 1 ? string.Join(".", parseResult.Parts.Take(i - 1)) : null;

                    if (!sectionDict.ContainsKey(ancestorNumber))
                    {
                        sectionDict[ancestorNumber] = new DetectedSectionDto
                        {
                            SectionNumber = ancestorNumber,
                            Title = $"Section {ancestorNumber}",
                            ParentSectionNumber = ancestorParent,
                            Level = i - 1,
                            ItemCount = 0
                        };
                    }
                }
            }
        }

        // Pass 2: Count items per section and create missing parent sections
        var knownSections = new HashSet<string>(sectionDict.Keys, StringComparer.OrdinalIgnoreCase);
        var itemCounts = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);

        foreach (var row in rows.Where(r => !string.IsNullOrWhiteSpace(r.ItemNumber)))
        {
            var isSectionHeader = IsSectionHeaderRow(row.ItemNumber, row.Quantity, row.Uom);
            if (isSectionHeader)
                continue;

            var sectionKey = FindBestSection(row.ItemNumber, knownSections);
            if (!itemCounts.ContainsKey(sectionKey))
                itemCounts[sectionKey] = 0;
            itemCounts[sectionKey]++;

            // Ensure this section exists
            if (!sectionDict.ContainsKey(sectionKey))
            {
                var parts = SplitPattern.Split(sectionKey);
                var parentNumber = parts.Length > 1
                    ? string.Join(".", parts.Take(parts.Length - 1))
                    : null;

                sectionDict[sectionKey] = new DetectedSectionDto
                {
                    SectionNumber = sectionKey,
                    Title = $"Section {sectionKey}",
                    ParentSectionNumber = parentNumber,
                    Level = parts.Length - 1,
                    ItemCount = 0
                };
                knownSections.Add(sectionKey);
            }
        }

        // Update item counts
        foreach (var (section, count) in itemCounts)
        {
            if (sectionDict.TryGetValue(section, out var sectionDto))
            {
                sectionDict[section] = sectionDto with { ItemCount = count };
            }
        }

        return sectionDict.Values
            .OrderBy(s => s.Level)
            .ThenBy(s => s.SectionNumber, new NaturalSortComparer())
            .ToList();
    }

    public string FindBestSection(string itemNumber, ISet<string> knownSectionNumbers)
    {
        var parseResult = ParseItemNumber(itemNumber);
        if (!parseResult.Success || parseResult.Parts.Count <= 1)
            return parseResult.Parts.Count == 1 ? parseResult.Parts[0] : "1";

        // Try converting item number to dot-notation as a section key
        // E.g., "E-001" → parts ["E","001"] → try "E.001" as section
        var dotNotation = string.Join(".", parseResult.Parts);
        if (knownSectionNumbers.Contains(dotNotation))
            return dotNotation;

        // Try parent: all parts except last joined with dots
        var parentSection = string.Join(".", parseResult.Parts.Take(parseResult.Parts.Count - 1));
        if (knownSectionNumbers.Contains(parentSection))
            return parentSection;

        // Try matching by converting the last numeric part
        // E.g., item "E-001" → try finding section "E.001"
        // Already covered by dotNotation above

        // Fall back to top-level
        if (knownSectionNumbers.Contains(parseResult.Parts[0]))
            return parseResult.Parts[0];

        return parentSection; // best guess
    }

    public string? GetParentSectionNumber(string sectionNumber)
    {
        if (string.IsNullOrWhiteSpace(sectionNumber))
        {
            return null;
        }

        var parts = SplitPattern.Split(sectionNumber);
        if (parts.Length <= 1)
        {
            return null;
        }

        return string.Join(".", parts.Take(parts.Length - 1));
    }

    /// <summary>
    /// Natural sort comparer for section numbers.
    /// </summary>
    private class NaturalSortComparer : IComparer<string>
    {
        public int Compare(string? x, string? y)
        {
            if (x == null && y == null) return 0;
            if (x == null) return -1;
            if (y == null) return 1;

            var xParts = SplitPattern.Split(x);
            var yParts = SplitPattern.Split(y);

            for (var i = 0; i < Math.Max(xParts.Length, yParts.Length); i++)
            {
                if (i >= xParts.Length) return -1;
                if (i >= yParts.Length) return 1;

                if (int.TryParse(xParts[i], out var xNum) && int.TryParse(yParts[i], out var yNum))
                {
                    var numCompare = xNum.CompareTo(yNum);
                    if (numCompare != 0) return numCompare;
                }
                else
                {
                    var strCompare = string.Compare(xParts[i], yParts[i], StringComparison.OrdinalIgnoreCase);
                    if (strCompare != 0) return strCompare;
                }
            }

            return 0;
        }
    }
}
