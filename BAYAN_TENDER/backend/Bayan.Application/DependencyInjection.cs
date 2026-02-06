namespace Bayan.Application;

using Bayan.Application.Common.Behaviors;
using Bayan.Application.Features.Boq.Services;
using FluentValidation;
using MediatR;
using Microsoft.Extensions.DependencyInjection;
using System.Reflection;

/// <summary>
/// Extension methods for registering application services.
/// </summary>
public static class DependencyInjection
{
    /// <summary>
    /// Adds application layer services to the dependency injection container.
    /// </summary>
    public static IServiceCollection AddApplicationServices(this IServiceCollection services)
    {
        services.AddValidatorsFromAssembly(Assembly.GetExecutingAssembly());

        services.AddAutoMapper(Assembly.GetExecutingAssembly());

        services.AddMediatR(cfg =>
        {
            cfg.RegisterServicesFromAssembly(Assembly.GetExecutingAssembly());
            cfg.AddBehavior(typeof(IPipelineBehavior<,>), typeof(ValidationBehavior<,>));
            cfg.AddBehavior(typeof(IPipelineBehavior<,>), typeof(LoggingBehavior<,>));
            cfg.AddBehavior(typeof(IPipelineBehavior<,>), typeof(AuditLogBehavior<,>));
        });

        // Register BOQ import services
        services.AddMemoryCache();
        services.AddScoped<IBoqImportSessionService, BoqImportSessionService>();
        services.AddScoped<IBoqColumnMappingService, BoqColumnMappingService>();
        services.AddScoped<IBoqSectionDetectionService, BoqSectionDetectionService>();

        return services;
    }
}
