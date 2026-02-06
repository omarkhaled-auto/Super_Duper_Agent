using MediatR;

namespace Bayan.Application.Features.Tenders.Queries.GetNextTenderReference;

/// <summary>
/// Query for generating the next available tender reference number.
/// Format: TNR-{YEAR}-{4-digit-sequence}
/// Example: TNR-2024-0001
/// </summary>
public class GetNextTenderReferenceQuery : IRequest<string>
{
}
