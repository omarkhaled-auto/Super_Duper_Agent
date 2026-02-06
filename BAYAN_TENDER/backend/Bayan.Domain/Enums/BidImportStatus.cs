namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the import status of a bid submission.
/// </summary>
public enum BidImportStatus
{
    /// <summary>
    /// File uploaded but not yet processed.
    /// </summary>
    Uploaded = 0,

    /// <summary>
    /// File is being parsed.
    /// </summary>
    Parsing = 1,

    /// <summary>
    /// File has been parsed.
    /// </summary>
    Parsed = 2,

    /// <summary>
    /// Items are being mapped.
    /// </summary>
    Mapping = 3,

    /// <summary>
    /// Items have been mapped.
    /// </summary>
    Mapped = 4,

    /// <summary>
    /// Items are being matched with BOQ.
    /// </summary>
    Matching = 5,

    /// <summary>
    /// Items have been matched.
    /// </summary>
    Matched = 6,

    /// <summary>
    /// Data is being validated.
    /// </summary>
    Validated = 7,

    /// <summary>
    /// Import completed successfully.
    /// </summary>
    Imported = 8,

    /// <summary>
    /// Import failed.
    /// </summary>
    Failed = 9
}
