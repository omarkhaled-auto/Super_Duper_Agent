using System.Diagnostics;
using Serilog;

namespace Bayan.API.Middleware;

/// <summary>
/// Middleware that logs every HTTP request with method, path, status code, duration, and user ID.
/// </summary>
public class RequestLoggingMiddleware
{
    private readonly RequestDelegate _next;

    public RequestLoggingMiddleware(RequestDelegate next)
    {
        _next = next;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var stopwatch = Stopwatch.StartNew();
        try
        {
            await _next(context);
        }
        finally
        {
            stopwatch.Stop();

            var userId = context.User?.FindFirst("sub")?.Value
                      ?? context.User?.FindFirst(System.Security.Claims.ClaimTypes.NameIdentifier)?.Value
                      ?? "anonymous";

            Log.Information(
                "HTTP {Method} {Path} responded {StatusCode} in {ElapsedMs}ms [User: {UserId}]",
                context.Request.Method,
                context.Request.Path,
                context.Response.StatusCode,
                stopwatch.ElapsedMilliseconds,
                userId);
        }
    }
}

/// <summary>
/// Extension methods for request logging middleware.
/// </summary>
public static class RequestLoggingMiddlewareExtensions
{
    /// <summary>
    /// Adds request logging middleware to the application pipeline.
    /// </summary>
    public static IApplicationBuilder UseRequestLogging(this IApplicationBuilder app)
    {
        return app.UseMiddleware<RequestLoggingMiddleware>();
    }
}
