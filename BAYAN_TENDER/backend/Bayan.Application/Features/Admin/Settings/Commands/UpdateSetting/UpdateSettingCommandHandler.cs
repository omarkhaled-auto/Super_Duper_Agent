namespace Bayan.Application.Features.Admin.Settings.Commands.UpdateSetting;

using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Admin.Settings.DTOs;
using MediatR;
using Microsoft.EntityFrameworkCore;

/// <summary>
/// Handler for updating a system setting.
/// </summary>
public class UpdateSettingCommandHandler : IRequestHandler<UpdateSettingCommand, UpdateSettingResponse>
{
    private readonly IApplicationDbContext _context;
    private readonly ICurrentUserService _currentUserService;

    public UpdateSettingCommandHandler(
        IApplicationDbContext context,
        ICurrentUserService currentUserService)
    {
        _context = context;
        _currentUserService = currentUserService;
    }

    public async Task<UpdateSettingResponse> Handle(UpdateSettingCommand request, CancellationToken cancellationToken)
    {
        var setting = await _context.SystemSettings
            .FirstOrDefaultAsync(s => s.Key == request.Key, cancellationToken);

        if (setting == null)
        {
            return new UpdateSettingResponse
            {
                Success = false,
                ErrorMessage = $"Setting with key '{request.Key}' not found."
            };
        }

        if (!setting.IsEditable)
        {
            return new UpdateSettingResponse
            {
                Success = false,
                ErrorMessage = $"Setting with key '{request.Key}' is not editable."
            };
        }

        // Validate value based on data type
        if (!ValidateValueForDataType(request.Value, setting.DataType, out var validationError))
        {
            return new UpdateSettingResponse
            {
                Success = false,
                ErrorMessage = validationError
            };
        }

        setting.Value = request.Value;
        setting.LastModifiedAt = DateTime.UtcNow;
        setting.LastModifiedBy = _currentUserService.UserId;

        await _context.SaveChangesAsync(cancellationToken);

        return new UpdateSettingResponse
        {
            Success = true,
            Setting = new SystemSettingDto
            {
                Id = setting.Id,
                Key = setting.Key,
                Value = setting.Value,
                Description = setting.Description,
                DataType = setting.DataType,
                Category = setting.Category,
                IsEditable = setting.IsEditable,
                DisplayOrder = setting.DisplayOrder,
                LastModifiedAt = setting.LastModifiedAt
            }
        };
    }

    private static bool ValidateValueForDataType(string value, string dataType, out string? error)
    {
        error = null;

        switch (dataType.ToLowerInvariant())
        {
            case "int":
            case "integer":
                if (!int.TryParse(value, out _))
                {
                    error = $"Value '{value}' is not a valid integer.";
                    return false;
                }
                break;

            case "decimal":
            case "number":
                if (!decimal.TryParse(value, out _))
                {
                    error = $"Value '{value}' is not a valid number.";
                    return false;
                }
                break;

            case "bool":
            case "boolean":
                if (!bool.TryParse(value, out _) && value != "0" && value != "1")
                {
                    error = $"Value '{value}' is not a valid boolean.";
                    return false;
                }
                break;

            case "string":
            default:
                // String values are always valid
                break;
        }

        return true;
    }
}
