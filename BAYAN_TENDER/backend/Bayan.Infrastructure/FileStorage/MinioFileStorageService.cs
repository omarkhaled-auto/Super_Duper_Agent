using Bayan.Application.Common.Interfaces;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Minio;
using Minio.DataModel.Args;
using Minio.Exceptions;

namespace Bayan.Infrastructure.FileStorage;

/// <summary>
/// MinIO implementation of file storage service.
/// </summary>
public class MinioFileStorageService : IFileStorageService
{
    private readonly IMinioClient _minioClient;
    private readonly MinioSettings _settings;
    private readonly ILogger<MinioFileStorageService> _logger;

    public MinioFileStorageService(
        IMinioClient minioClient,
        IOptions<MinioSettings> settings,
        ILogger<MinioFileStorageService> logger)
    {
        _minioClient = minioClient;
        _settings = settings.Value;
        _logger = logger;
    }

    /// <inheritdoc />
    public async Task<string> UploadFileAsync(
        Stream stream,
        string fileName,
        string contentType,
        string path,
        CancellationToken cancellationToken = default)
    {
        await EnsureBucketExistsAsync(cancellationToken);

        // Sanitize and construct the object name
        var sanitizedFileName = SanitizeFileName(fileName);
        var objectName = string.IsNullOrWhiteSpace(path)
            ? sanitizedFileName
            : $"{path.TrimEnd('/')}/{sanitizedFileName}";

        _logger.LogInformation(
            "Uploading file {FileName} to bucket {Bucket} at path {ObjectName}",
            fileName, _settings.BucketName, objectName);

        var putObjectArgs = new PutObjectArgs()
            .WithBucket(_settings.BucketName)
            .WithObject(objectName)
            .WithStreamData(stream)
            .WithObjectSize(stream.Length)
            .WithContentType(contentType);

        await _minioClient.PutObjectAsync(putObjectArgs, cancellationToken);

        _logger.LogInformation(
            "Successfully uploaded file {FileName} to {ObjectName}",
            fileName, objectName);

        return objectName;
    }

    /// <inheritdoc />
    public async Task<Stream> DownloadFileAsync(
        string filePath,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Downloading file from bucket {Bucket} at path {FilePath}",
            _settings.BucketName, filePath);

        var memoryStream = new MemoryStream();

        var getObjectArgs = new GetObjectArgs()
            .WithBucket(_settings.BucketName)
            .WithObject(filePath)
            .WithCallbackStream(stream =>
            {
                stream.CopyTo(memoryStream);
                memoryStream.Position = 0;
            });

        await _minioClient.GetObjectAsync(getObjectArgs, cancellationToken);

