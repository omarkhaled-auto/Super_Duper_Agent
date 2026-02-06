using Bayan.Application.Common.Interfaces;
using FluentAssertions;
using Moq;

namespace Bayan.Tests.Unit.Application.BidAnalysis;

/// <summary>
/// Unit tests for IFuzzyMatchingService implementation.
/// Tests fuzzy string matching capabilities for BOQ item matching.
/// </summary>
public class FuzzyMatchingServiceTests
{
    private readonly Mock<IFuzzyMatchingService> _fuzzyMatchingServiceMock;

    public FuzzyMatchingServiceTests()
    {
        _fuzzyMatchingServiceMock = new Mock<IFuzzyMatchingService>();
    }

    #region CalculateSimilarity Tests

    [Fact]
    public void CalculateSimilarity_WithExactStrings_Returns100()
    {
        // Arrange
        const string string1 = "Supply and install HVAC system";
        const string string2 = "Supply and install HVAC system";

        _fuzzyMatchingServiceMock
            .Setup(x => x.CalculateSimilarity(string1, string2))
            .Returns(100.0);

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.CalculateSimilarity(string1, string2);

        // Assert
        result.Should().Be(100.0);
    }

    [Fact]
    public void CalculateSimilarity_WithSimilarStrings_ReturnsHighScore()
    {
        // Arrange
        const string string1 = "Supply and install HVAC system";
        const string string2 = "Supply & install HVAC systems";

        _fuzzyMatchingServiceMock
            .Setup(x => x.CalculateSimilarity(string1, string2))
            .Returns(92.5);

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.CalculateSimilarity(string1, string2);

        // Assert
        result.Should().BeGreaterThan(80.0);
        result.Should().BeLessThan(100.0);
    }

    [Fact]
    public void CalculateSimilarity_WithDifferentStrings_ReturnsLowScore()
    {
        // Arrange
        const string string1 = "Supply and install HVAC system";
        const string string2 = "Concrete foundation works";

        _fuzzyMatchingServiceMock
            .Setup(x => x.CalculateSimilarity(string1, string2))
            .Returns(15.0);

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.CalculateSimilarity(string1, string2);

        // Assert
        result.Should().BeLessThan(50.0);
    }

    [Fact]
    public void CalculateSimilarity_WithNullFirstString_ReturnsZero()
    {
        // Arrange
        const string? string1 = null;
        const string string2 = "Supply and install HVAC system";

        _fuzzyMatchingServiceMock
            .Setup(x => x.CalculateSimilarity(string1, string2))
            .Returns(0.0);

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.CalculateSimilarity(string1, string2);

        // Assert
        result.Should().Be(0.0);
    }

    [Fact]
    public void CalculateSimilarity_WithNullSecondString_ReturnsZero()
    {
        // Arrange
        const string string1 = "Supply and install HVAC system";
        const string? string2 = null;

        _fuzzyMatchingServiceMock
            .Setup(x => x.CalculateSimilarity(string1, string2))
            .Returns(0.0);

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.CalculateSimilarity(string1, string2);

        // Assert
        result.Should().Be(0.0);
    }

    [Fact]
    public void CalculateSimilarity_WithBothNullStrings_ReturnsZero()
    {
        // Arrange
        const string? string1 = null;
        const string? string2 = null;

        _fuzzyMatchingServiceMock
            .Setup(x => x.CalculateSimilarity(string1, string2))
            .Returns(0.0);

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.CalculateSimilarity(string1, string2);

        // Assert
        result.Should().Be(0.0);
    }

    [Fact]
    public void CalculateSimilarity_WithEmptyStrings_ReturnsZero()
    {
        // Arrange
        const string string1 = "";
        const string string2 = "";

        _fuzzyMatchingServiceMock
            .Setup(x => x.CalculateSimilarity(string1, string2))
            .Returns(0.0);

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.CalculateSimilarity(string1, string2);

        // Assert
        result.Should().Be(0.0);
    }

