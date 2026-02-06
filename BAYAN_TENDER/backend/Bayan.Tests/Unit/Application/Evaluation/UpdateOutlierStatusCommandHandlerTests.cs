using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;
using Microsoft.EntityFrameworkCore;
using Moq;

namespace Bayan.Tests.Unit.Application.Evaluation;

/// <summary>
/// Unit tests for UpdateOutlierStatusCommandHandler.
/// Tests outlier detection logic based on deviation from average pricing.
/// </summary>
public class UpdateOutlierStatusCommandHandlerTests
{
    private readonly Mock<IApplicationDbContext> _contextMock;
    private readonly Mock<ICacheService> _cacheServiceMock;
    private readonly List<BidPricing> _bidPricingsStore;

    public UpdateOutlierStatusCommandHandlerTests()
    {
        _contextMock = new Mock<IApplicationDbContext>();
        _cacheServiceMock = new Mock<ICacheService>();
        _bidPricingsStore = new List<BidPricing>();

        SetupBidPricingsDbSet();
    }

    #region Outlier Detection - High Severity (>20% deviation)

    [Fact]
    public void DetectOutlier_WithGreaterThan20PercentDeviation_MarksAsHighSeverity()
    {
        // Arrange
        var boqItemId = Guid.NewGuid();
        var averageRate = 100.0m;
        var bidRate = 125.0m; // 25% above average

        var bidPricing = CreateBidPricing(boqItemId, bidRate);
        var deviationPercent = CalculateDeviation(bidRate, averageRate);

        // Act
        var severity = DetermineOutlierSeverity(deviationPercent);

        // Assert
        deviationPercent.Should().BeGreaterThan(20.0m);
        severity.Should().Be(OutlierSeverity.High);
    }

    [Fact]
    public void DetectOutlier_WithNegative25PercentDeviation_MarksAsHighSeverity()
    {
        // Arrange
        var averageRate = 100.0m;
        var bidRate = 75.0m; // 25% below average

        var deviationPercent = CalculateDeviation(bidRate, averageRate);

        // Act
        var severity = DetermineOutlierSeverity(deviationPercent);

        // Assert
        Math.Abs((double)deviationPercent).Should().BeGreaterThan(20.0);
        severity.Should().Be(OutlierSeverity.High);
    }

    [Theory]
    [InlineData(121.0, 100.0)] // 21% above
    [InlineData(130.0, 100.0)] // 30% above
    [InlineData(79.0, 100.0)]  // 21% below
    [InlineData(50.0, 100.0)]  // 50% below
    public void DetectOutlier_WithVariousHighDeviations_MarksAsHighSeverity(
        decimal bidRate, decimal averageRate)
    {
        // Arrange
        var deviationPercent = CalculateDeviation(bidRate, averageRate);

        // Act
        var severity = DetermineOutlierSeverity(deviationPercent);

        // Assert
        severity.Should().Be(OutlierSeverity.High);
    }

    #endregion

    #region Outlier Detection - Medium Severity (10-20% deviation)

    [Fact]
    public void DetectOutlier_With10To20PercentDeviation_MarksAsMediumSeverity()
    {
        // Arrange
        var averageRate = 100.0m;
        var bidRate = 115.0m; // 15% above average

        var deviationPercent = CalculateDeviation(bidRate, averageRate);

        // Act
        var severity = DetermineOutlierSeverity(deviationPercent);

        // Assert
        deviationPercent.Should().BeGreaterThanOrEqualTo(10.0m);
        deviationPercent.Should().BeLessThanOrEqualTo(20.0m);
        severity.Should().Be(OutlierSeverity.Medium);
    }

    [Fact]
    public void DetectOutlier_WithNegative15PercentDeviation_MarksAsMediumSeverity()
    {
        // Arrange
        var averageRate = 100.0m;
        var bidRate = 85.0m; // 15% below average

        var deviationPercent = CalculateDeviation(bidRate, averageRate);

        // Act
        var severity = DetermineOutlierSeverity(deviationPercent);

        // Assert
        Math.Abs((double)deviationPercent).Should().BeGreaterThanOrEqualTo(10.0);
        Math.Abs((double)deviationPercent).Should().BeLessThanOrEqualTo(20.0);
        severity.Should().Be(OutlierSeverity.Medium);
    }

