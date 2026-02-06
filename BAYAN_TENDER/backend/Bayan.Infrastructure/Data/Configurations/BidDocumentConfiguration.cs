using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class BidDocumentConfiguration : IEntityTypeConfiguration<BidDocument>
{
    public void Configure(EntityTypeBuilder<BidDocument> builder)
    {
        builder.ToTable("bid_documents");

        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.BidSubmissionId)
            .HasColumnName("bid_submission_id")
            .IsRequired();

        builder.Property(e => e.DocumentType)
            .HasColumnName("document_type")
            .HasMaxLength(50)
            .HasConversion<string>()
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

        builder.Property(e => e.UploadedAt)
            .HasColumnName("uploaded_at")
            .IsRequired();

        builder.Ignore(e => e.CreatedAt);
        builder.Ignore(e => e.UpdatedAt);

        // Relationships
        builder.HasOne(e => e.BidSubmission)
            .WithMany(bs => bs.BidDocuments)
            .HasForeignKey(e => e.BidSubmissionId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
