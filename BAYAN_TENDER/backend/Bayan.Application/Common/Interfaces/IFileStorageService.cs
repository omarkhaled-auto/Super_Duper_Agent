namespace Bayan.Application.Common.Interfaces;

/// <summary>
/// Interface for file storage operations (MinIO/S3 compatible).
/// </summary>
public interface IFileStorageService
{
    /// <summary>
    /// Uploads a file to storage.
    /// </summary>
    /// <param name="stream">File content stream.</param>
    /// <param name="fileName">Original file name.</param>
    /// <param name="contentType">MIME content type.</param>
    /// <param name="path">Storage path (e.g., "tender-documents/{tenderId}/{folder}").</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>The full path to the stored file.</returns>
    Task<string> UploadFileAsync(
        Stream stream,
        string fileName,
        string contentType,
        string path,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Downloads a file from storage.
    /// </summary>
    /// <param name="filePath">Full path to the file in storage.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Stream containing the file content.</returns>
    Task<Stream> DownloadFileAsync(
        string filePath,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Generates a presigned URL for downloading a file.
    /// </summary>
    /// <param name="filePath">Full path to the file in storage.</param>
    /// <param name="expiry">URL expiry duration.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>Presigned URL for file download.</returns>
    Task<string> GetPresignedUrlAsync(
        string filePath,
        TimeSpan expiry,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes a file from storage.
    /// </summary>
    /// <param name="filePath">Full path to the file in storage.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task DeleteFileAsync(
        string filePath,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Lists all files in a given path/prefix.
    /// </summary>
    /// <param name="path">Path prefix to list files from.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>List of file information.</returns>
    Task<IReadOnlyList<StorageFileInfo>> ListFilesAsync(
        string path,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Checks if a file exists in storage.
    /// </summary>
    /// <param name="filePath">Full path to the file in storage.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>True if the file exists, false otherwise.</returns>
    Task<bool> FileExistsAsync(
        string filePath,
        CancellationToken cancellationToken = default);
}

/// <summary>
/// Represents file information from storage.
/// </summary>
public record StorageFileInfo(
    string FileName,
    string FilePath,
    long Size,
    string ContentType,
    DateTime LastModified);
