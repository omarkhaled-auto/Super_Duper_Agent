namespace Bayan.Application.Features.VendorPricing.DTOs;

/// <summary>
/// Data transfer object for comparing multiple vendors side-by-side.
/// </summary>
public class VendorComparisonDto
{
    /// <summary>
    /// List of vendors being compared.
    /// </summary>
    public List<VendorComparisonVendorDto> Vendors { get; set; } = new();

    /// <summary>
    /// Items being compared with rates from each vendor.
    /// </summary>
    public List<VendorComparisonItemDto> Items { get; set; } = new();

    /// <summary>
    /// Summary statistics.
    /// </summary>
    public VendorComparisonSummaryDto Summary { get; set; } = new();
}

/// <summary>
/// Vendor information for comparison.
/// </summary>
public class VendorComparisonVendorDto
{
    /// <summary>
    /// Bidder identifier.
    /// </summary>
    public Guid BidderId { get; set; }

    /// <summary>
    /// Bidder company name.
    /// </summary>
    public string CompanyName { get; set; } = string.Empty;

    /// <summary>
    /// Number of items with pricing data.
    /// </summary>
    public int ItemsWithPricing { get; set; }

    /// <summary>
    /// Total amount across all compared items.
    /// </summary>
    public decimal TotalAmount { get; set; }

    /// <summary>
    /// Rank based on total amount (1 = lowest).
    /// </summary>
    public int Rank { get; set; }
}

/// <summary>
/// Item comparison with rates from multiple vendors.
/// </summary>
public class VendorComparisonItemDto
{
    /// <summary>
    /// Item description.
    /// </summary>
    public string ItemDescription { get; set; } = string.Empty;

    /// <summary>
    /// Unit of measurement.
    /// </summary>
    public string Uom { get; set; } = string.Empty;

    /// <summary>
    /// Rates from each vendor (keyed by bidder ID).
    /// </summary>
    public Dictionary<Guid, VendorComparisonRateDto> VendorRates { get; set; } = new();

    /// <summary>
    /// Average rate across all vendors.
    /// </summary>
    public decimal AverageRate { get; set; }

    /// <summary>
    /// Minimum rate (best price).
    /// </summary>
    public decimal MinRate { get; set; }

    /// <summary>
    /// Maximum rate.
    /// </summary>
    public decimal MaxRate { get; set; }

    /// <summary>
    /// Bidder ID with the lowest rate.
    /// </summary>
    public Guid? LowestBidderId { get; set; }
}

/// <summary>
/// Rate information for a specific vendor in a comparison.
/// </summary>
public class VendorComparisonRateDto
{
    /// <summary>
    /// Unit rate.
    /// </summary>
    public decimal Rate { get; set; }

    /// <summary>
    /// Deviation from average (as percentage).
    /// </summary>
    public decimal DeviationFromAverage { get; set; }

    /// <summary>
    /// Whether this is the lowest rate.
    /// </summary>
    public bool IsLowest { get; set; }

    /// <summary>
    /// Date when this rate was captured.
    /// </summary>
    public DateTime SnapshotDate { get; set; }

    /// <summary>
    /// Tender reference this rate came from.
    /// </summary>
    public string TenderReference { get; set; } = string.Empty;
}

/// <summary>
/// Summary statistics for vendor comparison.
/// </summary>
public class VendorComparisonSummaryDto
{
    /// <summary>
    /// Total number of items compared.
    /// </summary>
    public int TotalItemsCompared { get; set; }

    /// <summary>
    /// Number of items where all vendors have pricing.
    /// </summary>
    public int ItemsWithAllVendorPricing { get; set; }

    /// <summary>
    /// Bidder ID with the lowest overall total.
    /// </summary>
    public Guid? OverallLowestBidderId { get; set; }

    /// <summary>
    /// Company name of the lowest bidder.
    /// </summary>
    public string? OverallLowestBidderName { get; set; }

    /// <summary>
    /// Potential savings compared to highest bidder.
    /// </summary>
    public decimal PotentialSavings { get; set; }
}
