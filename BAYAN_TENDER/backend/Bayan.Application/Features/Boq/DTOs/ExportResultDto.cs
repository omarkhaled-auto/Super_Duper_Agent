namespace Bayan.Application.Features.Boq.DTOs;

/// <summary>
/// DTO for export result containing file data.
/// </summary>
public class ExportResultDto
{
    /// <summary>
    /// Generated file name.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// MIME content type for the file.
    /// </summary>
    public string ContentType { get; set; } = string.Empty;

    /// <summary>
    /// File content as byte array.
    /// </summary>
    public byte[] FileContent { get; set; } = Array.Empty<byte>();

    /// <summary>
    /// File size in bytes.
    /// </summary>
    public long FileSize => FileContent.Length;

    /// <summary>
    /// Creates an Excel export result.
    /// </summary>
    /// <param name="fileName">File name without extension.</param>
    /// <param name="content">Excel file content.</param>
    /// <returns>Export result configured for Excel.</returns>
    public static ExportResultDto Excel(string fileName, byte[] content)
    {
        return new ExportResultDto
        {
            FileName = $"{fileName}.xlsx",
            ContentType = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            FileContent = content
        };
    }
}
