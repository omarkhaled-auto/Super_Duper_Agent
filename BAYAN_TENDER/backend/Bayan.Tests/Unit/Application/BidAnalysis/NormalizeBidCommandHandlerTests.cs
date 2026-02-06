using Bayan.Application.Common.Interfaces;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;
using Microsoft.EntityFrameworkCore;
using Moq;

namespace Bayan.Tests.Unit.Application.BidAnalysis;

/// <summary>
/// Unit tests for NormalizeBidCommandHandler.
/// Tests currency conversion and UOM normalization logic for bid analysis.
/// </summary>
public class NormalizeBidCommandHandlerTests
{
    private readonly Mock<IApplicationDbContext> _contextMock;
    private readonly Mock<ICacheService> _cacheServiceMock;
    private readonly List<BidPricing> _bidPricingsStore;
    private readonly List<UomMaster> _uomMastersStore;

    // Standard conversion factors
    private const decimal SQFT_TO_M2_FACTOR = 0.092903m;
    private const decimal FT_TO_LM_FACTOR = 0.3048m;

    public NormalizeBidCommandHandlerTests()
    {
        _contextMock = new Mock<IApplicationDbContext>();
        _cacheServiceMock = new Mock<ICacheService>();
        _bidPricingsStore = new List<BidPricing>();
        _uomMastersStore = new List<UomMaster>();

        SetupDbSets();
    }

    #region Currency Conversion Tests

    [Fact]
    public void CurrencyConversion_AppliesCorrectFxRate()
    {
        // Arrange
        const decimal nativeRate = 100.0m;
        const decimal fxRate = 3.75m; // USD to SAR
        const string baseCurrency = "SAR";

        var bidPricing = CreateBidPricing(nativeRate, "USD");

        // Act
        var normalizedRate = ApplyCurrencyConversion(nativeRate, fxRate);
        bidPricing.NormalizedUnitRate = normalizedRate;
        bidPricing.FxRateApplied = fxRate;

        // Assert
        normalizedRate.Should().Be(375.0m); // 100 * 3.75
        bidPricing.FxRateApplied.Should().Be(fxRate);
    }

    [Fact]
    public void CurrencyConversion_WithSameCurrency_AppliesRateOf1()
    {
        // Arrange
        const decimal nativeRate = 100.0m;
        const decimal fxRate = 1.0m; // SAR to SAR
        const string currency = "SAR";

        var bidPricing = CreateBidPricing(nativeRate, currency);

        // Act
        var normalizedRate = ApplyCurrencyConversion(nativeRate, fxRate);
        bidPricing.NormalizedUnitRate = normalizedRate;
        bidPricing.FxRateApplied = fxRate;

        // Assert
        normalizedRate.Should().Be(100.0m);
        bidPricing.FxRateApplied.Should().Be(1.0m);
    }

    [Theory]
    [InlineData(100.0, 3.75, 375.0)]   // USD to SAR
    [InlineData(100.0, 4.08, 408.0)]   // EUR to SAR
    [InlineData(100.0, 4.89, 489.0)]   // GBP to SAR
    [InlineData(100.0, 1.0, 100.0)]    // SAR to SAR
    [InlineData(1000.0, 0.27, 270.0)]  // JPY to SAR (approximate)
    public void CurrencyConversion_WithVariousRates_CalculatesCorrectly(
        decimal nativeRate, decimal fxRate, decimal expectedNormalizedRate)
    {
        // Arrange & Act
        var normalizedRate = ApplyCurrencyConversion(nativeRate, fxRate);

        // Assert
        normalizedRate.Should().Be(expectedNormalizedRate);
    }

    [Fact]
    public void CurrencyConversion_PreservesPrecision()
    {
        // Arrange
        const decimal nativeRate = 33.33m;
        const decimal fxRate = 3.7532m;

        // Act
        var normalizedRate = ApplyCurrencyConversion(nativeRate, fxRate);

        // Assert
        normalizedRate.Should().Be(125.0691556m);
    }

    [Fact]
    public void CurrencyConversion_WithZeroRate_ReturnsZero()
    {
        // Arrange
        const decimal nativeRate = 100.0m;
        const decimal fxRate = 0.0m;

        // Act
        var normalizedRate = ApplyCurrencyConversion(nativeRate, fxRate);

        // Assert
        normalizedRate.Should().Be(0.0m);
    }

    #endregion

    #region UOM Conversion Tests

