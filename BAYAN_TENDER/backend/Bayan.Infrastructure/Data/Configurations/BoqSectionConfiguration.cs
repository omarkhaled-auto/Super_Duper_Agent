using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class BoqSectionConfiguration : IEntityTypeConfiguration<BoqSection>
{
    public void Configure(EntityTypeBuilder<BoqSection> builder)
    {
        builder.ToTable("boq_sections");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => e.TenderId);
        builder.HasIndex(e => e.ParentSectionId);

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.TenderId)
            .HasColumnName("tender_id")
            .IsRequired();

        builder.Property(e => e.ParentSectionId)
            .HasColumnName("parent_section_id");

        builder.Property(e => e.SectionNumber)
            .HasColumnName("section_number")
            .HasMaxLength(50)
            .IsRequired();

        builder.Property(e => e.Title)
            .HasColumnName("title")
            .HasMaxLength(500)
            .IsRequired();

        builder.Property(e => e.SortOrder)
            .HasColumnName("sort_order")
            .HasDefaultValue(0)
            .IsRequired();

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");

        // Relationships
        builder.HasOne(e => e.Tender)
            .WithMany(t => t.BoqSections)
            .HasForeignKey(e => e.TenderId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.ParentSection)
            .WithMany(s => s.ChildSections)
            .HasForeignKey(e => e.ParentSectionId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
