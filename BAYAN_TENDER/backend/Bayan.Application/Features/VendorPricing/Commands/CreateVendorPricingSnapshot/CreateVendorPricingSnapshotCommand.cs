using Bayan.Application.Features.VendorPricing.DTOs;
using MediatR;

namespace Bayan.Application.Features.VendorPricing.Commands.CreateVendorPricingSnapshot;

/// <summary>
/// Command to create a vendor pricing snapshot from bid pricing data.
/// Typically triggered after a successful bid import.
/// </summary>
public class CreateVendorPricingSnapshotCommand : IRequest<VendorPricingSnapshotDto>
{
    /// <summary>
    /// Bid submission ID to create snapshot from.
    /// </summary>
    public Guid BidSubmissionId { get; set; }

    /// <summary>
    /// Optional: Override the snapshot date (defaults to current UTC time).
    /// </summary>
    public DateTime? SnapshotDate { get; set; }
}
