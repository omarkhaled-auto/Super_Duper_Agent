using Bayan.Application.Features.Portal.DTOs;
using MediatR;

namespace Bayan.Application.Features.Portal.Documents;

/// <summary>
/// Query to get documents accessible to a qualified bidder.
/// </summary>
public class GetPortalDocumentsQuery : IRequest<List<PortalDocumentDto>>
{
    /// <summary>
    /// Tender unique identifier.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bidder ID for access validation.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Optional folder path filter.
    /// </summary>
    public string? FolderPath { get; set; }
}
