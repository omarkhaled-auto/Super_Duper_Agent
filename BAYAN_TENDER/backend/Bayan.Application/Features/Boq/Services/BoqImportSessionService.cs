using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.DTOs;
using Microsoft.Extensions.Caching.Memory;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Boq.Services;

/// <summary>
/// Service for managing BOQ import sessions.
/// </summary>
public interface IBoqImportSessionService
{
    /// <summary>
    /// Creates a new import session.
    /// </summary>
    Task<Guid> CreateSessionAsync(
        Guid tenderId,
        string fileName,
        long fileSize,
        ExcelParseResult parseResult,
        List<ColumnMappingDto> suggestedMappings,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets an existing import session.
    /// </summary>
    Task<BoqImportSession?> GetSessionAsync(Guid sessionId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Updates session with column mappings.
    /// </summary>
    Task UpdateMappingsAsync(Guid sessionId, List<ColumnMappingDto> mappings, CancellationToken cancellationToken = default);

    /// <summary>
    /// Updates session with validation result.
    /// </summary>
    Task UpdateValidationResultAsync(Guid sessionId, ImportValidationResultDto validationResult, CancellationToken cancellationToken = default);

    /// <summary>
    /// Marks session as completed.
    /// </summary>
    Task CompleteSessionAsync(Guid sessionId, CancellationToken cancellationToken = default);

    /// <summary>
    /// Removes an import session.
    /// </summary>
    Task RemoveSessionAsync(Guid sessionId, CancellationToken cancellationToken = default);
}

/// <summary>
/// Represents an import session state.
/// </summary>
public class BoqImportSession
{
    public Guid Id { get; set; }
    public Guid TenderId { get; set; }
    public string FileName { get; set; } = string.Empty;
    public long FileSize { get; set; }
    public ExcelParseResult ParseResult { get; set; } = new();
    public List<ColumnMappingDto> ColumnMappings { get; set; } = new();
    public ImportValidationResultDto? ValidationResult { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime ExpiresAt { get; set; }
    public ImportSessionStatus Status { get; set; }
}

/// <summary>
/// Import session status.
/// </summary>
public enum ImportSessionStatus
{
    Uploaded,
    MappingConfigured,
    Validated,
    Completed,
    Failed
}

/// <summary>
/// In-memory implementation of BOQ import session service.
/// For production, consider using distributed cache (Redis).
/// </summary>
public class BoqImportSessionService : IBoqImportSessionService
{
    private readonly IMemoryCache _cache;
    private readonly ILogger<BoqImportSessionService> _logger;
    private static readonly TimeSpan SessionTimeout = TimeSpan.FromHours(1);

    public BoqImportSessionService(IMemoryCache cache, ILogger<BoqImportSessionService> logger)
    {
        _cache = cache;
        _logger = logger;
    }

    public Task<Guid> CreateSessionAsync(
        Guid tenderId,
        string fileName,
        long fileSize,
        ExcelParseResult parseResult,
        List<ColumnMappingDto> suggestedMappings,
        CancellationToken cancellationToken = default)
    {
        var sessionId = Guid.NewGuid();
        var session = new BoqImportSession
        {
            Id = sessionId,
            TenderId = tenderId,
            FileName = fileName,
            FileSize = fileSize,
            ParseResult = parseResult,
            ColumnMappings = suggestedMappings,
            CreatedAt = DateTime.UtcNow,
            ExpiresAt = DateTime.UtcNow.Add(SessionTimeout),
            Status = ImportSessionStatus.Uploaded
        };

        var cacheKey = GetCacheKey(sessionId);
        _cache.Set(cacheKey, session, SessionTimeout);

        _logger.LogInformation("Created BOQ import session {SessionId} for tender {TenderId}", sessionId, tenderId);

        return Task.FromResult(sessionId);
    }

    public Task<BoqImportSession?> GetSessionAsync(Guid sessionId, CancellationToken cancellationToken = default)
    {
        var cacheKey = GetCacheKey(sessionId);
        _cache.TryGetValue(cacheKey, out BoqImportSession? session);
        return Task.FromResult(session);
    }

    public Task UpdateMappingsAsync(Guid sessionId, List<ColumnMappingDto> mappings, CancellationToken cancellationToken = default)
    {
        var cacheKey = GetCacheKey(sessionId);
        if (_cache.TryGetValue(cacheKey, out BoqImportSession? session) && session != null)
        {
            session.ColumnMappings = mappings;
            session.Status = ImportSessionStatus.MappingConfigured;
            _cache.Set(cacheKey, session, session.ExpiresAt - DateTime.UtcNow);
            _logger.LogDebug("Updated mappings for session {SessionId}", sessionId);
        }
        return Task.CompletedTask;
    }

    public Task UpdateValidationResultAsync(Guid sessionId, ImportValidationResultDto validationResult, CancellationToken cancellationToken = default)
    {
        var cacheKey = GetCacheKey(sessionId);
        if (_cache.TryGetValue(cacheKey, out BoqImportSession? session) && session != null)
        {
            session.ValidationResult = validationResult;
            session.Status = ImportSessionStatus.Validated;
            _cache.Set(cacheKey, session, session.ExpiresAt - DateTime.UtcNow);
            _logger.LogDebug("Updated validation result for session {SessionId}", sessionId);
        }
        return Task.CompletedTask;
    }

    public Task CompleteSessionAsync(Guid sessionId, CancellationToken cancellationToken = default)
    {
        var cacheKey = GetCacheKey(sessionId);
        if (_cache.TryGetValue(cacheKey, out BoqImportSession? session) && session != null)
        {
            session.Status = ImportSessionStatus.Completed;
            // Keep session for a short time after completion for reference
            _cache.Set(cacheKey, session, TimeSpan.FromMinutes(15));
            _logger.LogInformation("Completed BOQ import session {SessionId}", sessionId);
        }
        return Task.CompletedTask;
    }

    public Task RemoveSessionAsync(Guid sessionId, CancellationToken cancellationToken = default)
    {
        var cacheKey = GetCacheKey(sessionId);
        _cache.Remove(cacheKey);
        _logger.LogDebug("Removed BOQ import session {SessionId}", sessionId);
        return Task.CompletedTask;
    }

    private static string GetCacheKey(Guid sessionId) => $"boq-import-session:{sessionId}";
}
