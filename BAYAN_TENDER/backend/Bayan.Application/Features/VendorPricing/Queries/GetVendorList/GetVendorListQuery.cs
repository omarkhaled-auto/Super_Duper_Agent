using Bayan.Application.Common.Models;
using Bayan.Application.Features.VendorPricing.DTOs;
using MediatR;

namespace Bayan.Application.Features.VendorPricing.Queries.GetVendorList;

/// <summary>
/// Query to get a paginated list of vendors with pricing data.
/// </summary>
public class GetVendorListQuery : IRequest<PaginatedList<VendorListItemDto>>
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
    /// Optional search term for filtering by company name.
    /// </summary>
    public string? Search { get; set; }

    /// <summary>
    /// Optional filter by trade specialization.
    /// </summary>
    public string? TradeSpecialization { get; set; }

    /// <summary>
    /// If true, only return vendors with pricing data.
    /// </summary>
    public bool OnlyWithPricingData { get; set; } = false;

    /// <summary>
    /// Optional filter for active status.
    /// </summary>
    public bool? IsActive { get; set; }
}
