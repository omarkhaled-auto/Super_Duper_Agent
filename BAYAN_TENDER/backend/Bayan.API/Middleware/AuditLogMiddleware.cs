using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Entities;
using Serilog;

namespace Bayan.API.Middleware;

/// <summary>
/// Middleware that writes audit log entries for successful mutation requests (POST/PUT/DELETE/PATCH).
/// </summary>
public class AuditLogMiddleware
{
    private readonly RequestDelegate _next;

    public AuditLogMiddleware(RequestDelegate next)
    {
        _next = next;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        await _next(context);

        try
        {
            if (!IsMutationMethod(context.Request.Method))
                return;

            if (!IsSuccessStatusCode(context.Response.StatusCode))
                return;

            var userId = context.User?.FindFirst("sub")?.Value
                      ?? context.User?.FindFirst(System.Security.Claims.ClaimTypes.NameIdentifier)?.Value;

            var userEmail = context.User?.FindFirst(System.Security.Claims.ClaimTypes.Email)?.Value
                         ?? context.User?.FindFirst("email")?.Value;

            var routePath = context.Request.Path.Value ?? string.Empty;
            var entityType = ExtractEntityType(routePath);
            var action = $"{context.Request.Method} {routePath}";

            var auditLog = new AuditLog
            {
                Id = Guid.NewGuid(),
                UserId = Guid.TryParse(userId, out var uid) ? uid : null,
                UserEmail = userEmail,
                Action = action,
                EntityType = entityType,
                IpAddress = GetClientIpAddress(context),
                UserAgent = context.Request.Headers.UserAgent.ToString(),
                CreatedAt = DateTime.UtcNow
            };

            using var scope = context.RequestServices.CreateScope();
            var dbContext = scope.ServiceProvider.GetService<IApplicationDbContext>();
            if (dbContext != null)
            {
                dbContext.AuditLogs.Add(auditLog);
                await dbContext.SaveChangesAsync(CancellationToken.None);
            }
        }
        catch (Exception ex)
        {
            // Audit failure must never break requests
            Log.Warning(ex, "Failed to write audit log for {Method} {Path}",
                context.Request.Method, context.Request.Path);
        }
    }

    private static bool IsMutationMethod(string method) =>
        method is "POST" or "PUT" or "DELETE" or "PATCH";

    private static bool IsSuccessStatusCode(int statusCode) =>
        statusCode >= 200 && statusCode < 300;

    private static string ExtractEntityType(string path)
    {
        // Extract entity type from route: /api/tenders/... → Tender
        var segments = path.Split('/', StringSplitOptions.RemoveEmptyEntries);
        if (segments.Length >= 2 && segments[0].Equals("api", StringComparison.OrdinalIgnoreCase))
        {
            var entity = segments[1];
            // Singularize and capitalize
            if (entity.EndsWith("ies", StringComparison.OrdinalIgnoreCase))
                entity = entity[..^3] + "y";
            else if (entity.EndsWith("s", StringComparison.OrdinalIgnoreCase) && !entity.EndsWith("ss", StringComparison.OrdinalIgnoreCase))
                entity = entity[..^1];

            return char.ToUpper(entity[0]) + entity[1..];
        }
        return "Unknown";
    }

    private static string? GetClientIpAddress(HttpContext context)
    {
        var forwardedFor = context.Request.Headers["X-Forwarded-For"].FirstOrDefault();
        if (!string.IsNullOrEmpty(forwardedFor))
            return forwardedFor.Split(',').First().Trim();

        var realIp = context.Request.Headers["X-Real-IP"].FirstOrDefault();
        if (!string.IsNullOrEmpty(realIp))
            return realIp;

        return context.Connection.RemoteIpAddress?.ToString();
    }
}

/// <summary>
/// Extension methods for audit log middleware.
/// </summary>
public static class AuditLogMiddlewareExtensions
{
    /// <summary>
    /// Adds audit logging middleware to the application pipeline.
    /// </summary>
    public static IApplicationBuilder UseAuditLogging(this IApplicationBuilder app)
    {
        return app.UseMiddleware<AuditLogMiddleware>();
    }
}
