namespace Bayan.Application.Features.Admin.Settings.Queries.GetSettings;

using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Admin.Settings.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

/// <summary>
/// Handler for retrieving all system settings.
/// </summary>
public class GetSettingsQueryHandler : IRequestHandler<GetSettingsQuery, GetSettingsResponse>
{
    private readonly IApplicationDbContext _context;

    public GetSettingsQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<GetSettingsResponse> Handle(GetSettingsQuery request, CancellationToken cancellationToken)
    {
        var settingsQuery = _context.SystemSettings.AsQueryable();

        if (!string.IsNullOrWhiteSpace(request.Category))
        {
            settingsQuery = settingsQuery.Where(s => s.Category == request.Category);
        }

        var settings = await settingsQuery
            .OrderBy(s => s.DisplayOrder)
            .ThenBy(s => s.Key)
            .Select(s => new SystemSettingDto
            {
                Id = s.Id,
                Key = s.Key,
                Value = s.Value,
                Description = s.Description,
                DataType = s.DataType,
                Category = s.Category,
                IsEditable = s.IsEditable,
                DisplayOrder = s.DisplayOrder,
                LastModifiedAt = s.LastModifiedAt
            })
            .ToListAsync(cancellationToken);

        var unitsOfMeasure = await _context.UnitsOfMeasure
            .Where(u => u.IsActive)
            .OrderBy(u => u.Category)
            .ThenBy(u => u.DisplayOrder)
            .ThenBy(u => u.Code)
            .Select(u => new UnitOfMeasureDto
            {
                Id = u.Id,
                Code = u.Code,
                Name = u.Name,
                Category = u.Category,
                Description = u.Description,
                ConversionFactor = u.ConversionFactor,
                BaseUnitCode = u.BaseUnitCode,
                IsActive = u.IsActive,
                DisplayOrder = u.DisplayOrder
            })
            .ToListAsync(cancellationToken);

        return new GetSettingsResponse
        {
            Settings = settings,
            UnitsOfMeasure = unitsOfMeasure
        };
    }
}
