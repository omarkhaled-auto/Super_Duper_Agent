using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Enums;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Memory;
using Microsoft.Extensions.Logging;

namespace Bayan.Infrastructure.Services;

/// <summary>
/// Service for converting between different units of measurement.
/// Uses the UomMaster table for conversions and includes common hardcoded conversions as fallback.
/// </summary>
public class UomConversionService : IUomConversionService
{
    private readonly IApplicationDbContext _context;
    private readonly IMemoryCache _cache;
    private readonly ILogger<UomConversionService> _logger;
    private static readonly TimeSpan CacheDuration = TimeSpan.FromHours(1);
    private const string UomCacheKey = "UomMasterData";

    /// <summary>
    /// Common conversion factors as fallback when not in database.
    /// Key is (fromUom, toUom) tuple, value is the conversion factor.
    /// </summary>
    private static readonly Dictionary<(string, string), decimal> CommonConversions = new()
    {
        // Area conversions (base: m2)
        { ("sqft", "m2"), 0.092903m },
        { ("m2", "sqft"), 10.7639m },
        { ("sft", "m2"), 0.092903m },
        { ("m2", "sft"), 10.7639m },
        { ("sqm", "m2"), 1m },
        { ("m2", "sqm"), 1m },

        // Length conversions (base: m)
        { ("ft", "m"), 0.3048m },
        { ("m", "ft"), 3.28084m },
        { ("lm", "m"), 1m },
        { ("m", "lm"), 1m },
        { ("rm", "m"), 1m },
        { ("m", "rm"), 1m },
        { ("cm", "m"), 0.01m },
        { ("m", "cm"), 100m },
        { ("mm", "m"), 0.001m },
        { ("m", "mm"), 1000m },
        { ("in", "m"), 0.0254m },
        { ("m", "in"), 39.3701m },

        // Weight conversions (base: kg)
        { ("kg", "ton"), 0.001m },
        { ("ton", "kg"), 1000m },
        { ("mt", "kg"), 1000m },
        { ("kg", "mt"), 0.001m },
        { ("lb", "kg"), 0.453592m },
        { ("kg", "lb"), 2.20462m },
        { ("g", "kg"), 0.001m },
        { ("kg", "g"), 1000m },

        // Volume conversions (base: m3)
        { ("cft", "m3"), 0.0283168m },
        { ("m3", "cft"), 35.3147m },
        { ("l", "m3"), 0.001m },
        { ("m3", "l"), 1000m },
        { ("gal", "m3"), 0.00378541m },
        { ("m3", "gal"), 264.172m },
        { ("cum", "m3"), 1m },
        { ("m3", "cum"), 1m },

        // Count (always 1:1 within category)
        { ("nos", "no"), 1m },
        { ("no", "nos"), 1m },
        { ("ea", "nos"), 1m },
        { ("nos", "ea"), 1m },
        { ("pcs", "nos"), 1m },
        { ("nos", "pcs"), 1m },
        { ("set", "nos"), 1m },
        { ("nos", "set"), 1m },
    };

    /// <summary>
    /// UOM category mapping for common codes.
    /// </summary>
    private static readonly Dictionary<string, UomCategory> UomCategoryMap = new(StringComparer.OrdinalIgnoreCase)
    {
        // Area
        { "m2", UomCategory.Area },
        { "sqm", UomCategory.Area },
        { "sqft", UomCategory.Area },
        { "sft", UomCategory.Area },

        // Length
        { "m", UomCategory.Length },
        { "lm", UomCategory.Length },
        { "rm", UomCategory.Length },
        { "ft", UomCategory.Length },
        { "cm", UomCategory.Length },
        { "mm", UomCategory.Length },
        { "in", UomCategory.Length },

        // Weight
        { "kg", UomCategory.Weight },
        { "ton", UomCategory.Weight },
        { "mt", UomCategory.Weight },
        { "lb", UomCategory.Weight },
        { "g", UomCategory.Weight },

        // Volume
        { "m3", UomCategory.Volume },
        { "cum", UomCategory.Volume },
        { "cft", UomCategory.Volume },
        { "l", UomCategory.Volume },
        { "gal", UomCategory.Volume },

        // Count
        { "nos", UomCategory.Count },
        { "no", UomCategory.Count },
        { "ea", UomCategory.Count },
        { "pcs", UomCategory.Count },
        { "set", UomCategory.Count },

        // Lump sum
        { "ls", UomCategory.Lump },
        { "lumpsum", UomCategory.Lump },
        { "job", UomCategory.Lump },
        { "lot", UomCategory.Lump },
    };

