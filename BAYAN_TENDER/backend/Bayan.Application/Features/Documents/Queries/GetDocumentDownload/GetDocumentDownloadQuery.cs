using Bayan.Application.Features.Documents.DTOs;
using MediatR;

namespace Bayan.Application.Features.Documents.Queries.GetDocumentDownload;

/// <summary>
/// Query to get a presigned download URL for a document.
/// </summary>
public class GetDocumentDownloadQuery : IRequest<DocumentDownloadDto?>
{
    /// <summary>
    /// ID of the tender the document belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the document to download.
    /// </summary>
    public Guid DocumentId { get; set; }

    /// <summary>
    /// Initializes a new instance of the GetDocumentDownloadQuery.
    /// </summary>
    public GetDocumentDownloadQuery(Guid tenderId, Guid documentId)
    {
        TenderId = tenderId;
        DocumentId = documentId;
    }
}
