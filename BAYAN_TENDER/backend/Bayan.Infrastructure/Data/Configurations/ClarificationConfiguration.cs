using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class ClarificationConfiguration : IEntityTypeConfiguration<Clarification>
{
    public void Configure(EntityTypeBuilder<Clarification> builder)
    {
        builder.ToTable("clarifications");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => new { e.TenderId, e.ReferenceNumber }).IsUnique();
        builder.HasIndex(e => e.TenderId);
        builder.HasIndex(e => new { e.TenderId, e.Status });
        builder.HasIndex(e => e.SubmittedByBidderId);

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.TenderId)
            .HasColumnName("tender_id")
            .IsRequired();

        builder.Property(e => e.ReferenceNumber)
            .HasColumnName("reference_number")
            .HasMaxLength(50)
            .IsRequired();

        builder.Property(e => e.Subject)
            .HasColumnName("subject")
            .HasMaxLength(500)
            .IsRequired();

        builder.Property(e => e.Question)
            .HasColumnName("question")
            .IsRequired();

        builder.Property(e => e.SubmittedByBidderId)
            .HasColumnName("submitted_by_bidder_id");

        builder.Property(e => e.SubmittedByUserId)
            .HasColumnName("submitted_by_user_id");

        builder.Property(e => e.RelatedBoqSection)
            .HasColumnName("related_boq_section")
            .HasMaxLength(200);

        builder.Property(e => e.RelatedDocumentId)
            .HasColumnName("related_document_id");

        builder.Property(e => e.IsAnonymous)
            .HasColumnName("is_anonymous")
            .HasDefaultValue(false)
            .IsRequired();

        builder.Property(e => e.Priority)
            .HasColumnName("priority")
            .HasMaxLength(20)
            .HasConversion<string>()
            .HasDefaultValue("Normal");

        builder.Property(e => e.Answer)
            .HasColumnName("answer");

        builder.Property(e => e.AnsweredBy)
            .HasColumnName("answered_by");

        builder.Property(e => e.AnsweredAt)
            .HasColumnName("answered_at");

        builder.Property(e => e.ClarificationType)
            .HasColumnName("clarification_type")
            .HasMaxLength(50)
            .HasConversion<string>()
            .HasDefaultValue("BidderQuestion")
            .IsRequired();

        builder.Property(e => e.Status)
            .HasColumnName("status")
            .HasMaxLength(50)
            .HasConversion<string>()
            .HasDefaultValue("Submitted")
            .IsRequired();

        builder.Property(e => e.DuplicateOfId)
            .HasColumnName("duplicate_of_id");

        builder.Property(e => e.PublishedInBulletinId)
            .HasColumnName("published_in_bulletin_id");

        builder.Property(e => e.PublishedAt)
            .HasColumnName("published_at");

        builder.Property(e => e.SubmittedAt)
            .HasColumnName("submitted_at")
            .IsRequired();

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");

        // Relationships
        builder.HasOne(e => e.Tender)
            .WithMany(t => t.Clarifications)
            .HasForeignKey(e => e.TenderId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.SubmittedByBidder)
            .WithMany(b => b.Clarifications)
            .HasForeignKey(e => e.SubmittedByBidderId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne(e => e.SubmittedByUser)
            .WithMany(u => u.SubmittedClarifications)
            .HasForeignKey(e => e.SubmittedByUserId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne(e => e.RelatedDocument)
            .WithMany(d => d.ReferencingClarifications)
            .HasForeignKey(e => e.RelatedDocumentId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne(e => e.Answerer)
            .WithMany(u => u.AnsweredClarifications)
            .HasForeignKey(e => e.AnsweredBy)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property(e => e.AssignedToId)
            .HasColumnName("assigned_to_id");

        builder.HasOne(e => e.AssignedTo)
            .WithMany(u => u.AssignedClarifications)
            .HasForeignKey(e => e.AssignedToId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne(e => e.DuplicateOf)
            .WithMany(c => c.Duplicates)
            .HasForeignKey(e => e.DuplicateOfId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne(e => e.PublishedInBulletin)
            .WithMany(cb => cb.Clarifications)
            .HasForeignKey(e => e.PublishedInBulletinId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
