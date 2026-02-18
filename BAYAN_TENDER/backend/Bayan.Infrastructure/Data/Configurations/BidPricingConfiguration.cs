using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class BidPricingConfiguration : IEntityTypeConfiguration<BidPricing>
{
    public void Configure(EntityTypeBuilder<BidPricing> builder)
    {
        builder.ToTable("bid_pricing");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => e.BidSubmissionId);
        builder.HasIndex(e => e.BoqItemId);
        builder.HasIndex(e => e.BoqSectionId);
        builder.HasIndex(e => new { e.BidSubmissionId, e.IsOutlier });

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.BidSubmissionId)
            .HasColumnName("bid_submission_id")
            .IsRequired();

        builder.Property(e => e.BoqItemId)
            .HasColumnName("boq_item_id");

        builder.Property(e => e.BidderItemNumber)
            .HasColumnName("bidder_item_number")
            .HasMaxLength(50);

        builder.Property(e => e.BidderDescription)
            .HasColumnName("bidder_description")
            .HasMaxLength(2000);

        builder.Property(e => e.BidderQuantity)
            .HasColumnName("bidder_quantity")
            .HasPrecision(18, 4);

        builder.Property(e => e.BidderUom)
            .HasColumnName("bidder_uom")
            .HasMaxLength(50);

        builder.Property(e => e.NativeUnitRate)
            .HasColumnName("native_unit_rate")
            .HasPrecision(18, 4);

        builder.Property(e => e.NativeAmount)
            .HasColumnName("native_amount")
            .HasPrecision(18, 2);

        builder.Property(e => e.NativeCurrency)
            .HasColumnName("native_currency")
            .HasMaxLength(3)
            .IsRequired();

        builder.Property(e => e.NormalizedUnitRate)
            .HasColumnName("normalized_unit_rate")
            .HasPrecision(18, 4);

        builder.Property(e => e.NormalizedAmount)
            .HasColumnName("normalized_amount")
            .HasPrecision(18, 2);

        builder.Property(e => e.FxRateApplied)
            .HasColumnName("fx_rate_applied")
            .HasPrecision(10, 6);

        builder.Property(e => e.UomConversionFactor)
            .HasColumnName("uom_conversion_factor")
            .HasPrecision(18, 10);

        builder.Property(e => e.MatchType)
            .HasColumnName("match_type")
            .HasMaxLength(50)
            .HasConversion<string>();

        builder.Property(e => e.MatchConfidence)
            .HasColumnName("match_confidence")
            .HasPrecision(5, 2);

        builder.Property(e => e.IsIncludedInTotal)
            .HasColumnName("is_included_in_total")
            .HasDefaultValue(true)
            .IsRequired();

        builder.Property(e => e.IsOutlier)
            .HasColumnName("is_outlier")
            .HasDefaultValue(false)
            .IsRequired();

        builder.Property(e => e.OutlierSeverity)
            .HasColumnName("outlier_severity")
            .HasMaxLength(20)
            .HasConversion<string>();

        builder.Property(e => e.DeviationFromAverage)
            .HasColumnName("deviation_from_average")
            .HasPrecision(10, 4);

        builder.Property(e => e.HasFormulaError)
            .HasColumnName("has_formula_error")
            .HasDefaultValue(false)
            .IsRequired();

        builder.Property(e => e.IsNoBid)
            .HasColumnName("is_no_bid")
            .HasDefaultValue(false)
            .IsRequired();

        builder.Property(e => e.IsNonComparable)
            .HasColumnName("is_non_comparable")
            .HasDefaultValue(false)
            .IsRequired();

        builder.Property(e => e.Notes)
            .HasColumnName("notes");

        builder.Property(e => e.BoqSectionId)
            .HasColumnName("boq_section_id");

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");

        // Relationships
        builder.HasOne(e => e.BidSubmission)
            .WithMany(bs => bs.BidPricings)
            .HasForeignKey(e => e.BidSubmissionId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.BoqItem)
            .WithMany(bi => bi.BidPricings)
            .HasForeignKey(e => e.BoqItemId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne(e => e.BoqSection)
            .WithMany(bs => bs.BidPricings)
            .HasForeignKey(e => e.BoqSectionId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
