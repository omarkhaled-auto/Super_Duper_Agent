using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.DTOs;
using Bayan.Domain.Enums;
using ClosedXML.Excel;
using Microsoft.Extensions.Logging;

namespace Bayan.Infrastructure.Excel;

/// <summary>
/// Service for exporting BOQ templates to Excel using ClosedXML.
/// </summary>
public class TemplateExportService : ITemplateExportService
{
    private readonly ILogger<TemplateExportService> _logger;

    // Excel column mappings
    private static readonly Dictionary<string, int> ColumnIndices = new()
    {
        ["ItemNumber"] = 1,
        ["Description"] = 2,
        ["Quantity"] = 3,
        ["Uom"] = 4,
        ["UnitRate"] = 5,
        ["Amount"] = 6,
        ["Notes"] = 7
    };

    // Column header translations
    private static readonly Dictionary<string, (string English, string Arabic)> ColumnHeaders = new()
    {
        ["Section"] = ("Section", "القسم"),
        ["Level"] = ("Level", "المستوى"),
        ["ItemNumber"] = ("Item #", "رقم البند"),
        ["Description"] = ("Description", "الوصف"),
        ["Quantity"] = ("Qty", "الكمية"),
        ["Uom"] = ("UOM", "وحدة القياس"),
        ["UnitRate"] = ("Unit Rate", "سعر الوحدة"),
        ["Amount"] = ("Amount", "المبلغ"),
        ["Notes"] = ("Notes", "ملاحظات")
    };

    // Branding colors
    private static readonly XLColor HeaderBackgroundColor = XLColor.FromHtml("#1E3A5F"); // Dark blue
    private static readonly XLColor HeaderForegroundColor = XLColor.White;
    private static readonly XLColor SectionBackgroundColor = XLColor.FromHtml("#E8F4FD"); // Light blue
    private static readonly XLColor LockedCellColor = XLColor.FromHtml("#F5F5F5"); // Light gray
    private static readonly XLColor HighlightColor = XLColor.FromHtml("#FFEB3B"); // Yellow

    // Hierarchy-specific colors
    private static readonly XLColor BillBackgroundColor = XLColor.FromHtml("#DBEAFE"); // Blue-100
    private static readonly XLColor ItemGroupBackgroundColor = XLColor.FromHtml("#F1F5F9"); // Slate-100
    private static readonly XLColor NonPriceableBackgroundColor = XLColor.FromHtml("#E5E7EB"); // Gray-200

    public TemplateExportService(ILogger<TemplateExportService> logger)
    {
        _logger = logger;
    }

    /// <inheritdoc />
    public async Task<ExportResultDto> GenerateBoqTemplateAsync(
        BoqTemplateGenerationRequest request,
        CancellationToken cancellationToken = default)
    {
        _logger.LogDebug("Generating BOQ template for tender {TenderId}", request.TenderId);

        using var workbook = new XLWorkbook();

        // Create main BOQ worksheet
        var boqSheet = workbook.Worksheets.Add(GetSheetName("BOQ", request.Language));
        await Task.Run(() => BuildBoqWorksheet(boqSheet, request), cancellationToken);

        // Optionally add instructions sheet
        if (request.IncludeInstructions)
        {
            var instructionsSheet = workbook.Worksheets.Add(GetSheetName("Instructions", request.Language));
            await Task.Run(() => BuildInstructionsWorksheet(instructionsSheet, request), cancellationToken);
        }

        // Save to memory stream
        using var stream = new MemoryStream();
        workbook.SaveAs(stream);
        var content = stream.ToArray();

        // Generate filename
        var fileName = GenerateFileName(request.TenderReference);

        _logger.LogDebug("BOQ template generated. Size: {Size} bytes", content.Length);

        return ExportResultDto.Excel(fileName, content);
    }

