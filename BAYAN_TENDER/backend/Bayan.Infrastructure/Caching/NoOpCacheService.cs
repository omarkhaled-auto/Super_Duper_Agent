using Bayan.Application.Common.Interfaces;
using Microsoft.Extensions.Logging;

namespace Bayan.Infrastructure.Caching;

/// <summary>
/// No-operation cache service implementation.
/// Used when Redis is not configured or disabled.
/// </summary>
public class NoOpCacheService : ICacheService
{
    private readonly ILogger<NoOpCacheService> _logger;

    public NoOpCacheService(ILogger<NoOpCacheService> logger)
    {
        _logger = logger;
        _logger.LogWarning("Redis is disabled. Using no-op cache service.");
    }

    /// <inheritdoc />
    public Task<T?> GetAsync<T>(string key, CancellationToken cancellationToken = default) where T : class
    {
        return Task.FromResult<T?>(null);
    }

    /// <inheritdoc />
    public Task SetAsync<T>(string key, T value, TimeSpan ttl, CancellationToken cancellationToken = default) where T : class
    {
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public Task RemoveAsync(string key, CancellationToken cancellationToken = default)
    {
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public Task RemoveByPatternAsync(string pattern, CancellationToken cancellationToken = default)
    {
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public async Task<T?> GetOrSetAsync<T>(
        string key,
        Func<CancellationToken, Task<T?>> factory,
        TimeSpan ttl,
        CancellationToken cancellationToken = default) where T : class
    {
        // Always execute the factory since we're not caching
        return await factory(cancellationToken);
    }

    /// <inheritdoc />
    public Task<bool> ExistsAsync(string key, CancellationToken cancellationToken = default)
    {
        return Task.FromResult(false);
    }
}
