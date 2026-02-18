using System.Text.Json;
using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.BidAnalysis.Commands.NormalizeBid;
using Bayan.Application.Features.BidAnalysis.Commands.ValidateBidImport;
using Bayan.Application.Features.BidAnalysis.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.BidAnalysis.Commands.ExecuteBidImport;

/// <summary>
/// Handler for ExecuteBidImportCommand.
/// Executes the final import of a bid submission, updating status and creating snapshots.
/// </summary>
public class ExecuteBidImportCommandHandler : IRequestHandler<ExecuteBidImportCommand, ImportResultDto>
{
    private readonly IApplicationDbContext _context;
    private readonly IMediator _mediator;
    private readonly ICurrentUserService _currentUserService;
    private readonly ILogger<ExecuteBidImportCommandHandler> _logger;

    public ExecuteBidImportCommandHandler(
        IApplicationDbContext context,
        IMediator mediator,
        ICurrentUserService currentUserService,
        ILogger<ExecuteBidImportCommandHandler> logger)
    {
        _context = context;
        _mediator = mediator;
        _currentUserService = currentUserService;
        _logger = logger;
    }

    public async Task<ImportResultDto> Handle(ExecuteBidImportCommand request, CancellationToken cancellationToken)
    {
        _logger.LogInformation("Starting bid import execution for submission {BidSubmissionId}", request.BidSubmissionId);

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

        // Load tender
        var tender = await _context.Tenders
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == request.TenderId, cancellationToken);

        if (tender == null)
        {
            throw new NotFoundException($"Tender with ID {request.TenderId} not found.");
        }

        var result = new ImportResultDto
        {
            BidSubmissionId = bidSubmission.Id,
            TenderId = request.TenderId,
            BidderId = bidSubmission.BidderId,
            BidderCompanyName = bidSubmission.Bidder?.CompanyName ?? "Unknown",
            NativeCurrency = bidSubmission.NativeCurrency,
            BaseCurrency = tender.BaseCurrency ?? "AED",
            ImportedAt = DateTime.UtcNow,
            ImportedBy = _currentUserService.UserId,
            Warnings = new List<string>()
        };

