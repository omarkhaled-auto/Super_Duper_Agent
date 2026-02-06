using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class NotificationPreferenceConfiguration : IEntityTypeConfiguration<NotificationPreference>
{
    public void Configure(EntityTypeBuilder<NotificationPreference> builder)
    {
        builder.ToTable("notification_preferences");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => e.UserId).IsUnique();

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.UserId)
            .HasColumnName("user_id")
            .IsRequired();

        builder.Property(e => e.TenderInvitation)
            .HasColumnName("tender_invitation")
            .HasDefaultValue(true)
            .IsRequired();

        builder.Property(e => e.AddendumIssued)
            .HasColumnName("addendum_issued")
            .HasDefaultValue(true)
            .IsRequired();

        builder.Property(e => e.ClarificationPublished)
            .HasColumnName("clarification_published")
            .HasDefaultValue(true)
            .IsRequired();

        builder.Property(e => e.DeadlineReminder3Days)
            .HasColumnName("deadline_reminder_3days")
            .HasDefaultValue(true)
            .IsRequired();

        builder.Property(e => e.DeadlineReminder1Day)
            .HasColumnName("deadline_reminder_1day")
            .HasDefaultValue(true)
            .IsRequired();

        builder.Property(e => e.ApprovalRequest)
            .HasColumnName("approval_request")
            .HasDefaultValue(true)
            .IsRequired();

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");

        // Relationships
        builder.HasOne(e => e.User)
            .WithOne(u => u.NotificationPreference)
            .HasForeignKey<NotificationPreference>(e => e.UserId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}
