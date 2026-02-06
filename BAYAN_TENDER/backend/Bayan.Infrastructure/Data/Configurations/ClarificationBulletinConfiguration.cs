using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class ClarificationBulletinConfiguration : IEntityTypeConfiguration<ClarificationBulletin>
{
    public void Configure(EntityTypeBuilder<ClarificationBulletin> builder)
    {
        builder.ToTable("clarification_bulletins");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => new { e.TenderId, e.BulletinNumber }).IsUnique();

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.TenderId)
            .HasColumnName("tender_id")
            .IsRequired();

        builder.Property(e => e.BulletinNumber)
            .HasColumnName("bulletin_number")
            .IsRequired();

        builder.Property(e => e.IssueDate)
            .HasColumnName("issue_date")
            .IsRequired();

        builder.Property(e => e.Introduction)
            .HasColumnName("introduction");

        builder.Property(e => e.ClosingNotes)
            .HasColumnName("closing_notes");

        builder.Property(e => e.PdfPath)
            .HasColumnName("pdf_path")
            .HasMaxLength(1000);

        builder.Property(e => e.PublishedBy)
            .HasColumnName("published_by")
            .IsRequired();

        builder.Property(e => e.PublishedAt)
            .HasColumnName("published_at")
            .IsRequired();

        builder.Ignore(e => e.CreatedAt);
        builder.Ignore(e => e.UpdatedAt);

        // Relationships
        builder.HasOne(e => e.Tender)
            .WithMany(t => t.ClarificationBulletins)
            .HasForeignKey(e => e.TenderId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.Publisher)
            .WithMany(u => u.PublishedBulletins)
            .HasForeignKey(e => e.PublishedBy)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
