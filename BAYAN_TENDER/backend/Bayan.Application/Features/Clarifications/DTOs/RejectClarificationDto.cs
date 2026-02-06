namespace Bayan.Application.Features.Clarifications.DTOs;

/// <summary>
/// Data transfer object for rejecting a clarification.
/// </summary>
public class RejectClarificationDto
{
    /// <summary>
    /// Reason for rejection.
    /// </summary>
    public string Reason { get; set; } = string.Empty;
}
