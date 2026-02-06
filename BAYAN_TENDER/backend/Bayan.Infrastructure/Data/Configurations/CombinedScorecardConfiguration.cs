using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class CombinedScorecardConfiguration : IEntityTypeConfiguration<CombinedScorecard>
{
    public void Configure(EntityTypeBuilder<CombinedScorecard> builder)
    {
        builder.ToTable("combined_scorecards");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => new { e.TenderId, e.BidderId }).IsUnique();

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.TenderId)
            .HasColumnName("tender_id")
            .IsRequired();

        builder.Property(e => e.BidderId)
            .HasColumnName("bidder_id")
            .IsRequired();

        builder.Property(e => e.TechnicalScoreAvg)
            .HasColumnName("technical_score_avg")
            .HasPrecision(6, 2)
            .IsRequired();

        builder.Property(e => e.TechnicalRank)
            .HasColumnName("technical_rank")
            .IsRequired();

        builder.Property(e => e.CommercialScoreValue)
            .HasColumnName("commercial_score")
            .HasPrecision(6, 2)
            .IsRequired();

        builder.Property(e => e.CommercialRank)
            .HasColumnName("commercial_rank")
            .IsRequired();

        builder.Property(e => e.TechnicalWeight)
            .HasColumnName("technical_weight")
            .IsRequired();

        builder.Property(e => e.CommercialWeight)
            .HasColumnName("commercial_weight")
            .IsRequired();

        builder.Property(e => e.CombinedScore)
            .HasColumnName("combined_score")
            .HasPrecision(6, 2)
            .IsRequired();

        builder.Property(e => e.FinalRank)
            .HasColumnName("final_rank")
            .IsRequired();

        builder.Property(e => e.IsRecommended)
            .HasColumnName("is_recommended")
            .HasDefaultValue(false)
            .IsRequired();

        builder.Property(e => e.CalculatedAt)
            .HasColumnName("calculated_at")
            .IsRequired();

        builder.Ignore(e => e.CreatedAt);
        builder.Ignore(e => e.UpdatedAt);

        // Relationships
        builder.HasOne(e => e.Tender)
            .WithMany(t => t.CombinedScorecards)
            .HasForeignKey(e => e.TenderId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.Bidder)
            .WithMany(b => b.CombinedScorecards)
            .HasForeignKey(e => e.BidderId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