    private void BuildBoqWorksheet(IXLWorksheet worksheet, BoqTemplateGenerationRequest request)
    {
        int currentRow = 1;

        // Add branded header
        currentRow = AddBrandedHeader(worksheet, request, currentRow);
        currentRow += 1; // Empty row after header

        // Add column headers
        int headerRow = currentRow;
        currentRow = AddColumnHeaders(worksheet, request, currentRow);

        // Track data start row for formulas
        int dataStartRow = currentRow;

        // Add section data
        foreach (var section in request.Sections)
        {
            currentRow = AddSection(worksheet, section, request, currentRow, dataStartRow);
        }

        int dataEndRow = currentRow - 1;
        bool hasData = dataEndRow >= dataStartRow;

        if (hasData)
        {
            // Add summary row
            currentRow += 1; // Empty row
            AddSummaryRow(worksheet, request, currentRow, dataStartRow, dataEndRow);

            // Apply formatting
            ApplyWorksheetFormatting(worksheet, request, headerRow, dataEndRow);

            // Add UOM data validation
            if (request.IncludeColumns.Contains("Uom") && request.AvailableUoms.Any())
            {
                AddUomDataValidation(worksheet, request, dataStartRow, dataEndRow);
            }

            // Add conditional formatting for empty Unit Rate
            if (request.IncludeColumns.Contains("UnitRate"))
            {
                AddConditionalFormatting(worksheet, dataStartRow, dataEndRow);
            }

            // Lock specified columns
            ApplyColumnProtection(worksheet, request, dataStartRow, dataEndRow);
        }

        // Freeze header rows
        worksheet.SheetView.FreezeRows(headerRow);

        if (hasData)
        {
            // Enable auto-filter
            var filterRange = worksheet.Range(
                headerRow, 1,
                dataEndRow, request.IncludeColumns.Count);
            filterRange.SetAutoFilter();
        }

        // Auto-fit columns
        worksheet.Columns().AdjustToContents();

        // Set print layout
        SetupPrintLayout(worksheet);
    }

    private int AddBrandedHeader(IXLWorksheet worksheet, BoqTemplateGenerationRequest request, int startRow)
    {
        int row = startRow;

        // Title row
        var titleCell = worksheet.Cell(row, 1);
        titleCell.Value = request.Language == TemplateLanguage.Arabic
            ? "جدول الكميات"
            : "Bill of Quantities";
        titleCell.Style.Font.Bold = true;
        titleCell.Style.Font.FontSize = 16;
        titleCell.Style.Font.FontColor = HeaderBackgroundColor;
        worksheet.Range(row, 1, row, request.IncludeColumns.Count).Merge();
        row++;

        // Tender title
        var tenderTitleCell = worksheet.Cell(row, 1);
        tenderTitleCell.Value = request.TenderTitle;
        tenderTitleCell.Style.Font.Bold = true;
        tenderTitleCell.Style.Font.FontSize = 14;
        worksheet.Range(row, 1, row, request.IncludeColumns.Count).Merge();
        row++;

        // Reference
        var refLabel = request.Language == TemplateLanguage.Arabic ? "المرجع:" : "Reference:";
        worksheet.Cell(row, 1).Value = $"{refLabel} {request.TenderReference}";
        worksheet.Cell(row, 1).Style.Font.Bold = true;
        row++;

        // Submission deadline
        var deadlineLabel = request.Language == TemplateLanguage.Arabic ? "الموعد النهائي:" : "Submission Deadline:";
        worksheet.Cell(row, 1).Value = $"{deadlineLabel} {request.SubmissionDeadline:dd-MMM-yyyy HH:mm}";
        worksheet.Cell(row, 1).Style.Font.FontColor = XLColor.Red;
        worksheet.Cell(row, 1).Style.Font.Bold = true;
        row++;

        // Currency
        var currencyLabel = request.Language == TemplateLanguage.Arabic ? "العملة:" : "Currency:";
        worksheet.Cell(row, 1).Value = $"{currencyLabel} {request.Currency}";
        row++;

        // Pricing level
        var pricingLevelLabel = request.Language == TemplateLanguage.Arabic ? "مستوى التسعير:" : "Pricing Level:";
        var pricingLevelValue = request.PricingLevel switch
        {
            PricingLevel.Bill => request.Language == TemplateLanguage.Arabic ? "مستوى الفاتورة" : "Bill Level",
            PricingLevel.Item => request.Language == TemplateLanguage.Arabic ? "مستوى البند" : "Item Level",
            PricingLevel.SubItem => request.Language == TemplateLanguage.Arabic ? "مستوى البند الفرعي" : "Sub-Item Level",
            _ => "Sub-Item Level"
        };
        var pricingCell = worksheet.Cell(row, 1);
        pricingCell.Value = $"{pricingLevelLabel} {pricingLevelValue}";
        pricingCell.Style.Font.Bold = true;
        pricingCell.Style.Font.FontColor = XLColor.FromHtml("#1E3A5F");
        row++;

        return row;
    }

