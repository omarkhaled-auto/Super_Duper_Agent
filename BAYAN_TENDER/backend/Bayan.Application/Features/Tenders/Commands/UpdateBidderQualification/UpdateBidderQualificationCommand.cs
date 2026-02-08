using MediatR;

namespace Bayan.Application.Features.Tenders.Commands.UpdateBidderQualification;

/// <summary>
/// Command for updating a bidder's qualification status for a tender.
/// </summary>
public class UpdateBidderQualificationCommand : IRequest<Unit>
{
    /// <summary>
    /// The tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// The bidder ID.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// The new qualification status (Qualified or Rejected).
    /// </summary>
    public string QualificationStatus { get; set; } = string.Empty;

    /// <summary>
    /// Optional reason for the qualification decision.
    /// </summary>
    public string? Reason { get; set; }
}
