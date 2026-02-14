using MediatR;

namespace Bayan.Application.Features.Tenders.Queries.ExportTenders;

/// <summary>
/// Query for exporting all tenders to an Excel file.
/// </summary>
public class ExportTendersQuery : IRequest<ExportTendersResult>
{
}

/// <summary>
/// Result of the tender export operation.
/// </summary>
public class ExportTendersResult
{
    /// <summary>
    /// File content as byte array.
    /// </summary>
    public byte[] FileContent { get; set; } = Array.Empty<byte>();

    /// <summary>
    /// File name.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// Content type.
    /// </summary>
    public string ContentType { get; set; } = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
}