    private int AddColumnHeaders(IXLWorksheet worksheet, BoqTemplateGenerationRequest request, int startRow)
    {
        int col = 1;
        foreach (var column in request.IncludeColumns)
        {
            if (ColumnHeaders.TryGetValue(column, out var headers))
            {
                var headerText = request.Language switch
                {
                    TemplateLanguage.Arabic => headers.Arabic,
                    TemplateLanguage.Both => $"{headers.English}\n{headers.Arabic}",
                    _ => headers.English
                };

                var cell = worksheet.Cell(startRow, col);
                cell.Value = headerText;
                cell.Style.Fill.BackgroundColor = HeaderBackgroundColor;
                cell.Style.Font.FontColor = HeaderForegroundColor;
                cell.Style.Font.Bold = true;
                cell.Style.Alignment.Horizontal = XLAlignmentHorizontalValues.Center;
                cell.Style.Alignment.Vertical = XLAlignmentVerticalValues.Center;
                cell.Style.Alignment.WrapText = true;
                cell.Style.Border.OutsideBorder = XLBorderStyleValues.Thin;
                cell.Style.Border.OutsideBorderColor = XLColor.Black;
            }
            col++;
        }

        return startRow + 1;
    }

    private int AddSection(
        IXLWorksheet worksheet,
        BoqSectionExportDto section,
        BoqTemplateGenerationRequest request,
        int startRow,
        int dataStartRow)
    {
        int row = startRow;
        bool hasSectionColumn = request.IncludeColumns.Contains("Section");
        string sectionTitle = $"{section.SectionNumber} - {section.Title}";

        // Add a bill-level section header row (bold, colored background)
        if (!hasSectionColumn)
        {
            var sectionCell = worksheet.Cell(row, 1);
            sectionCell.Value = sectionTitle;
            sectionCell.Style.Font.Bold = true;
            sectionCell.Style.Font.FontSize = 11;
            sectionCell.Style.Fill.BackgroundColor = BillBackgroundColor;

            var sectionRange = worksheet.Range(row, 1, row, request.IncludeColumns.Count);
            sectionRange.Merge();
            sectionRange.Style.Border.OutsideBorder = XLBorderStyleValues.Thin;

            // Add "Level" value if that column exists in an unmerged context
            // (Merged row — level is implied as "Bill")
            row++;
        }

        // Add items with hierarchy-aware formatting
        foreach (var item in section.Items)
        {
            row = AddItem(worksheet, item, request, row, dataStartRow, sectionTitle);
        }

        return row;
    }

