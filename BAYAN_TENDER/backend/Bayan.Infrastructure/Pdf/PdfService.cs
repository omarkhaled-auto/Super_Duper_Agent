using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Evaluation.DTOs;
using Bayan.Domain.Entities;
using Microsoft.Extensions.Logging;
using QuestPDF.Fluent;
using QuestPDF.Helpers;
using QuestPDF.Infrastructure;
using QuestPdfDocument = QuestPDF.Fluent.Document;

namespace Bayan.Infrastructure.Pdf;

/// <summary>
/// PDF generation service using QuestPDF.
/// </summary>
public class PdfService : IPdfService
{
    private readonly ILogger<PdfService> _logger;

    // Color definitions for consistent styling
    private static readonly string PrimaryColor = "#2563eb";
    private static readonly string HeaderBgColor = "#1e40af";
    private static readonly string LightGrayBg = "#f8fafc";
    private static readonly string BorderColor = "#e5e7eb";
    private static readonly string TextColor = "#1f2937";
    private static readonly string SecondaryTextColor = "#6b7280";
    private static readonly string SuccessColor = "#059669";
    private static readonly string WarningColor = "#dc2626";

    static PdfService()
    {
        // Configure QuestPDF license for community use
        QuestPDF.Settings.License = LicenseType.Community;
    }

    public PdfService(ILogger<PdfService> logger)
    {
        _logger = logger;
    }

    /// <inheritdoc />
    public Task<byte[]> GenerateBulletinPdfAsync(
        ClarificationBulletin bulletin,
        Tender tender,
        IEnumerable<Clarification> clarifications,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Generating PDF for Bulletin #{BulletinNumber} of Tender {TenderReference}",
            bulletin.BulletinNumber, tender.Reference);

        var clarificationsList = clarifications.ToList();
        var bulletinReference = $"QB-{bulletin.BulletinNumber:D3}";

        var document = QuestPdfDocument.Create(container =>
        {
            container.Page(page =>
            {
                page.Size(PageSizes.A4);
                page.MarginTop(1, Unit.Centimetre);
                page.MarginBottom(1.5f, Unit.Centimetre);
                page.MarginHorizontal(1.5f, Unit.Centimetre);

                // Header
                page.Header().Element(c => ComposeHeader(c, bulletinReference, tender));

                // Content
                page.Content().Element(c => ComposeContent(c, bulletin, tender, clarificationsList));

                // Footer
                page.Footer().Element(c => ComposeFooter(c, tender.Reference));
            });
        });

        var pdfBytes = document.GeneratePdf();

        _logger.LogInformation(
            "Successfully generated PDF for Bulletin #{BulletinNumber}, size: {Size} bytes",
            bulletin.BulletinNumber, pdfBytes.Length);

