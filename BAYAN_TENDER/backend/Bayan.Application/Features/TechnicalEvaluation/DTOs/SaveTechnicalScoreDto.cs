namespace Bayan.Application.Features.TechnicalEvaluation.DTOs;

/// <summary>
/// DTO for saving technical scores (single or batch).
/// </summary>
public class SaveTechnicalScoreDto
{
    /// <summary>
    /// The bidder's unique identifier.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// The criterion's unique identifier.
    /// </summary>
    public Guid CriterionId { get; set; }

    /// <summary>
    /// The score value (0-10 scale).
    /// </summary>
    public decimal Score { get; set; }

    /// <summary>
    /// Comment/justification for the score.
    /// Required if score is less than 3 or greater than 8.
    /// </summary>
    public string? Comment { get; set; }
}

/// <summary>
/// DTO for bidder technical documents.
/// </summary>
public class BidderTechnicalDocumentDto
{
    /// <summary>
    /// The document's unique identifier.
    /// </summary>
    public Guid Id { get; set; }

    /// <summary>
    /// Document type (Technical Proposal, Certificate, etc.).
    /// </summary>
    public string DocumentType { get; set; } = string.Empty;

    /// <summary>
    /// Original file name.
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// File size in bytes.
    /// </summary>
    public long FileSizeBytes { get; set; }

    /// <summary>
    /// MIME content type.
    /// </summary>
    public string ContentType { get; set; } = string.Empty;

    /// <summary>
    /// When the document was uploaded.
    /// </summary>
    public DateTime UploadedAt { get; set; }

    /// <summary>
    /// URL for downloading the document.
    /// </summary>
    public string? DownloadUrl { get; set; }
}

/// <summary>
/// DTO for retrieving a bidder's technical documents for evaluation.
/// </summary>
public class BidderTechnicalDocumentsDto
{
    /// <summary>
    /// The bidder's unique identifier.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// The bidder's company name (null if blind mode).
    /// </summary>
    public string? CompanyName { get; set; }

    /// <summary>
    /// Anonymous identifier for the bidder.
    /// </summary>
    public string AnonymousId { get; set; } = string.Empty;

    /// <summary>
    /// Whether blind mode is enabled.
    /// </summary>
    public bool BlindMode { get; set; }

    /// <summary>
    /// List of technical documents.
    /// </summary>
    public List<BidderTechnicalDocumentDto> Documents { get; set; } = new();
}