    private int AddItem(
        IXLWorksheet worksheet,
        BoqItemExportDto item,
        BoqTemplateGenerationRequest request,
        int row,
        int dataStartRow,
        string sectionTitle = "")
    {
        bool isPriceable = IsItemPriceable(item, request.PricingLevel);
        int col = 1;

        foreach (var column in request.IncludeColumns)
        {
            var cell = worksheet.Cell(row, col);

            switch (column)
            {
                case "Section":
                    cell.Value = sectionTitle;
                    break;

                case "Level":
                    cell.Value = item.HierarchyLevel;
                    cell.Style.Alignment.Horizontal = XLAlignmentHorizontalValues.Center;
                    break;

                case "ItemNumber":
                    cell.Value = item.ItemNumber;
                    cell.Style.Alignment.Horizontal = XLAlignmentHorizontalValues.Center;
                    // Indent based on hierarchy level
                    if (item.IsGroup)
                    {
                        cell.Style.Alignment.Indent = 1;
                    }
                    else if (item.HasParent)
                    {
                        cell.Style.Alignment.Indent = 2;
                    }
                    break;

                case "Description":
                    cell.Value = item.Description;
                    cell.Style.Alignment.WrapText = true;
                    // Indent description based on hierarchy level
                    if (item.IsGroup)
                    {
                        cell.Style.Alignment.Indent = 1;
                    }
                    else if (item.HasParent)
                    {
                        cell.Style.Alignment.Indent = 2;
                    }
                    break;

                case "Quantity":
                    if (!item.IsGroup)
                    {
                        cell.Value = item.Quantity;
                        cell.Style.NumberFormat.Format = "#,##0.00";
                    }
                    cell.Style.Alignment.Horizontal = XLAlignmentHorizontalValues.Right;
                    break;

                case "Uom":
                    if (!item.IsGroup)
                    {
                        cell.Value = item.Uom;
                    }
                    cell.Style.Alignment.Horizontal = XLAlignmentHorizontalValues.Center;
                    break;

                case "UnitRate":
                    if (isPriceable)
                    {
                        // Leave blank for bidder to fill — this is a priceable row
                        cell.Style.NumberFormat.Format = "#,##0.00";
                    }
                    else
                    {
                        // Non-priceable: grey out and lock
                        cell.Style.Fill.BackgroundColor = NonPriceableBackgroundColor;
                        cell.Style.Protection.Locked = true;
                    }
                    cell.Style.Alignment.Horizontal = XLAlignmentHorizontalValues.Right;
                    break;

                case "Amount":
                    if (isPriceable)
                    {
                        // Formula: Quantity x Unit Rate
                        int qtyColIndex = request.IncludeColumns.IndexOf("Quantity") + 1;
                        int rateColIndex = request.IncludeColumns.IndexOf("UnitRate") + 1;

                        if (qtyColIndex > 0 && rateColIndex > 0)
                        {
                            string qtyCol = GetColumnLetter(qtyColIndex);
                            string rateCol = GetColumnLetter(rateColIndex);
                            cell.FormulaA1 = $"={qtyCol}{row}*{rateCol}{row}";
                        }
                    }
                    else
                    {
                        // Non-priceable: grey out and lock
                        cell.Style.Fill.BackgroundColor = NonPriceableBackgroundColor;
                        cell.Style.Protection.Locked = true;
                    }
                    cell.Style.NumberFormat.Format = "#,##0.00";
                    cell.Style.Alignment.Horizontal = XLAlignmentHorizontalValues.Right;
                    break;

                case "Notes":
                    cell.Value = item.Notes ?? string.Empty;
                    cell.Style.Alignment.WrapText = true;
                    break;
            }

            cell.Style.Border.OutsideBorder = XLBorderStyleValues.Thin;
            cell.Style.Border.OutsideBorderColor = XLColor.LightGray;

            col++;
        }

        // Apply hierarchy-level row formatting
        ApplyHierarchyRowFormatting(worksheet, row, request.IncludeColumns.Count, item, isPriceable);

        return row + 1;
    }

    /// <summary>
    /// Determines whether a given item is priceable at the specified PricingLevel.
    /// - SubItem level: all non-group items are priceable (most granular)
    /// - Item level: only standalone items (not sub-items) are priceable
    /// - Bill level: no individual items are priceable (pricing is at bill/section level)
    /// </summary>
    private static bool IsItemPriceable(BoqItemExportDto item, PricingLevel pricingLevel)
    {
        // Group headers are never directly priceable
        if (item.IsGroup) return false;

        return pricingLevel switch
        {
            PricingLevel.SubItem => true, // All leaf items are priceable
            PricingLevel.Item => !item.HasParent, // Only top-level items (not sub-items)
            PricingLevel.Bill => false, // No individual items — priced at bill level
            _ => true
        };
    }

