using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using Bayan.Application.Features.VendorPricing.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.VendorPricing.Queries.GetVendorRates;

/// <summary>
/// Handler for GetVendorRatesQuery.
/// </summary>
public class GetVendorRatesQueryHandler
    : IRequestHandler<GetVendorRatesQuery, PaginatedList<VendorItemRateDto>>
{
    private readonly IApplicationDbContext _context;

    public GetVendorRatesQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<PaginatedList<VendorItemRateDto>> Handle(
        GetVendorRatesQuery request,
        CancellationToken cancellationToken)
    {
        var ratesQuery = _context.VendorItemRates
            .AsNoTracking()
            .Include(r => r.Snapshot)
                .ThenInclude(s => s.Tender)
            .Where(r => r.Snapshot.BidderId == request.BidderId);

        // Apply filters
        if (!string.IsNullOrWhiteSpace(request.ItemDescription))
        {
            var descTerm = request.ItemDescription.ToLower();
            ratesQuery = ratesQuery.Where(r => r.ItemDescription.ToLower().Contains(descTerm));
        }

        if (!string.IsNullOrWhiteSpace(request.Uom))
        {
            ratesQuery = ratesQuery.Where(r => r.Uom.ToLower() == request.Uom.ToLower());
        }

        if (request.TenderId.HasValue)
        {
            ratesQuery = ratesQuery.Where(r => r.Snapshot.TenderId == request.TenderId.Value);
        }

        IQueryable<VendorItemRateDto> projectedQuery;

        if (request.LatestOnly)
        {
            // Get only the latest rate for each item description + UOM combination
            projectedQuery = ratesQuery
                .GroupBy(r => new { r.ItemDescription, r.Uom })
                .Select(g => g.OrderByDescending(r => r.Snapshot.SnapshotDate).First())
                .OrderBy(r => r.ItemDescription)
                .Select(r => new VendorItemRateDto
                {
                    Id = r.Id,
                    ItemDescription = r.ItemDescription,
                    Uom = r.Uom,
                    Rate = r.NormalizedUnitRate,
                    Currency = r.NormalizedCurrency,
                    Quantity = r.Quantity,
                    TotalAmount = r.TotalAmount,
                    TenderReference = r.Snapshot.Tender != null ? r.Snapshot.Tender.Reference : "Unknown",
                    SnapshotDate = r.Snapshot.SnapshotDate,
                    BoqItemId = r.BoqItemId
                });
        }
        else
        {
            // Get all rates ordered by date
            projectedQuery = ratesQuery
                .OrderByDescending(r => r.Snapshot.SnapshotDate)
                .ThenBy(r => r.ItemDescription)
                .Select(r => new VendorItemRateDto
                {
                    Id = r.Id,
                    ItemDescription = r.ItemDescription,
                    Uom = r.Uom,
                    Rate = r.NormalizedUnitRate,
                    Currency = r.NormalizedCurrency,
                    Quantity = r.Quantity,
                    TotalAmount = r.TotalAmount,
                    TenderReference = r.Snapshot.Tender != null ? r.Snapshot.Tender.Reference : "Unknown",
                    SnapshotDate = r.Snapshot.SnapshotDate,
                    BoqItemId = r.BoqItemId
                });
        }

        return await PaginatedList<VendorItemRateDto>.CreateAsync(
            projectedQuery,
            request.Page,
            request.PageSize,
            cancellationToken);
    }
}
