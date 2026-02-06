using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class DocumentConfiguration : IEntityTypeConfiguration<Document>
{
    public void Configure(EntityTypeBuilder<Document> builder)
    {
        builder.ToTable("documents");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => e.TenderId);
        builder.HasIndex(e => new { e.TenderId, e.FolderPath });

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.TenderId)
            .HasColumnName("tender_id")
            .IsRequired();

        builder.Property(e => e.FolderPath)
            .HasColumnName("folder_path")
            .HasMaxLength(500)
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

        builder.Property(e => e.Version)
            .HasColumnName("version")
            .HasDefaultValue(1)
            .IsRequired();

        builder.Property(e => e.IsLatest)
            .HasColumnName("is_latest")
            .HasDefaultValue(true)
            .IsRequired();

        builder.Property(e => e.UploadedBy)
            .HasColumnName("uploaded_by")
            .IsRequired();

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Ignore(e => e.UpdatedAt);

        // Relationships
        builder.HasOne(e => e.Tender)
            .WithMany(t => t.Documents)
            .HasForeignKey(e => e.TenderId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.Uploader)
            .WithMany(u => u.UploadedDocuments)
            .HasForeignKey(e => e.UploadedBy)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