    /// <summary>
    /// Applies visual formatting to a row based on its hierarchy level.
    /// </summary>
    private static void ApplyHierarchyRowFormatting(
        IXLWorksheet worksheet,
        int row,
        int columnCount,
        BoqItemExportDto item,
        bool isPriceable)
    {
        var rowRange = worksheet.Range(row, 1, row, columnCount);

        if (item.IsGroup)
        {
            // Item group rows: semi-bold, light background
            rowRange.Style.Font.Bold = true;
            rowRange.Style.Fill.BackgroundColor = ItemGroupBackgroundColor;
        }
        else if (item.HasParent)
        {
            // Sub-item rows: normal weight, slightly muted if non-priceable
            if (!isPriceable)
            {
                rowRange.Style.Font.FontColor = XLColor.FromHtml("#6B7280"); // Gray-500
            }
        }

        // Non-priceable rows get a distinct visual treatment
        if (!isPriceable && !item.IsGroup)
        {
            rowRange.Style.Font.Italic = true;
        }
    }

    private void AddSummaryRow(
        IXLWorksheet worksheet,
        BoqTemplateGenerationRequest request,
        int row,
        int dataStartRow,
        int dataEndRow)
    {
        // Total label
        int descColIndex = request.IncludeColumns.IndexOf("Description");
        if (descColIndex >= 0)
        {
            var totalLabelCell = worksheet.Cell(row, descColIndex + 1);
            totalLabelCell.Value = request.Language == TemplateLanguage.Arabic ? "الإجمالي:" : "TOTAL:";
            totalLabelCell.Style.Font.Bold = true;
            totalLabelCell.Style.Alignment.Horizontal = XLAlignmentHorizontalValues.Right;
        }

        // Total amount formula
        int amountColIndex = request.IncludeColumns.IndexOf("Amount");
        if (amountColIndex >= 0)
        {
            var totalCell = worksheet.Cell(row, amountColIndex + 1);
            string amountCol = GetColumnLetter(amountColIndex + 1);
            totalCell.FormulaA1 = $"=SUM({amountCol}{dataStartRow}:{amountCol}{dataEndRow})";
            totalCell.Style.Font.Bold = true;
            totalCell.Style.NumberFormat.Format = "#,##0.00";
            totalCell.Style.Fill.BackgroundColor = HeaderBackgroundColor;
            totalCell.Style.Font.FontColor = HeaderForegroundColor;
            totalCell.Style.Border.OutsideBorder = XLBorderStyleValues.Medium;
        }

        // Item count
        int itemCountColIndex = request.IncludeColumns.IndexOf("ItemNumber");
        if (itemCountColIndex >= 0)
        {
            var countCell = worksheet.Cell(row + 1, itemCountColIndex + 1);
            string itemCol = GetColumnLetter(itemCountColIndex + 1);
            countCell.FormulaA1 = $"=COUNTA({itemCol}{dataStartRow}:{itemCol}{dataEndRow})";

            var countLabelCell = worksheet.Cell(row + 1, itemCountColIndex + 2);
            countLabelCell.Value = request.Language == TemplateLanguage.Arabic ? "عدد البنود" : "Total Items";
            countLabelCell.Style.Font.Italic = true;
        }
    }

    private void AddUomDataValidation(
        IXLWorksheet worksheet,
        BoqTemplateGenerationRequest request,
        int dataStartRow,
        int dataEndRow)
    {
        int uomColIndex = request.IncludeColumns.IndexOf("Uom");
        if (uomColIndex < 0 || !request.AvailableUoms.Any()) return;

        var uomRange = worksheet.Range(
            dataStartRow, uomColIndex + 1,
            dataEndRow, uomColIndex + 1);

        var validation = uomRange.CreateDataValidation();
        validation.List(string.Join(",", request.AvailableUoms));
        validation.IgnoreBlanks = true;
        validation.InCellDropdown = true;
    }

    private void AddConditionalFormatting(IXLWorksheet worksheet, int dataStartRow, int dataEndRow)
    {
        // Find Unit Rate column
        var headerRow = worksheet.Row(dataStartRow - 1);
        int unitRateCol = -1;

        for (int col = 1; col <= worksheet.ColumnsUsed().Count(); col++)
        {
            var cellValue = worksheet.Cell(dataStartRow - 1, col).GetString();
            if (cellValue.Contains("Unit Rate") || cellValue.Contains("سعر الوحدة"))
            {
                unitRateCol = col;
                break;
            }
        }

        if (unitRateCol > 0)
        {
            var range = worksheet.Range(dataStartRow, unitRateCol, dataEndRow, unitRateCol);
            range.AddConditionalFormat()
                .WhenIsBlank()
                .Fill.SetBackgroundColor(HighlightColor);
        }
    }

