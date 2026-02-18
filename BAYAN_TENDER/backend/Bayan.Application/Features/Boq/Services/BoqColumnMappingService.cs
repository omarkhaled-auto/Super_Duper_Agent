using System.Text.RegularExpressions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.DTOs;

namespace Bayan.Application.Features.Boq.Services;

/// <summary>
/// Service for auto-detecting BOQ column mappings from Excel headers.
/// </summary>
public interface IBoqColumnMappingService
{
    /// <summary>
    /// Suggests column mappings based on Excel headers.
    /// </summary>
    List<ColumnMappingDto> SuggestMappings(List<string> headers);
}

/// <summary>
/// Implementation of BOQ column mapping detection.
/// </summary>
public class BoqColumnMappingService : IBoqColumnMappingService
{
    // Mapping patterns for each BOQ field
    private static readonly Dictionary<BoqField, string[]> FieldPatterns = new()
    {
        [BoqField.ItemNumber] = new[]
        {
            @"^item\s*no\.?$", @"^item\s*#$", @"^item\s*number$", @"^no\.?$",
            @"^ref\.?$", @"^reference$", @"^code$", @"^item$", @"^s\.?no\.?$",
            @"^serial\s*no\.?$", @"^sr\.?\s*no\.?$"
        },
        [BoqField.Description] = new[]
        {
            @"^description$", @"^desc\.?$", @"^item\s*description$",
            @"^particulars$", @"^detail$", @"^details$", @"^specification$",
            @"^scope$", @"^work\s*description$", @"^activity$"
        },
        [BoqField.Quantity] = new[]
        {
            @"^qty\.?$", @"^quantity$", @"^quantities$", @"^estimated\s*qty\.?$",
            @"^est\.?\s*qty\.?$", @"^amount$", @"^volume$"
        },
        [BoqField.Uom] = new[]
        {
            @"^uom$", @"^unit$", @"^units$", @"^unit\s*of\s*measure(ment)?$",
            @"^measure$", @"^u\.?o\.?m\.?$"
        },
        [BoqField.SectionTitle] = new[]
        {
            @"^section$", @"^section\s*title$", @"^category$", @"^group$",
            @"^division$", @"^trade$"
        },
        [BoqField.Notes] = new[]
        {
            @"^notes?$", @"^remarks?$", @"^comments?$", @"^observations?$"
        },
        [BoqField.UnitRate] = new[]
        {
            @"^rate$", @"^unit\s*rate$", @"^unit\s*price$", @"^price$",
            @"^cost$", @"^unit\s*cost$"
        },
        [BoqField.Amount] = new[]
        {
            @"^total$", @"^amount$", @"^total\s*amount$", @"^total\s*cost$",
            @"^total\s*price$", @"^value$", @"^ext\.?\s*amount$", @"^extension$"
        },
        [BoqField.Specification] = new[]
        {
            @"^spec\.?$", @"^specification$", @"^spec\s*ref\.?$",
            @"^technical\s*spec\.?$", @"^standard$"
        },
        [BoqField.BillNumber] = new[]
        {
            @"^bill\s*no\.?$", @"^bill\s*number$", @"^bill\s*#$", @"^bill$",
            @"^bill\s*ref\.?$"
        },
        [BoqField.SubItemLabel] = new[]
        {
            @"^sub[-\s]?item$", @"^sub[-\s]?item\s*label$", @"^sub[-\s]?item\s*no\.?$",
            @"^sub[-\s]?label$", @"^sub[-\s]?item\s*ref\.?$"
        }
    };

    public List<ColumnMappingDto> SuggestMappings(List<string> headers)
    {
        var mappings = new List<ColumnMappingDto>();
        var usedFields = new HashSet<BoqField>();

        for (var i = 0; i < headers.Count; i++)
        {
            var header = headers[i];
            if (string.IsNullOrWhiteSpace(header))
            {
                continue;
            }

            var normalizedHeader = header.ToLowerInvariant().Trim();
            var bestMatch = BoqField.None;
            var bestConfidence = 0;

            foreach (var (field, patterns) in FieldPatterns)
            {
                // Skip already assigned fields
                if (usedFields.Contains(field))
                {
                    continue;
                }

                foreach (var pattern in patterns)
                {
                    if (Regex.IsMatch(normalizedHeader, pattern, RegexOptions.IgnoreCase))
                    {
                        // Calculate confidence based on match specificity
                        var confidence = CalculateMatchConfidence(normalizedHeader, pattern);
                        if (confidence > bestConfidence)
                        {
                            bestMatch = field;
                            bestConfidence = confidence;
                        }
                    }
                }
            }

            if (bestMatch != BoqField.None && bestConfidence >= 50)
            {
                usedFields.Add(bestMatch);
                mappings.Add(new ColumnMappingDto
                {
                    ExcelColumn = header,
                    BoqField = bestMatch,
                    Confidence = bestConfidence,
                    IsAutoDetected = true
                });
            }
        }

        return mappings;
    }

    private static int CalculateMatchConfidence(string header, string pattern)
    {
        // Exact match gets highest confidence
        if (Regex.IsMatch(header, $"^{pattern.TrimStart('^').TrimEnd('$')}$", RegexOptions.IgnoreCase))
        {
            return 95;
        }

        // Pattern match (not exact) gets medium confidence
        if (pattern.StartsWith("^") && pattern.EndsWith("$"))
        {
            return 85;
        }

        // Contains match gets lower confidence
        return 70;
    }
}
