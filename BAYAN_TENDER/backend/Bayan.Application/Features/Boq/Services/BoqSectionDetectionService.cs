using System.Text.RegularExpressions;
using Bayan.Application.Features.Boq.DTOs;

namespace Bayan.Application.Features.Boq.Services;

/// <summary>
/// Classification of a BOQ row for hierarchy detection.
/// </summary>
public enum ItemHierarchyRole
{
    /// <summary>Row is a bill header (e.g., "BILL NO. 1").</summary>
    BillHeader,

    /// <summary>Row is a group item (has item number, no quantity/UOM — contains sub-items).</summary>
    Group,

    /// <summary>Row is a sub-item under a group (letter label, alphanumeric code, or child number).</summary>
    SubItem,

    /// <summary>Row is a standalone item (has item number, quantity, and UOM).</summary>
    Standalone,

    /// <summary>Row could not be classified (empty or unparseable).</summary>
    Unknown
}

/// <summary>
/// Result of hierarchy detection for a single BOQ row.
/// </summary>
public class ItemHierarchyInfo
{
    /// <summary>Row index in the sheet.</summary>
    public int RowIndex { get; set; }

    /// <summary>The item number value from this row.</summary>
    public string ItemNumber { get; set; } = string.Empty;

    /// <summary>Detected hierarchy role.</summary>
    public ItemHierarchyRole Role { get; set; } = ItemHierarchyRole.Unknown;

    /// <summary>
    /// For sub-items: the item number of the parent group row.
    /// Null for groups, standalone items, and bill headers.
    /// </summary>
    public string? ParentItemNumber { get; set; }