    private void ApplyColumnProtection(
        IXLWorksheet worksheet,
        BoqTemplateGenerationRequest request,
        int dataStartRow,
        int dataEndRow)
    {
        foreach (var lockColumn in request.LockColumns)
        {
            int colIndex = request.IncludeColumns.IndexOf(lockColumn);
            if (colIndex < 0) continue;

            var range = worksheet.Range(dataStartRow, colIndex + 1, dataEndRow, colIndex + 1);
            range.Style.Fill.BackgroundColor = LockedCellColor;
            range.Style.Protection.Locked = true;
        }

        // Protect the worksheet but allow editing unlocked cells
        var protection = worksheet.Protect();
        protection.AllowElement(XLSheetProtectionElements.FormatColumns);
        protection.AllowElement(XLSheetProtectionElements.FormatRows);
        protection.AllowElement(XLSheetProtectionElements.SelectLockedCells);
        protection.AllowElement(XLSheetProtectionElements.SelectUnlockedCells);
    }

    private void ApplyWorksheetFormatting(
        IXLWorksheet worksheet,
        BoqTemplateGenerationRequest request,
        int headerRow,
        int dataEndRow)
    {
        // Set column widths
        var columnWidths = new Dictionary<string, double>
        {
            ["Level"] = 12,
            ["ItemNumber"] = 12,
            ["Description"] = 50,
            ["Quantity"] = 12,
            ["Uom"] = 10,
            ["UnitRate"] = 15,
            ["Amount"] = 18,
            ["Notes"] = 30
        };

        int col = 1;
        foreach (var column in request.IncludeColumns)
        {
            if (columnWidths.TryGetValue(column, out var width))
            {
                worksheet.Column(col).Width = width;
            }
            col++;
        }

        // Set row heights
        worksheet.Row(headerRow).Height = 30;

        // Apply right-to-left for Arabic
        if (request.Language == TemplateLanguage.Arabic)
        {
            worksheet.RightToLeft = true;
        }
    }

    private void SetupPrintLayout(IXLWorksheet worksheet)
    {
        worksheet.PageSetup.PageOrientation = XLPageOrientation.Landscape;
        worksheet.PageSetup.PaperSize = XLPaperSize.A4Paper;
        worksheet.PageSetup.FitToPages(1, 0); // Fit to 1 page wide, unlimited pages tall
        worksheet.PageSetup.PrintAreas.Clear();
        var rangeUsed = worksheet.RangeUsed();
        if (rangeUsed != null)
        {
            worksheet.PageSetup.PrintAreas.Add(rangeUsed.RangeAddress.ToString());
        }
        worksheet.PageSetup.Header.Left.AddText("CONFIDENTIAL - FOR BIDDING PURPOSE ONLY");
        worksheet.PageSetup.Footer.Center.AddText("Page &P of &N");
        worksheet.PageSetup.ShowGridlines = true;
        worksheet.PageSetup.Margins.SetLeft(0.5);
        worksheet.PageSetup.Margins.SetRight(0.5);
        worksheet.PageSetup.Margins.SetTop(0.75);
        worksheet.PageSetup.Margins.SetBottom(0.75);
    }

