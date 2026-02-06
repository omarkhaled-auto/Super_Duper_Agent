using Bayan.Domain.Common;
using Bayan.Domain.Enums;

namespace Bayan.Domain.Entities;

/// <summary>
/// Represents a user in the Bayan Tender Management System.
/// </summary>
public class User : BaseEntity, IAuditableEntity
{
    /// <summary>
    /// User's email address (used for login).
    /// </summary>
    public string Email { get; set; } = string.Empty;

    /// <summary>
    /// Hashed password for authentication.
    /// </summary>
    public string PasswordHash { get; set; } = string.Empty;

    /// <summary>
    /// User's first name.
    /// </summary>
    public string FirstName { get; set; } = string.Empty;

    /// <summary>
    /// User's last name.
    /// </summary>
    public string LastName { get; set; } = string.Empty;

    /// <summary>
    /// User's full name (computed property).
    /// </summary>
    public string FullName => $"{FirstName} {LastName}".Trim();

    /// <summary>
    /// User's phone number.
    /// </summary>
    public string? PhoneNumber { get; set; }

    /// <summary>
    /// User's role in the system.
    /// </summary>
    public UserRole Role { get; set; }

    /// <summary>
    /// Indicates whether the user account is active.
    /// </summary>
    public bool IsActive { get; set; } = true;

    /// <summary>
    /// Indicates whether the user's email has been verified.
    /// </summary>
    public bool EmailVerified { get; set; }

    /// <summary>
    /// Token for email verification.
    /// </summary>
    public string? EmailVerificationToken { get; set; }

    /// <summary>
    /// Expiration time for the email verification token.
    /// </summary>
    public DateTime? EmailVerificationTokenExpiry { get; set; }

    /// <summary>
    /// Token for password reset.
    /// </summary>
    public string? PasswordResetToken { get; set; }

    /// <summary>
    /// Expiration time for the password reset token.
    /// </summary>
    public DateTime? PasswordResetTokenExpiry { get; set;  }

    /// <summary>
    /// Timestamp of the user's last login.
    /// </summary>
    public DateTime? LastLoginAt { get; set; }

    /// <summary>
    /// Number of failed login attempts.
    /// </summary>
    public int FailedLoginAttempts { get; set; }

    /// <summary>
    /// Timestamp until which the account is locked.
    /// </summary>
    public DateTime? LockoutEnd { get; set; }

    /// <summary>
    /// Refresh token for JWT authentication.
    /// </summary>
    public string? RefreshToken { get; set; }

    /// <summary>
    /// Expiration time for the refresh token.
    /// </summary>
    public DateTime? RefreshTokenExpiry { get; set; }

    /// <summary>
    /// Company name (for bidder users).
    /// </summary>
    public string? CompanyName { get; set; }

    /// <summary>
    /// Commercial registration number (for bidder users).
    /// </summary>
    public string? CommercialRegistrationNumber { get; set; }

    /// <summary>
    /// Department or organizational unit.
    /// </summary>
    public string? Department { get; set; }

    /// <summary>
    /// Job title or position.
    /// </summary>
    public string? JobTitle { get; set; }

    /// <summary>
    /// User's profile picture URL.
    /// </summary>
    public string? ProfilePictureUrl { get; set; }

    /// <summary>
    /// User's preferred language.
    /// </summary>
    public string PreferredLanguage { get; set; } = "ar";

    /// <summary>
    /// User's timezone.
    /// </summary>
    public string TimeZone { get; set; } = "Asia/Riyadh";

    // IAuditableEntity implementation
    public Guid? CreatedBy { get; set; }
    public Guid? LastModifiedBy { get; set; }
    public DateTime? LastModifiedAt { get; set; }

    // Navigation properties
    /// <summary>
    /// Refresh tokens for this user.
    /// </summary>
    public virtual ICollection<RefreshToken> RefreshTokens { get; set; } = new List<RefreshToken>();

    /// <summary>
    /// Tenders created by this user.
    /// </summary>
    public virtual ICollection<Tender> CreatedTenders { get; set; } = new List<Tender>();

    /// <summary>
    /// Documents uploaded by this user.
    /// </summary>
    public virtual ICollection<Document> UploadedDocuments { get; set; } = new List<Document>();

    /// <summary>
    /// Addenda issued by this user.
    /// </summary>
    public virtual ICollection<Addendum> IssuedAddenda { get; set; } = new List<Addendum>();

    /// <summary>
    /// Clarifications submitted by this user.
    /// </summary>
    public virtual ICollection<Clarification> SubmittedClarifications { get; set; } = new List<Clarification>();

    /// <summary>
    /// Clarifications answered by this user.
    /// </summary>
    public virtual ICollection<Clarification> AnsweredClarifications { get; set; } = new List<Clarification>();

    /// <summary>
    /// Clarifications assigned to this user.
    /// </summary>
    public virtual ICollection<Clarification> AssignedClarifications { get; set; } = new List<Clarification>();

    /// <summary>
    /// Clarification bulletins published by this user.
    /// </summary>
    public virtual ICollection<ClarificationBulletin> PublishedBulletins { get; set; } = new List<ClarificationBulletin>();

    /// <summary>
    /// Evaluation panels this user is assigned to.
    /// </summary>
    public virtual ICollection<EvaluationPanel> EvaluationPanels { get; set; } = new List<EvaluationPanel>();

    /// <summary>
    /// Technical scores given by this user.
    /// </summary>
    public virtual ICollection<TechnicalScore> TechnicalScores { get; set; } = new List<TechnicalScore>();

    /// <summary>
    /// Bid exceptions logged by this user.
    /// </summary>
    public virtual ICollection<BidException> LoggedExceptions { get; set; } = new List<BidException>();

    /// <summary>
    /// Approval workflows initiated by this user.
    /// </summary>
    public virtual ICollection<ApprovalWorkflow> InitiatedWorkflows { get; set; } = new List<ApprovalWorkflow>();

    /// <summary>
    /// Approval levels assigned to this user.
    /// </summary>
    public virtual ICollection<ApprovalLevel> ApprovalLevels { get; set; } = new List<ApprovalLevel>();

    /// <summary>
    /// Audit logs for this user.
    /// </summary>
    public virtual ICollection<AuditLog> AuditLogs { get; set; } = new List<AuditLog>();

    /// <summary>
    /// Notification preferences for this user.
    /// </summary>
    public virtual NotificationPreference? NotificationPreference { get; set; }
}
