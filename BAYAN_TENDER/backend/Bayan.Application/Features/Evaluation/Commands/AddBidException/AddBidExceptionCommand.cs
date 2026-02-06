using Bayan.Application.Features.Evaluation.DTOs;
using Bayan.Domain.Enums;
using MediatR;

namespace Bayan.Application.Features.Evaluation.Commands.AddBidException;

/// <summary>
/// Command to add a bid exception for a tender.
/// </summary>
public class AddBidExceptionCommand : IRequest<BidExceptionDto>
{
    /// <summary>
    /// Tender ID.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// Bidder ID the exception is for.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Type of exception.
    /// </summary>
    public ExceptionType ExceptionType { get; set; }

    /// <summary>
    /// Description of the exception.
    /// </summary>
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Cost impact of the exception (optional).
    /// </summary>
    public decimal? CostImpact { get; set; }

    /// <summary>
    /// Time impact in days (optional).
    /// </summary>
    public int? TimeImpactDays { get; set; }

    /// <summary>
    /// Risk level.
    /// </summary>
    public RiskLevel RiskLevel { get; set; }

    /// <summary>
    /// Mitigation strategy (optional).
    /// </summary>
    public string? Mitigation { get; set; }

    public AddBidExceptionCommand()
    {
    }

    public AddBidExceptionCommand(Guid tenderId, Guid bidderId)
    {
        TenderId = tenderId;
        BidderId = bidderId;
    }
}