    private void BuildInstructionsWorksheet(IXLWorksheet worksheet, BoqTemplateGenerationRequest request)
    {
        int row = 1;
        bool isArabic = request.Language == TemplateLanguage.Arabic;

        // Title
        var titleCell = worksheet.Cell(row, 1);
        titleCell.Value = isArabic ? "تعليمات ملء جدول الكميات" : "BOQ Completion Instructions";
        titleCell.Style.Font.Bold = true;
        titleCell.Style.Font.FontSize = 16;
        titleCell.Style.Font.FontColor = HeaderBackgroundColor;
        row += 2;

        // Instructions list
        var instructions = isArabic
            ? GetArabicInstructions()
            : GetEnglishInstructions();

        foreach (var instruction in instructions)
        {
            var cell = worksheet.Cell(row, 1);
            cell.Value = instruction;
            cell.Style.Alignment.WrapText = true;
            row++;
        }

        // Pricing level guidance
        row += 1;
        var pricingTitle = isArabic ? "مستوى التسعير:" : "Pricing Level:";
        worksheet.Cell(row, 1).Value = pricingTitle;
        worksheet.Cell(row, 1).Style.Font.Bold = true;
        worksheet.Cell(row, 1).Style.Font.FontSize = 12;
        row++;

        var pricingInstructions = GetPricingLevelInstructions(request.PricingLevel, isArabic);
        foreach (var instruction in pricingInstructions)
        {
            var cell = worksheet.Cell(row, 1);
            cell.Value = instruction;
            cell.Style.Alignment.WrapText = true;
            row++;
        }

        // Color legend
        row += 2;
        worksheet.Cell(row, 1).Value = isArabic ? "دليل الألوان:" : "Color Legend:";
        worksheet.Cell(row, 1).Style.Font.Bold = true;
        row++;

        // Locked cells
        worksheet.Cell(row, 1).Value = isArabic ? "خلايا محمية (للقراءة فقط)" : "Protected cells (read-only)";
        worksheet.Cell(row, 2).Style.Fill.BackgroundColor = LockedCellColor;
        worksheet.Cell(row, 2).Style.Border.OutsideBorder = XLBorderStyleValues.Thin;
        row++;

        // Cells requiring input
        worksheet.Cell(row, 1).Value = isArabic ? "خلايا تحتاج إدخال" : "Cells requiring input";
        worksheet.Cell(row, 2).Style.Fill.BackgroundColor = HighlightColor;
        worksheet.Cell(row, 2).Style.Border.OutsideBorder = XLBorderStyleValues.Thin;
        row++;

        // Bill/section rows
        worksheet.Cell(row, 1).Value = isArabic ? "صفوف الأقسام (الفواتير)" : "Bill/Section header rows";
        worksheet.Cell(row, 2).Style.Fill.BackgroundColor = BillBackgroundColor;
        worksheet.Cell(row, 2).Style.Border.OutsideBorder = XLBorderStyleValues.Thin;
        row++;

        // Item group rows
        worksheet.Cell(row, 1).Value = isArabic ? "صفوف مجموعات البنود" : "Item group rows";
        worksheet.Cell(row, 2).Style.Fill.BackgroundColor = ItemGroupBackgroundColor;
        worksheet.Cell(row, 2).Style.Border.OutsideBorder = XLBorderStyleValues.Thin;
        row++;

        // Non-priceable rows
        worksheet.Cell(row, 1).Value = isArabic ? "صفوف غير قابلة للتسعير (للعرض فقط)" : "Non-priceable rows (reference only)";
        worksheet.Cell(row, 2).Style.Fill.BackgroundColor = NonPriceableBackgroundColor;
        worksheet.Cell(row, 2).Style.Border.OutsideBorder = XLBorderStyleValues.Thin;
        row++;

        // Format
        worksheet.Column(1).Width = 60;
        worksheet.Column(2).Width = 20;

        if (isArabic)
        {
            worksheet.RightToLeft = true;
        }
    }

