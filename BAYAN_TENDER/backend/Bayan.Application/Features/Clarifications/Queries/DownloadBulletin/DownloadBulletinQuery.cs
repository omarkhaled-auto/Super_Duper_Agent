using Bayan.Application.Features.Clarifications.DTOs;
using MediatR;

namespace Bayan.Application.Features.Clarifications.Queries.DownloadBulletin;

/// <summary>
/// Query for downloading a bulletin PDF.
/// </summary>
public class DownloadBulletinQuery : IRequest<BulletinDownloadDto?>
{
    /// <summary>
    /// ID of the tender.
    /// </summary>
    public Guid TenderId { get; set; }

    /// <summary>
    /// ID of the bulletin.
    /// </summary>
    public Guid BulletinId { get; set; }

    public DownloadBulletinQuery(Guid tenderId, Guid bulletinId)
    {
        TenderId = tenderId;
        BulletinId = bulletinId;
    }
}