    [Theory]
    [InlineData("Reinforced Concrete Grade 40", "Reinforced Concrete Gr. 40", 95.0)]
    [InlineData("Steel Reinforcement 16mm dia", "Steel Rebar 16mm diameter", 85.0)]
    [InlineData("Electrical wiring CAT6", "CAT6 Electrical wiring", 90.0)]
    public void CalculateSimilarity_WithVariousStrings_ReturnsExpectedScores(
        string string1, string string2, double expectedMinScore)
    {
        // Arrange
        _fuzzyMatchingServiceMock
            .Setup(x => x.CalculateSimilarity(string1, string2))
            .Returns(expectedMinScore);

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.CalculateSimilarity(string1, string2);

        // Assert
        result.Should().BeGreaterThanOrEqualTo(expectedMinScore - 10.0);
    }

    #endregion

    #region FindBestMatch Tests

    [Fact]
    public void FindBestMatch_WithMatchingCandidate_ReturnsCorrectMatch()
    {
        // Arrange
        const string searchTerm = "Supply HVAC system";
        var candidates = new List<string>
        {
            "Concrete foundation works",
            "Supply and install HVAC system",
            "Electrical wiring installation",
            "Plumbing works"
        };

        _fuzzyMatchingServiceMock
            .Setup(x => x.FindBestMatch(searchTerm, candidates))
            .Returns(("Supply and install HVAC system", 92.5));

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.FindBestMatch(searchTerm, candidates);

        // Assert
        result.BestMatch.Should().Be("Supply and install HVAC system");
        result.Confidence.Should().BeGreaterThan(80.0);
    }

    [Fact]
    public void FindBestMatch_WithNoGoodMatch_ReturnsLowConfidence()
    {
        // Arrange
        const string searchTerm = "Excavation works for basement";
        var candidates = new List<string>
        {
            "Concrete foundation works",
            "Supply and install HVAC system",
            "Electrical wiring installation"
        };

        _fuzzyMatchingServiceMock
            .Setup(x => x.FindBestMatch(searchTerm, candidates))
            .Returns(("Concrete foundation works", 35.0));

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.FindBestMatch(searchTerm, candidates);

        // Assert
        result.Confidence.Should().BeLessThan(80.0);
    }

    [Fact]
    public void FindBestMatch_WithEmptyCandidates_ReturnsNullMatch()
    {
        // Arrange
        const string searchTerm = "Supply HVAC system";
        var candidates = new List<string>();

        _fuzzyMatchingServiceMock
            .Setup(x => x.FindBestMatch(searchTerm, candidates))
            .Returns((null, 0.0));

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.FindBestMatch(searchTerm, candidates);

        // Assert
        result.BestMatch.Should().BeNull();
        result.Confidence.Should().Be(0.0);
    }

    [Fact]
    public void FindBestMatch_WithNullSearchTerm_ReturnsNullMatch()
    {
        // Arrange
        const string? searchTerm = null;
        var candidates = new List<string>
        {
            "Concrete foundation works",
            "Supply and install HVAC system"
        };

        _fuzzyMatchingServiceMock
            .Setup(x => x.FindBestMatch(searchTerm, candidates))
            .Returns((null, 0.0));

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.FindBestMatch(searchTerm, candidates);

        // Assert
        result.BestMatch.Should().BeNull();
        result.Confidence.Should().Be(0.0);
    }

    [Fact]
    public void FindBestMatch_ReturnsHighestScoringCandidate()
    {
        // Arrange
        const string searchTerm = "Reinforced concrete Grade 40";
        var candidates = new List<string>
        {
            "Reinforced concrete Gr 40",        // Expected best match
            "Concrete Grade 40",                 // Lower match
            "Reinforced steel",                  // Low match
            "Plain concrete"                     // Lowest match
        };

        _fuzzyMatchingServiceMock
            .Setup(x => x.FindBestMatch(searchTerm, candidates))
            .Returns(("Reinforced concrete Gr 40", 95.0));

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.FindBestMatch(searchTerm, candidates);

        // Assert
        result.BestMatch.Should().Be("Reinforced concrete Gr 40");
    }

    #endregion

    #region CalculateTokenSetRatio Tests

