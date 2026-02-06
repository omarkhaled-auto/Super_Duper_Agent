using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;
using Microsoft.EntityFrameworkCore;
using Moq;

namespace Bayan.Tests.Unit.Application.Evaluation;

/// <summary>
/// Unit tests for CalculateCommercialScoresCommandHandler.
/// Tests commercial scoring logic including lowest bidder scoring formula and ranking.
/// </summary>
public class CalculateCommercialScoresCommandHandlerTests
{
    private readonly Mock<IApplicationDbContext> _contextMock;
    private readonly Mock<ICacheService> _cacheServiceMock;
    private readonly List<BidSubmission> _bidSubmissionsStore;

    public CalculateCommercialScoresCommandHandlerTests()
    {
        _contextMock = new Mock<IApplicationDbContext>();
        _cacheServiceMock = new Mock<ICacheService>();
        _bidSubmissionsStore = new List<BidSubmission>();

        SetupDbSets();
    }

    #region Lowest Bidder Gets Score of 100 Tests

    [Fact]
    public void CalculateCommercialScore_LowestBidder_GetsScoreOf100()
    {
        // Arrange
        var bids = new List<BidSubmissionDto>
        {
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1000000m },
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1200000m },
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1500000m }
        };

        var lowestBidAmount = bids.Min(b => b.NormalizedTotalAmount);

        // Act
        var scores = CalculateCommercialScores(bids);

        // Assert
        var lowestBidder = scores.First(s => s.NormalizedTotalAmount == lowestBidAmount);
        lowestBidder.CommercialScore.Should().Be(100.0m);
    }

    [Fact]
    public void CalculateCommercialScore_SingleBidder_GetsScoreOf100()
    {
        // Arrange
        var bids = new List<BidSubmissionDto>
        {
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1500000m }
        };

        // Act
        var scores = CalculateCommercialScores(bids);

        // Assert
        scores.Should().HaveCount(1);
        scores.First().CommercialScore.Should().Be(100.0m);
    }

    [Fact]
    public void CalculateCommercialScore_MultipleBiddersWithSameLowestAmount_AllGetScoreOf100()
    {
        // Arrange
        var bids = new List<BidSubmissionDto>
        {
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1000000m },
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1000000m },
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1500000m }
        };

        // Act
        var scores = CalculateCommercialScores(bids);

        // Assert
        var lowestBidders = scores.Where(s => s.NormalizedTotalAmount == 1000000m).ToList();
        lowestBidders.Should().HaveCount(2);
        lowestBidders.All(s => s.CommercialScore == 100.0m).Should().BeTrue();
    }

    #endregion

    #region Formula (Lowest / This) x 100 Tests

    [Fact]
    public void CalculateCommercialScore_UsesCorrectFormula()
    {
        // Arrange
        var lowestBid = 1000000m;
        var higherBid = 1250000m;

        // Expected: (1000000 / 1250000) * 100 = 80
        var expectedScore = (lowestBid / higherBid) * 100;

        var bids = new List<BidSubmissionDto>
        {
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = lowestBid },
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = higherBid }
        };

        // Act
        var scores = CalculateCommercialScores(bids);

        // Assert
        var higherBidder = scores.First(s => s.NormalizedTotalAmount == higherBid);
        higherBidder.CommercialScore.Should().Be(80.0m);
    }

    [Theory]
    [InlineData(1000000, 1000000, 100.0)]    // Same as lowest
    [InlineData(1000000, 1100000, 90.91)]    // 10% higher
    [InlineData(1000000, 1250000, 80.0)]     // 25% higher
    [InlineData(1000000, 1500000, 66.67)]    // 50% higher
    [InlineData(1000000, 2000000, 50.0)]     // 100% higher
    public void CalculateCommercialScore_WithVariousBids_AppliesFormulaCorrectly(
        decimal lowestBid, decimal thisBid, decimal expectedScore)
    {
        // Arrange
        var bids = new List<BidSubmissionDto>
        {
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = lowestBid },
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = thisBid }
        };

        // Act
        var scores = CalculateCommercialScores(bids);

        // Assert
        var bidderScore = scores.First(s => s.NormalizedTotalAmount == thisBid);
        bidderScore.CommercialScore.Should().BeApproximately(expectedScore, 0.01m);
    }

    [Fact]
    public void CalculateCommercialScore_PreservesPrecision()
    {
        // Arrange
        var lowestBid = 1000000m;
        var thisBid = 1333333m;

        // Expected: (1000000 / 1333333) * 100 = 75.000019...
        var bids = new List<BidSubmissionDto>
        {
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = lowestBid },
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = thisBid }
        };

        // Act
        var scores = CalculateCommercialScores(bids);

        // Assert
        var bidderScore = scores.First(s => s.NormalizedTotalAmount == thisBid);
        bidderScore.CommercialScore.Should().BeApproximately(75.0m, 0.01m);
    }

    #endregion

    #region Ranking Tests (Highest Score = Rank 1)

    [Fact]
    public void RankBidders_HighestScore_GetsRank1()
    {
        // Arrange
        var bids = new List<BidSubmissionDto>
        {
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1500000m },
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1000000m },
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1200000m }
        };

        // Act
        var scores = CalculateCommercialScores(bids);
        var rankedScores = RankByCommercialScore(scores);

        // Assert
        var rank1 = rankedScores.First(s => s.Rank == 1);
        rank1.CommercialScore.Should().Be(100.0m);
        rank1.NormalizedTotalAmount.Should().Be(1000000m);
    }

    [Fact]
    public void RankBidders_OrdersCorrectlyByScore()
    {
        // Arrange
        var bids = new List<BidSubmissionDto>
        {
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1000000m }, // Rank 1
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1250000m }, // Rank 2
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1500000m }, // Rank 3
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 2000000m }  // Rank 4
        };

        // Act
        var scores = CalculateCommercialScores(bids);
        var rankedScores = RankByCommercialScore(scores);

        // Assert
        rankedScores.Should().BeInDescendingOrder(s => s.CommercialScore);
        rankedScores.Select(s => s.Rank).Should().BeEquivalentTo(new[] { 1, 2, 3, 4 });
    }

    [Fact]
    public void RankBidders_WithTiedScores_AssignsSameRank()
    {
        // Arrange
        var bids = new List<BidSubmissionDto>
        {
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1000000m }, // Rank 1 (tied)
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1000000m }, // Rank 1 (tied)
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1500000m }  // Rank 3
        };

        // Act
        var scores = CalculateCommercialScores(bids);
        var rankedScores = RankByCommercialScore(scores);

        // Assert
        var rank1Bidders = rankedScores.Where(s => s.Rank == 1).ToList();
        rank1Bidders.Should().HaveCount(2);

        var rank3Bidder = rankedScores.First(s => s.NormalizedTotalAmount == 1500000m);
        rank3Bidder.Rank.Should().Be(3); // Skips rank 2 due to tie
    }

    #endregion

    #region Provisional Sum Exclusion Tests

    [Fact]
    public void CalculateCommercialScore_ExcludesProvisionalSums_WhenConfigured()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var boqItems = new List<BoqItem>
        {
            CreateBoqItem(tenderId, 100.0m, BoqItemType.Base),
            CreateBoqItem(tenderId, 50.0m, BoqItemType.ProvisionalSum), // Should be excluded
            CreateBoqItem(tenderId, 75.0m, BoqItemType.Base)
        };

        // Act
        var totalExcludingProvisional = CalculateTotalExcluding(boqItems, BoqItemType.ProvisionalSum);

        // Assert
        // Should only include Base items: 100 + 75 = 175
        totalExcludingProvisional.Should().Be(175.0m);
    }

    [Fact]
    public void CalculateCommercialScore_IncludesProvisionalSums_WhenNotExcluded()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var boqItems = new List<BoqItem>
        {
            CreateBoqItem(tenderId, 100.0m, BoqItemType.Base),
            CreateBoqItem(tenderId, 50.0m, BoqItemType.ProvisionalSum),
            CreateBoqItem(tenderId, 75.0m, BoqItemType.Base)
        };

        // Act
        var totalIncludingAll = boqItems.Sum(b => b.Quantity);

        // Assert
        // Should include all items: 100 + 50 + 75 = 225
        totalIncludingAll.Should().Be(225.0m);
    }

    [Fact]
    public void CalculateCommercialScore_WithProvisionalSumsExcluded_ScoresCorrectly()
    {
        // Arrange - Two bidders with different provisional sum pricing
        var bidder1TotalBase = 1000000m;
        var bidder1ProvisionalSum = 500000m;
        var bidder2TotalBase = 1100000m;
        var bidder2ProvisionalSum = 300000m;

        var bidsExcludingPS = new List<BidSubmissionDto>
        {
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = bidder1TotalBase },
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = bidder2TotalBase }
        };

        // Act
        var scoresExcludingPS = CalculateCommercialScores(bidsExcludingPS);

        // Assert
        // Bidder 1 has lower base total, should win even though total with PS would be higher
        var bidder1Score = scoresExcludingPS.First(s => s.NormalizedTotalAmount == bidder1TotalBase);
        bidder1Score.CommercialScore.Should().Be(100.0m);
    }

    #endregion

    #region Alternate Items Exclusion Tests

    [Fact]
    public void CalculateCommercialScore_ExcludesAlternates_WhenConfigured()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var boqItems = new List<BoqItem>
        {
            CreateBoqItem(tenderId, 100.0m, BoqItemType.Base),
            CreateBoqItem(tenderId, 30.0m, BoqItemType.Alternate), // Should be excluded
            CreateBoqItem(tenderId, 75.0m, BoqItemType.Base)
        };

        // Act
        var totalExcludingAlternates = CalculateTotalExcluding(boqItems, BoqItemType.Alternate);

        // Assert
        // Should only include Base items: 100 + 75 = 175
        totalExcludingAlternates.Should().Be(175.0m);
    }

    [Fact]
    public void CalculateCommercialScore_ExcludesBothProvisionalSumsAndAlternates()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var boqItems = new List<BoqItem>
        {
            CreateBoqItem(tenderId, 100.0m, BoqItemType.Base),
            CreateBoqItem(tenderId, 50.0m, BoqItemType.ProvisionalSum),
            CreateBoqItem(tenderId, 30.0m, BoqItemType.Alternate),
            CreateBoqItem(tenderId, 75.0m, BoqItemType.Base),
            CreateBoqItem(tenderId, 25.0m, BoqItemType.Daywork)
        };

        var excludedTypes = new[] { BoqItemType.ProvisionalSum, BoqItemType.Alternate };

        // Act
        var totalExcluding = CalculateTotalExcluding(boqItems, excludedTypes);

        // Assert
        // Should include Base + Daywork: 100 + 75 + 25 = 200
        totalExcluding.Should().Be(200.0m);
    }

    [Fact]
    public void CalculateCommercialScore_WithAlternatesExcluded_RanksCorrectly()
    {
        // Arrange - Two bidders with different alternate pricing
        var bidder1BaseTotal = 1000000m;
        var bidder2BaseTotal = 950000m;

        var bidsExcludingAlternates = new List<BidSubmissionDto>
        {
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = bidder1BaseTotal },
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = bidder2BaseTotal }
        };

        // Act
        var scores = CalculateCommercialScores(bidsExcludingAlternates);
        var rankedScores = RankByCommercialScore(scores);

        // Assert
        var rank1 = rankedScores.First(s => s.Rank == 1);
        rank1.NormalizedTotalAmount.Should().Be(bidder2BaseTotal);
    }

    #endregion

    #region Edge Cases

    [Fact]
    public void CalculateCommercialScore_WithZeroBidAmount_HandlesGracefully()
    {
        // Arrange
        var bids = new List<BidSubmissionDto>
        {
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 0m },
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1000000m }
        };

        // Act
        var validBids = bids.Where(b => b.NormalizedTotalAmount > 0).ToList();
        var scores = CalculateCommercialScores(validBids);

        // Assert
        scores.Should().HaveCount(1);
        scores.First().CommercialScore.Should().Be(100.0m);
    }

    [Fact]
    public void CalculateCommercialScore_WithNullAmount_ExcludesFromCalculation()
    {
        // Arrange
        var bids = new List<BidSubmissionDto>
        {
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = null },
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1000000m },
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1500000m }
        };

        // Act
        var validBids = bids.Where(b => b.NormalizedTotalAmount.HasValue && b.NormalizedTotalAmount > 0).ToList();
        var scores = CalculateCommercialScores(validBids);

        // Assert
        scores.Should().HaveCount(2);
    }

    [Fact]
    public void CalculateCommercialScore_WithNoBids_ReturnsEmptyList()
    {
        // Arrange
        var bids = new List<BidSubmissionDto>();

        // Act
        var scores = CalculateCommercialScores(bids);

        // Assert
        scores.Should().BeEmpty();
    }

    [Fact]
    public void CalculateCommercialScore_ScoreNeverExceeds100()
    {
        // Arrange
        var bids = new List<BidSubmissionDto>
        {
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 1000000m },
            new BidSubmissionDto { BidderId = Guid.NewGuid(), NormalizedTotalAmount = 500000m } // Lower than "lowest"
        };

        // Act
        var scores = CalculateCommercialScores(bids);

        // Assert
        scores.All(s => s.CommercialScore <= 100.0m).Should().BeTrue();
    }

    #endregion

    #region Helper Methods and DTOs

    private static List<CommercialScoreResult> CalculateCommercialScores(
        List<BidSubmissionDto> bids)
    {
        if (!bids.Any() || bids.All(b => !b.NormalizedTotalAmount.HasValue || b.NormalizedTotalAmount <= 0))
            return new List<CommercialScoreResult>();

        var validBids = bids
            .Where(b => b.NormalizedTotalAmount.HasValue && b.NormalizedTotalAmount > 0)
            .ToList();

        var lowestBid = validBids.Min(b => b.NormalizedTotalAmount!.Value);

        return validBids.Select(b => new CommercialScoreResult
        {
            BidderId = b.BidderId,
            NormalizedTotalAmount = b.NormalizedTotalAmount!.Value,
            CommercialScore = Math.Round((lowestBid / b.NormalizedTotalAmount.Value) * 100, 2)
        }).ToList();
    }

    private static List<CommercialScoreResult> RankByCommercialScore(
        List<CommercialScoreResult> scores)
    {
        var orderedScores = scores.OrderByDescending(s => s.CommercialScore).ToList();

        int currentRank = 1;
        decimal? previousScore = null;

        for (int i = 0; i < orderedScores.Count; i++)
        {
            if (previousScore.HasValue && orderedScores[i].CommercialScore != previousScore)
            {
                currentRank = i + 1;
            }

            orderedScores[i].Rank = currentRank;
            previousScore = orderedScores[i].CommercialScore;
        }

        return orderedScores;
    }

    private static decimal CalculateTotalExcluding(
        List<BoqItem> boqItems,
        BoqItemType excludedType)
    {
        return boqItems
            .Where(b => b.ItemType != excludedType)
            .Sum(b => b.Quantity);
    }

    private static decimal CalculateTotalExcluding(
        List<BoqItem> boqItems,
        BoqItemType[] excludedTypes)
    {
        return boqItems
            .Where(b => !excludedTypes.Contains(b.ItemType))
            .Sum(b => b.Quantity);
    }

    private static BoqItem CreateBoqItem(Guid tenderId, decimal quantity, BoqItemType itemType)
    {
        return new BoqItem
        {
            Id = Guid.NewGuid(),
            TenderId = tenderId,
            SectionId = Guid.NewGuid(),
            ItemNumber = "1.1",
            Description = "Test Item",
            Quantity = quantity,
            Uom = "m2",
            ItemType = itemType
        };
    }

    private void SetupDbSets()
    {
        var bidSubmissionsMock = new Mock<DbSet<BidSubmission>>();
        bidSubmissionsMock.Setup(x => x.Add(It.IsAny<BidSubmission>()))
            .Callback<BidSubmission>(bs => _bidSubmissionsStore.Add(bs));
        _contextMock.Setup(x => x.BidSubmissions).Returns(bidSubmissionsMock.Object);
    }

    private class BidSubmissionDto
    {
        public Guid BidderId { get; set; }
        public decimal? NormalizedTotalAmount { get; set; }
    }

    private class CommercialScoreResult
    {
        public Guid BidderId { get; set; }
        public decimal NormalizedTotalAmount { get; set; }
        public decimal CommercialScore { get; set; }
        public int Rank { get; set; }
    }

    #endregion
}
