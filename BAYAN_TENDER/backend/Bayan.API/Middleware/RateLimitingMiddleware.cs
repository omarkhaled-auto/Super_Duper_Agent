using System.Collections.Concurrent;
using System.Net;

namespace Bayan.API.Middleware;

/// <summary>
/// Simple in-memory rate limiting middleware.
/// For production, consider using AspNetCoreRateLimit or a distributed cache like Redis.
/// </summary>
public class RateLimitingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<RateLimitingMiddleware> _logger;
    private readonly RateLimitOptions _options;
    private static readonly ConcurrentDictionary<string, RateLimitEntry> _requestCounts = new();

    public RateLimitingMiddleware(
        RequestDelegate next,
        ILogger<RateLimitingMiddleware> logger,
        RateLimitOptions options)
    {
        _next = next;
        _logger = logger;
        _options = options;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        // Get the client identifier (user ID if authenticated, otherwise IP address)
        var clientId = GetClientIdentifier(context);

        if (!IsAllowed(clientId, out var retryAfterSeconds))
        {
            _logger.LogWarning("Rate limit exceeded for client: {ClientId}", clientId);

            context.Response.StatusCode = (int)HttpStatusCode.TooManyRequests;
            context.Response.Headers["Retry-After"] = retryAfterSeconds.ToString();
            context.Response.ContentType = "application/json";

            var errorResponse = new
            {
                statusCode = 429,
                message = "Rate limit exceeded. Please try again later.",
                retryAfterSeconds
            };

            await context.Response.WriteAsJsonAsync(errorResponse);
            return;
        }

        await _next(context);
    }

    private string GetClientIdentifier(HttpContext context)
    {
        // If user is authenticated, use user ID
        var userId = context.User?.FindFirst("sub")?.Value
                  ?? context.User?.FindFirst("id")?.Value;

        if (!string.IsNullOrEmpty(userId))
        {
            return $"user:{userId}";
        }

        // Otherwise use IP address
        var ipAddress = context.Connection.RemoteIpAddress?.ToString()
                     ?? context.Request.Headers["X-Forwarded-For"].FirstOrDefault()
                     ?? "unknown";

        return $"ip:{ipAddress}";
    }

    private bool IsAllowed(string clientId, out int retryAfterSeconds)
    {
        var now = DateTime.UtcNow;
        var windowStart = now.AddMinutes(-1);

        var entry = _requestCounts.AddOrUpdate(
            clientId,
            _ => new RateLimitEntry { Count = 1, WindowStart = now },
            (_, existing) =>
            {
                if (existing.WindowStart < windowStart)
                {
                    // Reset window
                    return new RateLimitEntry { Count = 1, WindowStart = now };
                }

                existing.Count++;
                return existing;
            });

        if (entry.Count > _options.RequestsPerMinute)
        {
            var windowEnd = entry.WindowStart.AddMinutes(1);
            retryAfterSeconds = Math.Max(1, (int)(windowEnd - now).TotalSeconds);
            return false;
        }

        retryAfterSeconds = 0;
        return true;
    }

    private class RateLimitEntry
    {
        public int Count { get; set; }
        public DateTime WindowStart { get; set; }
    }
}

/// <summary>
/// Rate limiting configuration options.
/// </summary>
public class RateLimitOptions
{
    /// <summary>
    /// Maximum number of requests per minute per user/IP. Default is 100.
    /// </summary>
    public int RequestsPerMinute { get; set; } = 100;

    /// <summary>
    /// Whether rate limiting is enabled. Default is true.
    /// </summary>
    public bool Enabled { get; set; } = true;
}

/// <summary>
/// Extension methods for rate limiting middleware.
/// </summary>
public static class RateLimitingMiddlewareExtensions
{
    /// <summary>
    /// Adds rate limiting middleware to the application pipeline.
    /// </summary>
    public static IApplicationBuilder UseRateLimiting(
        this IApplicationBuilder app,
        Action<RateLimitOptions>? configureOptions = null)
    {
        var options = new RateLimitOptions();
        configureOptions?.Invoke(options);

        if (!options.Enabled)
        {
            return app;
        }

        return app.UseMiddleware<RateLimitingMiddleware>(options);
    }
}
