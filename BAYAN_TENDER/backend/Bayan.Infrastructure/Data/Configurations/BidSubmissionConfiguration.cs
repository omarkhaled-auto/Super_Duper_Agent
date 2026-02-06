using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class BidSubmissionConfiguration : IEntityTypeConfiguration<BidSubmission>
{
    public void Configure(EntityTypeBuilder<BidSubmission> builder)
    {
        builder.ToTable("bid_submissions");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => new { e.TenderId, e.BidderId }).IsUnique();
        builder.HasIndex(e => e.TenderId);
        builder.HasIndex(e => e.BidderId);
        builder.HasIndex(e => e.ReceiptNumber).IsUnique();

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.TenderId)
            .HasColumnName("tender_id")
            .IsRequired();

        builder.Property(e => e.BidderId)
            .HasColumnName("bidder_id")
            .IsRequired();

        builder.Property(e => e.SubmissionTime)
            .HasColumnName("submission_time")
            .IsRequired();

        builder.Property(e => e.IsLate)
            .HasColumnName("is_late")
            .HasDefaultValue(false)
            .IsRequired();

        builder.Property(e => e.LateAccepted)
            .HasColumnName("late_accepted");

        builder.Property(e => e.LateAcceptedBy)
            .HasColumnName("late_accepted_by");

        builder.Property(e => e.OriginalFileName)
            .HasColumnName("original_file_name")
            .HasMaxLength(500);

        builder.Property(e => e.OriginalFilePath)
            .HasColumnName("original_file_path")
            .HasMaxLength(1000);

        builder.Property(e => e.NativeCurrency)
            .HasColumnName("native_currency")
            .HasMaxLength(3)
            .HasDefaultValue("AED")
            .IsRequired();

        builder.Property(e => e.NativeTotalAmount)
            .HasColumnName("native_total_amount")
            .HasPrecision(18, 2);

        builder.Property(e => e.FxRate)
            .HasColumnName("fx_rate")
            .HasPrecision(10, 6)
            .HasDefaultValue(1.0m);

        builder.Property(e => e.NormalizedTotalAmount)
            .HasColumnName("normalized_total_amount")
            .HasPrecision(18, 2);

        builder.Property(e => e.BidValidityDays)
            .HasColumnName("bid_validity_days")
            .HasDefaultValue(90);

        builder.Property(e => e.ImportStatus)
            .HasColumnName("import_status")
            .HasMaxLength(50)
            .HasConversion<string>()
            .HasDefaultValue("Uploaded")
            .IsRequired();

        builder.Property(e => e.ImportStartedAt)
            .HasColumnName("import_started_at");

        builder.Property(e => e.ImportCompletedAt)
            .HasColumnName("import_completed_at");

        builder.Property(e => e.ImportedBy)
            .HasColumnName("imported_by");

        builder.Property(e => e.ValidationSummary)
            .HasColumnName("validation_summary")
            .HasColumnType("jsonb");

        builder.Property(e => e.ReceiptNumber)
            .HasColumnName("receipt_number")
            .HasMaxLength(100)
            .IsRequired();

        builder.Property(e => e.ReceiptPdfPath)
            .HasColumnName("receipt_pdf_path")
            .HasMaxLength(1000);

        builder.Property(e => e.Status)
            .HasColumnName("status")
            .HasMaxLength(50)
            .HasConversion<string>()
            .HasDefaultValue("Submitted")
            .IsRequired();

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");

        // Relationships
        builder.HasOne(e => e.Tender)
            .WithMany(t => t.BidSubmissions)
            .HasForeignKey(e => e.TenderId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.Bidder)
            .WithMany(b => b.BidSubmissions)
            .HasForeignKey(e => e.BidderId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne(e => e.LateAcceptedByUser)
            .WithMany()
            .HasForeignKey(e => e.LateAcceptedBy)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne(e => e.Importer)
            .WithMany()
            .HasForeignKey(e => e.ImportedBy)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
