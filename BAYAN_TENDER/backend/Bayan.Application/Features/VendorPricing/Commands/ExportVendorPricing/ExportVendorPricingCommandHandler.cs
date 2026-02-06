using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.VendorPricing.DTOs;
using ClosedXML.Excel;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.VendorPricing.Commands.ExportVendorPricing;

/// <summary>
/// Handler for ExportVendorPricingCommand.
/// </summary>
public class ExportVendorPricingCommandHandler
    : IRequestHandler<ExportVendorPricingCommand, VendorPricingExportDto>
{
    private readonly IApplicationDbContext _context;

    public ExportVendorPricingCommandHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<VendorPricingExportDto> Handle(
        ExportVendorPricingCommand request,
        CancellationToken cancellationToken)
    {
        // Build query
        var query = _context.VendorPricingSnapshots
            .AsNoTracking()
            .Include(s => s.Bidder)
            .Include(s => s.Tender)
            .Include(s => s.ItemRates)
            .AsQueryable();

        if (request.BidderIds != null && request.BidderIds.Any())
        {
            query = query.Where(s => request.BidderIds.Contains(s.BidderId));
        }

        if (request.FromDate.HasValue)
        {
            query = query.Where(s => s.SnapshotDate >= request.FromDate.Value);
        }

        if (request.ToDate.HasValue)
        {
            query = query.Where(s => s.SnapshotDate <= request.ToDate.Value);
        }

        if (!string.IsNullOrWhiteSpace(request.TradeSpecialization))
        {
            query = query.Where(s =>
                s.Bidder.TradeSpecialization != null &&
                s.Bidder.TradeSpecialization.Contains(request.TradeSpecialization));
        }

        if (request.TenderId.HasValue)
        {
            query = query.Where(s => s.TenderId == request.TenderId.Value);
        }

        var snapshots = await query
            .OrderBy(s => s.Bidder.CompanyName)
            .ThenBy(s => s.SnapshotDate)
            .ToListAsync(cancellationToken);

        // Build export rows
        var exportRows = new List<VendorPricingExportRowDto>();

        foreach (var snapshot in snapshots)
        {
            if (request.IncludeItemDetails)
            {
                foreach (var rate in snapshot.ItemRates)
                {
                    exportRows.Add(new VendorPricingExportRowDto
                    {
                        VendorName = snapshot.Bidder.CompanyName,
                        Trade = snapshot.Bidder.TradeSpecialization,
                        TenderReference = snapshot.Tender?.Reference ?? "Unknown",
                        TenderTitle = snapshot.Tender?.Title ?? "Unknown",
                        Date = snapshot.SnapshotDate,
                        ItemDescription = rate.ItemDescription,
                        Uom = rate.Uom,
                        Rate = rate.NormalizedUnitRate,
                        Quantity = rate.Quantity,
                        TotalAmount = rate.TotalAmount,
                        Currency = rate.NormalizedCurrency
                    });
                }
            }
            else
            {
                // Add summary row per snapshot
                var avgRate = snapshot.ItemRates.Any()
                    ? snapshot.ItemRates.Average(r => r.NormalizedUnitRate)
                    : 0;

                exportRows.Add(new VendorPricingExportRowDto
                {
                    VendorName = snapshot.Bidder.CompanyName,
                    Trade = snapshot.Bidder.TradeSpecialization,
                    TenderReference = snapshot.Tender?.Reference ?? "Unknown",
                    TenderTitle = snapshot.Tender?.Title ?? "Unknown",
                    Date = snapshot.SnapshotDate,
                    ItemDescription = $"{snapshot.TotalItemsCount} items",
                    Uom = "N/A",
                    Rate = avgRate,
                    Quantity = null,
                    TotalAmount = snapshot.TotalBidAmount,
                    Currency = snapshot.TenderBaseCurrency
                });
            }
        }

        // Generate Excel file
        var content = GenerateExcelFile(exportRows, snapshots, request.IncludeSummary);

        var fileName = $"VendorPricing_{DateTime.UtcNow:yyyyMMdd_HHmmss}.xlsx";

        return new VendorPricingExportDto
        {
            FileName = fileName,
            Content = content,
            RecordCount = exportRows.Count,
            ExportedAt = DateTime.UtcNow
        };
    }

    private byte[] GenerateExcelFile(
        List<VendorPricingExportRowDto> rows,
        List<Domain.Entities.VendorPricingSnapshot> snapshots,
        bool includeSummary)
    {
        using var workbook = new XLWorkbook();

        // Summary sheet
        if (includeSummary)
        {
            var summarySheet = workbook.Worksheets.Add("Summary");

            // Title
            summarySheet.Cell(1, 1).Value = "Vendor Pricing Export Summary";
            summarySheet.Cell(1, 1).Style.Font.Bold = true;
            summarySheet.Cell(1, 1).Style.Font.FontSize = 16;
            summarySheet.Range(1, 1, 1, 4).Merge();

            summarySheet.Cell(3, 1).Value = "Export Date:";
            summarySheet.Cell(3, 2).Value = DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm:ss UTC");

            summarySheet.Cell(4, 1).Value = "Total Records:";
            summarySheet.Cell(4, 2).Value = rows.Count;

            summarySheet.Cell(5, 1).Value = "Total Vendors:";
            summarySheet.Cell(5, 2).Value = snapshots.Select(s => s.BidderId).Distinct().Count();

            summarySheet.Cell(6, 1).Value = "Total Tenders:";
            summarySheet.Cell(6, 2).Value = snapshots.Select(s => s.TenderId).Distinct().Count();

            summarySheet.Cell(7, 1).Value = "Total Bid Value:";
            summarySheet.Cell(7, 2).Value = snapshots.Sum(s => s.TotalBidAmount);
            summarySheet.Cell(7, 2).Style.NumberFormat.Format = "#,##0.00";

            // Vendor summary table
            summarySheet.Cell(9, 1).Value = "Vendor Summary";
            summarySheet.Cell(9, 1).Style.Font.Bold = true;

            summarySheet.Cell(10, 1).Value = "Vendor Name";
            summarySheet.Cell(10, 2).Value = "Trade";
            summarySheet.Cell(10, 3).Value = "Snapshots";
            summarySheet.Cell(10, 4).Value = "Total Value";
            summarySheet.Range(10, 1, 10, 4).Style.Font.Bold = true;
            summarySheet.Range(10, 1, 10, 4).Style.Fill.BackgroundColor = XLColor.LightGray;

            var vendorSummary = snapshots
                .GroupBy(s => new { s.BidderId, s.Bidder.CompanyName, s.Bidder.TradeSpecialization })
                .Select(g => new
                {
                    VendorName = g.Key.CompanyName,
                    Trade = g.Key.TradeSpecialization ?? "Unspecified",
                    SnapshotCount = g.Count(),
                    TotalValue = g.Sum(s => s.TotalBidAmount)
                })
                .OrderByDescending(v => v.TotalValue)
                .ToList();

            var row = 11;
            foreach (var vendor in vendorSummary)
            {
                summarySheet.Cell(row, 1).Value = vendor.VendorName;
                summarySheet.Cell(row, 2).Value = vendor.Trade;
                summarySheet.Cell(row, 3).Value = vendor.SnapshotCount;
                summarySheet.Cell(row, 4).Value = vendor.TotalValue;
                summarySheet.Cell(row, 4).Style.NumberFormat.Format = "#,##0.00";
                row++;
            }

            summarySheet.Columns().AdjustToContents();
        }

        // Data sheet
        var dataSheet = workbook.Worksheets.Add("Pricing Data");

        // Headers
        var headers = new[]
        {
            "Vendor Name", "Trade", "Tender Reference", "Tender Title",
            "Date", "Item Description", "UOM", "Rate", "Quantity",
            "Total Amount", "Currency"
        };

        for (var i = 0; i < headers.Length; i++)
        {
            dataSheet.Cell(1, i + 1).Value = headers[i];
        }

        var headerRange = dataSheet.Range(1, 1, 1, headers.Length);
        headerRange.Style.Font.Bold = true;
        headerRange.Style.Fill.BackgroundColor = XLColor.LightBlue;
        headerRange.Style.Border.OutsideBorder = XLBorderStyleValues.Thin;

        // Data rows
        var dataRow = 2;
        foreach (var item in rows)
        {
            dataSheet.Cell(dataRow, 1).Value = item.VendorName;
            dataSheet.Cell(dataRow, 2).Value = item.Trade ?? "Unspecified";
            dataSheet.Cell(dataRow, 3).Value = item.TenderReference;
            dataSheet.Cell(dataRow, 4).Value = item.TenderTitle;
            dataSheet.Cell(dataRow, 5).Value = item.Date;
            dataSheet.Cell(dataRow, 5).Style.NumberFormat.Format = "yyyy-MM-dd";
            dataSheet.Cell(dataRow, 6).Value = item.ItemDescription;
            dataSheet.Cell(dataRow, 7).Value = item.Uom;
            dataSheet.Cell(dataRow, 8).Value = item.Rate;
            dataSheet.Cell(dataRow, 8).Style.NumberFormat.Format = "#,##0.00";
            dataSheet.Cell(dataRow, 9).Value = item.Quantity ?? 0;
            dataSheet.Cell(dataRow, 9).Style.NumberFormat.Format = "#,##0.00";
            dataSheet.Cell(dataRow, 10).Value = item.TotalAmount ?? 0;
            dataSheet.Cell(dataRow, 10).Style.NumberFormat.Format = "#,##0.00";
            dataSheet.Cell(dataRow, 11).Value = item.Currency;

            dataRow++;
        }

        // Auto-fit columns
        dataSheet.Columns().AdjustToContents();

        // Add filters
        if (rows.Any())
        {
            dataSheet.Range(1, 1, dataRow - 1, headers.Length).SetAutoFilter();
        }

        // Freeze header row
        dataSheet.SheetView.FreezeRows(1);

        using var stream = new MemoryStream();
        workbook.SaveAs(stream);
        return stream.ToArray();
    }
}