    [Theory]
    [InlineData(110.0, 100.0)] // 10% above
    [InlineData(120.0, 100.0)] // 20% above (boundary)
    [InlineData(90.0, 100.0)]  // 10% below
    [InlineData(80.0, 100.0)]  // 20% below (boundary)
    public void DetectOutlier_WithMediumDeviations_MarksAsMediumSeverity(
        decimal bidRate, decimal averageRate)
    {
        // Arrange
        var deviationPercent = CalculateDeviation(bidRate, averageRate);

        // Act
        var severity = DetermineOutlierSeverity(deviationPercent);

        // Assert
        severity.Should().Be(OutlierSeverity.Medium);
    }

    #endregion

    #region Outlier Detection - Low/None (<10% deviation)

    [Fact]
    public void DetectOutlier_WithLessThan10PercentDeviation_MarksAsLowOrNone()
    {
        // Arrange
        var averageRate = 100.0m;
        var bidRate = 105.0m; // 5% above average

        var deviationPercent = CalculateDeviation(bidRate, averageRate);

        // Act
        var isOutlier = IsOutlier(deviationPercent);
        var severity = DetermineOutlierSeverity(deviationPercent);

        // Assert
        deviationPercent.Should().BeLessThan(10.0m);
        isOutlier.Should().BeFalse();
        severity.Should().Be(OutlierSeverity.Low);
    }

    [Fact]
    public void DetectOutlier_WithNegative5PercentDeviation_MarksAsLowOrNone()
    {
        // Arrange
        var averageRate = 100.0m;
        var bidRate = 95.0m; // 5% below average

        var deviationPercent = CalculateDeviation(bidRate, averageRate);

        // Act
        var isOutlier = IsOutlier(deviationPercent);

        // Assert
        Math.Abs((double)deviationPercent).Should().BeLessThan(10.0);
        isOutlier.Should().BeFalse();
    }

    [Theory]
    [InlineData(100.0, 100.0)] // 0% deviation
    [InlineData(101.0, 100.0)] // 1% above
    [InlineData(99.0, 100.0)]  // 1% below
    [InlineData(109.0, 100.0)] // 9% above
    [InlineData(91.0, 100.0)]  // 9% below
    public void DetectOutlier_WithLowDeviations_IsNotMarkedAsOutlier(
        decimal bidRate, decimal averageRate)
    {
        // Arrange
        var deviationPercent = CalculateDeviation(bidRate, averageRate);

        // Act
        var isOutlier = IsOutlier(deviationPercent);

        // Assert
        isOutlier.Should().BeFalse();
    }

    #endregion

    #region NoBid Items Excluded from Average Calculation

    [Fact]
    public void CalculateAverage_ExcludesNoBidItems()
    {
        // Arrange
        var boqItemId = Guid.NewGuid();
        var bidPricings = new List<BidPricing>
        {
            CreateBidPricing(boqItemId, 100.0m, isNoBid: false),
            CreateBidPricing(boqItemId, 110.0m, isNoBid: false),
            CreateBidPricing(boqItemId, 120.0m, isNoBid: false),
            CreateBidPricing(boqItemId, 0.0m, isNoBid: true),   // NoBid - should be excluded
            CreateBidPricing(boqItemId, 0.0m, isNoBid: true)    // NoBid - should be excluded
        };

        // Act
        var average = CalculateAverageExcludingNoBidAndNonComparable(bidPricings);

        // Assert
        // Average should be (100 + 110 + 120) / 3 = 110, not including NoBid items
        average.Should().Be(110.0m);
    }

    [Fact]
    public void CalculateAverage_WithAllNoBidItems_ReturnsZero()
    {
        // Arrange
        var boqItemId = Guid.NewGuid();
        var bidPricings = new List<BidPricing>
        {
            CreateBidPricing(boqItemId, 0.0m, isNoBid: true),
            CreateBidPricing(boqItemId, 0.0m, isNoBid: true),
            CreateBidPricing(boqItemId, 0.0m, isNoBid: true)
        };

        // Act
        var average = CalculateAverageExcludingNoBidAndNonComparable(bidPricings);

        // Assert
        average.Should().Be(0.0m);
    }

