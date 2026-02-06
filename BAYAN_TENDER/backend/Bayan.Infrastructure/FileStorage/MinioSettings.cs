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
}