        return memoryStream;
    }

    /// <inheritdoc />
    public async Task<string> GetPresignedUrlAsync(
        string filePath,
        TimeSpan expiry,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Generating presigned URL for file {FilePath} with expiry {Expiry}",
            filePath, expiry);

        // MinIO accepts expiry in seconds (integer)
        var expirySeconds = (int)Math.Min(expiry.TotalSeconds, int.MaxValue);

        var presignedGetObjectArgs = new PresignedGetObjectArgs()
            .WithBucket(_settings.BucketName)
            .WithObject(filePath)
            .WithExpiry(expirySeconds);

        var url = await _minioClient.PresignedGetObjectAsync(presignedGetObjectArgs);

        // If a public endpoint is configured, replace the internal endpoint in the URL
        // so the presigned URL is reachable from the browser (e.g., in Docker environments).
        if (!string.IsNullOrWhiteSpace(_settings.PublicEndpoint)
            && !string.IsNullOrWhiteSpace(_settings.Endpoint)
            && _settings.PublicEndpoint != _settings.Endpoint)
        {
            url = url.Replace(_settings.Endpoint, _settings.PublicEndpoint);
        }

        return url;
    }

    /// <inheritdoc />
    public async Task DeleteFileAsync(
        string filePath,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Deleting file from bucket {Bucket} at path {FilePath}",
            _settings.BucketName, filePath);

        var removeObjectArgs = new RemoveObjectArgs()
            .WithBucket(_settings.BucketName)
            .WithObject(filePath);

        await _minioClient.RemoveObjectAsync(removeObjectArgs, cancellationToken);

        _logger.LogInformation("Successfully deleted file {FilePath}", filePath);
    }

    /// <inheritdoc />
    public async Task<IReadOnlyList<StorageFileInfo>> ListFilesAsync(
        string path,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Listing files in bucket {Bucket} at path {Path}",
            _settings.BucketName, path);

        var files = new List<StorageFileInfo>();

        var listObjectsArgs = new ListObjectsArgs()
            .WithBucket(_settings.BucketName)
            .WithPrefix(path.TrimEnd('/') + "/")
            .WithRecursive(false);

        var observable = _minioClient.ListObjectsAsync(listObjectsArgs, cancellationToken);
        var tcs = new TaskCompletionSource<bool>();

        observable.Subscribe(
            item =>
            {
                if (!item.IsDir)
                {
                    files.Add(new StorageFileInfo(
                        FileName: Path.GetFileName(item.Key),
                        FilePath: item.Key,
                        Size: (long)item.Size,
                        ContentType: GetContentType(item.Key),
                        LastModified: item.LastModifiedDateTime ?? DateTime.UtcNow));
                }
            },
            ex => tcs.TrySetException(ex),
            () => tcs.TrySetResult(true));

        await tcs.Task;

        return files.AsReadOnly();
    }

    /// <inheritdoc />
    public async Task<bool> FileExistsAsync(
        string filePath,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var statObjectArgs = new StatObjectArgs()
                .WithBucket(_settings.BucketName)
                .WithObject(filePath);

            await _minioClient.StatObjectAsync(statObjectArgs, cancellationToken);
            return true;
        }
        catch (ObjectNotFoundException)
        {
            return false;
        }
        catch (BucketNotFoundException)
        {
            return false;
        }
    }

    /// <summary>
    /// Ensures the configured bucket exists, creating it if necessary.
    /// </summary>
    private async Task EnsureBucketExistsAsync(CancellationToken cancellationToken)
    {
        var bucketExistsArgs = new BucketExistsArgs()
            .WithBucket(_settings.BucketName);

        var exists = await _minioClient.BucketExistsAsync(bucketExistsArgs, cancellationToken);

        if (!exists)
        {
            _logger.LogInformation("Creating bucket {BucketName}", _settings.BucketName);

            var makeBucketArgs = new MakeBucketArgs()
                .WithBucket(_settings.BucketName);

            if (!string.IsNullOrWhiteSpace(_settings.Region))
            {
                makeBucketArgs = makeBucketArgs.WithLocation(_settings.Region);
            }

            await _minioClient.MakeBucketAsync(makeBucketArgs, cancellationToken);
        }
    }

    /// <summary>
    /// Sanitizes a file name to remove potentially problematic characters.
    /// </summary>
    private static string SanitizeFileName(string fileName)
    {
        // Replace potentially problematic characters
        var invalidChars = Path.GetInvalidFileNameChars();
        var sanitized = string.Join("_", fileName.Split(invalidChars, StringSplitOptions.RemoveEmptyEntries));

        // Add a unique suffix to prevent collisions
        var extension = Path.GetExtension(sanitized);
        var nameWithoutExtension = Path.GetFileNameWithoutExtension(sanitized);
        var timestamp = DateTime.UtcNow.ToString("yyyyMMddHHmmssfff");

        return $"{nameWithoutExtension}_{timestamp}{extension}";
    }

    /// <summary>
    /// Gets the content type based on file extension.
    /// </summary>
    private static string GetContentType(string fileName)
    {
        var extension = Path.GetExtension(fileName).ToLowerInvariant();
        return extension switch
        {
            ".pdf" => "application/pdf",
            ".doc" => "application/msword",
            ".docx" => "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls" => "application/vnd.ms-excel",
            ".xlsx" => "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ppt" => "application/vnd.ms-powerpoint",
            ".pptx" => "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".png" => "image/png",
            ".jpg" or ".jpeg" => "image/jpeg",
            ".gif" => "image/gif",
            ".svg" => "image/svg+xml",
            ".zip" => "application/zip",
            ".rar" => "application/x-rar-compressed",
            ".7z" => "application/x-7z-compressed",
            ".txt" => "text/plain",
            ".csv" => "text/csv",
            ".xml" => "application/xml",
            ".json" => "application/json",
            ".dwg" => "application/acad",
            ".dxf" => "application/dxf",
            _ => "application/octet-stream"
        };
    }
}
