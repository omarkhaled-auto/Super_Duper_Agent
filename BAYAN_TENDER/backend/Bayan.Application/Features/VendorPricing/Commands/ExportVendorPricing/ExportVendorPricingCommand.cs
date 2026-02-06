using Bayan.Application.Features.VendorPricing.DTOs;
using MediatR;

namespace Bayan.Application.Features.VendorPricing.Commands.ExportVendorPricing;

/// <summary>
/// Command to export vendor pricing data to Excel.
/// </summary>
public class ExportVendorPricingCommand : IRequest<VendorPricingExportDto>
{
    /// <summary>
    /// Optional list of bidder IDs to export (null for all).
    /// </summary>
    public List<Guid>? BidderIds { get; set; }

    /// <summary>
    /// Optional start date for filtering data.
    /// </summary>
    public DateTime? FromDate { get; set; }

    /// <summary>
    /// Optional end date for filtering data.
    /// </summary>
    public DateTime? ToDate { get; set; }

    /// <summary>
    /// Optional trade specialization filter.
    /// </summary>
    public string? TradeSpecialization { get; set; }

    /// <summary>
    /// Optional tender ID filter.
    /// </summary>
    public Guid? TenderId { get; set; }

    /// <summary>
    /// Include item-level details (default: true).
    /// </summary>
    public bool IncludeItemDetails { get; set; } = true;

    /// <summary>
    /// Include summary sheet (default: true).
    /// </summary>
    public bool IncludeSummary { get; set; } = true;
}
