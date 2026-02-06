namespace Bayan.Infrastructure.Caching;

/// <summary>
/// Configuration settings for Redis connection.
/// </summary>
public class RedisSettings
{
    /// <summary>
    /// Configuration section name.
    /// </summary>
    public const string SectionName = "RedisSettings";

    /// <summary>
    /// Redis connection string.
    /// Format: "host:port" or "host:port,password=xxx,ssl=true"
    /// </summary>
    public string ConnectionString { get; set; } = "localhost:6379";

    /// <summary>
    /// Instance name prefix for cache keys.
    /// </summary>
    public string InstanceName { get; set; } = "Bayan:";

    /// <summary>
    /// Whether to enable Redis caching.
    /// If false, a no-op cache implementation will be used.
    /// </summary>
    public bool Enabled { get; set; } = true;

    /// <summary>
    /// Connection timeout in milliseconds.
    /// </summary>
    public int ConnectTimeout { get; set; } = 5000;

    /// <summary>
    /// Sync timeout in milliseconds.
    /// </summary>
    public int SyncTimeout { get; set; } = 5000;

    /// <summary>
    /// Whether to abort on connection failure.
    /// </summary>
    public bool AbortOnConnectFail { get; set; } = false;
}