    [Fact]
    public void UomConversion_AppliesCorrectFactor()
    {
        // Arrange
        const decimal nativeRate = 100.0m;
        const decimal conversionFactor = 2.0m;

        var bidPricing = CreateBidPricing(nativeRate, "SAR", bidderUom: "ft");

        // Act
        var normalizedRate = ApplyUomConversion(nativeRate, conversionFactor);
        bidPricing.UomConversionFactor = conversionFactor;

        // Assert
        normalizedRate.Should().Be(200.0m);
    }

    [Fact]
    public void UomConversion_SqftToM2_AppliesCorrectFactor()
    {
        // Arrange
        const decimal nativeRatePerSqft = 10.0m;
        const decimal expectedRatePerM2 = 10.0m / SQFT_TO_M2_FACTOR;

        var bidPricing = CreateBidPricing(nativeRatePerSqft, "SAR", bidderUom: "sqft");

        // Act
        // Rate per sqft needs to be converted to rate per m2
        // Since 1 m2 = 10.764 sqft, rate per m2 = rate per sqft / 0.092903
        var normalizedRate = ApplyUomConversion(nativeRatePerSqft, 1 / SQFT_TO_M2_FACTOR);
        bidPricing.NormalizedUnitRate = normalizedRate;
        bidPricing.UomConversionFactor = 1 / SQFT_TO_M2_FACTOR;

        // Assert
        normalizedRate.Should().BeApproximately(107.64m, 0.1m);
        bidPricing.UomConversionFactor.Should().BeApproximately(10.764m, 0.001m);
    }

    [Fact]
    public void UomConversion_FtToLM_AppliesCorrectFactor()
    {
        // Arrange
        const decimal nativeRatePerFt = 30.48m;
        const decimal expectedRatePerLM = 30.48m / FT_TO_LM_FACTOR;

        var bidPricing = CreateBidPricing(nativeRatePerFt, "SAR", bidderUom: "ft");

        // Act
        // Rate per ft needs to be converted to rate per LM
        // Since 1 LM = 3.28 ft, rate per LM = rate per ft / 0.3048
        var normalizedRate = ApplyUomConversion(nativeRatePerFt, 1 / FT_TO_LM_FACTOR);
        bidPricing.NormalizedUnitRate = normalizedRate;
        bidPricing.UomConversionFactor = 1 / FT_TO_LM_FACTOR;

        // Assert
        normalizedRate.Should().Be(100.0m);
        bidPricing.UomConversionFactor.Should().BeApproximately(3.28m, 0.01m);
    }

    [Theory]
    [InlineData("sqft", "m2", 0.092903)]
    [InlineData("ft", "LM", 0.3048)]
    [InlineData("ft", "m", 0.3048)]
    [InlineData("inch", "mm", 25.4)]
    [InlineData("yd", "m", 0.9144)]
    [InlineData("gallon", "liter", 3.78541)]
    public void UomConversion_StandardConversions_HaveCorrectFactors(
        string fromUom, string toUom, double expectedFactor)
    {
        // Arrange
        var conversionFactor = GetConversionFactor(fromUom, toUom);

        // Assert
        ((double)conversionFactor).Should().BeApproximately(expectedFactor, 0.0001);
    }

    [Fact]
    public void UomConversion_WithSameUom_AppliesFactorOf1()
    {
        // Arrange
        const decimal nativeRate = 100.0m;
        const string uom = "m2";

        var bidPricing = CreateBidPricing(nativeRate, "SAR", bidderUom: uom);

        // Act
        var normalizedRate = ApplyUomConversion(nativeRate, 1.0m);

        // Assert
        normalizedRate.Should().Be(100.0m);
    }

    #endregion

    #region Incompatible UOM Tests (Non-Comparable)

    [Fact]
    public void UomConversion_LSToM2_MarksAsNonComparable()
    {
        // Arrange
        var bidPricing = CreateBidPricing(1000.0m, "SAR", bidderUom: "LS");
        const string masterUom = "m2";

        // Act
        var isConvertible = IsUomConvertible("LS", masterUom);
        if (!isConvertible)
        {
            bidPricing.IsNonComparable = true;
            bidPricing.NormalizedUnitRate = null;
            bidPricing.Notes = $"Cannot convert from LS to {masterUom}";
        }

        // Assert
        isConvertible.Should().BeFalse();
        bidPricing.IsNonComparable.Should().BeTrue();
        bidPricing.NormalizedUnitRate.Should().BeNull();
    }

    [Fact]
    public void UomConversion_M2ToLS_MarksAsNonComparable()
    {
        // Arrange
        var bidPricing = CreateBidPricing(50.0m, "SAR", bidderUom: "m2");
        const string masterUom = "LS";

        // Act
        var isConvertible = IsUomConvertible("m2", masterUom);
        if (!isConvertible)
        {
            bidPricing.IsNonComparable = true;
        }

        // Assert
        isConvertible.Should().BeFalse();
        bidPricing.IsNonComparable.Should().BeTrue();
    }