    [Fact]
    public void CalculateTokenSetRatio_WithSameWordsInDifferentOrder_ReturnsHighScore()
    {
        // Arrange
        const string string1 = "Supply and install HVAC system complete";
        const string string2 = "HVAC system complete supply and install";

        _fuzzyMatchingServiceMock
            .Setup(x => x.CalculateTokenSetRatio(string1, string2))
            .Returns(100.0);

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.CalculateTokenSetRatio(string1, string2);

        // Assert
        result.Should().BeGreaterThanOrEqualTo(95.0);
    }

    [Fact]
    public void CalculateTokenSetRatio_ForDescriptionMatching_HandlesReorderedWords()
    {
        // Arrange
        const string boqDescription = "Reinforced concrete grade 40 for columns";
        const string bidderDescription = "Columns reinforced concrete grade 40";

        _fuzzyMatchingServiceMock
            .Setup(x => x.CalculateTokenSetRatio(boqDescription, bidderDescription))
            .Returns(95.0);

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.CalculateTokenSetRatio(boqDescription, bidderDescription);

        // Assert
        result.Should().BeGreaterThanOrEqualTo(90.0);
    }

    [Fact]
    public void CalculateTokenSetRatio_WithPartialOverlap_ReturnsModerateScore()
    {
        // Arrange
        const string string1 = "Supply install HVAC system chiller";
        const string string2 = "Supply install HVAC system AHU";

        _fuzzyMatchingServiceMock
            .Setup(x => x.CalculateTokenSetRatio(string1, string2))
            .Returns(80.0);

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.CalculateTokenSetRatio(string1, string2);

        // Assert
        result.Should().BeGreaterThan(70.0);
        result.Should().BeLessThan(100.0);
    }

    [Fact]
    public void CalculateTokenSetRatio_WithNullStrings_ReturnsZero()
    {
        // Arrange
        const string? string1 = null;
        const string? string2 = null;

        _fuzzyMatchingServiceMock
            .Setup(x => x.CalculateTokenSetRatio(string1, string2))
            .Returns(0.0);

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.CalculateTokenSetRatio(string1, string2);

        // Assert
        result.Should().Be(0.0);
    }

    #endregion

    #region Auto-Match Threshold Tests (80%)

    [Fact]
    public void FindBestMatch_WithScoreAbove80_QualifiesForAutoMatch()
    {
        // Arrange
        const string searchTerm = "Supply and install fire alarm system";
        var candidates = new List<string>
        {
            "Supply & install fire alarm system complete"
        };

        _fuzzyMatchingServiceMock
            .Setup(x => x.FindBestMatch(searchTerm, candidates))
            .Returns(("Supply & install fire alarm system complete", 85.0));

        var service = _fuzzyMatchingServiceMock.Object;
        const double autoMatchThreshold = 80.0;

        // Act
        var result = service.FindBestMatch(searchTerm, candidates);
        var qualifiesForAutoMatch = result.Confidence >= autoMatchThreshold;

        // Assert
        qualifiesForAutoMatch.Should().BeTrue();
    }

    [Fact]
    public void FindBestMatch_WithScoreBelow80_DoesNotQualifyForAutoMatch()
    {
        // Arrange
        const string searchTerm = "Electrical conduit installation";
        var candidates = new List<string>
        {
            "PVC pipes for drainage"
        };

        _fuzzyMatchingServiceMock
            .Setup(x => x.FindBestMatch(searchTerm, candidates))
            .Returns(("PVC pipes for drainage", 45.0));

        var service = _fuzzyMatchingServiceMock.Object;
        const double autoMatchThreshold = 80.0;

        // Act
        var result = service.FindBestMatch(searchTerm, candidates);
        var qualifiesForAutoMatch = result.Confidence >= autoMatchThreshold;

        // Assert
        qualifiesForAutoMatch.Should().BeFalse();
    }

