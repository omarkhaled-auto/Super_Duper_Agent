using FluentValidation;

namespace Bayan.Application.Features.BidAnalysis.Commands.MapBidColumns;

/// <summary>
/// Validator for MapBidColumnsCommand.
/// </summary>
public class MapBidColumnsCommandValidator : AbstractValidator<MapBidColumnsCommand>
{
    public MapBidColumnsCommandValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");

        RuleFor(x => x.BidId)
            .NotEmpty()
            .WithMessage("Bid ID is required.");

        RuleFor(x => x.ColumnMappings)
            .NotNull()
            .WithMessage("Column mappings are required.");

        RuleFor(x => x.ColumnMappings.DescriptionColumn)
            .NotEmpty()
            .When(x => string.IsNullOrEmpty(x.ColumnMappings.ItemNumberColumn))
            .WithMessage("Either item number or description column must be mapped.");

        RuleFor(x => x.ColumnMappings.ItemNumberColumn)
            .NotEmpty()
            .When(x => string.IsNullOrEmpty(x.ColumnMappings.DescriptionColumn))
            .WithMessage("Either item number or description column must be mapped.");
    }
}
