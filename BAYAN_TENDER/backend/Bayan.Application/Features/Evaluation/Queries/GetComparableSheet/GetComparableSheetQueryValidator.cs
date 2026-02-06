using FluentValidation;

namespace Bayan.Application.Features.Evaluation.Queries.GetComparableSheet;

/// <summary>
/// Validator for GetComparableSheetQuery.
/// </summary>
public class GetComparableSheetQueryValidator : AbstractValidator<GetComparableSheetQuery>
{
    public GetComparableSheetQueryValidator()
    {
        RuleFor(x => x.TenderId)
            .NotEmpty()
            .WithMessage("Tender ID is required.");
    }
}
