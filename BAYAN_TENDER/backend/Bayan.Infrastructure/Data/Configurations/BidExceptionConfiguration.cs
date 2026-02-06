using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class BidExceptionConfiguration : IEntityTypeConfiguration<BidException>
{
    public void Configure(EntityTypeBuilder<BidException> builder)
    {
        builder.ToTable("bid_exceptions");

        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.TenderId)
            .HasColumnName("tender_id")
            .IsRequired();

        builder.Property(e => e.BidderId)
            .HasColumnName("bidder_id")
            .IsRequired();

        builder.Property(e => e.ExceptionType)
            .HasColumnName("exception_type")
            .HasMaxLength(50)
            .HasConversion<string>()
            .IsRequired();

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .IsRequired();

        builder.Property(e => e.CostImpact)
            .HasColumnName("cost_impact")
            .HasPrecision(18, 2);

        builder.Property(e => e.TimeImpactDays)
            .HasColumnName("time_impact_days");

        builder.Property(e => e.RiskLevel)
            .HasColumnName("risk_level")
            .HasMaxLength(10)
            .HasConversion<string>()
            .IsRequired();

        builder.Property(e => e.Mitigation)
            .HasColumnName("mitigation");

        builder.Property(e => e.LoggedBy)
            .HasColumnName("logged_by")
            .IsRequired();

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");

        // Relationships
        builder.HasOne(e => e.Tender)
            .WithMany(t => t.BidExceptions)
            .HasForeignKey(e => e.TenderId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.Bidder)
            .WithMany(b => b.BidExceptions)
            .HasForeignKey(e => e.BidderId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne(e => e.LoggedByUser)
            .WithMany(u => u.LoggedExceptions)
            .HasForeignKey(e => e.LoggedBy)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
