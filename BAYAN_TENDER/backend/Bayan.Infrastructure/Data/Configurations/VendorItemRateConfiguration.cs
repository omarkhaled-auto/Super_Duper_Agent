using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class VendorItemRateConfiguration : IEntityTypeConfiguration<VendorItemRate>
{
    public void Configure(EntityTypeBuilder<VendorItemRate> builder)
    {
        builder.ToTable("vendor_item_rates");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => e.SnapshotId);

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.SnapshotId)
            .HasColumnName("snapshot_id")
            .IsRequired();

        builder.Property(e => e.BoqItemId)
            .HasColumnName("boq_item_id");

        builder.Property(e => e.ItemDescription)
            .HasColumnName("item_description")
            .IsRequired();

        builder.Property(e => e.Uom)
            .HasColumnName("uom")
            .HasMaxLength(50)
            .IsRequired();

        builder.Property(e => e.NormalizedUnitRate)
            .HasColumnName("normalized_unit_rate")
            .HasPrecision(18, 4)
            .IsRequired();

        builder.Property(e => e.NormalizedCurrency)
            .HasColumnName("normalized_currency")
            .HasMaxLength(3)
            .IsRequired();

        builder.Property(e => e.Quantity)
            .HasColumnName("quantity")
            .HasPrecision(18, 4);

        builder.Property(e => e.TotalAmount)
            .HasColumnName("total_amount")
            .HasPrecision(18, 2);

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Ignore(e => e.UpdatedAt);

        // Relationships
        builder.HasOne(e => e.Snapshot)
            .WithMany(s => s.ItemRates)
            .HasForeignKey(e => e.SnapshotId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.BoqItem)
            .WithMany(bi => bi.VendorItemRates)
            .HasForeignKey(e => e.BoqItemId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
