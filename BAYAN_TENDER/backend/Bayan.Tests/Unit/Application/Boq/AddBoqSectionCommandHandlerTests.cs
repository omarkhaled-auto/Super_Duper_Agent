using AutoMapper;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Boq.Commands.AddBoqSection;
using Bayan.Application.Features.Boq.DTOs;
using Bayan.Domain.Entities;
using FluentAssertions;
using Microsoft.EntityFrameworkCore;
using MockQueryable.Moq;
using Moq;

namespace Bayan.Tests.Unit.Application.Boq;

/// <summary>
/// Unit tests for AddBoqSectionCommandHandler.
/// Tests BOQ section creation logic including entity mapping and persistence.
/// </summary>
public class AddBoqSectionCommandHandlerTests
{
    private readonly Mock<IApplicationDbContext> _contextMock;
    private readonly Mock<IMapper> _mapperMock;
    private readonly AddBoqSectionCommandHandler _handler;
    private readonly List<BoqSection> _boqSectionsStore;

    public AddBoqSectionCommandHandlerTests()
    {
        _contextMock = new Mock<IApplicationDbContext>();
        _mapperMock = new Mock<IMapper>();
        _boqSectionsStore = new List<BoqSection>();

        _handler = new AddBoqSectionCommandHandler(
            _contextMock.Object,
            _mapperMock.Object);
    }

    [Fact]
    public async Task Handle_WithValidData_CreatesSection()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var command = CreateValidCommand(tenderId);

        SetupBoqSectionsDbSetForAdd();
        SetupBoqSectionsDbSetForQuery();
        SetupSaveChanges();
        SetupMapper();

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _boqSectionsStore.Should().HaveCount(1);
        var createdSection = _boqSectionsStore[0];
        createdSection.TenderId.Should().Be(tenderId);
        createdSection.SectionNumber.Should().Be(command.SectionNumber);
        createdSection.Title.Should().Be(command.Title);
        createdSection.SortOrder.Should().Be(command.SortOrder);
        createdSection.ParentSectionId.Should().Be(command.ParentSectionId);
        createdSection.Id.Should().NotBeEmpty();
        createdSection.CreatedAt.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromMinutes(1));
    }

    [Fact]
    public async Task Handle_WithDuplicateSortOrder_HandlesCorrectly()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var existingSection = CreateTestSection(tenderId, sortOrder: 1);

        var command = new AddBoqSectionCommand
        {
            TenderId = tenderId,
            SectionNumber = "2",
            Title = "Second Section",
            SortOrder = 1, // Same sort order as existing section
            ParentSectionId = null
        };

        SetupBoqSectionsDbSetForAdd();
        SetupBoqSectionsDbSetForQuery(existingSection);
        SetupSaveChanges();
        SetupMapper();

        // Act
        // The handler does not validate sort order uniqueness; it simply creates the section.
        // Validation would be handled by the command validator or database constraints.
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        _boqSectionsStore.Should().HaveCount(1);
        _boqSectionsStore[0].SortOrder.Should().Be(1);
        result.Should().NotBeNull();
    }

    [Fact]
    public async Task Handle_CallsSaveChangesAsync()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var command = CreateValidCommand(tenderId);

        SetupBoqSectionsDbSetForAdd();
        SetupBoqSectionsDbSetForQuery();
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
    public async Task Handle_ReturnsSectionDto()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var command = CreateValidCommand(tenderId);

        var expectedDto = new BoqSectionDto
        {
            Id = Guid.NewGuid(),
            SectionNumber = command.SectionNumber,
            Title = command.Title,
            SortOrder = command.SortOrder,
            ParentSectionId = command.ParentSectionId,
            Items = new List<BoqItemDto>()
        };

        SetupBoqSectionsDbSetForAdd();
        SetupBoqSectionsDbSetForQuery();
        SetupSaveChanges();

        _mapperMock.Setup(x => x.Map<BoqSectionDto>(It.IsAny<BoqSection>()))
            .Returns(expectedDto);

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.SectionNumber.Should().Be(command.SectionNumber);
        result.Title.Should().Be(command.Title);
        result.SortOrder.Should().Be(command.SortOrder);
        _mapperMock.Verify(
            x => x.Map<BoqSectionDto>(It.IsAny<BoqSection>()),
            Times.Once);
    }

    [Fact]
    public async Task Handle_WithParentSectionId_SetsSectionHierarchy()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var parentSectionId = Guid.NewGuid();

        var command = new AddBoqSectionCommand
        {
            TenderId = tenderId,
            SectionNumber = "1.1",
            Title = "Child Section",
            SortOrder = 1,
            ParentSectionId = parentSectionId
        };

        SetupBoqSectionsDbSetForAdd();
        SetupBoqSectionsDbSetForQuery();
        SetupSaveChanges();
        SetupMapper();

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        _boqSectionsStore.Should().HaveCount(1);
        _boqSectionsStore[0].ParentSectionId.Should().Be(parentSectionId);
        _boqSectionsStore[0].SectionNumber.Should().Be("1.1");
    }

    #region Helper Methods

    private static AddBoqSectionCommand CreateValidCommand(Guid tenderId)
    {
        return new AddBoqSectionCommand
        {
            TenderId = tenderId,
            SectionNumber = "1",
            Title = "General Requirements",
            SortOrder = 1,
            ParentSectionId = null
        };
    }

    private static BoqSection CreateTestSection(
        Guid tenderId,
        int sortOrder = 1,
        string sectionNumber = "1")
    {
        return new BoqSection
        {
            Id = Guid.NewGuid(),
            TenderId = tenderId,
            SectionNumber = sectionNumber,
            Title = "Test Section",
            SortOrder = sortOrder,
            ParentSectionId = null,
            Items = new List<BoqItem>(),
            CreatedAt = DateTime.UtcNow
        };
    }

    private void SetupBoqSectionsDbSetForAdd()
    {
        var mockDbSet = new Mock<DbSet<BoqSection>>();

        mockDbSet.Setup(x => x.Add(It.IsAny<BoqSection>()))
            .Callback<BoqSection>(section => _boqSectionsStore.Add(section));

        _contextMock.Setup(x => x.BoqSections).Returns(mockDbSet.Object);
    }

    private void SetupBoqSectionsDbSetForQuery(params BoqSection[] existingSections)
    {
        // After SaveChangesAsync, the handler reloads the section by Id.
        // We combine existing sections with any sections that were added to the store.
        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1)
            .Callback(() =>
            {
                // Rebuild the DbSet to include newly added sections for the Include query
                var allSections = existingSections.Concat(_boqSectionsStore).ToList();

                // Ensure Items collection is initialized for all sections
                foreach (var section in allSections)
                {
                    section.Items ??= new List<BoqItem>();
                }

                var queryMockDbSet = allSections.AsQueryable().BuildMockDbSet();
                _contextMock.Setup(x => x.BoqSections).Returns(queryMockDbSet.Object);
            });
    }

    private void SetupSaveChanges()
    {
        // Base setup handled by SetupBoqSectionsDbSetForQuery callback
    }

    private void SetupMapper()
    {
        _mapperMock.Setup(x => x.Map<BoqSectionDto>(It.IsAny<BoqSection>()))
            .Returns((BoqSection section) => new BoqSectionDto
            {
                Id = section.Id,
                SectionNumber = section.SectionNumber,
                Title = section.Title,
                SortOrder = section.SortOrder,
                ParentSectionId = section.ParentSectionId,
                Items = new List<BoqItemDto>()
            });
    }

    #endregion
}
