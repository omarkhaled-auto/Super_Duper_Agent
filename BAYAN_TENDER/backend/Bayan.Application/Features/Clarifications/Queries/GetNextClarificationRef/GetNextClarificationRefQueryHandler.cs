using Bayan.Application.Common.Interfaces;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Bayan.Application.Features.Clarifications.Queries.GetNextClarificationRef;

/// <summary>
/// Handler for the GetNextClarificationRefQuery.
/// </summary>
public class GetNextClarificationRefQueryHandler : IRequestHandler<GetNextClarificationRefQuery, string>
{
    private readonly IApplicationDbContext _context;

    public GetNextClarificationRefQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<string> Handle(
        GetNextClarificationRefQuery request,
        CancellationToken cancellationToken)
    {
        // Get the highest reference number for this tender
        var clarifications = await _context.Clarifications
            .AsNoTracking()
            .Where(c => c.TenderId == request.TenderId)
            .Select(c => c.ReferenceNumber)
            .ToListAsync(cancellationToken);

        var maxSequence = 0;

        foreach (var refNumber in clarifications)
        {
            // Parse CL-XXX format
            if (refNumber.StartsWith("CL-") && refNumber.Length > 3)
            {
                var sequencePart = refNumber.Substring(3);
                if (int.TryParse(sequencePart, out var sequence) && sequence > maxSequence)
                {
                    maxSequence = sequence;
                }
            }
        }

        var nextSequence = maxSequence + 1;
        return $"CL-{nextSequence:D3}";
    }
}
