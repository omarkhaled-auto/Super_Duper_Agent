namespace Bayan.Domain.Enums;

/// <summary>
/// Defines the roles available in the Bayan Tender Management System.
/// </summary>
public enum UserRole
{
    /// <summary>
    /// System administrator with full access.
    /// </summary>
    Admin = 0,

    /// <summary>
    /// Manages tender lifecycle and operations.
    /// </summary>
    TenderManager = 1,

    /// <summary>
    /// Analyzes commercial aspects of bids.
    /// </summary>
    CommercialAnalyst = 2,

    /// <summary>
    /// Evaluates technical aspects of bids.
    /// </summary>
    TechnicalPanelist = 3,

    /// <summary>
    /// Approves tender decisions and awards.
    /// </summary>
    Approver = 4,

    /// <summary>
    /// Audits tender processes for compliance.
    /// </summary>
    Auditor = 5,

    /// <summary>
    /// External party submitting bids.
    /// </summary>
    Bidder = 6
}