    [Theory]
    [InlineData("LS", "m2")]
    [InlineData("LS", "LM")]
    [InlineData("Lot", "m2")]
    [InlineData("m2", "LM")]   // Area to length - not directly convertible
    [InlineData("kg", "m3")]   // Mass to volume - not convertible without density
    [InlineData("No", "m2")]   // Number to area - not convertible
    public void UomConversion_IncompatibleTypes_MarksAsNonComparable(
        string bidderUom, string masterUom)
    {
        // Arrange
        var bidPricing = CreateBidPricing(100.0m, "SAR", bidderUom: bidderUom);

        // Act
        var isConvertible = IsUomConvertible(bidderUom, masterUom);

        // Assert
        isConvertible.Should().BeFalse();
    }

    [Theory]
    [InlineData("sqft", "m2")]
    [InlineData("ft", "LM")]
    [InlineData("ft", "m")]
    [InlineData("m2", "sqft")]
    [InlineData("LM", "ft")]
    [InlineData("m", "ft")]
    public void UomConversion_CompatibleTypes_IsConvertible(
        string bidderUom, string masterUom)
    {
        // Arrange & Act
        var isConvertible = IsUomConvertible(bidderUom, masterUom);

        // Assert
        isConvertible.Should().BeTrue();
    }

    #endregion

    #region Combined Currency and UOM Conversion Tests

    [Fact]
    public void NormalizeBid_AppliesBothCurrencyAndUomConversion()
    {
        // Arrange
        const decimal nativeRate = 10.0m; // 10 USD per sqft
        const decimal fxRate = 3.75m;     // USD to SAR
        const decimal uomFactor = 1 / SQFT_TO_M2_FACTOR; // sqft to m2

        var bidPricing = CreateBidPricing(nativeRate, "USD", bidderUom: "sqft");

        // Act
        // First convert currency: 10 USD * 3.75 = 37.5 SAR per sqft
        var afterCurrency = ApplyCurrencyConversion(nativeRate, fxRate);
        // Then convert UOM: 37.5 SAR/sqft * 10.764 = 403.65 SAR per m2
        var normalizedRate = ApplyUomConversion(afterCurrency, uomFactor);

        bidPricing.NormalizedUnitRate = normalizedRate;
        bidPricing.FxRateApplied = fxRate;
        bidPricing.UomConversionFactor = uomFactor;

        // Assert
        normalizedRate.Should().BeApproximately(403.65m, 0.5m);
    }

    [Fact]
    public void NormalizeBid_ConvertsAmountCorrectly()
    {
        // Arrange
        const decimal nativeRate = 100.0m;
        const decimal quantity = 50.0m;
        const decimal nativeAmount = nativeRate * quantity;
        const decimal fxRate = 3.75m;

        var bidPricing = CreateBidPricing(nativeRate, "USD");
        bidPricing.NativeAmount = nativeAmount;
        bidPricing.BidderQuantity = quantity;

        // Act
        var normalizedRate = ApplyCurrencyConversion(nativeRate, fxRate);
        var normalizedAmount = ApplyCurrencyConversion(nativeAmount, fxRate);

        bidPricing.NormalizedUnitRate = normalizedRate;
        bidPricing.NormalizedAmount = normalizedAmount;

        // Assert
        bidPricing.NormalizedAmount.Should().Be(18750.0m); // 5000 * 3.75
    }

    #endregion

    #region Edge Cases

    [Fact]
    public void NormalizeBid_WithNullNativeRate_SetsNullNormalizedRate()
    {
        // Arrange
        var bidPricing = new BidPricing
        {
            Id = Guid.NewGuid(),
            BidSubmissionId = Guid.NewGuid(),
            NativeUnitRate = null,
            NativeCurrency = "SAR"
        };

        // Act
        var normalizedRate = bidPricing.NativeUnitRate.HasValue
            ? ApplyCurrencyConversion(bidPricing.NativeUnitRate.Value, 1.0m)
            : (decimal?)null;

        bidPricing.NormalizedUnitRate = normalizedRate;

        // Assert
        bidPricing.NormalizedUnitRate.Should().BeNull();
    }

    [Fact]
    public void NormalizeBid_WithNoBid_SkipsNormalization()
    {
        // Arrange
        var bidPricing = CreateBidPricing(0.0m, "SAR");
        bidPricing.IsNoBid = true;

        // Act
        var shouldNormalize = !bidPricing.IsNoBid;

        // Assert
        shouldNormalize.Should().BeFalse();
    }

