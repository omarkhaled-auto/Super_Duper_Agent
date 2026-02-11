using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class ClarificationAttachmentConfiguration : IEntityTypeConfiguration<ClarificationAttachment>
{
    public void Configure(EntityTypeBuilder<ClarificationAttachment> builder)
    {
        builder.ToTable("clarification_attachments");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => e.ClarificationId);

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.ClarificationId)
            .HasColumnName("clarification_id")
            .IsRequired();

        builder.Property(e => e.FileName)
            .HasColumnName("file_name")
            .HasMaxLength(500)
            .IsRequired();

        builder.Property(e => e.FilePath)
            .HasColumnName("file_path")
            .HasMaxLength(1000)
            .IsRequired();

        builder.Property(e => e.FileSizeBytes)
            .HasColumnName("file_size_bytes")
            .IsRequired();

        builder.Property(e => e.ContentType)
            .HasColumnName("content_type")
            .HasMaxLength(200)
            .IsRequired();

        builder.Property(e => e.UploadedByUserId)
            .HasColumnName("uploaded_by_user_id");

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");

        // Relationships
        builder.HasOne(e => e.Clarification)
            .WithMany(c => c.Attachments)
            .HasForeignKey(e => e.ClarificationId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.UploadedByUser)
            .WithMany()
            .HasForeignKey(e => e.UploadedByUserId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