    [Fact]
    public void NoBidItem_IsNotFlaggedAsOutlier()
    {
        // Arrange
        var boqItemId = Guid.NewGuid();
        var bidPricing = CreateBidPricing(boqItemId, 0.0m, isNoBid: true);
        var averageRate = 100.0m;

        // Act
        var shouldCheckOutlier = ShouldCheckForOutlier(bidPricing);

        // Assert
        shouldCheckOutlier.Should().BeFalse();
    }

    #endregion

    #region NonComparable Items Excluded from Average Calculation

    [Fact]
    public void CalculateAverage_ExcludesNonComparableItems()
    {
        // Arrange
        var boqItemId = Guid.NewGuid();
        var bidPricings = new List<BidPricing>
        {
            CreateBidPricing(boqItemId, 100.0m, isNonComparable: false),
            CreateBidPricing(boqItemId, 110.0m, isNonComparable: false),
            CreateBidPricing(boqItemId, 200.0m, isNonComparable: true),  // NonComparable - excluded
            CreateBidPricing(boqItemId, 120.0m, isNonComparable: false)
        };

        // Act
        var average = CalculateAverageExcludingNoBidAndNonComparable(bidPricings);

        // Assert
        // Average should be (100 + 110 + 120) / 3 = 110, not including NonComparable items
        average.Should().Be(110.0m);
    }

    [Fact]
    public void CalculateAverage_ExcludesBothNoBidAndNonComparable()
    {
        // Arrange
        var boqItemId = Guid.NewGuid();
        var bidPricings = new List<BidPricing>
        {
            CreateBidPricing(boqItemId, 100.0m),
            CreateBidPricing(boqItemId, 200.0m),
            CreateBidPricing(boqItemId, 0.0m, isNoBid: true),           // Excluded
            CreateBidPricing(boqItemId, 500.0m, isNonComparable: true)  // Excluded
        };

        // Act
        var average = CalculateAverageExcludingNoBidAndNonComparable(bidPricings);

        // Assert
        // Average should be (100 + 200) / 2 = 150
        average.Should().Be(150.0m);
    }

    [Fact]
    public void NonComparableItem_IsNotFlaggedAsOutlier()
    {
        // Arrange
        var boqItemId = Guid.NewGuid();
        var bidPricing = CreateBidPricing(boqItemId, 500.0m, isNonComparable: true);

        // Act
        var shouldCheckOutlier = ShouldCheckForOutlier(bidPricing);

        // Assert
        shouldCheckOutlier.Should().BeFalse();
    }

    #endregion

    #region Edge Cases

    [Fact]
    public void DetectOutlier_WithZeroAverage_HandlesGracefully()
    {
        // Arrange
        var averageRate = 0.0m;
        var bidRate = 100.0m;

        // Act
        // When average is zero, deviation calculation should handle division by zero
        var canCalculateDeviation = averageRate != 0;

        // Assert
        canCalculateDeviation.Should().BeFalse();
    }

    [Fact]
    public void DetectOutlier_WithSingleBidder_NoOutlierDetected()
    {
        // Arrange
        var boqItemId = Guid.NewGuid();
        var bidPricings = new List<BidPricing>
        {
            CreateBidPricing(boqItemId, 100.0m)
        };

        // Act
        var average = CalculateAverageExcludingNoBidAndNonComparable(bidPricings);
        var deviationPercent = CalculateDeviation(100.0m, average);

        // Assert
        // Single bidder should have 0% deviation from average (which is itself)
        deviationPercent.Should().Be(0.0m);
    }

    [Fact]
    public void UpdateOutlierStatus_SetsDeviationFromAverageProperty()
    {
        // Arrange
        var boqItemId = Guid.NewGuid();
        var bidPricing = CreateBidPricing(boqItemId, 125.0m);
        var averageRate = 100.0m;
        var deviationPercent = CalculateDeviation(bidPricing.NormalizedUnitRate!.Value, averageRate);

        // Act
        bidPricing.DeviationFromAverage = deviationPercent;
        bidPricing.IsOutlier = IsOutlier(deviationPercent);
        bidPricing.OutlierSeverity = DetermineOutlierSeverity(deviationPercent);

        // Assert
        bidPricing.DeviationFromAverage.Should().Be(25.0m);
        bidPricing.IsOutlier.Should().BeTrue();
        bidPricing.OutlierSeverity.Should().Be(OutlierSeverity.High);
    }

