using Bayan.Application.Features.Boq.DTOs;
using MediatR;

namespace Bayan.Application.Features.Boq.Queries.GetUomList;

/// <summary>
/// Query for retrieving the list of units of measurement.
/// </summary>
public class GetUomListQuery : IRequest<List<UomDto>>
{
    /// <summary>
    /// Optional category filter (Area, Volume, Length, Weight, etc.).
    /// </summary>
    public string? Category { get; set; }
}
