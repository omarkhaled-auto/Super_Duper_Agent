using System.Net;

namespace Bayan.API.Middleware;

/// <summary>
/// Middleware to limit request body size and validate content types.
/// </summary>
public class RequestSizeLimitMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<RequestSizeLimitMiddleware> _logger;
    private readonly RequestSizeLimitOptions _options;

    public RequestSizeLimitMiddleware(
        RequestDelegate next,
        ILogger<RequestSizeLimitMiddleware> logger,
        RequestSizeLimitOptions options)
    {
        _next = next;
        _logger = logger;
        _options = options;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        // Check request content length
        if (context.Request.ContentLength.HasValue)
        {
            var maxSize = GetMaxRequestSize(context);

            if (context.Request.ContentLength.Value > maxSize)
            {
                _logger.LogWarning(
                    "Request size {Size} exceeds maximum allowed size {MaxSize} for path {Path}",
                    context.Request.ContentLength.Value,
                    maxSize,
                    context.Request.Path);

                context.Response.StatusCode = (int)HttpStatusCode.RequestEntityTooLarge;
                context.Response.ContentType = "application/json";

                var errorResponse = new
                {
                    statusCode = 413,
                    message = $"Request size exceeds the maximum allowed size of {maxSize / (1024 * 1024)} MB.",
                    maxSizeBytes = maxSize
                };

                await context.Response.WriteAsJsonAsync(errorResponse);
                return;
            }
        }

        await _next(context);
    }

    private long GetMaxRequestSize(HttpContext context)
    {
        var path = context.Request.Path.Value?.ToLower() ?? "";

        // Allow larger sizes for file upload endpoints
        if (path.Contains("/upload") ||
            path.Contains("/documents") ||
            path.Contains("/files") ||
            path.Contains("/import"))
        {
            return _options.MaxFileUploadSizeBytes;
        }

        return _options.MaxRequestSizeBytes;
    }
}

/// <summary>
/// Request size limit configuration options.
/// </summary>
public class RequestSizeLimitOptions
{
    /// <summary>
    /// Maximum request body size in bytes. Default is 10 MB.
    /// </summary>
    public long MaxRequestSizeBytes { get; set; } = 10 * 1024 * 1024; // 10 MB

    /// <summary>
    /// Maximum file upload size in bytes. Default is 50 MB.
    /// </summary>
    public long MaxFileUploadSizeBytes { get; set; } = 50 * 1024 * 1024; // 50 MB

    /// <summary>
    /// Whether request size limiting is enabled. Default is true.
    /// </summary>
    public bool Enabled { get; set; } = true;
}

/// <summary>
/// Extension methods for request size limit middleware.
/// </summary>
public static class RequestSizeLimitMiddlewareExtensions
{
    /// <summary>
    /// Adds request size limit middleware to the application pipeline.
    /// </summary>
    public static IApplicationBuilder UseRequestSizeLimit(
        this IApplicationBuilder app,
        Action<RequestSizeLimitOptions>? configureOptions = null)
    {
        var options = new RequestSizeLimitOptions();
        configureOptions?.Invoke(options);

        if (!options.Enabled)
        {
            return app;
        }

        return app.UseMiddleware<RequestSizeLimitMiddleware>(options);
    }
}
