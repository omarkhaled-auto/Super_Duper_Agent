using Bayan.Application.Common.Interfaces;
using Bayan.Infrastructure.Caching;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Infrastructure.Jobs;

/// <summary>
/// Background job to warm up frequently accessed cache data on application start.
/// Pre-caches UOMs, system settings, and other commonly accessed data.
/// </summary>
public class CacheWarmupJob
{
    private readonly IApplicationDbContext _context;
    private readonly ICacheService _cacheService;
    private readonly ILogger<CacheWarmupJob> _logger;

    private const string UomsKey = "cache:uoms:all";
    private const string SystemSettingsKey = "cache:settings:all";
    private const string ActiveTendersKey = "cache:tenders:active";
    private const string ActiveBiddersKey = "cache:bidders:active";

    private static readonly TimeSpan DefaultTtl = TimeSpan.FromHours(1);
    private static readonly TimeSpan ShortTtl = TimeSpan.FromMinutes(15);

    public CacheWarmupJob(
        IApplicationDbContext context,
        ICacheService cacheService,
        ILogger<CacheWarmupJob> logger)
    {
        _context = context;
        _cacheService = cacheService;
        _logger = logger;
    }

    /// <summary>
    /// Executes the cache warmup job.
    /// </summary>
    public async Task ExecuteAsync()
    {
        _logger.LogInformation("Starting cache warmup job at {Time}", DateTime.UtcNow);

        var tasks = new List<Task>
        {
            WarmUpUomsAsync(),
            WarmUpSystemSettingsAsync(),
            WarmUpActiveTendersCountAsync(),
            WarmUpActiveBiddersCountAsync()
        };

        try
        {
            await Task.WhenAll(tasks);
            _logger.LogInformation("Cache warmup job completed successfully");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during cache warmup");
            throw;
        }
    }

    private async Task WarmUpUomsAsync()
    {
        try
        {
            _logger.LogDebug("Warming up UOMs cache...");

            var uoms = await _context.UnitsOfMeasure
                .AsNoTracking()
                .Select(u => new
                {
                    u.Id,
                    u.Code,
                    u.Name,
                    u.Category,
                    u.BaseUnitCode
                })
                .ToListAsync();

            await _cacheService.SetAsync(UomsKey, uoms, DefaultTtl);

            _logger.LogDebug("Cached {Count} UOMs", uoms.Count);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to warm up UOMs cache");
        }
    }

    private async Task WarmUpSystemSettingsAsync()
    {
        try
        {
            _logger.LogDebug("Warming up system settings cache...");

            var settings = await _context.SystemSettings
                .AsNoTracking()
                .ToDictionaryAsync(s => s.Key, s => s.Value);

            await _cacheService.SetAsync(SystemSettingsKey, settings, DefaultTtl);

            _logger.LogDebug("Cached {Count} system settings", settings.Count);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to warm up system settings cache");
        }
    }

    private async Task WarmUpActiveTendersCountAsync()
    {
        try
        {
            _logger.LogDebug("Warming up active tenders count cache...");

            var activeTenderStats = await _context.Tenders
                .AsNoTracking()
                .GroupBy(t => t.Status)
                .Select(g => new { Status = g.Key, Count = g.Count() })
                .ToDictionaryAsync(x => x.Status.ToString(), x => x.Count);

            await _cacheService.SetAsync(ActiveTendersKey, activeTenderStats, ShortTtl);

            _logger.LogDebug("Cached tender counts by status");
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to warm up active tenders count cache");
        }
    }

    private async Task WarmUpActiveBiddersCountAsync()
    {
        try
        {
            _logger.LogDebug("Warming up active bidders count cache...");

            var activeBiddersCount = await _context.Bidders
                .AsNoTracking()
                .CountAsync(b => b.IsActive);

            var totalBiddersCount = await _context.Bidders
                .AsNoTracking()
                .CountAsync();

            var bidderStats = new
            {
                Active = activeBiddersCount,
                Total = totalBiddersCount,
                Inactive = totalBiddersCount - activeBiddersCount
            };

            await _cacheService.SetAsync(ActiveBiddersKey, bidderStats, ShortTtl);

            _logger.LogDebug("Cached bidder counts: Active={Active}, Total={Total}",
                activeBiddersCount, totalBiddersCount);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to warm up active bidders count cache");
        }
    }
}
