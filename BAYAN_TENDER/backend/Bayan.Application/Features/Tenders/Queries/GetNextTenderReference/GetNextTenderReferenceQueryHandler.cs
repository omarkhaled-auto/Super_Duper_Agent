using Bayan.Application.Common.Interfaces;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Tenders.Queries.GetNextTenderReference;

/// <summary>
/// Handler for the GetNextTenderReferenceQuery.
/// Generates tender reference in format: TNR-{YEAR}-{4-digit-sequence}
/// </summary>
public class GetNextTenderReferenceQueryHandler : IRequestHandler<GetNextTenderReferenceQuery, string>
{
    private readonly IApplicationDbContext _context;

    public GetNextTenderReferenceQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<string> Handle(
        GetNextTenderReferenceQuery request,
        CancellationToken cancellationToken)
    {
        var currentYear = DateTime.UtcNow.Year;
        var prefix = $"TNR-{currentYear}-";

        // Find the highest sequence number for the current year
        var lastReference = await _context.Tenders
            .Where(t => t.Reference.StartsWith(prefix))
            .OrderByDescending(t => t.Reference)
            .Select(t => t.Reference)
            .FirstOrDefaultAsync(cancellationToken);

        int nextSequence = 1;

        if (!string.IsNullOrEmpty(lastReference))
        {
            // Extract the sequence number from the last reference
            var sequencePart = lastReference.Substring(prefix.Length);
            if (int.TryParse(sequencePart, out var lastSequence))
            {
                nextSequence = lastSequence + 1;
            }
        }

        // Format: TNR-2024-0001
        return $"{prefix}{nextSequence:D4}";
    }
}