        try
        {
            // Step 1: Validate the bid
            var validationResult = await _mediator.Send(new ValidateBidImportCommand
            {
                TenderId = request.TenderId,
                BidSubmissionId = request.BidSubmissionId,
                DetectOutliers = true
            }, cancellationToken);

            // Check for blocking errors
            if (validationResult.ErrorCount > 0)
            {
                result.Status = ImportStatus.Failed;
                result.Warnings.Add($"Import blocked due to {validationResult.ErrorCount} validation error(s).");
                foreach (var error in validationResult.Issues.Where(i => i.Severity == ValidationIssueSeverity.Error).Take(5))
                {
                    result.Warnings.Add($"Error: {error.Message}");
                }
                return result;
            }

            // Check for warnings if not forcing import
            if (validationResult.WarningCount > 0 && !request.ForceImport)
            {
                result.Status = ImportStatus.Failed;
                result.Warnings.Add($"Import blocked due to {validationResult.WarningCount} validation warning(s). Use ForceImport=true to proceed.");
                foreach (var warning in validationResult.Issues.Where(i => i.Severity == ValidationIssueSeverity.Warning).Take(5))
                {
                    result.Warnings.Add($"Warning: {warning.Message}");
                }
                return result;
            }

            // Create validation summary
            result.ValidationSummary = new ValidationSummaryDto
            {
                TotalItems = validationResult.TotalItemCount,
                ValidItems = validationResult.ValidCount,
                WarningItems = validationResult.WarningCount,
                FormulaErrorCount = validationResult.FormulaCheck.ItemsFailed,
                NonComparableCount = bidSubmission.BidPricings.Count(p => p.IsNonComparable),
                CoveragePercent = validationResult.CoverageCheck.CoveragePercent
            };

            // Step 2: Normalize the bid (persist results)
            var normalizationResult = await _mediator.Send(new NormalizeBidCommand
            {
                TenderId = request.TenderId,
                BidSubmissionId = request.BidSubmissionId,
                FxRate = request.FxRate,
                PersistResults = true
            }, cancellationToken);

            result.FxRate = normalizationResult.FxRate;

            // Step 3: Calculate totals
            decimal totalNative = 0m;
            decimal totalNormalized = 0m;
            int itemsImported = 0;
            int itemsSkipped = 0;

            foreach (var pricing in bidSubmission.BidPricings)
            {
                if (pricing.NativeAmount.HasValue)
                {
                    // Only include in total if IsIncludedInTotal flag is set
                    // This respects the tender's pricing level (SubItem/Item/Bill)
                    if (pricing.IsIncludedInTotal)
                    {
                        totalNative += pricing.NativeAmount.Value;
                    }
                    itemsImported++;
                }
                else
                {
                    itemsSkipped++;
                }

                if (pricing.NormalizedAmount.HasValue && pricing.IsIncludedInTotal)
                {
                    totalNormalized += pricing.NormalizedAmount.Value;
                }

                // Mark formula errors
                pricing.HasFormulaError = validationResult.FormulaCheck.Errors
                    .Any(e => e.ItemId == pricing.Id);
            }

            result.ItemsImported = itemsImported;
            result.ItemsSkipped = itemsSkipped;
            result.TotalAmount = totalNative;
            result.NormalizedTotal = totalNormalized;

            // Step 4: Update bid submission status
            bidSubmission.ImportStatus = BidImportStatus.Imported;
            bidSubmission.ImportCompletedAt = DateTime.UtcNow;
            bidSubmission.ImportedBy = _currentUserService.UserId;
            bidSubmission.NativeTotalAmount = totalNative;
            bidSubmission.NormalizedTotalAmount = totalNormalized;
            bidSubmission.FxRate = normalizationResult.FxRate;
            bidSubmission.ValidationSummary = JsonSerializer.Serialize(result.ValidationSummary);

            // Step 5: Create vendor pricing snapshot if requested
            if (request.CreateVendorSnapshot)
            {
                var snapshot = await CreateVendorPricingSnapshotAsync(
                    bidSubmission,
                    tender.BaseCurrency ?? "AED",
                    totalNormalized,
                    cancellationToken);

                result.VendorPricingSnapshotId = snapshot.Id;
            }

            await _context.SaveChangesAsync(cancellationToken);

            // Determine final status
            if (validationResult.WarningCount > 0)
            {
                result.Status = ImportStatus.ImportedWithWarnings;
                result.Warnings.Add($"Imported with {validationResult.WarningCount} warning(s).");
            }
            else if (itemsSkipped > 0)
            {
                result.Status = ImportStatus.PartiallyImported;
                result.Warnings.Add($"{itemsSkipped} item(s) were skipped due to missing data.");
            }
            else
            {
                result.Status = ImportStatus.Imported;
            }

            _logger.LogInformation(
                "Completed bid import for submission {BidSubmissionId}: {ItemsImported} items imported, total {TotalAmount:N2} {Currency}",
                request.BidSubmissionId, itemsImported, totalNormalized, result.BaseCurrency);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to import bid submission {BidSubmissionId}", request.BidSubmissionId);

            // Update status to failed
            bidSubmission.ImportStatus = BidImportStatus.Failed;
            await _context.SaveChangesAsync(cancellationToken);

            result.Status = ImportStatus.Failed;
            result.Warnings.Add($"Import failed: {ex.Message}");
        }

        return result;
    }

    private async Task<VendorPricingSnapshot> CreateVendorPricingSnapshotAsync(
        BidSubmission bidSubmission,
        string baseCurrency,
        decimal totalAmount,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation("Creating vendor pricing snapshot for bid {BidSubmissionId}", bidSubmission.Id);

        var snapshot = new VendorPricingSnapshot
        {
            Id = Guid.NewGuid(),
            BidderId = bidSubmission.BidderId,
            TenderId = bidSubmission.TenderId,
            BidSubmissionId = bidSubmission.Id,
            SnapshotDate = DateTime.UtcNow,
            TenderBaseCurrency = baseCurrency,
            TotalBidAmount = totalAmount,
            TotalItemsCount = bidSubmission.BidPricings.Count
        };

        // Add snapshot to context
        _context.VendorPricingSnapshots.Add(snapshot);

        // Create item rates
        foreach (var pricing in bidSubmission.BidPricings.Where(p => p.NormalizedUnitRate.HasValue))
        {
            var itemRate = new VendorItemRate
            {
                Id = Guid.NewGuid(),
                SnapshotId = snapshot.Id,
                BoqItemId = pricing.BoqItemId,
                ItemDescription = pricing.BidderDescription ?? pricing.BoqItem?.Description ?? "N/A",
                Uom = pricing.BoqItem?.Uom ?? pricing.BidderUom ?? "N/A",
                NormalizedUnitRate = pricing.NormalizedUnitRate.Value,
                NormalizedCurrency = baseCurrency,
                Quantity = pricing.BidderQuantity,
                TotalAmount = pricing.NormalizedAmount
            };

            _context.VendorItemRates.Add(itemRate);
        }

        return snapshot;
    }
}
