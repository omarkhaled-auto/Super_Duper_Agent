using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class BoqItemConfiguration : IEntityTypeConfiguration<BoqItem>
{
    public void Configure(EntityTypeBuilder<BoqItem> builder)
    {
        builder.ToTable("boq_items");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => new { e.TenderId, e.ItemNumber }).IsUnique();
        builder.HasIndex(e => e.TenderId);
        builder.HasIndex(e => e.SectionId);
        builder.HasIndex(e => e.ParentItemId);

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.TenderId)
            .HasColumnName("tender_id")
            .IsRequired();

        builder.Property(e => e.SectionId)
            .HasColumnName("section_id")
            .IsRequired();

        builder.Property(e => e.ItemNumber)
            .HasColumnName("item_number")
            .HasMaxLength(50)
            .IsRequired();

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(2000)
            .IsRequired();

        builder.Property(e => e.Quantity)
            .HasColumnName("quantity")
            .HasPrecision(18, 4)
            .IsRequired();

        builder.Property(e => e.Uom)
            .HasColumnName("uom")
            .HasMaxLength(50)
            .IsRequired();

        builder.Property(e => e.ItemType)
            .HasColumnName("item_type")
            .HasMaxLength(50)
            .HasConversion<string>()
            .HasDefaultValueSql("'Base'")
            .IsRequired();

        builder.Property(e => e.Notes)
            .HasColumnName("notes");

        builder.Property(e => e.SortOrder)
            .HasColumnName("sort_order")
            .HasDefaultValue(0)
            .IsRequired();

        builder.Property(e => e.ParentItemId)
            .HasColumnName("parent_item_id");

        builder.Property(e => e.IsGroup)
            .HasColumnName("is_group")
            .HasDefaultValue(false)
            .IsRequired();

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");

        // Relationships
        builder.HasOne(e => e.Tender)
            .WithMany(t => t.BoqItems)
            .HasForeignKey(e => e.TenderId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.Section)
            .WithMany(s => s.Items)
            .HasForeignKey(e => e.SectionId)
            .OnDelete(DeleteBehavior.Cascade);

        // Self-referencing hierarchy: group items → child sub-items
        builder.HasOne(e => e.ParentItem)
            .WithMany(e => e.ChildItems)
            .HasForeignKey(e => e.ParentItemId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
