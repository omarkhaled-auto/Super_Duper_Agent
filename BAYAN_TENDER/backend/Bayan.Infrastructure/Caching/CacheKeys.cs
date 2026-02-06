namespace Bayan.Infrastructure.Caching;

/// <summary>
/// Static class containing cache key patterns and helpers.
/// </summary>
public static class CacheKeys
{
    /// <summary>
    /// Cache key prefix for comparable sheet data.
    /// Format: comparable-sheet:{tenderId}
    /// </summary>
    public const string ComparableSheetPrefix = "comparable-sheet";

    /// <summary>
    /// Cache key prefix for vendor pricing data.
    /// Format: vendor-pricing:{bidderId}
    /// </summary>
    public const string VendorPricingPrefix = "vendor-pricing";

    /// <summary>
    /// Cache key prefix for vendor analytics.
    /// Format: vendor-analytics:{bidderId}
    /// </summary>
    public const string VendorAnalyticsPrefix = "vendor-analytics";

    /// <summary>
    /// Cache key prefix for vendor comparison data.
    /// Format: vendor-comparison:{hash of bidder ids}
    /// </summary>
    public const string VendorComparisonPrefix = "vendor-comparison";

    /// <summary>
    /// Default TTL for comparable sheet cache (5 minutes).
    /// </summary>
    public static readonly TimeSpan ComparableSheetTtl = TimeSpan.FromMinutes(5);

    /// <summary>
    /// Default TTL for vendor pricing cache (10 minutes).
    /// </summary>
    public static readonly TimeSpan VendorPricingTtl = TimeSpan.FromMinutes(10);

    /// <summary>
    /// Default TTL for vendor analytics cache (15 minutes).
    /// </summary>
    public static readonly TimeSpan VendorAnalyticsTtl = TimeSpan.FromMinutes(15);

    /// <summary>
    /// Default TTL for vendor comparison cache (10 minutes).
    /// </summary>
    public static readonly TimeSpan VendorComparisonTtl = TimeSpan.FromMinutes(10);

    /// <summary>
    /// Gets the cache key for a comparable sheet.
    /// </summary>
    /// <param name="tenderId">The tender ID.</param>
    /// <returns>The cache key.</returns>
    public static string GetComparableSheetKey(Guid tenderId)
        => $"{ComparableSheetPrefix}:{tenderId}";

    /// <summary>
    /// Gets the cache key for vendor pricing.
    /// </summary>
    /// <param name="bidderId">The bidder ID.</param>
    /// <returns>The cache key.</returns>
    public static string GetVendorPricingKey(Guid bidderId)
        => $"{VendorPricingPrefix}:{bidderId}";

    /// <summary>
    /// Gets the cache key for vendor analytics.
    /// </summary>
    /// <param name="bidderId">The bidder ID.</param>
    /// <returns>The cache key.</returns>
    public static string GetVendorAnalyticsKey(Guid bidderId)
        => $"{VendorAnalyticsPrefix}:{bidderId}";

    /// <summary>
    /// Gets the cache key pattern for all vendor pricing entries.
    /// </summary>
    /// <returns>The pattern string.</returns>
    public static string GetVendorPricingPattern()
        => $"{VendorPricingPrefix}:*";

    /// <summary>
    /// Gets the cache key pattern for all comparable sheet entries.
    /// </summary>
    /// <returns>The pattern string.</returns>
    public static string GetComparableSheetPattern()
        => $"{ComparableSheetPrefix}:*";

    /// <summary>
    /// Gets the cache key for vendor comparison.
    /// </summary>
    /// <param name="bidderIds">List of bidder IDs being compared.</param>
    /// <returns>The cache key.</returns>
    public static string GetVendorComparisonKey(IEnumerable<Guid> bidderIds)
    {
        var sortedIds = bidderIds.OrderBy(id => id).Select(id => id.ToString());
        var hash = string.Join("-", sortedIds).GetHashCode();
        return $"{VendorComparisonPrefix}:{hash}";
    }
}
