using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class AddendumAcknowledgmentConfiguration : IEntityTypeConfiguration<AddendumAcknowledgment>
{
    public void Configure(EntityTypeBuilder<AddendumAcknowledgment> builder)
    {
        builder.ToTable("addendum_acknowledgments");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => new { e.AddendumId, e.BidderId }).IsUnique();

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.AddendumId)
            .HasColumnName("addendum_id")
            .IsRequired();

        builder.Property(e => e.BidderId)
            .HasColumnName("bidder_id")
            .IsRequired();

        builder.Property(e => e.EmailSentAt)
            .HasColumnName("email_sent_at");

        builder.Property(e => e.EmailOpenedAt)
            .HasColumnName("email_opened_at");

        builder.Property(e => e.AcknowledgedAt)
            .HasColumnName("acknowledged_at");

        builder.Ignore(e => e.CreatedAt);
        builder.Ignore(e => e.UpdatedAt);

        // Relationships
        builder.HasOne(e => e.Addendum)
            .WithMany(a => a.Acknowledgments)
            .HasForeignKey(e => e.AddendumId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.Bidder)
            .WithMany(b => b.AddendumAcknowledgments)
            .HasForeignKey(e => e.BidderId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
