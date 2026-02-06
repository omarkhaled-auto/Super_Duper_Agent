using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class TechnicalScoreConfiguration : IEntityTypeConfiguration<TechnicalScore>
{
    public void Configure(EntityTypeBuilder<TechnicalScore> builder)
    {
        builder.ToTable("technical_scores");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => new { e.TenderId, e.BidderId, e.PanelistUserId, e.CriterionId }).IsUnique();
        builder.HasIndex(e => e.TenderId);
        builder.HasIndex(e => new { e.TenderId, e.BidderId });

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.TenderId)
            .HasColumnName("tender_id")
            .IsRequired();

        builder.Property(e => e.BidderId)
            .HasColumnName("bidder_id")
            .IsRequired();

        builder.Property(e => e.PanelistUserId)
            .HasColumnName("panelist_user_id")
            .IsRequired();

        builder.Property(e => e.CriterionId)
            .HasColumnName("criterion_id")
            .IsRequired();

        builder.Property(e => e.Score)
            .HasColumnName("score")
            .HasPrecision(4, 1)
            .IsRequired();

        builder.Property(e => e.Comment)
            .HasColumnName("comment");

        builder.Property(e => e.IsDraft)
            .HasColumnName("is_draft")
            .HasDefaultValue(true)
            .IsRequired();

        builder.Property(e => e.SubmittedAt)
            .HasColumnName("submitted_at");

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");

        // Relationships
        builder.HasOne(e => e.Tender)
            .WithMany(t => t.TechnicalScores)
            .HasForeignKey(e => e.TenderId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.Bidder)
            .WithMany(b => b.TechnicalScores)
            .HasForeignKey(e => e.BidderId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne(e => e.Panelist)
            .WithMany(u => u.TechnicalScores)
            .HasForeignKey(e => e.PanelistUserId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne(e => e.Criterion)
            .WithMany(ec => ec.TechnicalScores)
            .HasForeignKey(e => e.CriterionId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
