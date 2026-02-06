using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.BidAnalysis.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using MatchType = Bayan.Domain.Enums.MatchType;

namespace Bayan.Application.Features.BidAnalysis.Commands.MarkAsExtraItem;

/// <summary>
/// Handler for MarkAsExtraItemCommand.
/// </summary>
public class MarkAsExtraItemCommandHandler : IRequestHandler<MarkAsExtraItemCommand, BidItemMatchDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ILogger<MarkAsExtraItemCommandHandler> _logger;

    public MarkAsExtraItemCommandHandler(
        IApplicationDbContext context,
        ILogger<MarkAsExtraItemCommandHandler> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task<BidItemMatchDto> Handle(MarkAsExtraItemCommand request, CancellationToken cancellationToken)
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

        // Mark as extra item
        bidPricing.BoqItemId = null;
        bidPricing.MatchType = MatchType.ExtraItem;
        bidPricing.MatchConfidence = null;
        bidPricing.IsIncludedInTotal = request.IncludeInTotal;
        bidPricing.Notes = request.Notes ?? bidPricing.Notes;

        await _context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation(
            "Marked bid item {ItemId} as extra item for bid {BidId}. Include in total: {IncludeInTotal}",
            request.ItemId, request.BidId, request.IncludeInTotal);

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
            MatchedBoqItemId = null,
            MatchedBoqItemNumber = null,
            MatchedBoqDescription = null,
            MatchedBoqQuantity = null,
            MatchedBoqUom = null,
            MatchType = MatchType.ExtraItem,
            Confidence = 0,
            NeedsReview = false
        };
    }
}
