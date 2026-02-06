using Bayan.Application.Features.Documents.DTOs;
using MediatR;

namespace Bayan.Application.Features.Documents.Commands.CreateFolder;

/// <summary>
/// Command to create a new folder for a tender.
/// Note: Folders in this system are virtual - they exist only when documents are uploaded to them.
/// This command validates the folder name and returns folder information.
/// </summary>
public class CreateFolderCommand : IRequest<FolderDto>
{
    /// <summary>
    /// ID of the tender to create the folder in.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Name of the folder to create.
    /// </summary>
    public string FolderName { get; set; } = string.Empty;

    /// <summary>
    /// Parent folder path (empty for root level folders).
    /// </summary>
    public string? ParentPath { get; set; }
}
