using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Tenders.Commands.CreateTender;
using Bayan.Application.Features.Tenders.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;
using FluentValidation;
using MockQueryable.Moq;
using Moq;

namespace Bayan.Tests.Unit.Application.Tenders;

/// <summary>
/// Unit tests for CreateTenderCommandValidator.
/// </summary>
public class CreateTenderCommandValidatorTests
{
    private readonly Mock<IApplicationDbContext> _contextMock;
    private readonly Guid _validClientId = Guid.NewGuid();

    public CreateTenderCommandValidatorTests()
    {
        _contextMock = new Mock<IApplicationDbContext>();
    }

    [Fact]
    public async Task Validate_WithValidCommand_HasNoErrors()
    {
        // Arrange
        SetupClientsDbSet(new List<Client>
        {
            CreateActiveClient(_validClientId)
        });

        var validator = CreateValidator();
        var command = CreateValidCommand();

        // Act
        var result = await validator.ValidateAsync(command);

        // Assert
        result.IsValid.Should().BeTrue();
        result.Errors.Should().BeEmpty();
    }

    [Fact]
    public async Task Validate_WithEmptyTitle_HasError()
    {
        // Arrange
        SetupClientsDbSet(new List<Client> { CreateActiveClient(_validClientId) });

        var validator = CreateValidator();
        var command = CreateValidCommand();
        command.Title = string.Empty;

        // Act
        var result = await validator.ValidateAsync(command);

        // Assert
        result.IsValid.Should().BeFalse();
        result.Errors.Should().Contain(e =>
            e.PropertyName == "Title" &&
            e.ErrorMessage.Contains("required"));
    }

    [Fact]
    public async Task Validate_WithTitleTooLong_HasError()
    {
        // Arrange
        SetupClientsDbSet(new List<Client> { CreateActiveClient(_validClientId) });

        var validator = CreateValidator();
        var command = CreateValidCommand();
        command.Title = new string('A', 501);

        // Act
        var result = await validator.ValidateAsync(command);

        // Assert
        result.IsValid.Should().BeFalse();
        result.Errors.Should().Contain(e =>
            e.PropertyName == "Title" &&
            e.ErrorMessage.Contains("500"));
    }

    [Fact]
    public async Task Validate_WithInvalidClientId_HasError()
    {
        // Arrange
        SetupClientsDbSet(new List<Client> { CreateActiveClient(_validClientId) });

        var validator = CreateValidator();
        var command = CreateValidCommand();
        command.ClientId = Guid.Empty;

        // Act
        var result = await validator.ValidateAsync(command);

        // Assert
        result.IsValid.Should().BeFalse();
        result.Errors.Should().Contain(e =>
            e.PropertyName == "ClientId" &&
            e.ErrorMessage.Contains("required"));
    }

    [Fact]
    public async Task Validate_WithPastSubmissionDeadline_HasError()
    {
        // Arrange
        SetupClientsDbSet(new List<Client> { CreateActiveClient(_validClientId) });

        var validator = CreateValidator();
        var command = CreateValidCommand();
        // Set submission deadline before the clarification deadline + 3 days
        command.IssueDate = DateTime.UtcNow;
        command.ClarificationDeadline = DateTime.UtcNow.AddDays(7);
        command.SubmissionDeadline = DateTime.UtcNow.AddDays(8); // Only 1 day after clarification, needs 3+

        // Act
        var result = await validator.ValidateAsync(command);

        // Assert
        result.IsValid.Should().BeFalse();
        result.Errors.Should().Contain(e =>
            e.PropertyName == "SubmissionDeadline" &&
            e.ErrorMessage.Contains("at least 3 days"));
    }

    [Fact]
    public async Task Validate_WithClarificationAfterSubmission_HasError()
    {
        // Arrange
        SetupClientsDbSet(new List<Client> { CreateActiveClient(_validClientId) });

        var validator = CreateValidator();
        var command = CreateValidCommand();
        // Set clarification deadline after issue date is fine, but submission must be
        // at least 3 days after clarification. Setting submission before clarification violates this.
        command.IssueDate = DateTime.UtcNow;
        command.ClarificationDeadline = DateTime.UtcNow.AddDays(30);
        command.SubmissionDeadline = DateTime.UtcNow.AddDays(20); // Before clarification deadline
        command.OpeningDate = DateTime.UtcNow.AddDays(21);

        // Act
        var result = await validator.ValidateAsync(command);

        // Assert
        result.IsValid.Should().BeFalse();
        result.Errors.Should().Contain(e =>
            e.PropertyName == "SubmissionDeadline" &&
            e.ErrorMessage.Contains("at least 3 days after the clarification deadline"));
    }

