namespace Bayan.Application.Features.Documents.DTOs;

/// <summary>
/// Data transfer object for folder information.
/// </summary>
public class FolderDto
{
    /// <summary>
    /// Folder name/path.
    /// </summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Full path to the folder.
    /// </summary>
    public string Path { get; set; } = string.Empty;

    /// <summary>
    /// Number of documents in the folder.
    /// </summary>
    public int DocumentCount { get; set; }

    /// <summary>
    /// Total size of all documents in the folder.
    /// </summary>
    public long TotalSize { get; set; }

    /// <summary>
    /// Human-readable total size.
    /// </summary>
    public string TotalSizeFormatted { get; set; } = string.Empty;

    /// <summary>
    /// When the folder was created.
    /// </summary>
    public DateTime CreatedAt { get; set; }

    /// <summary>
    /// When the folder was last modified (most recent document upload).
    /// </summary>
    public DateTime? LastModifiedAt { get; set; }
}
