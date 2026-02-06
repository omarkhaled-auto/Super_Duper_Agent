using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Evaluation.DTOs;
using Bayan.Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Bayan.Application.Features.Evaluation.Commands.AddBidException;

/// <summary>
/// Handler for AddBidExceptionCommand.
/// </summary>
public class AddBidExceptionCommandHandler : IRequestHandler<AddBidExceptionCommand, BidExceptionDto>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;
    private readonly ILogger<AddBidExceptionCommandHandler> _logger;

    public AddBidExceptionCommandHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService,
        ILogger<AddBidExceptionCommandHandler> logger)
    {
        _context = context;
        _currentUserService = currentUserService;
        _logger = logger;
    }

    public async Task<BidExceptionDto> Handle(
        AddBidExceptionCommand request,
        CancellationToken cancellationToken)
    {
        _logger.LogInformation(
            "Adding bid exception for tender {TenderId}, bidder {BidderId}, type {ExceptionType}",
            request.TenderId, request.BidderId, request.ExceptionType);

        // Verify tender exists
        var tenderExists = await _context.Tenders
            .AnyAsync(t => t.Id == request.TenderId, cancellationToken);

        if (!tenderExists)
        {
            throw new KeyNotFoundException($"Tender with ID {request.TenderId} not found.");
        }

        // Verify bidder exists and is associated with the tender
        var bidder = await _context.Bidders
            .FirstOrDefaultAsync(b => b.Id == request.BidderId, cancellationToken);

        if (bidder == null)
        {
            throw new KeyNotFoundException($"Bidder with ID {request.BidderId} not found.");
        }

        // Verify bidder is associated with the tender
        var tenderBidderExists = await _context.TenderBidders
            .AnyAsync(tb => tb.TenderId == request.TenderId && tb.BidderId == request.BidderId, cancellationToken);

        if (!tenderBidderExists)
        {
            throw new InvalidOperationException(
                $"Bidder {request.BidderId} is not associated with tender {request.TenderId}.");
        }

        // Get current user info
        var currentUserId = _currentUserService.UserId ?? throw new UnauthorizedAccessException("User not authenticated.");
        var currentUser = await _context.Users
            .FirstOrDefaultAsync(u => u.Id == currentUserId, cancellationToken);

        var currentUserName = currentUser != null
            ? $"{currentUser.FirstName} {currentUser.LastName}".Trim()
            : "Unknown";

        // Create the exception
        var bidException = new BidException
        {
            TenderId = request.TenderId,
            BidderId = request.BidderId,
            ExceptionType = request.ExceptionType,
            Description = request.Description,
            CostImpact = request.CostImpact,
            TimeImpactDays = request.TimeImpactDays,
            RiskLevel = request.RiskLevel,
            Mitigation = request.Mitigation,
            LoggedBy = currentUserId
        };

        _context.BidExceptions.Add(bidException);
        await _context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation(
            "Bid exception {ExceptionId} added for tender {TenderId}, bidder {BidderId}",
            bidException.Id, request.TenderId, request.BidderId);

        return new BidExceptionDto
        {
            Id = bidException.Id,
            TenderId = bidException.TenderId,
            BidderId = bidException.BidderId,
            BidderCompanyName = bidder.CompanyName,
            ExceptionType = bidException.ExceptionType,
            Description = bidException.Description,
            CostImpact = bidException.CostImpact,
            TimeImpactDays = bidException.TimeImpactDays,
            RiskLevel = bidException.RiskLevel,
            Mitigation = bidException.Mitigation,
            LoggedBy = bidException.LoggedBy,
            LoggedByName = currentUserName,
            CreatedAt = bidException.CreatedAt
        };
    }
}
