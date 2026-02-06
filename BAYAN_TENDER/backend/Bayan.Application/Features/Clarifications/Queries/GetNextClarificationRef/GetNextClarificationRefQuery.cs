using MediatR;

namespace Bayan.Application.Features.Clarifications.Queries.GetNextClarificationRef;

/// <summary>
/// Query for getting the next clarification reference number for a tender.
/// Format: CL-{3-digit-sequence} (e.g., CL-001, CL-002)
/// </summary>
public class GetNextClarificationRefQuery : IRequest<string>
{
    /// <summary>
    /// ID of the tender to get the next reference for.
    /// </summary>
    public Guid TenderId { get; set; }

    public GetNextClarificationRefQuery()
    {
    }

    public GetNextClarificationRefQuery(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
