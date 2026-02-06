using Bayan.Application.Features.Documents.DTOs;
using MediatR;

namespace Bayan.Application.Features.Documents.Queries.GetFolders;

/// <summary>
/// Query to get all folders for a tender.
/// </summary>
public class GetFoldersQuery : IRequest<IReadOnlyList<FolderDto>>
{
    /// <summary>
    /// ID of the tender to get folders for.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Initializes a new instance of the GetFoldersQuery.
    /// </summary>
    public GetFoldersQuery(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
