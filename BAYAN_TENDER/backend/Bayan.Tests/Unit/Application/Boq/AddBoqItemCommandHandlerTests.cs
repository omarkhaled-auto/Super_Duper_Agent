using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.Commands.AddBoqItem;
using Bayan.Application.Features.Boq.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;
using Microsoft.EntityFrameworkCore;
using Moq;

namespace Bayan.Tests.Unit.Application.Boq;

/// <summary>
/// Unit tests for AddBoqItemCommandHandler.
/// Tests BOQ item creation logic including entity property mapping and persistence.
/// </summary>
public class AddBoqItemCommandHandlerTests
{
    private readonly Mock<IApplicationDbContext> _contextMock;
    private readonly Mock<IMapper> _mapperMock;
    private readonly AddBoqItemCommandHandler _handler;
    private readonly List<BoqItem> _boqItemsStore;

    public AddBoqItemCommandHandlerTests()
    {
        _contextMock = new Mock<IApplicationDbContext>();
        _mapperMock = new Mock<IMapper>();
        _boqItemsStore = new List<BoqItem>();

        SetupBoqItemsDbSet();

        _handler = new AddBoqItemCommandHandler(
            _contextMock.Object,
            _mapperMock.Object);
    }

    [Fact]
    public async Task Handle_WithValidData_CreatesItem()
    {
        // Arrange
        var command = CreateValidCommand();

        SetupSaveChanges();
        SetupMapper();

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _boqItemsStore.Should().HaveCount(1);
        var createdItem = _boqItemsStore[0];
        createdItem.TenderId.Should().Be(command.TenderId);
        createdItem.SectionId.Should().Be(command.SectionId);
        createdItem.Description.Should().Be(command.Description);
        createdItem.Quantity.Should().Be(command.Quantity);
        createdItem.Uom.Should().Be(command.Uom);
        createdItem.ItemType.Should().Be(command.ItemType);
        createdItem.Notes.Should().Be(command.Notes);
        createdItem.SortOrder.Should().Be(command.SortOrder);
        createdItem.Id.Should().NotBeEmpty();
        createdItem.CreatedAt.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromMinutes(1));
    }

    [Fact]
    public async Task Handle_SetsItemNumberCorrectly()
    {
        // Arrange
        var command = new AddBoqItemCommand
        {
            TenderId = Guid.NewGuid(),
            SectionId = Guid.NewGuid(),
            ItemNumber = "1.2.3",
            Description = "Supply and install HVAC ducts",
            Quantity = 500.0m,
            Uom = "LM",
            ItemType = BoqItemType.Base,
            SortOrder = 3
        };

        SetupSaveChanges();
        SetupMapper();

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _boqItemsStore.Should().HaveCount(1);
        _boqItemsStore[0].ItemNumber.Should().Be("1.2.3");
    }

    [Fact]
    public async Task Handle_WithNonExistentSection_CreatesItemWithSectionId()
    {
        // Arrange
        // The handler does not validate section existence; it sets the SectionId directly.
        // FK validation would be handled at the database level.
        var nonExistentSectionId = Guid.NewGuid();
        var command = new AddBoqItemCommand
        {
            TenderId = Guid.NewGuid(),
            SectionId = nonExistentSectionId,
            ItemNumber = "1.1.1",
            Description = "Test item",
            Quantity = 10.0m,
            Uom = "m2",
            ItemType = BoqItemType.Base,
            SortOrder = 1
        };

        SetupSaveChanges();
        SetupMapper();

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _boqItemsStore.Should().HaveCount(1);
        _boqItemsStore[0].SectionId.Should().Be(nonExistentSectionId);
    }

    [Fact]
    public async Task Handle_CallsSaveChangesAsync()
    {
        // Arrange
        var command = CreateValidCommand();

        SetupSaveChanges();
        SetupMapper();

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _contextMock.Verify(
            x => x.SaveChangesAsync(It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task Handle_ReturnsBoqItemDto()
    {
        // Arrange
        var command = CreateValidCommand();

        var expectedDto = new BoqItemDto
        {
            Id = Guid.NewGuid(),
            ItemNumber = command.ItemNumber,
            Description = command.Description,
            Quantity = command.Quantity,
            Uom = command.Uom,
            ItemType = command.ItemType,
            Notes = command.Notes,
            SectionId = command.SectionId,
            SortOrder = command.SortOrder
        };

        SetupSaveChanges();

        _mapperMock.Setup(x => x.Map<BoqItemDto>(It.IsAny<BoqItem>()))
            .Returns(expectedDto);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.ItemNumber.Should().Be(command.ItemNumber);
        result.Description.Should().Be(command.Description);
        result.Quantity.Should().Be(command.Quantity);
        result.Uom.Should().Be(command.Uom);
        result.ItemType.Should().Be(command.ItemType);
        _mapperMock.Verify(
            x => x.Map<BoqItemDto>(It.IsAny<BoqItem>()),
            Times.Once);
    }

    [Theory]
    [InlineData(BoqItemType.Base)]
    [InlineData(BoqItemType.Alternate)]
    [InlineData(BoqItemType.ProvisionalSum)]
    [InlineData(BoqItemType.Daywork)]
    public async Task Handle_WithDifferentItemTypes_SetsItemTypeCorrectly(BoqItemType itemType)
    {
        // Arrange
        var command = new AddBoqItemCommand
        {
            TenderId = Guid.NewGuid(),
            SectionId = Guid.NewGuid(),
            ItemNumber = "1.1.1",
            Description = "Test Item",
            Quantity = 100.0m,
            Uom = "m2",
            ItemType = itemType,
            SortOrder = 1
        };

        SetupSaveChanges();
        SetupMapper();

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _boqItemsStore.Last().ItemType.Should().Be(itemType);
    }

    #region Helper Methods

    private static AddBoqItemCommand CreateValidCommand()
    {
        return new AddBoqItemCommand
        {
            TenderId = Guid.NewGuid(),
            SectionId = Guid.NewGuid(),
            ItemNumber = "1.1.1",
            Description = "Supply and install reinforced concrete foundations",
            Quantity = 250.0m,
            Uom = "m3",
            ItemType = BoqItemType.Base,
            Notes = "Including formwork and rebar",
            SortOrder = 1
        };
    }

    private void SetupBoqItemsDbSet()
    {
        var mockDbSet = new Mock<DbSet<BoqItem>>();

        mockDbSet.Setup(x => x.Add(It.IsAny<BoqItem>()))
            .Callback<BoqItem>(item => _boqItemsStore.Add(item));

        _contextMock.Setup(x => x.BoqItems).Returns(mockDbSet.Object);
    }

    private void SetupSaveChanges()
    {
        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);
    }

    private void SetupMapper()
    {
        _mapperMock.Setup(x => x.Map<BoqItemDto>(It.IsAny<BoqItem>()))
            .Returns((BoqItem item) => new BoqItemDto
            {
                Id = item.Id,
                ItemNumber = item.ItemNumber,
                Description = item.Description,
                Quantity = item.Quantity,
                Uom = item.Uom,
                ItemType = item.ItemType,
                Notes = item.Notes,
                SectionId = item.SectionId,
                SortOrder = item.SortOrder
            });
    }

    #endregion
}
