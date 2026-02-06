using Hangfire.Dashboard;
using Microsoft.AspNetCore.Http;

namespace Bayan.Infrastructure.Jobs;

/// <summary>
/// Authorization filter for Hangfire dashboard.
/// Only allows authenticated users with specific roles.
/// </summary>
public class HangfireDashboardAuthorizationFilter : IDashboardAuthorizationFilter
{
    private readonly string[] _allowedRoles;

    public HangfireDashboardAuthorizationFilter(string[] allowedRoles)
    {
        _allowedRoles = allowedRoles ?? Array.Empty<string>();
    }

    public bool Authorize(DashboardContext context)
    {
        var httpContext = context.GetHttpContext();

        // Check if user is authenticated
        if (httpContext.User?.Identity?.IsAuthenticated != true)
        {
            return false;
        }

        // If no specific roles are required, allow any authenticated user
        if (_allowedRoles.Length == 0)
        {
            return true;
        }

        // Check if user has any of the allowed roles
        foreach (var role in _allowedRoles)
        {
            if (httpContext.User.IsInRole(role))
            {
                return true;
            }
        }

        return false;
    }
}

/// <summary>
/// Local-only authorization filter for development.
/// Only allows access from localhost.
/// </summary>
public class HangfireLocalAuthorizationFilter : IDashboardAuthorizationFilter
{
    public bool Authorize(DashboardContext context)
    {
        var httpContext = context.GetHttpContext();

        // Allow access only from localhost
        return httpContext.Connection.RemoteIpAddress?.ToString() == "127.0.0.1" ||
               httpContext.Connection.RemoteIpAddress?.ToString() == "::1" ||
               httpContext.Connection.LocalIpAddress?.Equals(httpContext.Connection.RemoteIpAddress) == true;
    }
}
