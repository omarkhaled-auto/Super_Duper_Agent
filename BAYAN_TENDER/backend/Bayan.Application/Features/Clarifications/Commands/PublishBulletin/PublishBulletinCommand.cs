using Bayan.Application.Features.Clarifications.DTOs;
using MediatR;

namespace Bayan.Application.Features.Clarifications.Commands.PublishBulletin;

/// <summary>
/// Command for publishing a clarification bulletin.
/// </summary>
public class PublishBulletinCommand : IRequest<ClarificationBulletinDto>
{
    /// <summary>
    /// ID of the tender.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// IDs of clarifications to include in the bulletin.
    /// </summary>
    public List<Guid> ClarificationIds { get; set; } = new();

    /// <summary>
    /// Optional introduction text for the bulletin.
    /// </summary>
    public string? Introduction { get; set; }

    /// <summary>
    /// Optional closing notes for the bulletin.
    /// </summary>
    public string? ClosingNotes { get; set; }

    public PublishBulletinCommand()
    {
    }

    public PublishBulletinCommand(Guid tenderId, CreateBulletinDto dto)
    {
        TenderId = tenderId;
        ClarificationIds = dto.ClarificationIds;
        Introduction = dto.Introduction;
        ClosingNotes = dto.ClosingNotes;
    }
}