        return Task.FromResult(pdfBytes);
    }

    /// <inheritdoc />
    public Task<byte[]> GenerateBidReceiptPdfAsync(
        BidSubmission bidSubmission,
        Tender tender,
        Bidder bidder,
        IEnumerable<BidDocument> bidDocuments,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Generating bid receipt PDF for Receipt #{ReceiptNumber} of Tender {TenderReference}",
            bidSubmission.ReceiptNumber, tender.Reference);

        var documentsList = bidDocuments.ToList();

        var document = QuestPdfDocument.Create(container =>
        {
            container.Page(page =>
            {
                page.Size(PageSizes.A4);
                page.MarginTop(1, Unit.Centimetre);
                page.MarginBottom(1.5f, Unit.Centimetre);
                page.MarginHorizontal(1.5f, Unit.Centimetre);

                // Header
                page.Header().Element(c => ComposeBidReceiptHeader(c, bidSubmission, tender));

                // Content
                page.Content().Element(c => ComposeBidReceiptContent(c, bidSubmission, tender, bidder, documentsList));

                // Footer
                page.Footer().Element(c => ComposeBidReceiptFooter(c, bidSubmission.ReceiptNumber));
            });
        });

        var pdfBytes = document.GeneratePdf();

        _logger.LogInformation(
            "Successfully generated bid receipt PDF for Receipt #{ReceiptNumber}, size: {Size} bytes",
            bidSubmission.ReceiptNumber, pdfBytes.Length);

        return Task.FromResult(pdfBytes);
    }

    private void ComposeBidReceiptHeader(IContainer container, BidSubmission bidSubmission, Tender tender)
    {
        container.Column(column =>
        {
            // Top banner with company branding
            column.Item().Background(SuccessColor).Padding(15).Row(row =>
            {
                // Logo placeholder (left side)
                row.RelativeItem(1).AlignLeft().AlignMiddle().Text(text =>
                {
                    text.Span("BAYAN").FontSize(20).Bold().FontColor(Colors.White);
                    text.Span(" Tender System").FontSize(14).FontColor(Colors.White);
                });

                // Receipt title (right side)
                row.RelativeItem(1).AlignRight().AlignMiddle().Text(text =>
                {
                    text.Span("BID RECEIPT").FontSize(18).Bold().FontColor(Colors.White);
                });
            });

            // Late submission warning banner if applicable
            if (bidSubmission.IsLate)
            {
                column.Item().Background(WarningColor).Padding(10).AlignCenter()
                    .Text("LATE SUBMISSION")
                    .FontSize(14).Bold().FontColor(Colors.White);
            }

            // Receipt info section
            column.Item().PaddingVertical(15).Background(LightGrayBg).Padding(15).Row(row =>
            {
                // Left column - Receipt details
                row.RelativeItem(1).Column(col =>
                {
                    col.Item().Text(text =>
                    {
                        text.Span("Receipt Number: ").Bold().FontSize(11).FontColor(TextColor);
                        text.Span(bidSubmission.ReceiptNumber).FontSize(11).FontColor(SuccessColor).Bold();
                    });
                    col.Item().PaddingTop(5).Text(text =>
                    {
                        text.Span("Submission Date: ").Bold().FontSize(10).FontColor(TextColor);
                        text.Span(bidSubmission.SubmissionTime.ToString("MMMM dd, yyyy HH:mm:ss 'UTC'"))
                            .FontSize(10).FontColor(SecondaryTextColor);
                    });
                });

                // Right column - Tender details
                row.RelativeItem(1).Column(col =>
                {
                    col.Item().Text(text =>
                    {
                        text.Span("Tender Reference: ").Bold().FontSize(10).FontColor(TextColor);
                        text.Span(tender.Reference).FontSize(10).FontColor(SecondaryTextColor);
                    });
                    col.Item().PaddingTop(5).Text(text =>
                    {
                        text.Span("Tender Title: ").Bold().FontSize(10).FontColor(TextColor);
                    });
                    col.Item().Text(tender.Title).FontSize(10).FontColor(PrimaryColor);
                });
            });

            // Separator line
            column.Item().LineHorizontal(1).LineColor(BorderColor);
        });
    }

    private void ComposeBidReceiptContent(
        IContainer container,
        BidSubmission bidSubmission,
        Tender tender,
        Bidder bidder,
        List<BidDocument> documents)
    {
        container.PaddingVertical(10).Column(column =>
        {
            // Bidder Information Section
            column.Item().PaddingBottom(15).Column(bidderCol =>
            {
                bidderCol.Item().Text("Bidder Information").FontSize(12).Bold().FontColor(HeaderBgColor);
                bidderCol.Item().PaddingTop(10).Background(LightGrayBg).Padding(15).Column(infoCol =>
                {
                    infoCol.Item().Row(row =>
                    {
                        row.RelativeItem().Column(leftCol =>
                        {
                            leftCol.Item().Text(text =>
                            {
                                text.Span("Company Name: ").Bold().FontSize(10).FontColor(TextColor);
                            });
                            leftCol.Item().Text(bidder.CompanyName).FontSize(10).FontColor(SecondaryTextColor);
                        });

                        row.RelativeItem().Column(rightCol =>
                        {
                            rightCol.Item().Text(text =>
                            {
                                text.Span("Contact Person: ").Bold().FontSize(10).FontColor(TextColor);
                            });
                            rightCol.Item().Text(bidder.ContactPerson).FontSize(10).FontColor(SecondaryTextColor);
                        });
                    });

                    infoCol.Item().PaddingTop(10).Row(row =>
                    {
                        row.RelativeItem().Column(leftCol =>
                        {
                            leftCol.Item().Text(text =>
                            {
                                text.Span("Email: ").Bold().FontSize(10).FontColor(TextColor);
                            });
                            leftCol.Item().Text(bidder.Email).FontSize(10).FontColor(SecondaryTextColor);
                        });

                        if (!string.IsNullOrEmpty(bidder.CRNumber))
                        {
                            row.RelativeItem().Column(rightCol =>
                            {
                                rightCol.Item().Text(text =>
                                {
                                    text.Span("CR Number: ").Bold().FontSize(10).FontColor(TextColor);
                                });
                                rightCol.Item().Text(bidder.CRNumber).FontSize(10).FontColor(SecondaryTextColor);
                            });
                        }
                    });
                });
            });

            column.Item().PaddingBottom(10).LineHorizontal(0.5f).LineColor(BorderColor);

            // Submission Details Section
            column.Item().PaddingBottom(15).Column(detailsCol =>
            {
                detailsCol.Item().Text("Submission Details").FontSize(12).Bold().FontColor(HeaderBgColor);
                detailsCol.Item().PaddingTop(10).Background(LightGrayBg).Padding(15).Column(infoCol =>
                {
                    infoCol.Item().Row(row =>
                    {
                        row.RelativeItem().Column(leftCol =>
                        {
                            leftCol.Item().Text(text =>
                            {
                                text.Span("Submission Deadline: ").Bold().FontSize(10).FontColor(TextColor);
                            });
                            leftCol.Item().Text(tender.SubmissionDeadline.ToString("MMMM dd, yyyy HH:mm:ss 'UTC'"))
                                .FontSize(10).FontColor(SecondaryTextColor);
                        });

                        row.RelativeItem().Column(rightCol =>
                        {
                            rightCol.Item().Text(text =>
                            {
                                text.Span("Actual Submission: ").Bold().FontSize(10).FontColor(TextColor);
                            });
                            rightCol.Item().Text(bidSubmission.SubmissionTime.ToString("MMMM dd, yyyy HH:mm:ss 'UTC'"))
                                .FontSize(10).FontColor(bidSubmission.IsLate ? WarningColor : SuccessColor);
                        });
                    });

                    infoCol.Item().PaddingTop(10).Row(row =>
                    {
                        row.RelativeItem().Column(leftCol =>
                        {
                            leftCol.Item().Text(text =>
                            {
                                text.Span("Bid Validity: ").Bold().FontSize(10).FontColor(TextColor);
                            });
                            leftCol.Item().Text($"{bidSubmission.BidValidityDays} days")
                                .FontSize(10).FontColor(SecondaryTextColor);
                        });

                        row.RelativeItem().Column(rightCol =>
                        {
                            rightCol.Item().Text(text =>
                            {
                                text.Span("Submission Status: ").Bold().FontSize(10).FontColor(TextColor);
                            });
                            rightCol.Item().Text(bidSubmission.IsLate ? "LATE" : "On Time")
                                .FontSize(10).Bold().FontColor(bidSubmission.IsLate ? WarningColor : SuccessColor);
                        });
                    });
                });
            });

            column.Item().PaddingBottom(10).LineHorizontal(0.5f).LineColor(BorderColor);

            // Submitted Documents Section
            column.Item().PaddingBottom(15).Column(docsCol =>
            {
                docsCol.Item().Text("Submitted Documents").FontSize(12).Bold().FontColor(HeaderBgColor);
                docsCol.Item().PaddingTop(10);

                // Documents table
                docsCol.Item().Table(table =>
                {
                    // Define columns
                    table.ColumnsDefinition(columns =>
                    {
                        columns.ConstantColumn(30);  // Row number
                        columns.RelativeColumn(2);   // Document type
                        columns.RelativeColumn(3);   // File name
                        columns.RelativeColumn(1);   // File size
                    });

                    // Header row
                    table.Header(header =>
                    {
                        header.Cell().Background(HeaderBgColor).Padding(8)
                            .Text("#").FontSize(9).Bold().FontColor(Colors.White);
                        header.Cell().Background(HeaderBgColor).Padding(8)
                            .Text("Document Type").FontSize(9).Bold().FontColor(Colors.White);
                        header.Cell().Background(HeaderBgColor).Padding(8)
                            .Text("File Name").FontSize(9).Bold().FontColor(Colors.White);
                        header.Cell().Background(HeaderBgColor).Padding(8).AlignRight()
                            .Text("Size").FontSize(9).Bold().FontColor(Colors.White);
                    });

                    // Document rows
                    int rowNum = 1;
                    foreach (var doc in documents.OrderBy(d => d.DocumentType))
                    {
                        var bgColor = rowNum % 2 == 0 ? LightGrayBg : Colors.White.ToString();

                        table.Cell().Background(bgColor).Padding(8)
                            .Text(rowNum.ToString()).FontSize(9).FontColor(TextColor);
                        table.Cell().Background(bgColor).Padding(8)
                            .Text(doc.DocumentType.ToString()).FontSize(9).Bold().FontColor(TextColor);
                        table.Cell().Background(bgColor).Padding(8)
                            .Text(doc.FileName).FontSize(9).FontColor(SecondaryTextColor);
                        table.Cell().Background(bgColor).Padding(8).AlignRight()
                            .Text(FormatFileSize(doc.FileSizeBytes)).FontSize(9).FontColor(SecondaryTextColor);

                        rowNum++;
                    }
                });

                // Total files summary
                var totalSize = documents.Sum(d => d.FileSizeBytes);
                docsCol.Item().PaddingTop(10).AlignRight().Text(text =>
                {
                    text.Span($"Total: {documents.Count} files, ").FontSize(10).FontColor(SecondaryTextColor);
                    text.Span(FormatFileSize(totalSize)).FontSize(10).Bold().FontColor(TextColor);
                });
            });

            // Signature section
            column.Item().PaddingTop(30).Column(sigCol =>
            {
                sigCol.Item().LineHorizontal(0.5f).LineColor(BorderColor);
                sigCol.Item().PaddingTop(20).Row(row =>
                {
                    row.RelativeItem().Column(leftCol =>
                    {
                        leftCol.Item().Text("Authorized Signature:").FontSize(10).Bold().FontColor(TextColor);
                        leftCol.Item().PaddingTop(30).LineHorizontal(1).LineColor(TextColor);
                        leftCol.Item().PaddingTop(5).Text("Date: _________________")
                            .FontSize(9).FontColor(SecondaryTextColor);
                    });

                    row.ConstantItem(50); // Spacer

                    row.RelativeItem().Column(rightCol =>
                    {
                        rightCol.Item().Text("Official Stamp:").FontSize(10).Bold().FontColor(TextColor);
                        rightCol.Item().PaddingTop(5).Height(60).Background(LightGrayBg)
                            .Border(1).BorderColor(BorderColor).AlignCenter().AlignMiddle()
                            .Text("").FontSize(9).FontColor(SecondaryTextColor);
                    });
                });
            });

            // Important notice at the end
            column.Item().PaddingTop(20).Background(LightGrayBg).Padding(10).Column(noticeCol =>
            {
                noticeCol.Item().Text("Important Notice").FontSize(10).Bold().FontColor(TextColor);
                noticeCol.Item().PaddingTop(5).Text(
                    "This receipt confirms the submission of your bid documents. It does not constitute acceptance or " +
                    "evaluation of your bid. The evaluation process will commence after the tender opening date. " +
                    "Please retain this receipt for your records.")
                    .FontSize(9).FontColor(SecondaryTextColor).LineHeight(1.3f);
            });
        });
    }

    private void ComposeBidReceiptFooter(IContainer container, string receiptNumber)
    {
        container.Column(column =>
        {
            column.Item().LineHorizontal(1).LineColor(BorderColor);
            column.Item().PaddingTop(10).Row(row =>
            {
                // Left side - Receipt number
                row.RelativeItem().AlignLeft().Text(text =>
                {
                    text.Span("Receipt: ").FontSize(8).FontColor(SecondaryTextColor);
                    text.Span(receiptNumber).FontSize(8).Bold().FontColor(TextColor);
                });

                // Center - Page number
                row.RelativeItem().AlignCenter().Text(text =>
                {
                    text.Span("Page ").FontSize(8).FontColor(SecondaryTextColor);
                    text.CurrentPageNumber().FontSize(8).FontColor(TextColor);
                    text.Span(" of ").FontSize(8).FontColor(SecondaryTextColor);
                    text.TotalPages().FontSize(8).FontColor(TextColor);
                });

                // Right side - Generated timestamp
                row.RelativeItem().AlignRight().Text(text =>
                {
                    text.Span("Generated: ").FontSize(8).FontColor(SecondaryTextColor);
                    text.Span(DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm UTC")).FontSize(8).FontColor(TextColor);
                });
            });

            // Confidentiality notice
            column.Item().PaddingTop(5).AlignCenter().Text(
                "OFFICIAL DOCUMENT - Bayan Tender Management System")
                .FontSize(7).FontColor(SecondaryTextColor).Italic();
        });
    }

    private static string FormatFileSize(long bytes)
    {
        string[] sizes = { "B", "KB", "MB", "GB", "TB" };
        int order = 0;
        double size = bytes;

        while (size >= 1024 && order < sizes.Length - 1)
        {
            order++;
            size /= 1024;
        }

        return $"{size:0.##} {sizes[order]}";
    }

    private void ComposeHeader(IContainer container, string bulletinReference, Tender tender)
    {
        container.Column(column =>
        {
            // Top banner with company branding
            column.Item().Background(HeaderBgColor).Padding(15).Row(row =>
            {
                // Logo placeholder (left side)
                row.RelativeItem(1).AlignLeft().AlignMiddle().Text(text =>
                {
                    text.Span("BAYAN").FontSize(20).Bold().FontColor(Colors.White);
                    text.Span(" Tender System").FontSize(14).FontColor(Colors.White);
                });

                // Bulletin title (right side)
                row.RelativeItem(1).AlignRight().AlignMiddle().Text(text =>
                {
                    text.Span("Q&A BULLETIN").FontSize(18).Bold().FontColor(Colors.White);
                });
            });

            // Bulletin info section
            column.Item().PaddingVertical(15).Background(LightGrayBg).Padding(15).Row(row =>
            {
                // Left column - Bulletin details
                row.RelativeItem(1).Column(col =>
                {
                    col.Item().Text(text =>
                    {
                        text.Span("Bulletin Number: ").Bold().FontSize(11).FontColor(TextColor);
                        text.Span(bulletinReference).FontSize(11).FontColor(PrimaryColor).Bold();
                    });
                    col.Item().PaddingTop(5).Text(text =>
                    {
                        text.Span("Issue Date: ").Bold().FontSize(10).FontColor(TextColor);
                        text.Span(DateTime.UtcNow.ToString("MMMM dd, yyyy")).FontSize(10).FontColor(SecondaryTextColor);
                    });
                });

                // Right column - Tender details
                row.RelativeItem(1).Column(col =>
                {
                    col.Item().Text(text =>
                    {
                        text.Span("Tender Reference: ").Bold().FontSize(10).FontColor(TextColor);
                        text.Span(tender.Reference).FontSize(10).FontColor(SecondaryTextColor);
                    });
                    col.Item().PaddingTop(5).Text(text =>
                    {
                        text.Span("Tender Title: ").Bold().FontSize(10).FontColor(TextColor);
                    });
                    col.Item().Text(tender.Title).FontSize(10).FontColor(PrimaryColor);
                });
            });

            // Separator line
            column.Item().LineHorizontal(1).LineColor(BorderColor);
        });
    }

    private void ComposeContent(
        IContainer container,
        ClarificationBulletin bulletin,
        Tender tender,
        List<Clarification> clarifications)
    {
        container.PaddingVertical(10).Column(column =>
        {
            // Introduction section
            if (!string.IsNullOrWhiteSpace(bulletin.Introduction))
            {
                column.Item().PaddingBottom(15).Column(introCol =>
                {
                    introCol.Item().Text("Introduction").FontSize(12).Bold().FontColor(HeaderBgColor);
                    introCol.Item().PaddingTop(5).Text(bulletin.Introduction)
                        .FontSize(10).FontColor(TextColor).LineHeight(1.4f);
                });

                column.Item().PaddingBottom(10).LineHorizontal(0.5f).LineColor(BorderColor);
            }

            // Q&A List section header
            column.Item().PaddingBottom(10).Text("Questions & Answers")
                .FontSize(14).Bold().FontColor(HeaderBgColor);

            // Q&A items
            int questionNumber = 1;
            foreach (var clarification in clarifications.OrderBy(c => c.ReferenceNumber))
            {
                column.Item().Element(c => ComposeQaItem(c, clarification, questionNumber));
                questionNumber++;
            }

            // Closing notes section
            if (!string.IsNullOrWhiteSpace(bulletin.ClosingNotes))
            {
                column.Item().PaddingTop(15).LineHorizontal(0.5f).LineColor(BorderColor);
                column.Item().PaddingTop(15).Column(closingCol =>
                {
                    closingCol.Item().Text("Closing Notes").FontSize(12).Bold().FontColor(HeaderBgColor);
                    closingCol.Item().PaddingTop(5).Text(bulletin.ClosingNotes)
                        .FontSize(10).FontColor(TextColor).LineHeight(1.4f);
                });
            }

            // Important notice at the end
            column.Item().PaddingTop(20).Background(LightGrayBg).Padding(10).Column(noticeCol =>
            {
                noticeCol.Item().Text("Important Notice").FontSize(10).Bold().FontColor(TextColor);
                noticeCol.Item().PaddingTop(5).Text(
                    "This Q&A Bulletin forms an integral part of the tender documentation. All bidders are required " +
                    "to acknowledge receipt and consider the contents herein when preparing their submissions. " +
                    "The clarifications provided supersede any conflicting information in the original tender documents.")
                    .FontSize(9).FontColor(SecondaryTextColor).LineHeight(1.3f);
            });
        });
    }

    private void ComposeQaItem(IContainer container, Clarification clarification, int number)
    {
        container.PaddingBottom(15).Column(column =>
        {
            // Question header with number and reference
            column.Item().Background(LightGrayBg).Padding(10).Row(row =>
            {
                // Question number badge
                row.ConstantItem(40).AlignCenter().AlignMiddle()
                    .Background(PrimaryColor)
                    .Padding(5)
                    .Text($"Q{number}")
                    .FontSize(12).Bold().FontColor(Colors.White);

                // Question details
                row.RelativeItem().PaddingLeft(10).Column(detailsCol =>
                {
                    detailsCol.Item().Row(detailsRow =>
                    {
                        detailsRow.RelativeItem().Text(text =>
                        {
                            text.Span("Reference: ").FontSize(9).FontColor(SecondaryTextColor);
                            text.Span(clarification.ReferenceNumber).FontSize(9).Bold().FontColor(TextColor);
                        });

                        if (!string.IsNullOrWhiteSpace(clarification.RelatedBoqSection))
                        {
                            detailsRow.RelativeItem().AlignRight().Text(text =>
                            {
                                text.Span("BOQ Section: ").FontSize(9).FontColor(SecondaryTextColor);
                                text.Span(clarification.RelatedBoqSection).FontSize(9).FontColor(TextColor);
                            });
                        }
                    });

                    detailsCol.Item().PaddingTop(3).Text(clarification.Subject)
                        .FontSize(11).Bold().FontColor(TextColor);
                });
            });

            // Question text
            column.Item().PaddingTop(10).PaddingHorizontal(10).Column(qCol =>
            {
                qCol.Item().Text("Question:").FontSize(10).Bold().FontColor(PrimaryColor);
                qCol.Item().PaddingTop(3).Text(clarification.Question)
                    .FontSize(10).FontColor(TextColor).LineHeight(1.4f);
            });

            // Answer text
            column.Item().PaddingTop(10).PaddingHorizontal(10).Column(aCol =>
            {
                aCol.Item().Text("Answer:").FontSize(10).Bold().FontColor("#059669"); // Green color for answer
                aCol.Item().PaddingTop(3).Text(clarification.Answer ?? "No answer provided.")
                    .FontSize(10).FontColor(TextColor).LineHeight(1.4f);
            });

            // Separator line
            column.Item().PaddingTop(10).LineHorizontal(0.5f).LineColor(BorderColor);
        });
    }

    private void ComposeFooter(IContainer container, string tenderReference)
    {
        container.Column(column =>
        {
            column.Item().LineHorizontal(1).LineColor(BorderColor);
            column.Item().PaddingTop(10).Row(row =>
            {
                // Left side - Tender reference
                row.RelativeItem().AlignLeft().Text(text =>
                {
                    text.Span("Tender: ").FontSize(8).FontColor(SecondaryTextColor);
                    text.Span(tenderReference).FontSize(8).Bold().FontColor(TextColor);
                });

                // Center - Page number
                row.RelativeItem().AlignCenter().Text(text =>
                {
                    text.Span("Page ").FontSize(8).FontColor(SecondaryTextColor);
                    text.CurrentPageNumber().FontSize(8).FontColor(TextColor);
                    text.Span(" of ").FontSize(8).FontColor(SecondaryTextColor);
                    text.TotalPages().FontSize(8).FontColor(TextColor);
                });

                // Right side - Generated timestamp
                row.RelativeItem().AlignRight().Text(text =>
                {
                    text.Span("Generated: ").FontSize(8).FontColor(SecondaryTextColor);
                    text.Span(DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm UTC")).FontSize(8).FontColor(TextColor);
                });
            });

            // Confidentiality notice
            column.Item().PaddingTop(5).AlignCenter().Text(
                "CONFIDENTIAL - This document is intended for authorized recipients only.")
                .FontSize(7).FontColor(SecondaryTextColor).Italic();
        });
    }

    /// <inheritdoc />
    public Task<byte[]> GenerateAwardPackPdfAsync(
        AwardPackDataDto data,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation(
            "Generating Award Pack PDF for Tender {TenderReference}",
            data.TenderReference);

        var document = QuestPdfDocument.Create(container =>
        {
            container.Page(page =>
            {
                page.Size(PageSizes.A4);
                page.MarginTop(1, Unit.Centimetre);
                page.MarginBottom(1.5f, Unit.Centimetre);
                page.MarginHorizontal(1.5f, Unit.Centimetre);

                // Header
                page.Header().Element(c => ComposeAwardPackHeader(c, data));

                // Content
                page.Content().Element(c => ComposeAwardPackContent(c, data));

                // Footer
                page.Footer().Element(c => ComposeAwardPackFooter(c, data.TenderReference));
            });
        });

        var pdfBytes = document.GeneratePdf();

        _logger.LogInformation(
            "Successfully generated Award Pack PDF for Tender {TenderReference}, size: {Size} bytes",
            data.TenderReference, pdfBytes.Length);

        return Task.FromResult(pdfBytes);
    }

    private void ComposeAwardPackHeader(IContainer container, AwardPackDataDto data)
    {
        container.Column(column =>
        {
            // Top banner
            column.Item().Background(HeaderBgColor).Padding(15).Row(row =>
            {
                row.RelativeItem(1).AlignLeft().AlignMiddle().Text(text =>
                {
                    text.Span("BAYAN").FontSize(20).Bold().FontColor(Colors.White);
                    text.Span(" Tender System").FontSize(14).FontColor(Colors.White);
                });

                row.RelativeItem(1).AlignRight().AlignMiddle().Text(text =>
                {
                    text.Span("AWARD RECOMMENDATION PACK").FontSize(16).Bold().FontColor(Colors.White);
                });
            });

            // Tender info section
            column.Item().PaddingVertical(15).Background(LightGrayBg).Padding(15).Row(row =>
            {
                row.RelativeItem(1).Column(col =>
                {
                    col.Item().Text(text =>
                    {
                        text.Span("Tender Reference: ").Bold().FontSize(10).FontColor(TextColor);
                        text.Span(data.TenderReference).FontSize(10).FontColor(PrimaryColor).Bold();
                    });
                    col.Item().PaddingTop(5).Text(text =>
                    {
                        text.Span("Client: ").Bold().FontSize(10).FontColor(TextColor);
                        text.Span(data.ClientName).FontSize(10).FontColor(SecondaryTextColor);
                    });
                });

                row.RelativeItem(1).Column(col =>
                {
                    col.Item().Text(text =>
                    {
                        text.Span("Tender Title: ").Bold().FontSize(10).FontColor(TextColor);
                    });
                    col.Item().Text(data.TenderTitle).FontSize(10).FontColor(PrimaryColor);
                    col.Item().PaddingTop(5).Text(text =>
                    {
                        text.Span("Generated: ").Bold().FontSize(10).FontColor(TextColor);
                        text.Span(data.GeneratedAt.ToString("MMMM dd, yyyy HH:mm 'UTC'"))
                            .FontSize(10).FontColor(SecondaryTextColor);
                    });
                });
            });

            column.Item().LineHorizontal(1).LineColor(BorderColor);
        });
    }

    private void ComposeAwardPackContent(IContainer container, AwardPackDataDto data)
    {
        container.PaddingVertical(10).Column(column =>
        {
            // Table of Contents
            column.Item().Element(c => ComposeTableOfContents(c, data));

            // Executive Summary
            column.Item().PageBreak();
            column.Item().Element(c => ComposeExecutiveSummary(c, data));

            // Evaluation Methodology
            column.Item().PageBreak();
            column.Item().Element(c => ComposeEvaluationMethodology(c, data));

            // Technical Evaluation Results
            if (data.IncludeTechnicalDetails && data.TechnicalResults.Any())
            {
                column.Item().PageBreak();
                column.Item().Element(c => ComposeTechnicalEvaluationSection(c, data));
            }

            // Commercial Evaluation Results
            if (data.IncludeCommercialDetails && data.CommercialResults.Any())
            {
                column.Item().PageBreak();
                column.Item().Element(c => ComposeCommercialEvaluationSection(c, data));
            }

            // Combined Scorecard
            if (data.CombinedScorecard != null && data.CombinedScorecard.Entries.Any())
            {
                column.Item().PageBreak();
                column.Item().Element(c => ComposeCombinedScorecardSection(c, data));
            }

            // Sensitivity Analysis
            if (data.IncludeSensitivityAnalysis && data.SensitivityAnalysis != null && data.SensitivityAnalysis.Rows.Any())
            {
                column.Item().PageBreak();
                column.Item().Element(c => ComposeSensitivityAnalysisSection(c, data));
            }

            // Recommendation
            if (data.Recommendation != null)
            {
                column.Item().PageBreak();
                column.Item().Element(c => ComposeRecommendationSection(c, data));
            }

            // Exceptions/Risks
            if (data.IncludeExceptions && data.Exceptions.Any())
            {
                column.Item().PageBreak();
                column.Item().Element(c => ComposeExceptionsSection(c, data));
            }

            // Appendices placeholder
            column.Item().PageBreak();
            column.Item().Element(c => ComposeAppendicesSection(c, data));
        });
    }

    private void ComposeTableOfContents(IContainer container, AwardPackDataDto data)
    {
        container.Column(column =>
        {
            column.Item().Text("TABLE OF CONTENTS").FontSize(14).Bold().FontColor(HeaderBgColor);
            column.Item().PaddingTop(15);

            var sections = new List<string>
            {
                "1. Executive Summary",
                "2. Evaluation Methodology"
            };

            int sectionNum = 3;

            if (data.IncludeTechnicalDetails && data.TechnicalResults.Any())
                sections.Add($"{sectionNum++}. Technical Evaluation Results");

            if (data.IncludeCommercialDetails && data.CommercialResults.Any())
                sections.Add($"{sectionNum++}. Commercial Evaluation Results");

            if (data.CombinedScorecard != null && data.CombinedScorecard.Entries.Any())
                sections.Add($"{sectionNum++}. Combined Scorecard");

            if (data.IncludeSensitivityAnalysis && data.SensitivityAnalysis != null)
                sections.Add($"{sectionNum++}. Sensitivity Analysis");

            if (data.Recommendation != null)
                sections.Add($"{sectionNum++}. Recommendation");

            if (data.IncludeExceptions && data.Exceptions.Any())
                sections.Add($"{sectionNum++}. Exceptions & Risks");

            sections.Add($"{sectionNum}. Appendices");

            foreach (var section in sections)
            {
                column.Item().PaddingVertical(3).Text(section).FontSize(11).FontColor(TextColor);
            }
        });
    }

    private void ComposeExecutiveSummary(IContainer container, AwardPackDataDto data)
    {
        container.Column(column =>
        {
            column.Item().Text("1. EXECUTIVE SUMMARY").FontSize(14).Bold().FontColor(HeaderBgColor);
            column.Item().PaddingTop(15);

            if (!string.IsNullOrWhiteSpace(data.ExecutiveSummary))
            {
                column.Item().Text(data.ExecutiveSummary).FontSize(10).FontColor(TextColor).LineHeight(1.4f);
            }
            else
            {
                // Auto-generated summary
                column.Item().Text(text =>
                {
                    text.Span("This Award Recommendation Pack presents the evaluation results for tender ")
                        .FontSize(10).FontColor(TextColor);
                    text.Span(data.TenderReference).FontSize(10).Bold().FontColor(PrimaryColor);
                    text.Span(" - ").FontSize(10).FontColor(TextColor);
                    text.Span(data.TenderTitle).FontSize(10).FontColor(TextColor);
                    text.Span(".").FontSize(10).FontColor(TextColor);
                });

                column.Item().PaddingTop(10);

                // Key facts
                column.Item().Background(LightGrayBg).Padding(10).Column(factsCol =>
                {
                    factsCol.Item().Text("Key Facts:").FontSize(10).Bold().FontColor(TextColor);
                    factsCol.Item().PaddingTop(5);

                    factsCol.Item().Text(text =>
                    {
                        text.Span("Client: ").FontSize(10).Bold().FontColor(SecondaryTextColor);
                        text.Span(data.ClientName).FontSize(10).FontColor(TextColor);
                    });

                    factsCol.Item().Text(text =>
                    {
                        text.Span("Tender Type: ").FontSize(10).Bold().FontColor(SecondaryTextColor);
                        text.Span(data.TenderType.ToString()).FontSize(10).FontColor(TextColor);
                    });

                    factsCol.Item().Text(text =>
                    {
                        text.Span("Evaluation Weighting: ").FontSize(10).Bold().FontColor(SecondaryTextColor);
                        text.Span($"Technical {data.TechnicalWeight}% / Commercial {data.CommercialWeight}%")
                            .FontSize(10).FontColor(TextColor);
                    });

                    factsCol.Item().Text(text =>
                    {
                        text.Span("Bidders Evaluated: ").FontSize(10).Bold().FontColor(SecondaryTextColor);
                        text.Span(data.CombinedScorecard?.Entries.Count.ToString() ?? "N/A")
                            .FontSize(10).FontColor(TextColor);
                    });

                    if (data.Recommendation != null)
                    {
                        factsCol.Item().Text(text =>
                        {
                            text.Span("Recommended Bidder: ").FontSize(10).Bold().FontColor(SecondaryTextColor);
                            text.Span(data.Recommendation.RecommendedBidderName).FontSize(10).FontColor(SuccessColor).Bold();
                        });

                        factsCol.Item().Text(text =>
                        {
                            text.Span("Recommended Amount: ").FontSize(10).Bold().FontColor(SecondaryTextColor);
                            text.Span($"{data.BaseCurrency} {data.Recommendation.RecommendedBidAmount:N2}")
                                .FontSize(10).FontColor(TextColor);
                        });
                    }
                });
            }
        });
    }

    private void ComposeEvaluationMethodology(IContainer container, AwardPackDataDto data)
    {
        container.Column(column =>
        {
            column.Item().Text("2. EVALUATION METHODOLOGY").FontSize(14).Bold().FontColor(HeaderBgColor);
            column.Item().PaddingTop(15);

            column.Item().Text(
                "The evaluation was conducted using a weighted scoring approach combining technical and commercial assessments.")
                .FontSize(10).FontColor(TextColor).LineHeight(1.4f);

            column.Item().PaddingTop(10);

            // Weighting breakdown
            column.Item().Text("Weighting:").FontSize(11).Bold().FontColor(TextColor);
            column.Item().PaddingTop(5).Row(row =>
            {
                row.RelativeItem().Background(PrimaryColor).Padding(10).AlignCenter()
                    .Text($"Technical: {data.TechnicalWeight}%").FontSize(12).Bold().FontColor(Colors.White);
                row.ConstantItem(10);
                row.RelativeItem().Background(SuccessColor).Padding(10).AlignCenter()
                    .Text($"Commercial: {data.CommercialWeight}%").FontSize(12).Bold().FontColor(Colors.White);
            });

            // Technical criteria table
            if (data.EvaluationCriteria.Any())
            {
                column.Item().PaddingTop(20);
                column.Item().Text("Technical Evaluation Criteria:").FontSize(11).Bold().FontColor(TextColor);
                column.Item().PaddingTop(10);

                column.Item().Table(table =>
                {
                    table.ColumnsDefinition(columns =>
                    {
                        columns.ConstantColumn(30);
                        columns.RelativeColumn(3);
                        columns.RelativeColumn(1);
                    });

                    table.Header(header =>
                    {
                        header.Cell().Background(HeaderBgColor).Padding(8)
                            .Text("#").FontSize(9).Bold().FontColor(Colors.White);
                        header.Cell().Background(HeaderBgColor).Padding(8)
                            .Text("Criterion").FontSize(9).Bold().FontColor(Colors.White);
                        header.Cell().Background(HeaderBgColor).Padding(8).AlignRight()
                            .Text("Weight").FontSize(9).Bold().FontColor(Colors.White);
                    });

                    int rowNum = 1;
                    foreach (var criterion in data.EvaluationCriteria.OrderBy(c => c.SortOrder))
                    {
                        var bgColor = rowNum % 2 == 0 ? LightGrayBg : Colors.White.ToString();

                        table.Cell().Background(bgColor).Padding(8)
                            .Text(rowNum.ToString()).FontSize(9).FontColor(TextColor);
                        table.Cell().Background(bgColor).Padding(8)
                            .Text(criterion.Name).FontSize(9).FontColor(TextColor);
                        table.Cell().Background(bgColor).Padding(8).AlignRight()
                            .Text($"{criterion.WeightPercentage:F1}%").FontSize(9).FontColor(TextColor);

                        rowNum++;
                    }
                });
            }

            // Formula
            column.Item().PaddingTop(20);
            column.Item().Text("Combined Score Formula:").FontSize(11).Bold().FontColor(TextColor);
            column.Item().PaddingTop(5).Background(LightGrayBg).Padding(10).AlignCenter()
                .Text($"Combined Score = ({data.TechnicalWeight}/100 x Technical Score) + ({data.CommercialWeight}/100 x Commercial Score)")
                .FontSize(10).FontColor(TextColor).Italic();
        });
    }

    private void ComposeTechnicalEvaluationSection(IContainer container, AwardPackDataDto data)
    {
        container.Column(column =>
        {
            column.Item().Text("TECHNICAL EVALUATION RESULTS").FontSize(14).Bold().FontColor(HeaderBgColor);
            column.Item().PaddingTop(15);

            column.Item().Table(table =>
            {
                table.ColumnsDefinition(columns =>
                {
                    columns.ConstantColumn(30);
                    columns.RelativeColumn(3);
                    columns.RelativeColumn(1);
                    columns.RelativeColumn(1);
                });

                table.Header(header =>
                {
                    header.Cell().Background(HeaderBgColor).Padding(8)
                        .Text("Rank").FontSize(9).Bold().FontColor(Colors.White);
                    header.Cell().Background(HeaderBgColor).Padding(8)
                        .Text("Bidder").FontSize(9).Bold().FontColor(Colors.White);
                    header.Cell().Background(HeaderBgColor).Padding(8).AlignRight()
                        .Text("Avg Score").FontSize(9).Bold().FontColor(Colors.White);
                    header.Cell().Background(HeaderBgColor).Padding(8).AlignRight()
                        .Text("Max Score").FontSize(9).Bold().FontColor(Colors.White);
                });

                foreach (var result in data.TechnicalResults.OrderBy(r => r.Rank))
                {
                    var bgColor = result.Rank == 1 ? "#dcfce7" : (result.Rank % 2 == 0 ? LightGrayBg : Colors.White.ToString());
                    var textWeight = result.Rank == 1 ? "Bold" : "Normal";

                    table.Cell().Background(bgColor).Padding(8)
                        .Text(result.Rank.ToString()).FontSize(9).FontColor(TextColor);
                    table.Cell().Background(bgColor).Padding(8)
                        .Text(result.CompanyName).FontSize(9).FontColor(TextColor);
                    table.Cell().Background(bgColor).Padding(8).AlignRight()
                        .Text($"{result.AverageScore:F2}").FontSize(9).FontColor(TextColor);
                    table.Cell().Background(bgColor).Padding(8).AlignRight()
                        .Text("100.00").FontSize(9).FontColor(SecondaryTextColor);
                }
            });
        });
    }

    private void ComposeCommercialEvaluationSection(IContainer container, AwardPackDataDto data)
    {
        container.Column(column =>
        {
            column.Item().Text("COMMERCIAL EVALUATION RESULTS").FontSize(14).Bold().FontColor(HeaderBgColor);
            column.Item().PaddingTop(15);

            column.Item().Table(table =>
            {
                table.ColumnsDefinition(columns =>
                {
                    columns.ConstantColumn(30);
                    columns.RelativeColumn(3);
                    columns.RelativeColumn(2);
                    columns.RelativeColumn(1);
                });

                table.Header(header =>
                {
                    header.Cell().Background(HeaderBgColor).Padding(8)
                        .Text("Rank").FontSize(9).Bold().FontColor(Colors.White);
                    header.Cell().Background(HeaderBgColor).Padding(8)
                        .Text("Bidder").FontSize(9).Bold().FontColor(Colors.White);
                    header.Cell().Background(HeaderBgColor).Padding(8).AlignRight()
                        .Text($"Total ({data.BaseCurrency})").FontSize(9).Bold().FontColor(Colors.White);
                    header.Cell().Background(HeaderBgColor).Padding(8).AlignRight()
                        .Text("Score").FontSize(9).Bold().FontColor(Colors.White);
                });

                foreach (var result in data.CommercialResults.OrderBy(r => r.Rank))
                {
                    var bgColor = result.Rank == 1 ? "#dcfce7" : (result.Rank % 2 == 0 ? LightGrayBg : Colors.White.ToString());

                    table.Cell().Background(bgColor).Padding(8)
                        .Text(result.Rank.ToString()).FontSize(9).FontColor(TextColor);
                    table.Cell().Background(bgColor).Padding(8)
                        .Text(result.CompanyName).FontSize(9).FontColor(TextColor);
                    table.Cell().Background(bgColor).Padding(8).AlignRight()
                        .Text($"{result.TotalPrice:N2}").FontSize(9).FontColor(TextColor);
                    table.Cell().Background(bgColor).Padding(8).AlignRight()
                        .Text($"{result.CommercialScore:F2}").FontSize(9).FontColor(TextColor);
                }
            });

            // Note about formula
            column.Item().PaddingTop(10).Text(
                "Note: Commercial score calculated as (Lowest Price / Bidder Price) x 100. Lowest bidder receives 100 points.")
                .FontSize(9).FontColor(SecondaryTextColor).Italic();
        });
    }

    private void ComposeCombinedScorecardSection(IContainer container, AwardPackDataDto data)
    {
        container.Column(column =>
        {
            column.Item().Text("COMBINED SCORECARD").FontSize(14).Bold().FontColor(HeaderBgColor);
            column.Item().PaddingTop(15);

            column.Item().Table(table =>
            {
                table.ColumnsDefinition(columns =>
                {
                    columns.ConstantColumn(35);   // Rank
                    columns.RelativeColumn(2.5f); // Bidder
                    columns.RelativeColumn(1);    // Tech Score
                    columns.RelativeColumn(1);    // Tech Rank
                    columns.RelativeColumn(1);    // Comm Score
                    columns.RelativeColumn(1);    // Comm Rank
                    columns.RelativeColumn(1);    // Combined
                });

                table.Header(header =>
                {
                    header.Cell().Background(HeaderBgColor).Padding(6)
                        .Text("Rank").FontSize(8).Bold().FontColor(Colors.White);
                    header.Cell().Background(HeaderBgColor).Padding(6)
                        .Text("Bidder").FontSize(8).Bold().FontColor(Colors.White);
                    header.Cell().Background(HeaderBgColor).Padding(6).AlignRight()
                        .Text("Tech").FontSize(8).Bold().FontColor(Colors.White);
                    header.Cell().Background(HeaderBgColor).Padding(6).AlignCenter()
                        .Text("T.Rank").FontSize(8).Bold().FontColor(Colors.White);
                    header.Cell().Background(HeaderBgColor).Padding(6).AlignRight()
                        .Text("Comm").FontSize(8).Bold().FontColor(Colors.White);
                    header.Cell().Background(HeaderBgColor).Padding(6).AlignCenter()
                        .Text("C.Rank").FontSize(8).Bold().FontColor(Colors.White);
                    header.Cell().Background(HeaderBgColor).Padding(6).AlignRight()
                        .Text("Combined").FontSize(8).Bold().FontColor(Colors.White);
                });

                foreach (var entry in data.CombinedScorecard!.Entries.OrderBy(e => e.FinalRank))
                {
                    var bgColor = entry.IsRecommended ? "#dcfce7" : (entry.FinalRank % 2 == 0 ? LightGrayBg : Colors.White.ToString());

                    table.Cell().Background(bgColor).Padding(6)
                        .Text(entry.FinalRank.ToString()).FontSize(8).FontColor(TextColor);
                    table.Cell().Background(bgColor).Padding(6)
                        .Text(entry.CompanyName).FontSize(8).FontColor(TextColor);
                    table.Cell().Background(bgColor).Padding(6).AlignRight()
                        .Text($"{entry.TechnicalScoreAvg:F2}").FontSize(8).FontColor(TextColor);
                    table.Cell().Background(bgColor).Padding(6).AlignCenter()
                        .Text(entry.TechnicalRank.ToString()).FontSize(8).FontColor(SecondaryTextColor);
                    table.Cell().Background(bgColor).Padding(6).AlignRight()
                        .Text($"{entry.CommercialScoreValue:F2}").FontSize(8).FontColor(TextColor);
                    table.Cell().Background(bgColor).Padding(6).AlignCenter()
                        .Text(entry.CommercialRank.ToString()).FontSize(8).FontColor(SecondaryTextColor);
                    table.Cell().Background(bgColor).Padding(6).AlignRight()
                        .Text($"{entry.CombinedScore:F2}").FontSize(8).Bold().FontColor(entry.IsRecommended ? SuccessColor : TextColor);
                }
            });

            // Weight reminder
            column.Item().PaddingTop(10).Text(text =>
            {
                text.Span("Weights Applied: ").FontSize(9).Bold().FontColor(SecondaryTextColor);
                text.Span($"Technical {data.CombinedScorecard.TechnicalWeight}% / Commercial {data.CombinedScorecard.CommercialWeight}%")
                    .FontSize(9).FontColor(TextColor);
            });
        });
    }

    private void ComposeSensitivityAnalysisSection(IContainer container, AwardPackDataDto data)
    {
        container.Column(column =>
        {
            column.Item().Text("SENSITIVITY ANALYSIS").FontSize(14).Bold().FontColor(HeaderBgColor);
            column.Item().PaddingTop(15);

            column.Item().Text(
                "This section shows how rankings would change under different technical/commercial weight combinations.")
                .FontSize(10).FontColor(TextColor);

            column.Item().PaddingTop(15);

            var analysis = data.SensitivityAnalysis!;

            // Winner changes alert
            if (analysis.WinnerChanges)
            {
                column.Item().Background(WarningColor).Padding(10)
                    .Text("ALERT: The recommended winner changes under different weight scenarios!")
                    .FontSize(10).Bold().FontColor(Colors.White);
                column.Item().PaddingTop(10);
            }

            // Ranks table
            column.Item().Table(table =>
            {
                // Define columns: Bidder + weight splits
                table.ColumnsDefinition(columns =>
                {
                    columns.RelativeColumn(2); // Bidder
                    foreach (var _ in analysis.WeightSplits)
                    {
                        columns.RelativeColumn(1); // Each weight split
                    }
                });

                // Header
                table.Header(header =>
                {
                    header.Cell().Background(HeaderBgColor).Padding(6)
                        .Text("Bidder").FontSize(8).Bold().FontColor(Colors.White);

                    foreach (var split in analysis.WeightSplits)
                    {
                        header.Cell().Background(HeaderBgColor).Padding(6).AlignCenter()
                            .Text(split).FontSize(8).Bold().FontColor(Colors.White);
                    }
                });

                int rowNum = 0;
                foreach (var row in analysis.Rows)
                {
                    var bgColor = row.HasRankVariation ? "#fef3c7" : (rowNum % 2 == 0 ? LightGrayBg : Colors.White.ToString());

                    table.Cell().Background(bgColor).Padding(6)
                        .Text(row.CompanyName).FontSize(8).FontColor(TextColor);

                    foreach (var split in analysis.WeightSplits)
                    {
                        var rank = row.RanksByWeightSplit.TryGetValue(split, out var r) ? r : 0;
                        var isWinner = rank == 1;

                        table.Cell().Background(bgColor).Padding(6).AlignCenter()
                            .Text(rank.ToString()).FontSize(8).FontColor(isWinner ? SuccessColor : TextColor);
                    }

                    rowNum++;
                }
            });

            // Legend
            column.Item().PaddingTop(10).Row(row =>
            {
                row.RelativeItem().Text(text =>
                {
                    text.Span("Highlighted rows indicate rank variation across weight splits.")
                        .FontSize(8).FontColor(SecondaryTextColor).Italic();
                });
            });
        });
    }

    private void ComposeRecommendationSection(IContainer container, AwardPackDataDto data)
    {
        container.Column(column =>
        {
            column.Item().Text("RECOMMENDATION").FontSize(14).Bold().FontColor(HeaderBgColor);
            column.Item().PaddingTop(15);

            // Recommendation box
            column.Item().Background(SuccessColor).Padding(15).Column(recCol =>
            {
                recCol.Item().Text("RECOMMENDED FOR AWARD").FontSize(12).Bold().FontColor(Colors.White);
                recCol.Item().PaddingTop(10);
                recCol.Item().Text(data.Recommendation!.RecommendedBidderName).FontSize(16).Bold().FontColor(Colors.White);
            });

            column.Item().PaddingTop(15);

            // Details
            column.Item().Background(LightGrayBg).Padding(15).Column(detailsCol =>
            {
                detailsCol.Item().Text("Award Details:").FontSize(11).Bold().FontColor(TextColor);
                detailsCol.Item().PaddingTop(10);

                detailsCol.Item().Row(row =>
                {
                    row.RelativeItem().Column(leftCol =>
                    {
                        leftCol.Item().Text(text =>
                        {
                            text.Span("Contract Value: ").FontSize(10).Bold().FontColor(SecondaryTextColor);
                            text.Span($"{data.BaseCurrency} {data.Recommendation.RecommendedBidAmount:N2}")
                                .FontSize(10).FontColor(TextColor);
                        });
                        leftCol.Item().Text(text =>
                        {
                            text.Span("Combined Score: ").FontSize(10).Bold().FontColor(SecondaryTextColor);
                            text.Span($"{data.Recommendation.CombinedScore:F2}").FontSize(10).FontColor(TextColor);
                        });
                    });

                    row.RelativeItem().Column(rightCol =>
                    {
                        rightCol.Item().Text(text =>
                        {
                            text.Span("Technical Rank: ").FontSize(10).Bold().FontColor(SecondaryTextColor);
                            text.Span(data.Recommendation.TechnicalRank.ToString()).FontSize(10).FontColor(TextColor);
                        });
                        rightCol.Item().Text(text =>
                        {
                            text.Span("Commercial Rank: ").FontSize(10).Bold().FontColor(SecondaryTextColor);
                            text.Span(data.Recommendation.CommercialRank.ToString()).FontSize(10).FontColor(TextColor);
                        });
                    });
                });

                if (!string.IsNullOrWhiteSpace(data.Recommendation.Notes))
                {
                    detailsCol.Item().PaddingTop(15).Text("Additional Notes:").FontSize(10).Bold().FontColor(TextColor);
                    detailsCol.Item().PaddingTop(5).Text(data.Recommendation.Notes)
                        .FontSize(10).FontColor(TextColor).LineHeight(1.4f);
                }
            });

            // Signature section
            column.Item().PaddingTop(30).Column(sigCol =>
            {
                sigCol.Item().Text("Approval Signatures:").FontSize(11).Bold().FontColor(TextColor);
                sigCol.Item().PaddingTop(20).Row(row =>
                {
                    row.RelativeItem().Column(leftCol =>
                    {
                        leftCol.Item().Text("Prepared By:").FontSize(10).FontColor(SecondaryTextColor);
                        leftCol.Item().PaddingTop(30).LineHorizontal(1).LineColor(TextColor);
                        leftCol.Item().PaddingTop(5).Text($"Name: {data.GeneratedByName}")
                            .FontSize(9).FontColor(SecondaryTextColor);
                        leftCol.Item().Text($"Date: {data.GeneratedAt:yyyy-MM-dd}")
                            .FontSize(9).FontColor(SecondaryTextColor);
                    });

                    row.ConstantItem(30);

                    row.RelativeItem().Column(midCol =>
                    {
                        midCol.Item().Text("Reviewed By:").FontSize(10).FontColor(SecondaryTextColor);
                        midCol.Item().PaddingTop(30).LineHorizontal(1).LineColor(TextColor);
                        midCol.Item().PaddingTop(5).Text("Name: _________________")
                            .FontSize(9).FontColor(SecondaryTextColor);
                        midCol.Item().Text("Date: _________________")
                            .FontSize(9).FontColor(SecondaryTextColor);
                    });

                    row.ConstantItem(30);

                    row.RelativeItem().Column(rightCol =>
                    {
                        rightCol.Item().Text("Approved By:").FontSize(10).FontColor(SecondaryTextColor);
                        rightCol.Item().PaddingTop(30).LineHorizontal(1).LineColor(TextColor);
                        rightCol.Item().PaddingTop(5).Text("Name: _________________")
                            .FontSize(9).FontColor(SecondaryTextColor);
                        rightCol.Item().Text("Date: _________________")
                            .FontSize(9).FontColor(SecondaryTextColor);
                    });
                });
            });
        });
    }

    private void ComposeExceptionsSection(IContainer container, AwardPackDataDto data)
    {
        container.Column(column =>
        {
            column.Item().Text("EXCEPTIONS & RISKS").FontSize(14).Bold().FontColor(HeaderBgColor);
            column.Item().PaddingTop(15);

            // Summary
            var highCount = data.Exceptions.Count(e => e.RiskLevel == Domain.Enums.RiskLevel.High);
            var mediumCount = data.Exceptions.Count(e => e.RiskLevel == Domain.Enums.RiskLevel.Medium);
            var lowCount = data.Exceptions.Count(e => e.RiskLevel == Domain.Enums.RiskLevel.Low);

            column.Item().Row(row =>
            {
                row.RelativeItem().Background(WarningColor).Padding(10).AlignCenter().Column(col =>
                {
                    col.Item().Text(highCount.ToString()).FontSize(20).Bold().FontColor(Colors.White);
                    col.Item().Text("High Risk").FontSize(10).FontColor(Colors.White);
                });
                row.ConstantItem(10);
                row.RelativeItem().Background("#f59e0b").Padding(10).AlignCenter().Column(col =>
                {
                    col.Item().Text(mediumCount.ToString()).FontSize(20).Bold().FontColor(Colors.White);
                    col.Item().Text("Medium Risk").FontSize(10).FontColor(Colors.White);
                });
                row.ConstantItem(10);
                row.RelativeItem().Background(SuccessColor).Padding(10).AlignCenter().Column(col =>
                {
                    col.Item().Text(lowCount.ToString()).FontSize(20).Bold().FontColor(Colors.White);
                    col.Item().Text("Low Risk").FontSize(10).FontColor(Colors.White);
                });
            });

            column.Item().PaddingTop(20);

            // Exceptions list
            foreach (var exception in data.Exceptions.OrderByDescending(e => e.RiskLevel))
            {
                var riskColor = exception.RiskLevel switch
                {
                    Domain.Enums.RiskLevel.High => WarningColor,
                    Domain.Enums.RiskLevel.Medium => "#f59e0b",
                    _ => SuccessColor
                };

                column.Item().PaddingBottom(10).Border(1).BorderColor(BorderColor).Column(excCol =>
                {
                    // Header with risk badge
                    excCol.Item().Background(LightGrayBg).Padding(10).Row(row =>
                    {
                        row.RelativeItem().Column(leftCol =>
                        {
                            leftCol.Item().Text(exception.BidderCompanyName).FontSize(10).Bold().FontColor(TextColor);
                            leftCol.Item().Text(exception.ExceptionTypeName).FontSize(9).FontColor(SecondaryTextColor);
                        });
                        row.ConstantItem(80).Background(riskColor).Padding(5).AlignCenter()
                            .Text(exception.RiskLevelName.ToUpper()).FontSize(9).Bold().FontColor(Colors.White);
                    });

                    // Description
                    excCol.Item().Padding(10).Column(descCol =>
                    {
                        descCol.Item().Text(exception.Description).FontSize(10).FontColor(TextColor).LineHeight(1.3f);

                        if (exception.CostImpact.HasValue || exception.TimeImpactDays.HasValue)
                        {
                            descCol.Item().PaddingTop(10).Row(impactRow =>
                            {
                                if (exception.CostImpact.HasValue)
                                {
                                    impactRow.RelativeItem().Text(text =>
                                    {
                                        text.Span("Cost Impact: ").FontSize(9).Bold().FontColor(SecondaryTextColor);
                                        text.Span($"{data.BaseCurrency} {exception.CostImpact.Value:N2}")
                                            .FontSize(9).FontColor(TextColor);
                                    });
                                }
                                if (exception.TimeImpactDays.HasValue)
                                {
                                    impactRow.RelativeItem().Text(text =>
                                    {
                                        text.Span("Time Impact: ").FontSize(9).Bold().FontColor(SecondaryTextColor);
                                        text.Span($"{exception.TimeImpactDays.Value} days").FontSize(9).FontColor(TextColor);
                                    });
                                }
                            });
                        }

                        if (!string.IsNullOrWhiteSpace(exception.Mitigation))
                        {
                            descCol.Item().PaddingTop(10).Text(text =>
                            {
                                text.Span("Mitigation: ").FontSize(9).Bold().FontColor(SecondaryTextColor);
                                text.Span(exception.Mitigation).FontSize(9).FontColor(TextColor);
                            });
                        }
                    });
                });
            }
        });
    }

    private void ComposeAppendicesSection(IContainer container, AwardPackDataDto data)
    {
        container.Column(column =>
        {
            column.Item().Text("APPENDICES").FontSize(14).Bold().FontColor(HeaderBgColor);
            column.Item().PaddingTop(15);

            column.Item().Text("The following documents are referenced as part of this Award Pack:")
                .FontSize(10).FontColor(TextColor);

            column.Item().PaddingTop(10).Column(listCol =>
            {
                listCol.Item().Text("A. Tender Documents").FontSize(10).Bold().FontColor(TextColor);
                listCol.Item().Text("B. Bid Submission Documents").FontSize(10).Bold().FontColor(TextColor);
                listCol.Item().Text("C. Clarification Bulletins").FontSize(10).Bold().FontColor(TextColor);
                listCol.Item().Text("D. Technical Evaluation Worksheets").FontSize(10).Bold().FontColor(TextColor);
                listCol.Item().Text("E. Commercial Analysis Comparable Sheet").FontSize(10).Bold().FontColor(TextColor);
            });

            column.Item().PaddingTop(20).Background(LightGrayBg).Padding(10)
                .Text("Note: Detailed appendix documents are available upon request from the Procurement Department.")
                .FontSize(9).FontColor(SecondaryTextColor).Italic();
        });
    }

    private void ComposeAwardPackFooter(IContainer container, string tenderReference)
    {
        container.Column(column =>
        {
            column.Item().LineHorizontal(1).LineColor(BorderColor);
            column.Item().PaddingTop(10).Row(row =>
            {
                row.RelativeItem().AlignLeft().Text(text =>
                {
                    text.Span("Tender: ").FontSize(8).FontColor(SecondaryTextColor);
                    text.Span(tenderReference).FontSize(8).Bold().FontColor(TextColor);
                });

                row.RelativeItem().AlignCenter().Text(text =>
                {
                    text.Span("Page ").FontSize(8).FontColor(SecondaryTextColor);
                    text.CurrentPageNumber().FontSize(8).FontColor(TextColor);
                    text.Span(" of ").FontSize(8).FontColor(SecondaryTextColor);
                    text.TotalPages().FontSize(8).FontColor(TextColor);
                });

                row.RelativeItem().AlignRight().Text(text =>
                {
                    text.Span("Generated: ").FontSize(8).FontColor(SecondaryTextColor);
                    text.Span(DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm UTC")).FontSize(8).FontColor(TextColor);
                });
            });

            column.Item().PaddingTop(5).AlignCenter().Text(
                "CONFIDENTIAL - Award Recommendation Pack - Bayan Tender Management System")
                .FontSize(7).FontColor(SecondaryTextColor).Italic();
        });
    }
}
