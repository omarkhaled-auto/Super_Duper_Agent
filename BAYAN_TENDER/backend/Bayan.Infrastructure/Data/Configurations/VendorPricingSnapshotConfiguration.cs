using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class VendorPricingSnapshotConfiguration : IEntityTypeConfiguration<VendorPricingSnapshot>
{
    public void Configure(EntityTypeBuilder<VendorPricingSnapshot> builder)
    {
        builder.ToTable("vendor_pricing_snapshots");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => e.BidderId);
        builder.HasIndex(e => e.TenderId);

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.BidderId)
            .HasColumnName("bidder_id")
            .IsRequired();

        builder.Property(e => e.TenderId)
            .HasColumnName("tender_id")
            .IsRequired();

        builder.Property(e => e.BidSubmissionId)
            .HasColumnName("bid_submission_id")
            .IsRequired();

        builder.Property(e => e.SnapshotDate)
            .HasColumnName("snapshot_date")
            .IsRequired();

        builder.Property(e => e.TenderBaseCurrency)
            .HasColumnName("tender_base_currency")
            .HasMaxLength(3)
            .IsRequired();

        builder.Property(e => e.TotalBidAmount)
            .HasColumnName("total_bid_amount")
            .HasPrecision(18, 2)
            .IsRequired();

        builder.Property(e => e.TotalItemsCount)
            .HasColumnName("total_items_count")
            .IsRequired();

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Ignore(e => e.UpdatedAt);

        // Relationships
        builder.HasOne(e => e.Bidder)
            .WithMany(b => b.VendorPricingSnapshots)
            .HasForeignKey(e => e.BidderId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne(e => e.Tender)
            .WithMany(t => t.VendorPricingSnapshots)
            .HasForeignKey(e => e.TenderId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne(e => e.BidSubmission)
            .WithOne(bs => bs.VendorPricingSnapshot)
            .HasForeignKey<VendorPricingSnapshot>(e => e.BidSubmissionId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
