using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.BidAnalysis.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.BidAnalysis.Commands.NormalizeBid;

/// <summary>
/// Handler for NormalizeBidCommand.
/// Applies FX rate conversion and UOM normalization to bid pricing items.
/// </summary>
public class NormalizeBidCommandHandler : IRequestHandler<NormalizeBidCommand, NormalizationResultDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IUomConversionService _uomConversionService;
    private readonly ILogger<NormalizeBidCommandHandler> _logger;

    public NormalizeBidCommandHandler(
        IApplicationDbContext context,
        IUomConversionService uomConversionService,
        ILogger<NormalizeBidCommandHandler> logger)
    {
        _context = context;
        _uomConversionService = uomConversionService;
        _logger = logger;
    }

    public async Task<NormalizationResultDto> Handle(NormalizeBidCommand request, CancellationToken cancellationToken)
    {
        _logger.LogInformation("Starting bid normalization for submission {BidSubmissionId}", request.BidSubmissionId);

        // Load bid submission with related data
        var bidSubmission = await _context.BidSubmissions
            .Include(b => b.Bidder)
            .Include(b => b.BidPricings)
                .ThenInclude(bp => bp.BoqItem)
            .FirstOrDefaultAsync(b => b.Id == request.BidSubmissionId && b.TenderId == request.TenderId, cancellationToken);

        if (bidSubmission == null)
        {
            throw new NotFoundException($"Bid submission with ID {request.BidSubmissionId} not found for tender {request.TenderId}.");
        }

        // Load tender for base currency
        var tender = await _context.Tenders
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new NotFoundException($"Tender with ID {request.TenderId} not found.");
        }

        // Determine FX rate to use
        var fxRate = request.FxRate ?? bidSubmission.FxRate;
        var fxRateSource = request.FxRateSource ?? "System Default";
        var baseCurrency = tender.BaseCurrency ?? "AED";

        var result = new NormalizationResultDto
        {
            BidSubmissionId = bidSubmission.Id,
            TenderId = request.TenderId,
            BidderId = bidSubmission.BidderId,
            BidderCompanyName = bidSubmission.Bidder?.CompanyName ?? "Unknown",
            NativeCurrency = bidSubmission.NativeCurrency,
            BaseCurrency = baseCurrency,
            FxRate = fxRate,
            FxRateSource = fxRateSource,
            FxRateDate = DateTime.UtcNow,
            TotalItemsCount = bidSubmission.BidPricings.Count,
            Warnings = new List<string>()
        };

        decimal originalTotal = 0m;
        decimal normalizedTotal = 0m;
        int normalizedCount = 0;
        int convertibleMismatchCount = 0;
        int nonComparableCount = 0;

        foreach (var pricing in bidSubmission.BidPricings)
        {
            var normalizedItem = await NormalizeItemAsync(pricing, fxRate, baseCurrency, cancellationToken);
            result.NormalizedItems.Add(normalizedItem);

            // Track totals
            if (pricing.NativeAmount.HasValue)
            {
                originalTotal += pricing.NativeAmount.Value;
            }

            if (normalizedItem.NormalizedAmount.HasValue)
            {
                normalizedTotal += normalizedItem.NormalizedAmount.Value;
                normalizedCount++;
            }

            // Track UOM mismatches
            if (pricing.BoqItem != null && !string.IsNullOrEmpty(pricing.BidderUom))
            {
                var masterUom = pricing.BoqItem.Uom;
                if (!string.Equals(pricing.BidderUom, masterUom, StringComparison.OrdinalIgnoreCase))
                {
                    var canConvert = await _uomConversionService.CanConvertAsync(pricing.BidderUom, masterUom, cancellationToken);
                    var conversionFactor = canConvert
                        ? await _uomConversionService.GetConversionFactorAsync(pricing.BidderUom, masterUom, cancellationToken)
                        : null;

                    var mismatch = new UomMismatchDto
                    {
                        ItemId = pricing.BoqItem.Id,
                        ItemNumber = pricing.BoqItem.ItemNumber,
                        Description = pricing.BoqItem.Description,
                        BidderUom = pricing.BidderUom,
                        MasterUom = masterUom,
                        ConversionFactor = conversionFactor,
                        CanConvert = canConvert,
                        NonConvertibleReason = canConvert ? null : await _uomConversionService.GetNonConvertibleReasonAsync(pricing.BidderUom, masterUom, cancellationToken)
                    };

                    result.UomMismatches.Add(mismatch);

                    if (canConvert)
                    {
                        convertibleMismatchCount++;
                    }
                    else
                    {
                        nonComparableCount++;
                    }
                }
            }

            if (normalizedItem.IsNonComparable)
            {
                result.Warnings.Add($"Item {normalizedItem.ItemNumber}: {normalizedItem.NonComparableReason}");
            }

            // Update pricing entity if persisting
            if (request.PersistResults)
            {
                pricing.FxRateApplied = fxRate;
                pricing.UomConversionFactor = normalizedItem.UomConversionFactor;
                pricing.NormalizedUnitRate = normalizedItem.NormalizedUnitRate;
                pricing.NormalizedAmount = normalizedItem.NormalizedAmount;
                pricing.IsNonComparable = normalizedItem.IsNonComparable;
            }
        }

        result.OriginalTotalAmount = originalTotal;
        result.NormalizedTotalAmount = normalizedTotal;
        result.NormalizedItemsCount = normalizedCount;
        result.ConvertibleMismatchCount = convertibleMismatchCount;
        result.NonComparableCount = nonComparableCount;
        result.IsSuccess = true;

        // Update bid submission if persisting
        if (request.PersistResults)
        {
            bidSubmission.FxRate = fxRate;
            bidSubmission.NormalizedTotalAmount = normalizedTotal;
            await _context.SaveChangesAsync(cancellationToken);
            _logger.LogInformation("Persisted normalization results for bid submission {BidSubmissionId}", request.BidSubmissionId);
        }

        _logger.LogInformation(
            "Completed bid normalization for submission {BidSubmissionId}: {NormalizedCount}/{TotalCount} items normalized, {NonComparableCount} non-comparable",
            request.BidSubmissionId, normalizedCount, result.TotalItemsCount, nonComparableCount);

        return result;
    }

    private async Task<NormalizedItemDto> NormalizeItemAsync(
        Domain.Entities.BidPricing pricing,
        decimal fxRate,
        string baseCurrency,
        CancellationToken cancellationToken)
    {
        var item = new NormalizedItemDto
        {
            BidPricingId = pricing.Id,
            BoqItemId = pricing.BoqItemId,
            ItemNumber = pricing.BidderItemNumber ?? pricing.BoqItem?.ItemNumber ?? "N/A",
            Description = pricing.BidderDescription ?? pricing.BoqItem?.Description ?? "N/A",
            OriginalQuantity = pricing.BidderQuantity,
            OriginalUom = pricing.BidderUom,
            OriginalUnitRate = pricing.NativeUnitRate,
            OriginalAmount = pricing.NativeAmount,
            NativeCurrency = pricing.NativeCurrency,
            FxRateApplied = fxRate,
            BaseCurrency = baseCurrency
        };

        // Determine target UOM (master BOQ UOM if matched, otherwise bidder's UOM)
        var targetUom = pricing.BoqItem?.Uom ?? pricing.BidderUom;
        item.NormalizedUom = targetUom;

        // Calculate UOM conversion factor if needed
        decimal uomFactor = 1m;
        if (!string.IsNullOrEmpty(pricing.BidderUom) && !string.IsNullOrEmpty(targetUom))
        {
            if (!string.Equals(pricing.BidderUom, targetUom, StringComparison.OrdinalIgnoreCase))
            {
                var canConvert = await _uomConversionService.CanConvertAsync(pricing.BidderUom, targetUom, cancellationToken);
                if (canConvert)
                {
                    var factor = await _uomConversionService.GetConversionFactorAsync(pricing.BidderUom, targetUom, cancellationToken);
                    if (factor.HasValue)
                    {
                        uomFactor = factor.Value;
                    }
                }
                else
                {
                    // Mark as non-comparable
                    item.IsNonComparable = true;
                    item.NonComparableReason = await _uomConversionService.GetNonConvertibleReasonAsync(pricing.BidderUom, targetUom, cancellationToken);
                }
            }
        }

        item.UomConversionFactor = uomFactor;

        // Calculate normalized values
        // Normalized Unit Rate = Native Rate * FX Rate / UOM Factor
        // (Division by UOM factor because if bidder quotes in sqft and we convert to m2,
        //  the rate per m2 should be higher since m2 > sqft)
        if (pricing.NativeUnitRate.HasValue && !item.IsNonComparable)
        {
            // When converting rate: Rate_m2 = Rate_sqft / (sqft/m2) = Rate_sqft * (m2/sqft) = Rate_sqft / factor
            // If factor converts sqft -> m2, then rate in m2 = rate_sqft / factor
            item.NormalizedUnitRate = pricing.NativeUnitRate.Value * fxRate / uomFactor;
        }

        // Normalized Amount = Native Amount * FX Rate
        if (pricing.NativeAmount.HasValue && !item.IsNonComparable)
        {
            item.NormalizedAmount = pricing.NativeAmount.Value * fxRate;
        }

        return item;
    }
}
