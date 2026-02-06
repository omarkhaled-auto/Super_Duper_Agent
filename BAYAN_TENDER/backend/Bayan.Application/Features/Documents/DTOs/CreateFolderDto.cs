namespace Bayan.Application.Features.Documents.DTOs;

/// <summary>
/// Data transfer object for creating a folder.
/// </summary>
public class CreateFolderDto
{
    /// <summary>
    /// Name of the folder to create.
    /// </summary>
    public string FolderName { get; set; } = string.Empty;

    /// <summary>
    /// Parent folder path (empty for root level folders).
    /// </summary>
    public string? ParentPath { get; set; }
}
