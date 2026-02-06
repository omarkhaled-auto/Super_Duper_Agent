using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class EvaluationCriteriaConfiguration : IEntityTypeConfiguration<EvaluationCriteria>
{
    public void Configure(EntityTypeBuilder<EvaluationCriteria> builder)
    {
        builder.ToTable("evaluation_criteria");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => e.TenderId);

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.TenderId)
            .HasColumnName("tender_id")
            .IsRequired();

        builder.Property(e => e.Name)
            .HasColumnName("name")
            .HasMaxLength(200)
            .IsRequired();

        builder.Property(e => e.WeightPercentage)
            .HasColumnName("weight_percentage")
            .HasPrecision(5, 2)
            .IsRequired();

        builder.Property(e => e.GuidanceNotes)
            .HasColumnName("guidance_notes");

        builder.Property(e => e.SortOrder)
            .HasColumnName("sort_order")
            .HasDefaultValue(0);

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Ignore(e => e.UpdatedAt);

        // Relationships
        builder.HasOne(e => e.Tender)
            .WithMany(t => t.EvaluationCriteria)
            .HasForeignKey(e => e.TenderId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
