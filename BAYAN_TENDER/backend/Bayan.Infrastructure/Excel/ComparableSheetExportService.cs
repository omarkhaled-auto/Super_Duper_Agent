using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Evaluation.DTOs;
using Bayan.Domain.Enums;
using ClosedXML.Excel;
using Microsoft.Extensions.Logging;

namespace Bayan.Infrastructure.Excel;

/// <summary>
/// Service for exporting comparable sheets to Excel using ClosedXML.
/// </summary>
public class ComparableSheetExportService : IComparableSheetExportService
{
    private readonly ILogger<ComparableSheetExportService> _logger;

    // Column widths
    private const double ItemNumberWidth = 12;
    private const double DescriptionWidth = 45;
    private const double QuantityWidth = 12;
    private const double UomWidth = 10;
    private const double AverageWidth = 15;
    private const double BidderRateWidth = 15;
    private const double BidderAmountWidth = 18;

    // Colors for outlier severity
    private static readonly XLColor HighSeverityColor = XLColor.FromArgb(255, 199, 206); // Light red
    private static readonly XLColor MediumSeverityColor = XLColor.FromArgb(255, 235, 156); // Light yellow
    private static readonly XLColor LowSeverityColor = XLColor.FromArgb(198, 239, 206); // Light green
    private static readonly XLColor HeaderColor = XLColor.FromArgb(68, 84, 106); // Dark blue-gray
    private static readonly XLColor SectionTotalColor = XLColor.FromArgb(217, 225, 242); // Light blue
    private static readonly XLColor GrandTotalColor = XLColor.FromArgb(155, 194, 230); // Medium blue

    public ComparableSheetExportService(ILogger<ComparableSheetExportService> logger)
    {
        _logger = logger;
    }

    public async Task<ExportComparableSheetResultDto> ExportToExcelAsync(
        ComparableSheetDto comparableSheet,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Generating Excel export for tender {TenderId}: {ItemCount} items, {BidderCount} bidders",
            comparableSheet.TenderId, comparableSheet.Items.Count, comparableSheet.Bidders.Count);

        using var workbook = new XLWorkbook();
        var worksheet = workbook.Worksheets.Add("Comparable Sheet");

        var currentRow = 1;

        // Add title
        currentRow = AddTitle(worksheet, comparableSheet, currentRow);

        // Add summary
        currentRow = AddSummary(worksheet, comparableSheet, currentRow);

        // Add main header row
        var headerRow = currentRow;
        currentRow = AddHeader(worksheet, comparableSheet.Bidders, currentRow);

        // Add data rows grouped by section
        var itemsBySection = comparableSheet.Items
            .GroupBy(i => new { i.SectionId, i.SectionName })
            .OrderBy(g => comparableSheet.Items.Where(i => i.SectionId == g.Key.SectionId).Min(i => i.SortOrder));

        foreach (var section in itemsBySection)
        {
            cancellationToken.ThrowIfCancellationRequested();

            // Add section header
            currentRow = AddSectionHeader(worksheet, section.Key.SectionName, comparableSheet.Bidders.Count, currentRow);

            // Add items in section
            foreach (var item in section.OrderBy(i => i.SortOrder))
            {
                currentRow = AddItemRow(worksheet, item, comparableSheet.Bidders, currentRow);
            }

            // Add section total
            var sectionTotal = comparableSheet.SectionTotals.FirstOrDefault(st => st.SectionId == section.Key.SectionId);
            if (sectionTotal != null)
            {
                currentRow = AddSectionTotal(worksheet, sectionTotal, comparableSheet.Bidders, currentRow);
            }
        }

        // Add grand totals
        currentRow = AddGrandTotals(worksheet, comparableSheet.GrandTotals, comparableSheet.Bidders, currentRow);

        // Apply formatting
        ApplyFormatting(worksheet, headerRow, currentRow - 1, comparableSheet.Bidders.Count);

        // Freeze panes (first 4 columns + header rows)
        worksheet.SheetView.FreezeRows(headerRow);
        worksheet.SheetView.FreezeColumns(4);

