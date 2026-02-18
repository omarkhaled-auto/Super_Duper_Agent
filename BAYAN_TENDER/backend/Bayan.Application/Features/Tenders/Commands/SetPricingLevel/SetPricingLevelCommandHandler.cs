using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Commands.SetPricingLevel;

/// <summary>
/// Handler for SetPricingLevelCommand.
/// Validates that no bids have been submitted before allowing the change.
/// </summary>
public class SetPricingLevelCommandHandler : IRequestHandler<SetPricingLevelCommand, SetPricingLevelResult?>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;

    public SetPricingLevelCommandHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _currentUserService = currentUserService;
    }

    public async Task<SetPricingLevelResult?> Handle(
        SetPricingLevelCommand request,
        CancellationToken cancellationToken)
    {
        var tender = await _context.Tenders
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            return null;
        }

        // Check if any bids have been submitted — cannot change pricing level after that
        var hasBids = await _context.BidSubmissions
            .AnyAsync(bs => bs.TenderId == request.TenderId, cancellationToken);

        if (hasBids)
        {
            throw new InvalidOperationException(
                "Cannot change pricing level after bids have been submitted.");
        }

        // Update pricing level
        tender.PricingLevel = request.PricingLevel;
        tender.UpdatedAt = DateTime.UtcNow;
        tender.LastModifiedBy = _currentUserService.UserId;
        tender.LastModifiedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync(cancellationToken);

        // Count priceable nodes at the new level
        var priceableNodeCount = await CountPriceableNodesAsync(
            request.TenderId, request.PricingLevel, cancellationToken);

        return new SetPricingLevelResult
        {
            TenderId = request.TenderId,
            PricingLevel = request.PricingLevel,
            PriceableNodeCount = priceableNodeCount
        };
    }

    private async Task<int> CountPriceableNodesAsync(
        Guid tenderId, PricingLevel level, CancellationToken ct)
    {
        return level switch
        {
            PricingLevel.Bill => await _context.BoqSections
                .CountAsync(s => s.TenderId == tenderId && s.ParentSectionId == null, ct),

            PricingLevel.Item => await _context.BoqItems
                .CountAsync(i => i.TenderId == tenderId && i.ParentItemId == null, ct),

            PricingLevel.SubItem => await _context.BoqItems
                .CountAsync(i => i.TenderId == tenderId && !i.IsGroup, ct),

            _ => 0
        };
    }
}
