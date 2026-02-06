using Bayan.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Bayan.Infrastructure.Data.Configurations;

public class ApprovalLevelConfiguration : IEntityTypeConfiguration<ApprovalLevel>
{
    public void Configure(EntityTypeBuilder<ApprovalLevel> builder)
    {
        builder.ToTable("approval_levels");

        builder.HasKey(e => e.Id);

        builder.HasIndex(e => new { e.WorkflowId, e.LevelNumber }).IsUnique();

        builder.Property(e => e.Id)
            .HasColumnName("id");

        builder.Property(e => e.WorkflowId)
            .HasColumnName("workflow_id")
            .IsRequired();

        builder.Property(e => e.LevelNumber)
            .HasColumnName("level_number")
            .IsRequired();

        builder.Property(e => e.ApproverUserId)
            .HasColumnName("approver_user_id")
            .IsRequired();

        builder.Property(e => e.Deadline)
            .HasColumnName("deadline");

        builder.Property(e => e.Decision)
            .HasColumnName("decision")
            .HasMaxLength(50)
            .HasConversion<string>();

        builder.Property(e => e.DecisionComment)
            .HasColumnName("decision_comment");

        builder.Property(e => e.DecidedAt)
            .HasColumnName("decided_at");

        builder.Property(e => e.Status)
            .HasColumnName("status")
            .HasMaxLength(50)
            .HasConversion<string>()
            .HasDefaultValue("Waiting")
            .IsRequired();

        builder.Property(e => e.NotifiedAt)
            .HasColumnName("notified_at");

        builder.Property(e => e.CreatedAt)
            .HasColumnName("created_at")
            .IsRequired();

        builder.Property(e => e.UpdatedAt)
            .HasColumnName("updated_at");

        // Relationships
        builder.HasOne(e => e.Workflow)
            .WithMany(w => w.Levels)
            .HasForeignKey(e => e.WorkflowId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.HasOne(e => e.Approver)
            .WithMany(u => u.ApprovalLevels)
            .HasForeignKey(e => e.ApproverUserId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