    public UomConversionService(
        IApplicationDbContext context,
        IMemoryCache cache,
        ILogger<UomConversionService> logger)
    {
        _context = context;
        _cache = cache;
        _logger = logger;
    }

    /// <inheritdoc/>
    public async Task<decimal?> GetConversionFactorAsync(string fromUom, string toUom, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(fromUom) || string.IsNullOrWhiteSpace(toUom))
        {
            return null;
        }

        var normalizedFrom = NormalizeUomCode(fromUom);
        var normalizedTo = NormalizeUomCode(toUom);

        // Same UOM, factor is 1
        if (string.Equals(normalizedFrom, normalizedTo, StringComparison.OrdinalIgnoreCase))
        {
            return 1m;
        }

        // Check if they are in the same category first
        var fromCategory = await GetUomCategoryInternalAsync(normalizedFrom, cancellationToken);
        var toCategory = await GetUomCategoryInternalAsync(normalizedTo, cancellationToken);

        if (fromCategory == null || toCategory == null || fromCategory != toCategory)
        {
            // Cannot convert between different categories or unknown UOMs
            return null;
        }

        // Lump sum items cannot be converted
        if (fromCategory == UomCategory.Lump)
        {
            return null;
        }

        // Try database lookup first
        var dbFactor = await GetDbConversionFactorAsync(normalizedFrom, normalizedTo, cancellationToken);
        if (dbFactor.HasValue)
        {
            return dbFactor.Value;
        }

        // Try common conversions as fallback
        if (CommonConversions.TryGetValue((normalizedFrom, normalizedTo), out var factor))
        {
            return factor;
        }

        // Try to compute through base unit
        var computedFactor = await ComputeConversionThroughBaseAsync(normalizedFrom, normalizedTo, cancellationToken);
        if (computedFactor.HasValue)
        {
            return computedFactor.Value;
        }

