namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the type of bid document.
/// </summary>
public enum BidDocumentType
{
    /// <summary>
    /// Priced Bill of Quantities.
    /// </summary>
    PricedBOQ = 0,

    /// <summary>
    /// Methodology document.
    /// </summary>
    Methodology = 1,

    /// <summary>
    /// Team CVs.
    /// </summary>
    TeamCVs = 2,

    /// <summary>
    /// Project program/schedule.
    /// </summary>
    Program = 3,

    /// <summary>
    /// Health, Safety, Environment plan.
    /// </summary>
    HSEPlan = 4,

    /// <summary>
    /// Other supporting documents.
    /// </summary>
    Supporting = 5
}
