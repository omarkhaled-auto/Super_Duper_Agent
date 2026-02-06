using System.Diagnostics;
using System.Text.Json;
using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Common.Behaviors;

/// <summary>
/// MediatR pipeline behavior that writes audit log entries for command executions.
/// Only fires for requests whose type name ends with "Command".
/// </summary>
public class AuditLogBehavior<TRequest, TResponse> : IPipelineBehavior<TRequest, TResponse>
    where TRequest : notnull
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUser;
    private readonly ILogger<AuditLogBehavior<TRequest, TResponse>> _logger;

    public AuditLogBehavior(
        IApplicationDbContext context,
        ICurrentUserService currentUser,
        ILogger<AuditLogBehavior<TRequest, TResponse>> logger)
    {
        _context = context;
        _currentUser = currentUser;
        _logger = logger;
    }

    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        var requestName = typeof(TRequest).Name;

        if (!requestName.EndsWith("Command"))
        {
            return await next();
        }

        var stopwatch = Stopwatch.StartNew();
        var response = await next();
        stopwatch.Stop();

        try
        {
            var entityType = DeriveEntityType(requestName);
            string? serializedRequest = null;
            try
            {
                serializedRequest = JsonSerializer.Serialize(request, new JsonSerializerOptions
                {
                    MaxDepth = 3,
                    DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull
                });
            }
            catch
            {
                serializedRequest = $"{{\"type\":\"{requestName}\"}}";
            }

            var auditLog = new AuditLog
            {
                Id = Guid.NewGuid(),
                UserId = _currentUser.UserId,
                UserEmail = _currentUser.Email,
                Action = requestName,
                EntityType = entityType,
                NewValues = serializedRequest,
                CreatedAt = DateTime.UtcNow
            };

            _context.AuditLogs.Add(auditLog);
            await _context.SaveChangesAsync(cancellationToken);
        }
        catch (Exception ex)
        {
            // Audit failure must not break the command
            _logger.LogWarning(ex, "Failed to write audit log for {RequestName}", requestName);
        }

        return response;
    }

    private static string DeriveEntityType(string commandName)
    {
        // "CreateTenderCommand" → "Tender", "SubmitBidCommand" → "Bid"
        var name = commandName;
        if (name.EndsWith("Command"))
            name = name[..^7]; // Remove "Command"

        // Remove common verb prefixes
        string[] prefixes = ["Create", "Update", "Delete", "Submit", "Publish", "Cancel", "Approve", "Reject",
            "Initiate", "Add", "Remove", "Upload", "Execute", "Generate", "Calculate", "Lock", "Save",
            "Assign", "Acknowledge", "Issue", "Invite", "Open", "Accept", "Disqualify", "Normalize",
            "Parse", "Map", "Match", "Validate"];

        foreach (var prefix in prefixes)
        {
            if (name.StartsWith(prefix, StringComparison.Ordinal) && name.Length > prefix.Length)
            {
                return name[prefix.Length..];
            }
        }

        return name;
    }
}
