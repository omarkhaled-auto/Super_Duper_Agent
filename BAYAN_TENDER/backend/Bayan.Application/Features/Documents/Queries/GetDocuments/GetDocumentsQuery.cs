using Bayan.Application.Common.Models;
using Bayan.Application.Features.Documents.DTOs;
using MediatR;

namespace Bayan.Application.Features.Documents.Queries.GetDocuments;

/// <summary>
/// Query to get documents for a tender, optionally filtered by folder.
/// </summary>
public class GetDocumentsQuery : IRequest<PaginatedList<DocumentDto>>
{
    /// <summary>
    /// ID of the tender to get documents for.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Optional folder path to filter documents.
    /// </summary>
    public string? FolderPath { get; set; }

    /// <summary>
    /// Whether to include only latest versions (default: true).
    /// </summary>
    public bool LatestOnly { get; set; } = true;

    /// <summary>
    /// Page number (1-based).
    /// </summary>
    public int Page { get; set; } = 1;

    /// <summary>
    /// Number of items per page.
    /// </summary>
    public int PageSize { get; set; } = 20;

    /// <summary>
    /// Optional search term for filtering by file name.
    /// </summary>
    public string? Search { get; set; }
}
