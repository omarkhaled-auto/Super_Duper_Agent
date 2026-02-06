using System.Text.RegularExpressions;
using Bayan.Application.Features.Boq.DTOs;

namespace Bayan.Application.Features.Boq.Services;

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
    // Pattern to match item numbers like "1", "1.1", "1.1.1", "1-1", "1-1-1", "A.1", etc.
    private static readonly Regex ItemNumberPattern = new(
        @"^([A-Za-z]?\d+)([.\-/]([A-Za-z]?\d+))*$",
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
