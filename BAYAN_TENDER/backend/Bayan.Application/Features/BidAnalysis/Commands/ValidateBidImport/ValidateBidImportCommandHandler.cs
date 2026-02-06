using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.BidAnalysis.DTOs;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.BidAnalysis.Commands.ValidateBidImport;

/// <summary>
/// Handler for ValidateBidImportCommand.
/// Performs comprehensive validation of bid data before import.
/// </summary>
public class ValidateBidImportCommandHandler : IRequestHandler<ValidateBidImportCommand, ValidationResultDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ILogger<ValidateBidImportCommandHandler> _logger;

    public ValidateBidImportCommandHandler(
        IApplicationDbContext context,
        ILogger<ValidateBidImportCommandHandler> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task<ValidationResultDto> Handle(ValidateBidImportCommand request, CancellationToken cancellationToken)
    {
        _logger.LogInformation("Starting bid validation for submission {BidSubmissionId}", request.BidSubmissionId);

        // Load bid submission with pricing data
        var bidSubmission = await _context.BidSubmissions
            .Include(b => b.BidPricings)
                .ThenInclude(bp => bp.BoqItem)
            .FirstOrDefaultAsync(b => b.Id == request.BidSubmissionId && b.TenderId == request.TenderId, cancellationToken);

        if (bidSubmission == null)
        {
            throw new NotFoundException($"Bid submission with ID {request.BidSubmissionId} not found for tender {request.TenderId}.");
        }

        // Load master BOQ items for coverage check
        var masterBoqItems = await _context.BoqItems
            .AsNoTracking()
            .Where(b => b.TenderId == request.TenderId)
            .ToListAsync(cancellationToken);

        var result = new ValidationResultDto
        {
            BidSubmissionId = bidSubmission.Id,
            TenderId = request.TenderId,
            TotalItemCount = bidSubmission.BidPricings.Count,
            ValidatedAt = DateTime.UtcNow,
            Issues = new List<ValidationIssueDto>()
        };

        // Perform formula check
        result.FormulaCheck = PerformFormulaCheck(bidSubmission.BidPricings.ToList(), request.FormulaTolerancePercent, result.Issues);

        // Perform data validation
        result.DataValidation = PerformDataValidation(bidSubmission.BidPricings.ToList(), result.Issues);

        // Perform coverage check
        result.CoverageCheck = PerformCoverageCheck(bidSubmission.BidPricings.ToList(), masterBoqItems, result.Issues);

        // Perform outlier detection if requested and other bids exist
        if (request.DetectOutliers)
        {
            result.OutlierDetection = await PerformOutlierDetectionAsync(
                request.TenderId,
                bidSubmission.Id,
                bidSubmission.BidPricings.ToList(),
                request.OutlierThresholdPercent,
                result.Issues,
                cancellationToken);
        }

        // Calculate summary counts
        result.ErrorCount = result.Issues.Count(i => i.Severity == ValidationIssueSeverity.Error);
        result.WarningCount = result.Issues.Count(i => i.Severity == ValidationIssueSeverity.Warning);
        result.InfoCount = result.Issues.Count(i => i.Severity == ValidationIssueSeverity.Info);
        result.ValidCount = result.TotalItemCount - result.ErrorCount;

        _logger.LogInformation(
            "Completed bid validation for submission {BidSubmissionId}: {ValidCount} valid, {ErrorCount} errors, {WarningCount} warnings",
            request.BidSubmissionId, result.ValidCount, result.ErrorCount, result.WarningCount);

        return result;
    }

    private FormulaCheckResultDto PerformFormulaCheck(
        List<Domain.Entities.BidPricing> pricings,
        decimal tolerancePercent,
        List<ValidationIssueDto> issues)
    {
        var result = new FormulaCheckResultDto
        {
            TolerancePercent = tolerancePercent,
            Errors = new List<FormulaErrorDto>()
        };

        foreach (var pricing in pricings)
        {
            // Skip items without complete data
            if (!pricing.BidderQuantity.HasValue || !pricing.NativeUnitRate.HasValue || !pricing.NativeAmount.HasValue)
            {
                continue;
            }

            result.ItemsChecked++;

            var calculatedAmount = pricing.BidderQuantity.Value * pricing.NativeUnitRate.Value;
            var providedAmount = pricing.NativeAmount.Value;

            // Calculate deviation percentage
            decimal deviationPercent = 0;
            if (providedAmount != 0)
            {
                deviationPercent = Math.Abs((calculatedAmount - providedAmount) / providedAmount) * 100;
            }
            else if (calculatedAmount != 0)
            {
                deviationPercent = 100; // 100% error if provided is 0 but calculated is not
            }

            if (deviationPercent <= tolerancePercent)
            {
                result.ItemsPassed++;
            }
            else
            {
                result.ItemsFailed++;

                var error = new FormulaErrorDto
                {
                    ItemId = pricing.Id,
                    ItemNumber = pricing.BidderItemNumber ?? pricing.BoqItem?.ItemNumber ?? "N/A",
                    Quantity = pricing.BidderQuantity,
                    UnitRate = pricing.NativeUnitRate,
                    AmountProvided = providedAmount,
                    AmountCalculated = calculatedAmount,
                    DeviationPercent = deviationPercent
                };

                result.Errors.Add(error);

                issues.Add(new ValidationIssueDto
                {
                    Severity = ValidationIssueSeverity.Warning,
                    Code = "FORMULA_ERROR",
                    Message = $"Formula mismatch: Qty ({pricing.BidderQuantity}) x Rate ({pricing.NativeUnitRate:N2}) = {calculatedAmount:N2}, but provided amount is {providedAmount:N2} ({deviationPercent:N1}% deviation)",
                    ItemId = pricing.Id,
                    ItemNumber = error.ItemNumber,
                    Field = "NativeAmount",
                    ExpectedValue = calculatedAmount.ToString("N2"),
                    ActualValue = providedAmount.ToString("N2"),
                    CanAutoCorrect = true,
                    SuggestedCorrection = calculatedAmount.ToString("N2")
                });
            }
        }

        return result;
    }

    private DataValidationResultDto PerformDataValidation(
        List<Domain.Entities.BidPricing> pricings,
        List<ValidationIssueDto> issues)
    {
        var result = new DataValidationResultDto
        {
            NegativeValueItems = new List<Guid>(),
            ZeroRateItems = new List<Guid>()
        };

        foreach (var pricing in pricings)
        {
            bool hasIssue = false;

            // Check for negative values
            if (pricing.NativeUnitRate.HasValue && pricing.NativeUnitRate.Value < 0)
            {
                result.NegativeValueCount++;
                result.NegativeValueItems.Add(pricing.Id);
                hasIssue = true;

                issues.Add(new ValidationIssueDto
                {
                    Severity = ValidationIssueSeverity.Error,
                    Code = "NEGATIVE_RATE",
                    Message = "Unit rate cannot be negative",
                    ItemId = pricing.Id,
                    ItemNumber = pricing.BidderItemNumber ?? pricing.BoqItem?.ItemNumber ?? "N/A",
                    Field = "NativeUnitRate",
                    ExpectedValue = "> 0",
                    ActualValue = pricing.NativeUnitRate.Value.ToString("N2"),
                    CanAutoCorrect = false
                });
            }

            if (pricing.NativeAmount.HasValue && pricing.NativeAmount.Value < 0)
            {
                result.NegativeValueCount++;
                result.NegativeValueItems.Add(pricing.Id);
                hasIssue = true;

                issues.Add(new ValidationIssueDto
                {
                    Severity = ValidationIssueSeverity.Error,
                    Code = "NEGATIVE_AMOUNT",
                    Message = "Amount cannot be negative",
                    ItemId = pricing.Id,
                    ItemNumber = pricing.BidderItemNumber ?? pricing.BoqItem?.ItemNumber ?? "N/A",
                    Field = "NativeAmount",
                    ExpectedValue = ">= 0",
                    ActualValue = pricing.NativeAmount.Value.ToString("N2"),
                    CanAutoCorrect = false
                });
            }

            if (pricing.BidderQuantity.HasValue && pricing.BidderQuantity.Value < 0)
            {
                result.NegativeValueCount++;
                result.NegativeValueItems.Add(pricing.Id);
                hasIssue = true;

                issues.Add(new ValidationIssueDto
                {
                    Severity = ValidationIssueSeverity.Error,
                    Code = "NEGATIVE_QUANTITY",
                    Message = "Quantity cannot be negative",
                    ItemId = pricing.Id,
                    ItemNumber = pricing.BidderItemNumber ?? pricing.BoqItem?.ItemNumber ?? "N/A",
                    Field = "BidderQuantity",
                    ExpectedValue = ">= 0",
                    ActualValue = pricing.BidderQuantity.Value.ToString("N2"),
                    CanAutoCorrect = false
                });
            }

            // Check for zero rates (warning only)
            if (pricing.NativeUnitRate.HasValue && pricing.NativeUnitRate.Value == 0 && !pricing.IsNoBid)
            {
                result.ZeroRateCount++;
                result.ZeroRateItems.Add(pricing.Id);

                issues.Add(new ValidationIssueDto
                {
                    Severity = ValidationIssueSeverity.Warning,
                    Code = "ZERO_RATE",
                    Message = "Unit rate is zero. Is this intentional?",
                    ItemId = pricing.Id,
                    ItemNumber = pricing.BidderItemNumber ?? pricing.BoqItem?.ItemNumber ?? "N/A",
                    Field = "NativeUnitRate",
                    ExpectedValue = "> 0",
                    ActualValue = "0",
                    CanAutoCorrect = false
                });
            }

            // Check for missing required fields
            if (!pricing.NativeUnitRate.HasValue && !pricing.IsNoBid)
            {
                result.MissingFieldCount++;
                hasIssue = true;

                issues.Add(new ValidationIssueDto
                {
                    Severity = ValidationIssueSeverity.Warning,
                    Code = "MISSING_RATE",
                    Message = "Unit rate is missing",
                    ItemId = pricing.Id,
                    ItemNumber = pricing.BidderItemNumber ?? pricing.BoqItem?.ItemNumber ?? "N/A",
                    Field = "NativeUnitRate",
                    CanAutoCorrect = false
                });
            }

            if (!hasIssue)
            {
                result.ValidItems++;
            }
        }

        return result;
    }

    private CoverageCheckResultDto PerformCoverageCheck(
        List<Domain.Entities.BidPricing> pricings,
        List<Domain.Entities.BoqItem> masterItems,
        List<ValidationIssueDto> issues)
    {
        var result = new CoverageCheckResultDto
        {
            MasterBoqItemCount = masterItems.Count,
            UnmatchedMasterItemIds = new List<Guid>(),
            ExtraItemIds = new List<Guid>()
        };

        var matchedMasterIds = pricings
            .Where(p => p.BoqItemId.HasValue)
            .Select(p => p.BoqItemId!.Value)
            .ToHashSet();

        // Find unmatched master items
        foreach (var masterItem in masterItems)
        {
            if (matchedMasterIds.Contains(masterItem.Id))
            {
                result.MatchedItemCount++;
            }
            else
            {
                result.UnmatchedMasterItemCount++;
                result.UnmatchedMasterItemIds.Add(masterItem.Id);

                issues.Add(new ValidationIssueDto
                {
                    Severity = ValidationIssueSeverity.Warning,
                    Code = "UNMATCHED_MASTER_ITEM",
                    Message = $"Master BOQ item not matched in bid",
                    ItemId = masterItem.Id,
                    ItemNumber = masterItem.ItemNumber,
                    CanAutoCorrect = false
                });
            }
        }

        // Find extra items (not in master BOQ)
        var extraItems = pricings.Where(p => !p.BoqItemId.HasValue).ToList();
        result.ExtraItemCount = extraItems.Count;
        result.ExtraItemIds = extraItems.Select(p => p.Id).ToList();

        foreach (var extra in extraItems)
        {
            issues.Add(new ValidationIssueDto
            {
                Severity = ValidationIssueSeverity.Info,
                Code = "EXTRA_ITEM",
                Message = "Item not matched to master BOQ (may be an additional item from bidder)",
                ItemId = extra.Id,
                ItemNumber = extra.BidderItemNumber ?? "N/A",
                CanAutoCorrect = false
            });
        }

        // Coverage warning if below 90%
        if (result.CoveragePercent < 90 && masterItems.Count > 0)
        {
            issues.Add(new ValidationIssueDto
            {
                Severity = ValidationIssueSeverity.Warning,
                Code = "LOW_COVERAGE",
                Message = $"BOQ coverage is only {result.CoveragePercent:N1}%. {result.UnmatchedMasterItemCount} master items are not matched.",
                CanAutoCorrect = false
            });
        }

        return result;
    }

    private async Task<OutlierDetectionResultDto?> PerformOutlierDetectionAsync(
        Guid tenderId,
        Guid currentBidId,
        List<Domain.Entities.BidPricing> pricings,
        decimal thresholdPercent,
        List<ValidationIssueDto> issues,
        CancellationToken cancellationToken)
    {
        // Get other imported bids for comparison
        var otherBidPricings = await _context.BidSubmissions
            .Where(b => b.TenderId == tenderId
                && b.Id != currentBidId
                && b.ImportStatus == BidImportStatus.Imported)
            .SelectMany(b => b.BidPricings)
            .Where(p => p.BoqItemId.HasValue && p.NormalizedUnitRate.HasValue)
            .GroupBy(p => p.BoqItemId)
            .Select(g => new
            {
                BoqItemId = g.Key,
                AverageRate = g.Average(p => p.NormalizedUnitRate!.Value),
                Count = g.Count()
            })
            .ToListAsync(cancellationToken);

        if (otherBidPricings.Count == 0)
        {
            return null; // No other bids to compare against
        }

        var result = new OutlierDetectionResultDto
        {
            ComparableBidCount = otherBidPricings.Select(p => p.Count).DefaultIfEmpty(0).Max(),
            Outliers = new List<OutlierItemDto>()
        };

        var averageRates = otherBidPricings.ToDictionary(p => p.BoqItemId!.Value, p => p.AverageRate);

        foreach (var pricing in pricings.Where(p => p.BoqItemId.HasValue && p.NormalizedUnitRate.HasValue))
        {
            if (!averageRates.TryGetValue(pricing.BoqItemId!.Value, out var avgRate) || avgRate == 0)
            {
                continue;
            }

            var bidRate = pricing.NormalizedUnitRate!.Value;
            var deviationPercent = ((bidRate - avgRate) / avgRate) * 100;

            if (Math.Abs(deviationPercent) > thresholdPercent)
            {
                result.OutlierCount++;
                var isHighOutlier = deviationPercent > 0;

                if (isHighOutlier)
                {
                    result.HighOutlierCount++;
                }
                else
                {
                    result.LowOutlierCount++;
                }

                result.Outliers.Add(new OutlierItemDto
                {
                    ItemId = pricing.Id,
                    ItemNumber = pricing.BidderItemNumber ?? pricing.BoqItem?.ItemNumber ?? "N/A",
                    BidRate = bidRate,
                    AverageRate = avgRate,
                    DeviationPercent = deviationPercent,
                    IsHighOutlier = isHighOutlier
                });

                issues.Add(new ValidationIssueDto
                {
                    Severity = ValidationIssueSeverity.Warning,
                    Code = isHighOutlier ? "HIGH_OUTLIER" : "LOW_OUTLIER",
                    Message = $"Rate is {Math.Abs(deviationPercent):N1}% {(isHighOutlier ? "above" : "below")} average ({avgRate:N2})",
                    ItemId = pricing.Id,
                    ItemNumber = pricing.BidderItemNumber ?? pricing.BoqItem?.ItemNumber ?? "N/A",
                    Field = "NormalizedUnitRate",
                    ExpectedValue = avgRate.ToString("N2"),
                    ActualValue = bidRate.ToString("N2"),
                    CanAutoCorrect = false
                });
            }
        }

        return result;
    }
}
