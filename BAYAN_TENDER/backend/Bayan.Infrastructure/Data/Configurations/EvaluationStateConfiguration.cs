using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class EvaluationStateConfiguration : IEntityTypeConfiguration<EvaluationState>
{
    public void Configure(EntityTypeBuilder<EvaluationState> builder)
    {
        builder.ToTable("evaluation_state");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => e.TenderId).IsUnique();

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.TenderId)
            .HasColumnName("tender_id")
            .IsRequired();

        builder.Property(e => e.ScoringMethod)
            .HasColumnName("scoring_method")
            .HasMaxLength(20)
            .HasConversion<string>()
            .HasDefaultValueSql("'Numeric'")
            .IsRequired();

        builder.Property(e => e.BlindMode)
            .HasColumnName("blind_mode")
            .HasDefaultValue(true)
            .IsRequired();

        builder.Property(e => e.TechnicalEvaluationDeadline)
            .HasColumnName("technical_evaluation_deadline");

        builder.Property(e => e.TechnicalScoresLocked)
            .HasColumnName("technical_scores_locked")
            .HasDefaultValue(false)
            .IsRequired();

        builder.Property(e => e.TechnicalLockedAt)
            .HasColumnName("technical_locked_at");

        builder.Property(e => e.TechnicalLockedBy)
            .HasColumnName("technical_locked_by");

        builder.Property(e => e.CommercialScoresCalculated)
            .HasColumnName("commercial_scores_calculated")
            .HasDefaultValue(false)
            .IsRequired();

        builder.Property(e => e.CombinedScoresCalculated)
            .HasColumnName("combined_scores_calculated")
            .HasDefaultValue(false)
            .IsRequired();

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");

        // Relationships
        builder.HasOne(e => e.Tender)
            .WithOne(t => t.EvaluationState)
            .HasForeignKey<EvaluationState>(e => e.TenderId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.LockedByUser)
            .WithMany()
            .HasForeignKey(e => e.TechnicalLockedBy)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
