using System.Text;
using Bayan.Application.Common.Interfaces;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Queries.ExportTenders;

/// <summary>
/// Handler for ExportTendersQuery. Generates a CSV file with all tenders.
/// </summary>
public class ExportTendersQueryHandler : IRequestHandler<ExportTendersQuery, ExportTendersResult>
{
    private readonly IApplicationDbContext _context;

    public ExportTendersQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<ExportTendersResult> Handle(
        ExportTendersQuery request,
        CancellationToken cancellationToken)
    {
        var tenders = await _context.Tenders
            .Include(t => t.Client)
            .Include(t => t.TenderBidders)
            .AsNoTracking()
            .OrderByDescending(t => t.CreatedAt)
            .Select(t => new
            {
                t.Reference,
                t.Title,
                ClientName = t.Client.Name,
                t.TenderType,
                t.Status,
                t.BaseCurrency,
                t.EstimatedValue,
                t.SubmissionDeadline,
                BidderCount = t.TenderBidders.Count,
                DaysRemaining = (int)(t.SubmissionDeadline - DateTime.UtcNow).TotalDays,
                t.CreatedAt
            })
            .ToListAsync(cancellationToken);

        var sb = new StringBuilder();

        // BOM for Excel to detect UTF-8
        // Header row
        sb.AppendLine("Reference,Title,Client,Type,Status,Currency,Estimated Value,Submission Deadline,Bidders,Days Remaining,Created");

        foreach (var t in tenders)
        {
            sb.AppendLine(string.Join(",",
                Escape(t.Reference),
                Escape(t.Title),
                Escape(t.ClientName),
                Escape(t.TenderType.ToString()),
                Escape(t.Status.ToString()),
                Escape(t.BaseCurrency),
                t.EstimatedValue?.ToString("F2") ?? "",
                Escape(t.SubmissionDeadline.ToString("yyyy-MM-dd HH:mm")),
                t.BidderCount,
                t.DaysRemaining,
                Escape(t.CreatedAt.ToString("yyyy-MM-dd"))
            ));
        }

        // Add UTF-8 BOM so Excel detects encoding correctly
        var bom = Encoding.UTF8.GetPreamble();
        var content = Encoding.UTF8.GetBytes(sb.ToString());
        var fileContent = new byte[bom.Length + content.Length];
        bom.CopyTo(fileContent, 0);
        content.CopyTo(fileContent, bom.Length);

        var fileName = $"Tenders_Export_{DateTime.UtcNow:yyyyMMdd_HHmmss}.csv";

        return new ExportTendersResult
        {
            FileContent = fileContent,
            FileName = fileName,
            ContentType = "text/csv; charset=utf-8"
        };
    }

    private static string Escape(string value)
    {
        if (string.IsNullOrEmpty(value)) return "";
        if (value.Contains(',') || value.Contains('"') || value.Contains('\n'))
        {
            return $"\"{value.Replace("\"", "\"\"")}\"";
        }
        return value;
    }
}