        _logger.LogWarning("No conversion factor found from {FromUom} to {ToUom}", fromUom, toUom);
        return null;
    }

    /// <inheritdoc/>
    public async Task<bool> CanConvertAsync(string fromUom, string toUom, CancellationToken cancellationToken = default)
    {
        var factor = await GetConversionFactorAsync(fromUom, toUom, cancellationToken);
        return factor.HasValue;
    }

    /// <inheritdoc/>
    public async Task<decimal?> ConvertAsync(decimal value, string fromUom, string toUom, CancellationToken cancellationToken = default)
    {
        var factor = await GetConversionFactorAsync(fromUom, toUom, cancellationToken);
        if (!factor.HasValue)
        {
            return null;
        }

        return value * factor.Value;
    }

    /// <inheritdoc/>
    public async Task<string?> GetNonConvertibleReasonAsync(string fromUom, string toUom, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(fromUom) || string.IsNullOrWhiteSpace(toUom))
        {
            return "Invalid UOM code provided.";
        }

        var normalizedFrom = NormalizeUomCode(fromUom);
        var normalizedTo = NormalizeUomCode(toUom);

        // Same UOM
        if (string.Equals(normalizedFrom, normalizedTo, StringComparison.OrdinalIgnoreCase))
        {
            return null; // Can convert (factor = 1)
        }

        var fromCategory = await GetUomCategoryInternalAsync(normalizedFrom, cancellationToken);
        var toCategory = await GetUomCategoryInternalAsync(normalizedTo, cancellationToken);

        if (fromCategory == null)
        {
            return $"Unknown UOM: {fromUom}";
        }

        if (toCategory == null)
        {
            return $"Unknown UOM: {toUom}";
        }

        if (fromCategory != toCategory)
        {
            return $"Different categories: {fromCategory} vs {toCategory}";
        }

        if (fromCategory == UomCategory.Lump)
        {
            return "Lump sum items cannot be converted to other units.";
        }

        // If we reach here, conversion should be possible
        var factor = await GetConversionFactorAsync(fromUom, toUom, cancellationToken);
        if (factor.HasValue)
        {
            return null;
        }

        return $"No conversion factor defined between {fromUom} and {toUom}.";
    }

    /// <inheritdoc/>
    public async Task<string?> GetUomCategoryAsync(string uomCode, CancellationToken cancellationToken = default)
    {
        var category = await GetUomCategoryInternalAsync(uomCode, cancellationToken);
        return category?.ToString();
    }

    private static string NormalizeUomCode(string code)
    {
        return code.Trim().ToLowerInvariant()
            .Replace(" ", "")
            .Replace(".", "")
            .Replace("-", "");
    }

    private async Task<UomCategory?> GetUomCategoryInternalAsync(string uomCode, CancellationToken cancellationToken)
    {
        var normalized = NormalizeUomCode(uomCode);

        // Check hardcoded map first
        if (UomCategoryMap.TryGetValue(normalized, out var category))
        {
            return category;
        }

        // Check database
        var uomData = await GetCachedUomDataAsync(cancellationToken);
        var dbUom = uomData.FirstOrDefault(u =>
            string.Equals(NormalizeUomCode(u.Code), normalized, StringComparison.OrdinalIgnoreCase));

        return dbUom?.Category;
    }

    private async Task<decimal?> GetDbConversionFactorAsync(string fromUom, string toUom, CancellationToken cancellationToken)
    {
        var uomData = await GetCachedUomDataAsync(cancellationToken);

        var fromEntry = uomData.FirstOrDefault(u =>
            string.Equals(NormalizeUomCode(u.Code), fromUom, StringComparison.OrdinalIgnoreCase));
        var toEntry = uomData.FirstOrDefault(u =>
            string.Equals(NormalizeUomCode(u.Code), toUom, StringComparison.OrdinalIgnoreCase));

        if (fromEntry == null || toEntry == null)
        {
            return null;
        }

        // If they have the same base unit
        if (!string.IsNullOrEmpty(fromEntry.BaseUnitCode) &&
            !string.IsNullOrEmpty(toEntry.BaseUnitCode) &&
            string.Equals(fromEntry.BaseUnitCode, toEntry.BaseUnitCode, StringComparison.OrdinalIgnoreCase))
        {
            if (fromEntry.ConversionToBase.HasValue && toEntry.ConversionToBase.HasValue && toEntry.ConversionToBase.Value != 0)
            {
                // from -> base -> to
                return fromEntry.ConversionToBase.Value / toEntry.ConversionToBase.Value;
            }
        }

        // If converting to the base unit
        if (!string.IsNullOrEmpty(fromEntry.BaseUnitCode) &&
            string.Equals(NormalizeUomCode(fromEntry.BaseUnitCode), toUom, StringComparison.OrdinalIgnoreCase))
        {
            return fromEntry.ConversionToBase;
        }

        // If converting from the base unit
        if (!string.IsNullOrEmpty(toEntry.BaseUnitCode) &&
            string.Equals(NormalizeUomCode(toEntry.BaseUnitCode), fromUom, StringComparison.OrdinalIgnoreCase) &&
            toEntry.ConversionToBase.HasValue && toEntry.ConversionToBase.Value != 0)
        {
            return 1m / toEntry.ConversionToBase.Value;
        }

        return null;
    }

    private async Task<decimal?> ComputeConversionThroughBaseAsync(string fromUom, string toUom, CancellationToken cancellationToken)
    {
        // Try to find a common base unit in the category
        var category = await GetUomCategoryInternalAsync(fromUom, cancellationToken);
        if (category == null)
        {
            return null;
        }

        string? baseUnit = category switch
        {
            UomCategory.Area => "m2",
            UomCategory.Length => "m",
            UomCategory.Weight => "kg",
            UomCategory.Volume => "m3",
            UomCategory.Count => "nos",
            _ => null
        };

        if (baseUnit == null)
        {
            return null;
        }

        // Try: fromUom -> baseUnit -> toUom
        decimal? fromToBase = null;
        decimal? baseToTo = null;

        if (CommonConversions.TryGetValue((fromUom, baseUnit), out var ftb))
        {
            fromToBase = ftb;
        }

        if (CommonConversions.TryGetValue((baseUnit, toUom), out var btt))
        {
            baseToTo = btt;
        }

        if (fromToBase.HasValue && baseToTo.HasValue)
        {
            return fromToBase.Value * baseToTo.Value;
        }

        return null;
    }

    private async Task<List<UomMasterCacheEntry>> GetCachedUomDataAsync(CancellationToken cancellationToken)
    {
        if (_cache.TryGetValue(UomCacheKey, out List<UomMasterCacheEntry>? cached) && cached != null)
        {
            return cached;
        }

        var data = await _context.UomMasters
            .AsNoTracking()
            .Select(u => new UomMasterCacheEntry
            {
                Code = u.Code,
                Category = u.Category,
                BaseUnitCode = u.BaseUnitCode,
                ConversionToBase = u.ConversionToBase
            })
            .ToListAsync(cancellationToken);

        _cache.Set(UomCacheKey, data, CacheDuration);
        return data;
    }

    private class UomMasterCacheEntry
    {
        public string Code { get; set; } = string.Empty;
        public UomCategory Category { get; set; }
        public string? BaseUnitCode { get; set; }
        public decimal? ConversionToBase { get; set; }
    }
}
