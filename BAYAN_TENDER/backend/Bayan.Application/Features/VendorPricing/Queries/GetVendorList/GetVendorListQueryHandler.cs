using Bayan.Application.Common.Interfaces;
using Bayan.Application.Common.Models;
using Bayan.Application.Features.VendorPricing.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.VendorPricing.Queries.GetVendorList;

/// <summary>
/// Handler for GetVendorListQuery.
/// </summary>
public class GetVendorListQueryHandler
    : IRequestHandler<GetVendorListQuery, PaginatedList<VendorListItemDto>>
{
    private readonly IApplicationDbContext _context;

    public GetVendorListQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<PaginatedList<VendorListItemDto>> Handle(
        GetVendorListQuery request,
        CancellationToken cancellationToken)
    {
        var query = _context.Bidders.AsNoTracking();

        // Apply search filter
        if (!string.IsNullOrWhiteSpace(request.Search))
        {
            var searchTerm = request.Search.ToLower();
            query = query.Where(b => b.CompanyName.ToLower().Contains(searchTerm));
        }

        // Apply trade specialization filter
        if (!string.IsNullOrWhiteSpace(request.TradeSpecialization))
        {
            var tradeTerm = request.TradeSpecialization.ToLower();
            query = query.Where(b =>
                b.TradeSpecialization != null &&
                b.TradeSpecialization.ToLower().Contains(tradeTerm));
        }

        // Apply active status filter
        if (request.IsActive.HasValue)
        {
            query = query.Where(b => b.IsActive == request.IsActive.Value);
        }

        // If only vendors with pricing data
        if (request.OnlyWithPricingData)
        {
            var biddersWithPricing = await _context.VendorPricingSnapshots
                .AsNoTracking()
                .Select(s => s.BidderId)
                .Distinct()
                .ToListAsync(cancellationToken);

            query = query.Where(b => biddersWithPricing.Contains(b.Id));
        }

        // Project to DTO with aggregated pricing data
        var projectedQuery = query
            .OrderBy(b => b.CompanyName)
            .Select(b => new VendorListItemDto
            {
                BidderId = b.Id,
                CompanyName = b.CompanyName,
                ContactPerson = b.ContactPerson,
                Email = b.Email,
                TradeSpecialization = b.TradeSpecialization,
                IsActive = b.IsActive,
                SnapshotCount = _context.VendorPricingSnapshots
                    .Count(s => s.BidderId == b.Id),
                TenderCount = _context.VendorPricingSnapshots
                    .Where(s => s.BidderId == b.Id)
                    .Select(s => s.TenderId)
                    .Distinct()
                    .Count(),
                TotalBidValue = _context.VendorPricingSnapshots
                    .Where(s => s.BidderId == b.Id)
                    .Sum(s => s.TotalBidAmount),
                LastPricingDate = _context.VendorPricingSnapshots
                    .Where(s => s.BidderId == b.Id)
                    .OrderByDescending(s => s.SnapshotDate)
                    .Select(s => (DateTime?)s.SnapshotDate)
                    .FirstOrDefault()
            });

        return await PaginatedList<VendorListItemDto>.CreateAsync(
            projectedQuery,
            request.Page,
            request.PageSize,
            cancellationToken);
    }
}
