using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class TenderBidderConfiguration : IEntityTypeConfiguration<TenderBidder>
{
    public void Configure(EntityTypeBuilder<TenderBidder> builder)
    {
        builder.ToTable("tender_bidders");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => new { e.TenderId, e.BidderId }).IsUnique();
        builder.HasIndex(e => e.TenderId);
        builder.HasIndex(e => e.BidderId);

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.TenderId)
            .HasColumnName("tender_id")
            .IsRequired();

        builder.Property(e => e.BidderId)
            .HasColumnName("bidder_id")
            .IsRequired();

        builder.Property(e => e.InvitationSentAt)
            .HasColumnName("invitation_sent_at");

        builder.Property(e => e.InvitationOpenedAt)
            .HasColumnName("invitation_opened_at");

        builder.Property(e => e.RegisteredAt)
            .HasColumnName("registered_at");

        builder.Property(e => e.NdaStatus)
            .HasColumnName("nda_status")
            .HasMaxLength(50)
            .HasConversion<string>()
            .HasDefaultValueSql("'Pending'");

        builder.Property(e => e.NdaDocumentPath)
            .HasColumnName("nda_document_path")
            .HasMaxLength(1000);

        builder.Property(e => e.NdaSignedDate)
            .HasColumnName("nda_signed_date");

        builder.Property(e => e.NdaExpiryDate)
            .HasColumnName("nda_expiry_date");

        builder.Property(e => e.QualificationStatus)
            .HasColumnName("qualification_status")
            .HasMaxLength(50)
            .HasConversion<string>()
            .HasDefaultValueSql("'Pending'");

        builder.Property(e => e.QualifiedAt)
            .HasColumnName("qualified_at");

        builder.Property(e => e.QualificationReason)
            .HasColumnName("qualification_reason")
            .HasMaxLength(1000);

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");

        // Relationships
        builder.HasOne(e => e.Tender)
            .WithMany(t => t.TenderBidders)
            .HasForeignKey(e => e.TenderId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.Bidder)
            .WithMany(b => b.TenderBidders)
            .HasForeignKey(e => e.BidderId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