        // Add auto-filter
        var lastColumn = GetLastColumn(comparableSheet.Bidders.Count);
        worksheet.Range(headerRow, 1, currentRow - 1, lastColumn).SetAutoFilter();

        // Adjust column widths
        AdjustColumnWidths(worksheet, comparableSheet.Bidders.Count);

        // Save to memory stream
        using var stream = new MemoryStream();
        workbook.SaveAs(stream);

        var fileName = $"ComparableSheet_{comparableSheet.TenderName.Replace(" ", "_")}_{DateTime.UtcNow:yyyyMMdd_HHmmss}.xlsx";

        _logger.LogInformation("Excel export completed: {FileName}, {Size} bytes", fileName, stream.Length);

        return await Task.FromResult(new ExportComparableSheetResultDto
        {
            FileContent = stream.ToArray(),
            FileName = fileName,
            ContentType = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        });
    }

    private int AddTitle(IXLWorksheet worksheet, ComparableSheetDto data, int row)
    {
        var cell = worksheet.Cell(row, 1);
        cell.Value = $"Comparable Sheet - {data.TenderName}";
        cell.Style.Font.Bold = true;
        cell.Style.Font.FontSize = 16;
        worksheet.Range(row, 1, row, 10).Merge();

        row++;
        worksheet.Cell(row, 1).Value = $"Generated: {data.GeneratedAt:yyyy-MM-dd HH:mm} UTC";
        worksheet.Cell(row, 1).Style.Font.Italic = true;
        worksheet.Cell(row, 1).Style.Font.FontColor = XLColor.Gray;

        return row + 2;
    }

    private int AddSummary(IXLWorksheet worksheet, ComparableSheetDto data, int row)
    {
        worksheet.Cell(row, 1).Value = "Summary";
        worksheet.Cell(row, 1).Style.Font.Bold = true;

        row++;
        worksheet.Cell(row, 1).Value = "Total Items:";
        worksheet.Cell(row, 2).Value = data.Summary.TotalItems;

        row++;
        worksheet.Cell(row, 1).Value = "Bidders:";
        worksheet.Cell(row, 2).Value = data.Summary.BidderCount;

        row++;
        worksheet.Cell(row, 1).Value = "Outliers Detected:";
        worksheet.Cell(row, 2).Value = data.Summary.OutlierCount;

        row++;
        worksheet.Cell(row, 1).Value = "Max Deviation:";
        worksheet.Cell(row, 2).Value = $"{data.Summary.MaxDeviation:F2}%";

        return row + 2;
    }

    private int AddHeader(IXLWorksheet worksheet, List<ComparableSheetBidderDto> bidders, int row)
    {
        var col = 1;

        // Fixed columns
        SetHeaderCell(worksheet, row, col++, "Item #");
        SetHeaderCell(worksheet, row, col++, "Description");
        SetHeaderCell(worksheet, row, col++, "Qty");
        SetHeaderCell(worksheet, row, col++, "UOM");
        SetHeaderCell(worksheet, row, col++, "Average Rate");

        // Bidder columns (Rate and Amount for each)
        foreach (var bidder in bidders.OrderBy(b => b.Rank))
        {
            SetHeaderCell(worksheet, row, col++, $"{bidder.CompanyName} (Rank {bidder.Rank})\nRate");
            SetHeaderCell(worksheet, row, col++, $"{bidder.CompanyName}\nAmount");
        }

        return row + 1;
    }

    private void SetHeaderCell(IXLWorksheet worksheet, int row, int col, string value)
    {
        var cell = worksheet.Cell(row, col);
        cell.Value = value;
        cell.Style.Font.Bold = true;
        cell.Style.Font.FontColor = XLColor.White;
        cell.Style.Fill.BackgroundColor = HeaderColor;
        cell.Style.Alignment.WrapText = true;
        cell.Style.Alignment.Vertical = XLAlignmentVerticalValues.Center;
        cell.Style.Alignment.Horizontal = XLAlignmentHorizontalValues.Center;
        cell.Style.Border.OutsideBorder = XLBorderStyleValues.Thin;
    }

    private int AddSectionHeader(IXLWorksheet worksheet, string sectionName, int bidderCount, int row)
    {
        var lastCol = GetLastColumn(bidderCount);

        var cell = worksheet.Cell(row, 1);
        cell.Value = sectionName;
        cell.Style.Font.Bold = true;
        cell.Style.Font.FontSize = 11;
        cell.Style.Fill.BackgroundColor = XLColor.FromArgb(242, 242, 242);

        worksheet.Range(row, 1, row, lastCol).Merge();
        worksheet.Range(row, 1, row, lastCol).Style.Border.OutsideBorder = XLBorderStyleValues.Thin;

        return row + 1;
    }

    private int AddItemRow(
        IXLWorksheet worksheet,
        ComparableSheetItemDto item,
        List<ComparableSheetBidderDto> bidders,
        int row)
    {
        var col = 1;

        // Fixed columns
        worksheet.Cell(row, col++).Value = item.ItemNumber;
        worksheet.Cell(row, col++).Value = item.Description;
        worksheet.Cell(row, col++).Value = item.Quantity;
        worksheet.Cell(row, col++).Value = item.Uom;
        worksheet.Cell(row, col++).Value = item.AverageRate ?? 0;

        // Bidder rates
        foreach (var bidder in bidders.OrderBy(b => b.Rank))
        {
            var bidderRate = item.BidderRates.FirstOrDefault(r => r.BidderId == bidder.Id);

            var rateCell = worksheet.Cell(row, col++);
            var amountCell = worksheet.Cell(row, col++);

            if (bidderRate == null || bidderRate.IsNoBid)
            {
                rateCell.Value = "No Bid";
                rateCell.Style.Font.Italic = true;
                rateCell.Style.Font.FontColor = XLColor.Gray;
                amountCell.Value = "-";
                amountCell.Style.Font.FontColor = XLColor.Gray;
            }
            else if (bidderRate.IsNonComparable)
            {
                rateCell.Value = "N/C";
                rateCell.Style.Font.Italic = true;
                rateCell.Style.Font.FontColor = XLColor.DarkOrange;
                amountCell.Value = "-";
                amountCell.Style.Font.FontColor = XLColor.Gray;
            }
            else
            {
                rateCell.Value = bidderRate.Rate ?? 0;
                amountCell.Value = bidderRate.Amount ?? 0;

                // Apply outlier coloring
                if (bidderRate.IsOutlier && bidderRate.Severity.HasValue)
                {
                    var color = bidderRate.Severity.Value switch
                    {
                        OutlierSeverity.High => HighSeverityColor,
                        OutlierSeverity.Medium => MediumSeverityColor,
                        _ => LowSeverityColor
                    };

                    rateCell.Style.Fill.BackgroundColor = color;
                    amountCell.Style.Fill.BackgroundColor = color;

                    // Add comment with deviation info
                    if (bidderRate.Deviation.HasValue)
                    {
                        rateCell.CreateComment().AddText($"Deviation: {bidderRate.Deviation:F2}%");
                    }
                }
            }
        }

        // Apply borders to row
        var lastCol = GetLastColumn(bidders.Count);
        worksheet.Range(row, 1, row, lastCol).Style.Border.OutsideBorder = XLBorderStyleValues.Thin;
        worksheet.Range(row, 1, row, lastCol).Style.Border.InsideBorder = XLBorderStyleValues.Thin;

        return row + 1;
    }

    private int AddSectionTotal(
        IXLWorksheet worksheet,
        ComparableSheetSectionTotalDto sectionTotal,
        List<ComparableSheetBidderDto> bidders,
        int row)
    {
        var col = 1;
        var lastCol = GetLastColumn(bidders.Count);

        worksheet.Cell(row, col++).Value = "";
        worksheet.Cell(row, col++).Value = $"Section Total - {sectionTotal.SectionName}";
        worksheet.Cell(row, col++).Value = "";
        worksheet.Cell(row, col++).Value = "";
        worksheet.Cell(row, col++).Value = "";

        foreach (var bidder in bidders.OrderBy(b => b.Rank))
        {
            var bidderTotal = sectionTotal.BidderTotals.FirstOrDefault(bt => bt.BidderId == bidder.Id);

            worksheet.Cell(row, col++).Value = ""; // Rate column
            worksheet.Cell(row, col++).Value = bidderTotal?.Total ?? 0; // Amount column
        }

        // Style section total row
        var range = worksheet.Range(row, 1, row, lastCol);
        range.Style.Font.Bold = true;
        range.Style.Fill.BackgroundColor = SectionTotalColor;
        range.Style.Border.OutsideBorder = XLBorderStyleValues.Thin;

        return row + 1;
    }

    private int AddGrandTotals(
        IXLWorksheet worksheet,
        List<BidderGrandTotalDto> grandTotals,
        List<ComparableSheetBidderDto> bidders,
        int row)
    {
        var col = 1;
        var lastCol = GetLastColumn(bidders.Count);

        // Add a blank row before grand totals
        row++;

        worksheet.Cell(row, col++).Value = "";
        worksheet.Cell(row, col++).Value = "GRAND TOTAL";
        worksheet.Cell(row, col++).Value = "";
        worksheet.Cell(row, col++).Value = "";
        worksheet.Cell(row, col++).Value = "";

        foreach (var bidder in bidders.OrderBy(b => b.Rank))
        {
            var grandTotal = grandTotals.FirstOrDefault(gt => gt.BidderId == bidder.Id);

            worksheet.Cell(row, col++).Value = ""; // Rate column
            worksheet.Cell(row, col++).Value = grandTotal?.GrandTotal ?? 0; // Amount column
        }

        // Style grand total row
        var range = worksheet.Range(row, 1, row, lastCol);
        range.Style.Font.Bold = true;
        range.Style.Font.FontSize = 12;
        range.Style.Fill.BackgroundColor = GrandTotalColor;
        range.Style.Border.OutsideBorder = XLBorderStyleValues.Medium;

        return row + 1;
    }

    private void ApplyFormatting(IXLWorksheet worksheet, int headerRow, int lastRow, int bidderCount)
    {
        var lastCol = GetLastColumn(bidderCount);

        // Format quantity column
        worksheet.Range(headerRow + 1, 3, lastRow, 3).Style.NumberFormat.Format = "#,##0.00";

        // Format average rate column
        worksheet.Range(headerRow + 1, 5, lastRow, 5).Style.NumberFormat.Format = "#,##0.00";

        // Format bidder rate and amount columns
        for (int bidderIndex = 0; bidderIndex < bidderCount; bidderIndex++)
        {
            var rateCol = 6 + (bidderIndex * 2);
            var amountCol = rateCol + 1;

            worksheet.Range(headerRow + 1, rateCol, lastRow, rateCol).Style.NumberFormat.Format = "#,##0.00";
            worksheet.Range(headerRow + 1, amountCol, lastRow, amountCol).Style.NumberFormat.Format = "#,##0.00";
        }

        // Center align certain columns
        worksheet.Column(1).Style.Alignment.Horizontal = XLAlignmentHorizontalValues.Center; // Item #
        worksheet.Column(3).Style.Alignment.Horizontal = XLAlignmentHorizontalValues.Right; // Qty
        worksheet.Column(4).Style.Alignment.Horizontal = XLAlignmentHorizontalValues.Center; // UOM
        worksheet.Column(5).Style.Alignment.Horizontal = XLAlignmentHorizontalValues.Right; // Average
    }

    private void AdjustColumnWidths(IXLWorksheet worksheet, int bidderCount)
    {
        worksheet.Column(1).Width = ItemNumberWidth;
        worksheet.Column(2).Width = DescriptionWidth;
        worksheet.Column(3).Width = QuantityWidth;
        worksheet.Column(4).Width = UomWidth;
        worksheet.Column(5).Width = AverageWidth;

        for (int bidderIndex = 0; bidderIndex < bidderCount; bidderIndex++)
        {
            var rateCol = 6 + (bidderIndex * 2);
            var amountCol = rateCol + 1;

            worksheet.Column(rateCol).Width = BidderRateWidth;
            worksheet.Column(amountCol).Width = BidderAmountWidth;
        }
    }

    private int GetLastColumn(int bidderCount)
    {
        // 5 fixed columns + 2 columns per bidder (rate + amount)
        return 5 + (bidderCount * 2);
    }
}