    [Fact]
    public void FindBestMatch_WithScoreExactly80_QualifiesForAutoMatch()
    {
        // Arrange
        const string searchTerm = "Steel reinforcement 16mm";
        var candidates = new List<string>
        {
            "Steel rebar 16mm dia"
        };

        _fuzzyMatchingServiceMock
            .Setup(x => x.FindBestMatch(searchTerm, candidates))
            .Returns(("Steel rebar 16mm dia", 80.0));

        var service = _fuzzyMatchingServiceMock.Object;
        const double autoMatchThreshold = 80.0;

        // Act
        var result = service.FindBestMatch(searchTerm, candidates);
        var qualifiesForAutoMatch = result.Confidence >= autoMatchThreshold;

        // Assert
        qualifiesForAutoMatch.Should().BeTrue();
    }

    [Theory]
    [InlineData(79.9, false)]
    [InlineData(80.0, true)]
    [InlineData(80.1, true)]
    [InlineData(100.0, true)]
    [InlineData(50.0, false)]
    public void AutoMatchThreshold_CorrectlyDeterminesEligibility(
        double confidence, bool expectedEligibility)
    {
        // Arrange
        const double autoMatchThreshold = 80.0;

        // Act
        var qualifiesForAutoMatch = confidence >= autoMatchThreshold;

        // Assert
        qualifiesForAutoMatch.Should().Be(expectedEligibility);
    }

    #endregion

    #region FindMatches Tests

    [Fact]
    public void FindMatches_WithMinConfidence_FiltersCorrectly()
    {
        // Arrange
        const string searchTerm = "Concrete works";
        var candidates = new List<string>
        {
            "Concrete foundation works",
            "Concrete column works",
            "Steel reinforcement",
            "Electrical works"
        };

        var expectedMatches = new List<(string Match, double Confidence)>
        {
            ("Concrete foundation works", 90.0),
            ("Concrete column works", 85.0)
        };

        _fuzzyMatchingServiceMock
            .Setup(x => x.FindMatches(searchTerm, candidates, 80.0))
            .Returns(expectedMatches);

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.FindMatches(searchTerm, candidates, 80.0).ToList();

        // Assert
        result.Should().HaveCount(2);
        result.All(r => r.Confidence >= 80.0).Should().BeTrue();
    }

    [Fact]
    public void FindMatches_ReturnsResultsOrderedByConfidenceDescending()
    {
        // Arrange
        const string searchTerm = "Steel";
        var candidates = new List<string>
        {
            "Steel reinforcement",
            "Structural steel",
            "Steel plates"
        };

        var expectedMatches = new List<(string Match, double Confidence)>
        {
            ("Structural steel", 95.0),
            ("Steel reinforcement", 90.0),
            ("Steel plates", 85.0)
        };

        _fuzzyMatchingServiceMock
            .Setup(x => x.FindMatches(searchTerm, candidates, 0.0))
            .Returns(expectedMatches);

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.FindMatches(searchTerm, candidates, 0.0).ToList();

        // Assert
        result.Should().BeInDescendingOrder(r => r.Confidence);
    }

    #endregion

    #region FindBestMatch with KeySelector Tests

    [Fact]
    public void FindBestMatch_WithKeySelector_MatchesOnSelectedProperty()
    {
        // Arrange
        const string searchTerm = "HVAC installation";
        var candidates = new List<TestCandidate>
        {
            new TestCandidate { Id = 1, Description = "Concrete works" },
            new TestCandidate { Id = 2, Description = "HVAC system installation" },
            new TestCandidate { Id = 3, Description = "Electrical works" }
        };

        _fuzzyMatchingServiceMock
            .Setup(x => x.FindBestMatch(
                searchTerm,
                candidates,
                It.IsAny<Func<TestCandidate, string?>>()))
            .Returns((candidates[1], 92.0));

        var service = _fuzzyMatchingServiceMock.Object;

        // Act
        var result = service.FindBestMatch(searchTerm, candidates, c => c.Description);

        // Assert
        result.BestMatch.Should().NotBeNull();
        result.BestMatch!.Id.Should().Be(2);
        result.Confidence.Should().BeGreaterThan(80.0);
    }

    private class TestCandidate
    {
        public int Id { get; set; }
        public string Description { get; set; } = string.Empty;
    }

    #endregion
}
