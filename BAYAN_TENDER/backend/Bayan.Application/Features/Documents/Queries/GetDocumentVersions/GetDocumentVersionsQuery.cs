using Bayan.Application.Features.Documents.DTOs;
using MediatR;

namespace Bayan.Application.Features.Documents.Queries.GetDocumentVersions;

/// <summary>
/// Query to get all versions of a document.
/// </summary>
public class GetDocumentVersionsQuery : IRequest<IReadOnlyList<DocumentDto>>
{
    /// <summary>
    /// ID of the tender the document belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of any version of the document.
    /// </summary>
    public Guid DocumentId { get; set; }

    /// <summary>
    /// Initializes a new instance of the GetDocumentVersionsQuery.
    /// </summary>
    public GetDocumentVersionsQuery(Guid tenderId, Guid documentId)
    {
        TenderId = tenderId;
        DocumentId = documentId;
    }
}