    [Fact]
    public async Task Validate_WithWeightsNotSumTo100_HasError()
    {
        // Arrange
        SetupClientsDbSet(new List<Client> { CreateActiveClient(_validClientId) });

        var validator = CreateValidator();
        var command = CreateValidCommand();
        command.TechnicalWeight = 30;
        command.CommercialWeight = 30;

        // Act
        var result = await validator.ValidateAsync(command);

        // Assert
        result.IsValid.Should().BeFalse();
        result.Errors.Should().Contain(e =>
            e.ErrorMessage.Contains("sum to 100"));
    }

    [Fact]
    public async Task Validate_WithNegativeWeights_HasError()
    {
        // Arrange
        SetupClientsDbSet(new List<Client> { CreateActiveClient(_validClientId) });

        var validator = CreateValidator();
        var command = CreateValidCommand();
        command.TechnicalWeight = -10;
        command.CommercialWeight = 110;

        // Act
        var result = await validator.ValidateAsync(command);

        // Assert
        result.IsValid.Should().BeFalse();
        result.Errors.Should().Contain(e =>
            e.PropertyName == "TechnicalWeight" &&
            e.ErrorMessage.Contains("between 0 and 100"));
    }

    [Fact]
    public async Task Validate_WithInvalidCurrency_HasError()
    {
        // Arrange
        SetupClientsDbSet(new List<Client> { CreateActiveClient(_validClientId) });

        var validator = CreateValidator();
        var command = CreateValidCommand();
        command.BaseCurrency = "us"; // Lowercase, only 2 chars

        // Act
        var result = await validator.ValidateAsync(command);

        // Assert
        result.IsValid.Should().BeFalse();
        result.Errors.Should().Contain(e =>
            e.PropertyName == "BaseCurrency");
    }

    [Fact]
    public async Task Validate_WithEmptyDescription_IsValid()
    {
        // Arrange
        SetupClientsDbSet(new List<Client> { CreateActiveClient(_validClientId) });

        var validator = CreateValidator();
        var command = CreateValidCommand();
        command.Description = null;

        // Act
        var result = await validator.ValidateAsync(command);

        // Assert
        // Description is optional, so a null/empty description should not cause a validation error
        result.Errors.Should().NotContain(e => e.PropertyName == "Description");
    }

    [Fact]
    public async Task Validate_WithValidBidValidityDays_HasNoErrors()
    {
        // Arrange
        SetupClientsDbSet(new List<Client> { CreateActiveClient(_validClientId) });

        var validator = CreateValidator();
        var command = CreateValidCommand();
        command.BidValidityDays = 90;

        // Act
        var result = await validator.ValidateAsync(command);

        // Assert
        result.Errors.Should().NotContain(e => e.PropertyName == "BidValidityDays");
    }

    [Fact]
    public async Task Validate_WithZeroBidValidityDays_HasError()
    {
        // Arrange
        SetupClientsDbSet(new List<Client> { CreateActiveClient(_validClientId) });

        var validator = CreateValidator();
        var command = CreateValidCommand();
        command.BidValidityDays = 0;

        // Act
        var result = await validator.ValidateAsync(command);

        // Assert
        result.IsValid.Should().BeFalse();
        result.Errors.Should().Contain(e =>
            e.PropertyName == "BidValidityDays" &&
            e.ErrorMessage.Contains("greater than 0"));
    }

    #region Helper Methods

    private CreateTenderCommandValidator CreateValidator()
    {
        return new CreateTenderCommandValidator(_contextMock.Object);
    }

    private CreateTenderCommand CreateValidCommand()
    {
        var issueDate = DateTime.UtcNow;
        var clarificationDeadline = issueDate.AddDays(7);
        var submissionDeadline = clarificationDeadline.AddDays(14);
        var openingDate = submissionDeadline.AddDays(1);

        return new CreateTenderCommand
        {
            Title = "Test Tender for Building Construction",
            Description = "A comprehensive tender for building construction services.",
            ClientId = _validClientId,
            TenderType = TenderType.Open,
            BaseCurrency = "AED",
            BidValidityDays = 90,
            IssueDate = issueDate,
            ClarificationDeadline = clarificationDeadline,
            SubmissionDeadline = submissionDeadline,
            OpeningDate = openingDate,
            TechnicalWeight = 40,
            CommercialWeight = 60,
            EvaluationCriteria = new List<CreateEvaluationCriterionDto>()
        };
    }

    private static Client CreateActiveClient(Guid clientId)
    {
        return new Client
        {
            Id = clientId,
            Name = "ADNOC",
            ContactPerson = "John Doe",
            Email = "contact@adnoc.ae",
            IsActive = true,
            CreatedAt = DateTime.UtcNow.AddMonths(-6)
        };
    }

    private void SetupClientsDbSet(List<Client> clients)
    {
        var mockDbSet = clients.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.Clients).Returns(mockDbSet.Object);
    }

    #endregion
}
