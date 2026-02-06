using Bayan.Application.Features.Evaluation.DTOs;
using MediatR;

namespace Bayan.Application.Features.Evaluation.Queries.GetComparableSheet;

/// <summary>
/// Query to get the comparable sheet for a tender.
/// </summary>
public class GetComparableSheetQuery : IRequest<ComparableSheetDto>
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Whether to include provisional sums in calculations.
    /// </summary>
    public bool IncludeProvisionalSums { get; set; } = true;

    /// <summary>
    /// Whether to include alternates in calculations.
    /// </summary>
    public bool IncludeAlternates { get; set; } = true;

    /// <summary>
    /// Whether to include daywork items.
    /// </summary>
    public bool IncludeDaywork { get; set; } = true;

    public GetComparableSheetQuery()
    {
    }

    public GetComparableSheetQuery(Guid tenderId)
    {
        TenderId = tenderId;
    }
}
