using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class CommercialScoreConfiguration : IEntityTypeConfiguration<CommercialScore>
{
    public void Configure(EntityTypeBuilder<CommercialScore> builder)
    {
        builder.ToTable("commercial_scores");

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

        builder.Property(e => e.NormalizedTotalPrice)
            .HasColumnName("normalized_total_price")
            .HasPrecision(18, 2)
            .IsRequired();

        builder.Property(e => e.CommercialScoreValue)
            .HasColumnName("commercial_score")
            .HasPrecision(6, 2)
            .IsRequired();

        builder.Property(e => e.Rank)
            .HasColumnName("rank")
            .IsRequired();

        builder.Property(e => e.IncludeProvisionalSums)
            .HasColumnName("include_provisional_sums")
            .HasDefaultValue(false)
            .IsRequired();

        builder.Property(e => e.IncludeAlternates)
            .HasColumnName("include_alternates")
            .HasDefaultValue(false)
            .IsRequired();

        builder.Property(e => e.CalculatedAt)
            .HasColumnName("calculated_at")
            .IsRequired();

        builder.Ignore(e => e.CreatedAt);
        builder.Ignore(e => e.UpdatedAt);

        // Relationships
        builder.HasOne(e => e.Tender)
            .WithMany(t => t.CommercialScores)
            .HasForeignKey(e => e.TenderId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.Bidder)
            .WithMany(b => b.CommercialScores)
            .HasForeignKey(e => e.BidderId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