    /// <summary>
    /// Returns pricing level-specific instructions for the instructions sheet.
    /// </summary>
    private static List<string> GetPricingLevelInstructions(PricingLevel pricingLevel, bool isArabic)
    {
        if (isArabic)
        {
            return pricingLevel switch
            {
                PricingLevel.Bill => new List<string>
                {
                    "• هذا المناقصة تستخدم تسعير على مستوى الفاتورة.",
                    "• يجب تقديم مبلغ إجمالي واحد لكل قسم/فاتورة.",
                    "• البنود الفردية مدرجة كمرجع فقط ولا تحتاج إلى تسعير.",
                    "• الصفوف الرمادية هي بنود مرجعية للقراءة فقط."
                },
                PricingLevel.Item => new List<string>
                {
                    "• هذا المناقصة تستخدم تسعير على مستوى البند.",
                    "• يجب إدخال سعر الوحدة لكل بند رئيسي.",
                    "• البنود الفرعية مدرجة كتفاصيل للقراءة فقط.",
                    "• الصفوف الرمادية هي بنود فرعية مرجعية ولا تحتاج إلى تسعير."
                },
                PricingLevel.SubItem => new List<string>
                {
                    "• هذا المناقصة تستخدم تسعير على مستوى البند الفرعي (الأكثر تفصيلاً).",
                    "• يجب إدخال سعر الوحدة لكل بند فرعي.",
                    "• مجموعات البنود هي عناوين ولا تحتاج إلى تسعير مباشر."
                },
                _ => new List<string>()
            };
        }

        return pricingLevel switch
        {
            PricingLevel.Bill => new List<string>
            {
                "- This tender uses BILL-LEVEL pricing.",
                "- You must provide a single lump-sum amount per bill/section.",
                "- Individual items are listed for reference only and do not require pricing.",
                "- Greyed-out rows are reference items (read-only)."
            },
            PricingLevel.Item => new List<string>
            {
                "- This tender uses ITEM-LEVEL pricing.",
                "- You must enter a unit rate for each main item.",
                "- Sub-items are listed as read-only detail for reference.",
                "- Greyed-out rows are sub-item details that do not require pricing."
            },
            PricingLevel.SubItem => new List<string>
            {
                "- This tender uses SUB-ITEM-LEVEL pricing (most granular).",
                "- You must enter a unit rate for each sub-item.",
                "- Item group headers do not require direct pricing."
            },
            _ => new List<string>()
        };
    }

    private static List<string> GetEnglishInstructions()
    {
        return new List<string>
        {
            "1. DO NOT modify the Item #, Description, Quantity, or UOM columns.",
            "2. Enter your Unit Rate for each line item in the 'Unit Rate' column.",
            "3. The Amount column is calculated automatically (Quantity x Unit Rate).",
            "4. All prices should be in the currency specified in the header.",
            "5. Yellow highlighted cells indicate required input.",
            "6. Use the dropdown list for UOM if available.",
            "7. Ensure all unit rates are filled before submission.",
            "8. Save the file in .xlsx format after completion.",
            "9. Do not add, delete, or reorder rows.",
            "10. Contact the procurement team for any clarifications."
        };
    }

    private static List<string> GetArabicInstructions()
    {
        return new List<string>
        {
            "1. لا تقم بتعديل أعمدة رقم البند أو الوصف أو الكمية أو وحدة القياس.",
            "2. أدخل سعر الوحدة لكل بند في عمود 'سعر الوحدة'.",
            "3. يتم حساب عمود المبلغ تلقائياً (الكمية × سعر الوحدة).",
            "4. يجب أن تكون جميع الأسعار بالعملة المحددة في الرأس.",
            "5. الخلايا المميزة باللون الأصفر تشير إلى إدخال مطلوب.",
            "6. استخدم القائمة المنسدلة لوحدة القياس إن توفرت.",
            "7. تأكد من ملء جميع أسعار الوحدات قبل التقديم.",
            "8. احفظ الملف بصيغة .xlsx بعد الانتهاء.",
            "9. لا تقم بإضافة أو حذف أو إعادة ترتيب الصفوف.",
            "10. تواصل مع فريق المشتريات لأي استفسارات."
        };
    }

    private static string GetSheetName(string baseName, TemplateLanguage language)
    {
        return language switch
        {
            TemplateLanguage.Arabic => baseName switch
            {
                "BOQ" => "جدول الكميات",
                "Instructions" => "التعليمات",
                _ => baseName
            },
            _ => baseName
        };
    }

    private static string GetColumnLetter(int columnNumber)
    {
        string columnLetter = string.Empty;
        while (columnNumber > 0)
        {
            int modulo = (columnNumber - 1) % 26;
            columnLetter = Convert.ToChar('A' + modulo) + columnLetter;
            columnNumber = (columnNumber - modulo) / 26;
        }
        return columnLetter;
    }

    private static string GenerateFileName(string tenderReference)
    {
        var sanitizedRef = string.Join("_", tenderReference.Split(Path.GetInvalidFileNameChars()));
        return $"BOQ_Template_{sanitizedRef}_{DateTime.UtcNow:yyyyMMdd_HHmmss}";
    }
}
