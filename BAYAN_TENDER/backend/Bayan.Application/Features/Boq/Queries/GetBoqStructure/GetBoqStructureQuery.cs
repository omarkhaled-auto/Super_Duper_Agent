using Bayan.Application.Features.Boq.DTOs;
using MediatR;

namespace Bayan.Application.Features.Boq.Queries.GetBoqStructure;

/// <summary>
/// Query for retrieving the full hierarchical BOQ structure for a tender.
/// Returns sections with nested child sections and items.
/// </summary>
public class GetBoqStructureQuery : IRequest<List<BoqTreeNodeDto>>
{
    /// <summary>
    /// The tender's unique identifier.
    /// </summary>
    public Guid TenderId { get; }

    public GetBoqStructureQuery(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
