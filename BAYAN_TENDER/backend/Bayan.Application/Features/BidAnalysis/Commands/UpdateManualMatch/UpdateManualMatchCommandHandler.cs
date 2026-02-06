using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.BidAnalysis.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using MatchType = Bayan.Domain.Enums.MatchType;

namespace Bayan.Application.Features.BidAnalysis.Commands.UpdateManualMatch;

/// <summary>
/// Handler for UpdateManualMatchCommand.
/// </summary>
public class UpdateManualMatchCommandHandler : IRequestHandler<UpdateManualMatchCommand, BidItemMatchDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ILogger<UpdateManualMatchCommandHandler> _logger;

    public UpdateManualMatchCommandHandler(
        IApplicationDbContext context,
        ILogger<UpdateManualMatchCommandHandler> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task<BidItemMatchDto> Handle(UpdateManualMatchCommand request, CancellationToken cancellationToken)
    {
        // Get bid submission
        var bid = await _context.BidSubmissions
            .FirstOrDefaultAsync(b => b.Id == request.BidId && b.TenderId == request.TenderId, cancellationToken);

        if (bid == null)
        {
            throw new NotFoundException("BidSubmission", request.BidId);
        }

        // Get the bid pricing item
        var bidPricing = await _context.BidPricings
            .FirstOrDefaultAsync(bp => bp.Id == request.ItemId && bp.BidSubmissionId == request.BidId, cancellationToken);

        if (bidPricing == null)
        {
            throw new NotFoundException("BidPricing", request.ItemId);
        }

        // Get the BOQ item to match to
        var boqItem = await _context.BoqItems
            .Include(b => b.Section)
            .FirstOrDefaultAsync(b => b.Id == request.BoqItemId && b.TenderId == request.TenderId, cancellationToken);

        if (boqItem == null)
        {
            throw new NotFoundException("BoqItem", request.BoqItemId);
        }

        // Check if this BOQ item is already matched to another bid item
        var existingMatch = await _context.BidPricings
            .Where(bp => bp.BidSubmissionId == request.BidId &&
                         bp.BoqItemId == request.BoqItemId &&
                         bp.Id != request.ItemId)
            .FirstOrDefaultAsync(cancellationToken);

        if (existingMatch != null)
        {
            throw new InvalidOperationException(
                $"BOQ item '{boqItem.ItemNumber}' is already matched to another bid item. " +
                "Please unmatch the existing item first or choose a different BOQ item.");
        }

        // Update the bid pricing with manual match
        bidPricing.BoqItemId = boqItem.Id;
        bidPricing.MatchType = MatchType.ManualMatch;
        bidPricing.MatchConfidence = 100; // Manual match is always 100% confidence
        bidPricing.Notes = request.Notes ?? bidPricing.Notes;

        await _context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation(
            "Manually matched bid item {ItemId} to BOQ item {BoqItemId} for bid {BidId}",
            request.ItemId, request.BoqItemId, request.BidId);

        return new BidItemMatchDto
        {
            RowIndex = 0, // Not applicable for persisted items
            BidItemNumber = bidPricing.BidderItemNumber,
            BidDescription = bidPricing.BidderDescription,
            BidQuantity = bidPricing.BidderQuantity,
            BidUom = bidPricing.BidderUom,
            BidUnitRate = bidPricing.NativeUnitRate,
            BidAmount = bidPricing.NativeAmount,
            Currency = bidPricing.NativeCurrency,
            MatchedBoqItemId = boqItem.Id,
            MatchedBoqItemNumber = boqItem.ItemNumber,
            MatchedBoqDescription = boqItem.Description,
            MatchedBoqQuantity = boqItem.Quantity,
            MatchedBoqUom = boqItem.Uom,
            MatchType = MatchType.ManualMatch,
            Confidence = 100,
            NeedsReview = false
        };
    }
}
