namespace Bayan.Infrastructure.FileStorage;

/// <summary>
/// Configuration settings for MinIO object storage.
/// </summary>
public class MinioSettings
{
    /// <summary>
    /// Configuration section name in appsettings.json.
    /// </summary>
    public const string SectionName = "MinioSettings";

    /// <summary>
    /// MinIO server endpoint (e.g., "localhost:9000" or "minio.example.com").
    /// </summary>
    public string Endpoint { get; set; } = "localhost:9000";

    /// <summary>
    /// MinIO access key (username).
    /// </summary>
    public string AccessKey { get; set; } = string.Empty;

    /// <summary>
    /// MinIO secret key (password).
    /// </summary>
    public string SecretKey { get; set; } = string.Empty;

    /// <summary>
    /// Whether to use SSL/TLS for connections.
    /// </summary>
    public bool UseSSL { get; set; } = false;

    /// <summary>
    /// Default bucket name for tender documents.
    /// </summary>
    public string BucketName { get; set; } = "tender-documents";

    /// <summary>
    /// Region for the bucket (optional, used for AWS S3 compatibility).
    /// </summary>
    public string? Region { get; set; }

    /// <summary>
    /// Public endpoint for presigned URLs (e.g., "localhost:9000" from the browser's perspective).
    /// When running in Docker, the internal Endpoint (e.g., "minio:9000") is unreachable from the browser.
    /// Set this to the externally accessible host:port so presigned URLs work from the client.
    /// If empty/null, the internal Endpoint is used as-is (backward compatible).
    /// </summary>
    public string? PublicEndpoint { get; set; }
}