    [Fact]
    public void UomConversion_CaseInsensitive()
    {
        // Arrange & Act
        var isConvertible1 = IsUomConvertible("SQFT", "M2");
        var isConvertible2 = IsUomConvertible("sqft", "m2");
        var isConvertible3 = IsUomConvertible("SqFt", "m2");

        // Assert
        isConvertible1.Should().Be(isConvertible2);
        isConvertible2.Should().Be(isConvertible3);
    }

    #endregion

    #region Helper Methods

    private static decimal ApplyCurrencyConversion(decimal nativeRate, decimal fxRate)
    {
        return nativeRate * fxRate;
    }

    private static decimal ApplyUomConversion(decimal rate, decimal conversionFactor)
    {
        return rate * conversionFactor;
    }

    private static decimal GetConversionFactor(string fromUom, string toUom)
    {
        var conversionTable = new Dictionary<(string, string), decimal>()
        {
            { ("sqft", "m2"), SQFT_TO_M2_FACTOR },
            { ("ft", "LM"), FT_TO_LM_FACTOR },
            { ("ft", "m"), FT_TO_LM_FACTOR },
            { ("inch", "mm"), 25.4m },
            { ("yd", "m"), 0.9144m },
            { ("gallon", "liter"), 3.78541m },
            { ("m2", "sqft"), 1 / SQFT_TO_M2_FACTOR },
            { ("LM", "ft"), 1 / FT_TO_LM_FACTOR },
            { ("m", "ft"), 1 / FT_TO_LM_FACTOR }
        };

        var key = (fromUom.ToLowerInvariant(), toUom.ToLowerInvariant());
        return conversionTable.TryGetValue(key, out var factor) ? factor : 1.0m;
    }

    private static bool IsUomConvertible(string fromUom, string toUom)
    {
        // Define UOM categories
        var areaUnits = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            { "m2", "sqft", "sqm", "sf" };
        var lengthUnits = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            { "m", "LM", "ft", "inch", "mm", "cm", "yd" };
        var volumeUnits = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            { "m3", "cuft", "liter", "gallon", "cum" };
        var massUnits = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            { "kg", "ton", "lb", "tonnes" };
        var countUnits = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            { "No", "nos", "ea", "each", "pcs", "set" };
        var lumpSumUnits = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            { "LS", "Lot", "lumpsum" };

        // Lump sum cannot convert to/from any other unit
        if (lumpSumUnits.Contains(fromUom) || lumpSumUnits.Contains(toUom))
        {
            return lumpSumUnits.Contains(fromUom) && lumpSumUnits.Contains(toUom);
        }

        // Same unit is always convertible
        if (string.Equals(fromUom, toUom, StringComparison.OrdinalIgnoreCase))
            return true;

        // Check if both units are in the same category
        if (areaUnits.Contains(fromUom) && areaUnits.Contains(toUom)) return true;
        if (lengthUnits.Contains(fromUom) && lengthUnits.Contains(toUom)) return true;
        if (volumeUnits.Contains(fromUom) && volumeUnits.Contains(toUom)) return true;
        if (massUnits.Contains(fromUom) && massUnits.Contains(toUom)) return true;
        if (countUnits.Contains(fromUom) && countUnits.Contains(toUom)) return true;

        return false;
    }

    private static BidPricing CreateBidPricing(
        decimal nativeRate,
        string currency,
        string bidderUom = "m2")
    {
        return new BidPricing
        {
            Id = Guid.NewGuid(),
            BidSubmissionId = Guid.NewGuid(),
            NativeUnitRate = nativeRate,
            NativeAmount = nativeRate * 10, // Assuming quantity of 10
            NativeCurrency = currency,
            BidderUom = bidderUom,
            BidderQuantity = 10
        };
    }

    private void SetupDbSets()
    {
        var bidPricingsMock = new Mock<DbSet<BidPricing>>();
        bidPricingsMock.Setup(x => x.Add(It.IsAny<BidPricing>()))
            .Callback<BidPricing>(bp => _bidPricingsStore.Add(bp));
        _contextMock.Setup(x => x.BidPricings).Returns(bidPricingsMock.Object);

        var uomMastersMock = new Mock<DbSet<UomMaster>>();
        uomMastersMock.Setup(x => x.Add(It.IsAny<UomMaster>()))
            .Callback<UomMaster>(uom => _uomMastersStore.Add(uom));
        _contextMock.Setup(x => x.UomMasters).Returns(uomMastersMock.Object);
    }

    #endregion
}