    /// <summary>Description text from the row.</summary>
    public string? Description { get; set; }
}

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

    /// <summary>
    /// Detects item hierarchy from a list of BOQ rows, classifying each as
    /// BillHeader, Group, SubItem, or Standalone. Sub-items are linked to their parent group.
    /// </summary>
    List<ItemHierarchyInfo> DetectItemHierarchy(IReadOnlyList<BoqRowContext> rows);
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

    // ── Bill header pattern: "BILL NO. X" or "BILL NO.X" ──
    private static readonly Regex BillHeaderPattern = new(
        @"^\s*BILL\s+NO\.?\s*\d+",
        RegexOptions.Compiled | RegexOptions.IgnoreCase);

    // ── Bill total row: "Total Bill No. X Carried To Collection" ──
    private static readonly Regex BillTotalPattern = new(
        @"^\s*Total\s+Bill\s+No\.?\s*\d+",
        RegexOptions.Compiled | RegexOptions.IgnoreCase);

    // ── Sub-item patterns ──
    // Single letter: a, b, c, A, B, C
    private static readonly Regex SingleLetterPattern = new(
        @"^[A-Za-z]$",
        RegexOptions.Compiled);

    // Alphanumeric code: F1, S2, W3, FC1, EFS-14
    private static readonly Regex AlphanumericCodePattern = new(
        @"^[A-Za-z]{1,4}[-]?\d{1,3}$",
        RegexOptions.Compiled);

    public List<ItemHierarchyInfo> DetectItemHierarchy(IReadOnlyList<BoqRowContext> rows)
    {
        var results = new List<ItemHierarchyInfo>(rows.Count);

        // First pass: classify each row
        string? currentGroupItemNumber = null;
        int currentGroupIndex = -1;

        for (var i = 0; i < rows.Count; i++)
        {
            var row = rows[i];
            var info = new ItemHierarchyInfo
            {
                RowIndex = i,
                ItemNumber = row.ItemNumber?.Trim() ?? string.Empty,
                Description = row.Description
            };

            var itemNum = info.ItemNumber;
            var desc = (row.Description ?? string.Empty).Trim();

            // 1. Check for bill header rows
            if (IsBillHeaderRow(itemNum, desc))
            {
                info.Role = ItemHierarchyRole.BillHeader;
                currentGroupItemNumber = null;
                currentGroupIndex = -1;
                results.Add(info);
                continue;
            }

            // 2. Check for bill total rows
            if (IsBillTotalRow(desc))
            {
                info.Role = ItemHierarchyRole.BillHeader;
                currentGroupItemNumber = null;
                currentGroupIndex = -1;
                results.Add(info);
                continue;
            }

            // Skip rows with no item number — they can't be classified
            if (string.IsNullOrWhiteSpace(itemNum))
            {
                info.Role = ItemHierarchyRole.Unknown;
                results.Add(info);
                continue;
            }

            var hasQuantity = !string.IsNullOrWhiteSpace(row.Quantity) &&
                              decimal.TryParse(row.Quantity, out var qty) && qty != 0;
            var hasUom = !string.IsNullOrWhiteSpace(row.Uom);

            // 3. If currently inside a group context, check if this row is a sub-item
            if (currentGroupItemNumber != null)
            {
                if (IsSubItemOf(itemNum, currentGroupItemNumber))
                {
                    info.Role = ItemHierarchyRole.SubItem;
                    info.ParentItemNumber = currentGroupItemNumber;
                    results.Add(info);
                    continue;
                }
                else
                {
                    // Exited the group context
                    currentGroupItemNumber = null;
                    currentGroupIndex = -1;
                }
            }

            // 4. Row with item number but no quantity and no UOM → potential group
            if (!hasQuantity && !hasUom)
            {
                // Parse to see if it looks like a structured item number (X.XX or just a number)
                var parseResult = ParseItemNumber(itemNum);
                if (parseResult.Success)
                {
                    // Check if the next non-empty row could be a sub-item
                    if (HasPotentialSubItems(rows, i, itemNum))
                    {
                        info.Role = ItemHierarchyRole.Group;
                        currentGroupItemNumber = itemNum;
                        currentGroupIndex = i;
                        results.Add(info);
                        continue;
                    }
                }

                // No sub-items detected — treat as section header or standalone
                // (Section headers are already filtered in the import handler)
                info.Role = ItemHierarchyRole.Standalone;
                results.Add(info);
                continue;
            }

            // 5. Row with item number + quantity + UOM → standalone item
            info.Role = ItemHierarchyRole.Standalone;
            results.Add(info);
        }

        // Second pass: retroactively fix groups that ended up with no sub-items
        // (edge case where HasPotentialSubItems was wrong due to lookahead limits)
        var groupIndices = new HashSet<int>();
        var subItemParents = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var r in results)
        {
            if (r.Role == ItemHierarchyRole.Group)
                groupIndices.Add(r.RowIndex);
            if (r.Role == ItemHierarchyRole.SubItem && r.ParentItemNumber != null)
                subItemParents.Add(r.ParentItemNumber);
        }

        foreach (var r in results)
        {
            if (r.Role == ItemHierarchyRole.Group && !subItemParents.Contains(r.ItemNumber))
            {
                // This group has no actual sub-items — downgrade to Standalone
                r.Role = ItemHierarchyRole.Standalone;
            }
        }

        return results;
    }

    /// <summary>
    /// Checks if a row is a bill header (e.g., "BILL NO. 1 : GENERAL REQUIREMENTS").
    /// The bill text can appear in the item number column or description column.
    /// </summary>
    private static bool IsBillHeaderRow(string itemNumber, string description)
    {
        return BillHeaderPattern.IsMatch(itemNumber) ||
               BillHeaderPattern.IsMatch(description);
    }

    /// <summary>
    /// Checks if a row is a bill total row (e.g., "Total Bill No. 1 Carried To Collection").
    /// </summary>
    private static bool IsBillTotalRow(string description)
    {
        return BillTotalPattern.IsMatch(description);
    }

    /// <summary>
    /// Determines if itemNumber is a sub-item of parentItemNumber.
    /// Handles: letter labels (a,b,c), alphanumeric codes (F1, S2, EFS-14),
    /// and numbered sub-items (9.11, 9.12 under 9.1).
    /// </summary>
    private bool IsSubItemOf(string itemNumber, string parentItemNumber)
    {
        // Pattern 1: Single letter (a, b, c, A, B, C)
        if (SingleLetterPattern.IsMatch(itemNumber))
            return true;

        // Pattern 2: Alphanumeric code (F1, S2, W3, FC1, EFS-14)
        if (AlphanumericCodePattern.IsMatch(itemNumber))
            return true;

        // Pattern 3: Numbered sub-item — child's item number starts with parent's + separator
        // e.g., "9.11" is a sub-item of "9.1", "3.2.1" is a sub-item of "3.2"
        var normalizedParent = parentItemNumber.Trim().Replace("-", ".").Replace("/", ".");
        var normalizedChild = itemNumber.Trim().Replace("-", ".").Replace("/", ".");

        if (normalizedChild.StartsWith(normalizedParent + ".", StringComparison.OrdinalIgnoreCase) &&
            normalizedChild.Length > normalizedParent.Length + 1)
        {
            // Ensure the remaining part is a simple number (no further nesting)
            var remainder = normalizedChild[(normalizedParent.Length + 1)..];
            if (int.TryParse(remainder, out _))
                return true;
        }

        return false;
    }

    /// <summary>
    /// Looks ahead from the current group row to see if subsequent rows look like sub-items.
    /// Scans up to 15 rows ahead to find at least one sub-item candidate.
    /// </summary>
    private bool HasPotentialSubItems(IReadOnlyList<BoqRowContext> rows, int groupIndex, string groupItemNumber)
    {
        const int lookahead = 15;
        var limit = Math.Min(groupIndex + lookahead + 1, rows.Count);

        for (var j = groupIndex + 1; j < limit; j++)
        {
            var nextRow = rows[j];
            var nextItemNum = nextRow.ItemNumber?.Trim() ?? string.Empty;

            if (string.IsNullOrWhiteSpace(nextItemNum))
                continue;

            // If we hit another structured item number that ISN'T a sub-item, stop looking
            var nextParse = ParseItemNumber(nextItemNum);
            if (nextParse.Success && !IsSubItemOf(nextItemNum, groupItemNumber))
            {
                // Check if this could be a section header — if so, keep scanning
                if (IsSectionHeaderRow(nextItemNum, nextRow.Quantity, nextRow.Uom))
                    continue;
                return false;
            }

            if (IsSubItemOf(nextItemNum, groupItemNumber))
                return true;
        }

        return false;
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
