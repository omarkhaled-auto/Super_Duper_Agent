using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class EmailLogConfiguration : IEntityTypeConfiguration<EmailLog>
{
    public void Configure(EntityTypeBuilder<EmailLog> builder)
    {
        builder.ToTable("email_logs");

        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.TenderId)
            .HasColumnName("tender_id");

        builder.Property(e => e.RecipientEmail)
            .HasColumnName("recipient_email")
            .HasMaxLength(255)
            .IsRequired();

        builder.Property(e => e.RecipientName)
            .HasColumnName("recipient_name")
            .HasMaxLength(200);

        builder.Property(e => e.EmailType)
            .HasColumnName("email_type")
            .HasMaxLength(100)
            .HasConversion<string>()
            .IsRequired();

        builder.Property(e => e.Subject)
            .HasColumnName("subject")
            .HasMaxLength(500)
            .IsRequired();

        builder.Property(e => e.Body)
            .HasColumnName("body");

        builder.Property(e => e.Status)
            .HasColumnName("status")
            .HasMaxLength(50)
            .HasConversion<string>()
            .HasDefaultValue("Pending")
            .IsRequired();

        builder.Property(e => e.SentAt)
            .HasColumnName("sent_at");

        builder.Property(e => e.ErrorMessage)
            .HasColumnName("error_message");

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Ignore(e => e.UpdatedAt);

        // Relationships
        builder.HasOne(e => e.Tender)
            .WithMany(t => t.EmailLogs)
            .HasForeignKey(e => e.TenderId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
