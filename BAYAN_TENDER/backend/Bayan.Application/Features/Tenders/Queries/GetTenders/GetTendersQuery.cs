using Bayan.Application.Common.Models;
using Bayan.Application.Features.Tenders.DTOs;
using Bayan.Domain.Enums;
using MediatR;

namespace Bayan.Application.Features.Tenders.Queries.GetTenders;

/// <summary>
/// Query for retrieving a paginated list of tenders with filtering options.
/// </summary>
public class GetTendersQuery : IRequest<PaginatedList<TenderListDto>>
{
    /// <summary>
    /// Page number (1-based).
    /// </summary>
    public int Page { get; set; } = 1;

    /// <summary>
    /// Number of items per page.
    /// </summary>
    public int PageSize { get; set; } = 10;

    /// <summary>
    /// Optional filter by tender status.
    /// </summary>
    public TenderStatus? Status { get; set; }

    /// <summary>
    /// Optional filter by client ID.
    /// </summary>
    public Guid? ClientId { get; set; }

    /// <summary>
    /// Optional filter by start date (tenders created on or after this date).
    /// </summary>
    public DateTime? DateFrom { get; set; }

    /// <summary>
    /// Optional filter by end date (tenders created on or before this date).
    /// </summary>
    public DateTime? DateTo { get; set; }

    /// <summary>
    /// Optional search term for filtering by title or reference.
    /// </summary>
    public string? Search { get; set; }

    /// <summary>
    /// Optional filter by tender type.
    /// </summary>
    public TenderType? TenderType { get; set; }

    /// <summary>
    /// Sort field (default: CreatedAt).
    /// </summary>
    public string SortBy { get; set; } = "CreatedAt";

    /// <summary>
    /// Sort direction (default: descending).
    /// </summary>
    public bool SortDescending { get; set; } = true;
}