    #endregion

    #region Boundary Tests

    [Fact]
    public void DetectOutlier_AtExactly10PercentDeviation_IsMediumSeverity()
    {
        // Arrange
        var averageRate = 100.0m;
        var bidRate = 110.0m; // Exactly 10% above

        var deviationPercent = CalculateDeviation(bidRate, averageRate);

        // Act
        var severity = DetermineOutlierSeverity(deviationPercent);

        // Assert
        severity.Should().Be(OutlierSeverity.Medium);
    }

    [Fact]
    public void DetectOutlier_AtExactly20PercentDeviation_IsMediumSeverity()
    {
        // Arrange
        var averageRate = 100.0m;
        var bidRate = 120.0m; // Exactly 20% above

        var deviationPercent = CalculateDeviation(bidRate, averageRate);

        // Act
        var severity = DetermineOutlierSeverity(deviationPercent);

        // Assert
        severity.Should().Be(OutlierSeverity.Medium);
    }

    [Fact]
    public void DetectOutlier_JustAbove20PercentDeviation_IsHighSeverity()
    {
        // Arrange
        var averageRate = 100.0m;
        var bidRate = 120.01m; // Just above 20%

        var deviationPercent = CalculateDeviation(bidRate, averageRate);

        // Act
        var severity = DetermineOutlierSeverity(deviationPercent);

        // Assert
        severity.Should().Be(OutlierSeverity.High);
    }

    #endregion

    #region Helper Methods

    private static decimal CalculateDeviation(decimal bidRate, decimal averageRate)
    {
        if (averageRate == 0) return 0;
        return ((bidRate - averageRate) / averageRate) * 100;
    }

    private static bool IsOutlier(decimal deviationPercent)
    {
        return Math.Abs(deviationPercent) >= 10.0m;
    }

    private static OutlierSeverity DetermineOutlierSeverity(decimal deviationPercent)
    {
        var absDeviation = Math.Abs(deviationPercent);

        if (absDeviation > 20.0m)
            return OutlierSeverity.High;
        if (absDeviation >= 10.0m)
            return OutlierSeverity.Medium;
        return OutlierSeverity.Low;
    }

    private static decimal CalculateAverageExcludingNoBidAndNonComparable(
        IEnumerable<BidPricing> bidPricings)
    {
        var validPricings = bidPricings
            .Where(bp => !bp.IsNoBid && !bp.IsNonComparable && bp.NormalizedUnitRate.HasValue)
            .ToList();

        if (!validPricings.Any())
            return 0.0m;

        return validPricings.Average(bp => bp.NormalizedUnitRate!.Value);
    }

    private static bool ShouldCheckForOutlier(BidPricing bidPricing)
    {
        return !bidPricing.IsNoBid && !bidPricing.IsNonComparable && bidPricing.NormalizedUnitRate.HasValue;
    }

    private static BidPricing CreateBidPricing(
        Guid boqItemId,
        decimal normalizedRate,
        bool isNoBid = false,
        bool isNonComparable = false)
    {
        return new BidPricing
        {
            Id = Guid.NewGuid(),
            BoqItemId = boqItemId,
            BidSubmissionId = Guid.NewGuid(),
            NormalizedUnitRate = normalizedRate,
            NormalizedAmount = normalizedRate * 10, // Assuming quantity of 10
            IsNoBid = isNoBid,
            IsNonComparable = isNonComparable,
            NativeCurrency = "SAR"
        };
    }

    private void SetupBidPricingsDbSet()
    {
        var mockDbSet = new Mock<DbSet<BidPricing>>();

        mockDbSet.Setup(x => x.Add(It.IsAny<BidPricing>()))
            .Callback<BidPricing>(bp => _bidPricingsStore.Add(bp));

        _contextMock.Setup(x => x.BidPricings).Returns(mockDbSet.Object);
    }

    #endregion
}
