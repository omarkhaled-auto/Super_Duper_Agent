using MediatR;

namespace Bayan.Application.Features.Documents.Commands.DeleteDocument;

/// <summary>
/// Command to delete a document from a tender.
/// </summary>
public class DeleteDocumentCommand : IRequest<bool>
{
    /// <summary>
    /// ID of the tender the document belongs to.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the document to delete.
    /// </summary>
    public Guid DocumentId { get; set; }

    /// <summary>
    /// Whether to delete all versions of the document.
    /// </summary>
    public bool DeleteAllVersions { get; set; } = false;

    /// <summary>
    /// Initializes a new instance of the DeleteDocumentCommand.
    /// </summary>
    public DeleteDocumentCommand(Guid tenderId, Guid documentId, bool deleteAllVersions = false)
    {
        TenderId = tenderId;
        DocumentId = documentId;
        DeleteAllVersions = deleteAllVersions;
    }
}
