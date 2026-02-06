using Bayan.Application.Common.Exceptions;
using Bayan.Application.Common.Interfaces;
using Bayan.Application.Features.Bids.Commands.GenerateBidReceiptPdf;
using Bayan.Application.Features.Bids.Commands.SubmitBid;
using Bayan.Application.Features.Bids.DTOs;
using Bayan.Domain.Entities;
using Bayan.Domain.Enums;
using FluentAssertions;
using MediatR;
using MockQueryable.Moq;
using Moq;

namespace Bayan.Tests.Unit.Application.Bids;

/// <summary>
/// Unit tests for SubmitBidCommandHandler.
/// </summary>
public class SubmitBidCommandHandlerTests
{
    private readonly Mock<IApplicationDbContext> _contextMock;
    private readonly Mock<IMediator> _mediatorMock;
    private readonly Mock<IEmailService> _emailServiceMock;
    private readonly Mock<IDateTime> _dateTimeMock;
    private readonly Mock<IFileStorageService> _fileStorageMock;
    private readonly SubmitBidCommandHandler _handler;

    private readonly DateTime _fixedUtcNow = new DateTime(2025, 6, 15, 10, 0, 0, DateTimeKind.Utc);

    public SubmitBidCommandHandlerTests()
    {
        _contextMock = new Mock<IApplicationDbContext>();
        _mediatorMock = new Mock<IMediator>();
        _emailServiceMock = new Mock<IEmailService>();
        _dateTimeMock = new Mock<IDateTime>();
        _fileStorageMock = new Mock<IFileStorageService>();

        _dateTimeMock.Setup(x => x.UtcNow).Returns(_fixedUtcNow);

        _contextMock.Setup(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(1);

        _mediatorMock.Setup(x => x.Send(It.IsAny<GenerateBidReceiptPdfCommand>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new GenerateBidReceiptPdfResult
            {
                PdfContent = new byte[] { 0x25, 0x50, 0x44, 0x46 },
                FilePath = "/receipts/receipt.pdf"
            });

        _emailServiceMock.Setup(x => x.SendTemplatedEmailAsync(
                It.IsAny<string>(),
                It.IsAny<string>(),
                It.IsAny<Dictionary<string, string>>(),
                It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        _handler = new SubmitBidCommandHandler(
            _contextMock.Object,
            _mediatorMock.Object,
            _emailServiceMock.Object,
            _dateTimeMock.Object,
            _fileStorageMock.Object);
    }

    [Fact]
    public async Task Handle_WithValidData_CreatesBidSubmission()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var bidderId = Guid.NewGuid();
        SetupValidSubmissionScenario(tenderId, bidderId);

        var command = new SubmitBidCommand
        {
            TenderId = tenderId,
            BidderId = bidderId,
            BidValidityDays = 90
        };

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.BidId.Should().NotBeEmpty();
        result.Receipt.Should().NotBeNull();
        result.Message.Should().Contain("successfully");
    }

    [Fact]
    public async Task Handle_WithNonExistentTender_ThrowsNotFoundException()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var bidderId = Guid.NewGuid();

        SetupTendersDbSet(new List<Tender>()); // No tenders
        SetupBiddersDbSet(new List<Bidder>());
        SetupTenderBiddersDbSet(new List<TenderBidder>());
        SetupBidSubmissionsDbSet(new List<BidSubmission>());

        var command = new SubmitBidCommand
        {
            TenderId = tenderId,
            BidderId = bidderId,
            BidValidityDays = 90
        };

        // Act
        var act = async () => await _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<NotFoundException>()
            .WithMessage("*Tender*");
    }

    [Fact]
    public async Task Handle_WithClosedTender_ThrowsInvalidOperationException()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var bidderId = Guid.NewGuid();

        var tender = CreateTestTender(tenderId, TenderStatus.Evaluation); // Not Active
        SetupTendersDbSet(new List<Tender> { tender });
        SetupBiddersDbSet(new List<Bidder>());
        SetupTenderBiddersDbSet(new List<TenderBidder>());
        SetupBidSubmissionsDbSet(new List<BidSubmission>());

        var command = new SubmitBidCommand
        {
            TenderId = tenderId,
            BidderId = bidderId,
            BidValidityDays = 90
        };

        // Act
        var act = async () => await _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<InvalidOperationException>()
            .WithMessage("*not accepting bid submissions*");
    }

    [Fact]
    public async Task Handle_WithNonExistentBidder_ThrowsNotFoundException()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var bidderId = Guid.NewGuid();

        var tender = CreateTestTender(tenderId, TenderStatus.Active);
        SetupTendersDbSet(new List<Tender> { tender });
        SetupBiddersDbSet(new List<Bidder>()); // No bidders
        SetupTenderBiddersDbSet(new List<TenderBidder>());
        SetupBidSubmissionsDbSet(new List<BidSubmission>());

        var command = new SubmitBidCommand
        {
            TenderId = tenderId,
            BidderId = bidderId,
            BidValidityDays = 90
        };

        // Act
        var act = async () => await _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<NotFoundException>()
            .WithMessage("*Bidder*");
    }

    [Fact]
    public async Task Handle_SetsStatusToSubmitted()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var bidderId = Guid.NewGuid();
        var bidSubmission = SetupValidSubmissionScenario(tenderId, bidderId);

        var command = new SubmitBidCommand
        {
            TenderId = tenderId,
            BidderId = bidderId,
            BidValidityDays = 90
        };

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        bidSubmission.Status.Should().Be(BidSubmissionStatus.Submitted);
    }

    [Fact]
    public async Task Handle_SetsSubmittedAtTimestamp()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var bidderId = Guid.NewGuid();
        var bidSubmission = SetupValidSubmissionScenario(tenderId, bidderId);

        var command = new SubmitBidCommand
        {
            TenderId = tenderId,
            BidderId = bidderId,
            BidValidityDays = 90
        };

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        bidSubmission.SubmissionTime.Should().Be(_fixedUtcNow);
    }

    [Fact]
    public async Task Handle_WithExistingSubmittedBid_ThrowsInvalidOperationException()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var bidderId = Guid.NewGuid();
        var bidSubmissionId = Guid.NewGuid();

        var tender = CreateTestTender(tenderId, TenderStatus.Active);
        var bidder = CreateTestBidder(bidderId);
        var tenderBidder = CreateTestTenderBidder(tenderId, bidderId);

        // Create a pending bid submission (ReceiptNumber = "")
        var pendingBid = CreateTestBidSubmission(bidSubmissionId, tenderId, bidderId);

        // Also create an already-submitted bid (ReceiptNumber != "")
        var submittedBid = new BidSubmission
        {
            Id = Guid.NewGuid(),
            TenderId = tenderId,
            BidderId = bidderId,
            ReceiptNumber = "REC-EXISTING-0001",
            Status = BidSubmissionStatus.Submitted,
            BidDocuments = CreateRequiredDocuments(),
            CreatedAt = DateTime.UtcNow
        };

        SetupTendersDbSet(new List<Tender> { tender });
        SetupBiddersDbSet(new List<Bidder> { bidder });
        SetupTenderBiddersDbSet(new List<TenderBidder> { tenderBidder });
        SetupBidSubmissionsDbSet(new List<BidSubmission> { pendingBid, submittedBid });

        var command = new SubmitBidCommand
        {
            TenderId = tenderId,
            BidderId = bidderId,
            BidValidityDays = 90
        };

        // Act
        var act = async () => await _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<InvalidOperationException>()
            .WithMessage("*already been submitted*");
    }

    [Fact]
    public async Task Handle_WithPastDeadline_SetsIsLateToTrue()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var bidderId = Guid.NewGuid();

        // Set submission deadline to before our fixed time
        var pastDeadline = _fixedUtcNow.AddHours(-1);
        var bidSubmission = SetupValidSubmissionScenario(tenderId, bidderId, submissionDeadline: pastDeadline);

        var command = new SubmitBidCommand
        {
            TenderId = tenderId,
            BidderId = bidderId,
            BidValidityDays = 90
        };

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.IsLate.Should().BeTrue();
        bidSubmission.IsLate.Should().BeTrue();
        result.Message.Should().Contain("LATE");
    }

    [Fact]
    public async Task Handle_CallsSaveChangesAsync()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var bidderId = Guid.NewGuid();
        SetupValidSubmissionScenario(tenderId, bidderId);

        var command = new SubmitBidCommand
        {
            TenderId = tenderId,
            BidderId = bidderId,
            BidValidityDays = 90
        };

        // Act
        await _handler.Handle(command, CancellationToken.None);

        // Assert
        // Called at least twice: once after updating submission, once after storing receipt PDF path
        _contextMock.Verify(x => x.SaveChangesAsync(It.IsAny<CancellationToken>()), Times.AtLeast(2));
    }

    [Fact]
    public async Task Handle_ReturnsBidSubmissionDto()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var bidderId = Guid.NewGuid();
        SetupValidSubmissionScenario(tenderId, bidderId);

        var command = new SubmitBidCommand
        {
            TenderId = tenderId,
            BidderId = bidderId,
            BidValidityDays = 90
        };

        // Act
        var result = await _handler.Handle(command, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.Should().BeOfType<SubmitBidResultDto>();
        result.BidId.Should().NotBeEmpty();
        result.Receipt.Should().NotBeNull();
        result.Receipt.TenderId.Should().Be(tenderId);
        result.Receipt.ReceiptNumber.Should().StartWith("REC-");
        result.Receipt.BidderCompanyName.Should().NotBeNullOrEmpty();
        result.Receipt.Files.Should().NotBeEmpty();
    }

    [Fact]
    public async Task Handle_WithNonInvitedBidder_ThrowsInvalidOperationException()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var bidderId = Guid.NewGuid();

        var tender = CreateTestTender(tenderId, TenderStatus.Active);
        var bidder = CreateTestBidder(bidderId);

        SetupTendersDbSet(new List<Tender> { tender });
        SetupBiddersDbSet(new List<Bidder> { bidder });
        SetupTenderBiddersDbSet(new List<TenderBidder>()); // Not invited
        SetupBidSubmissionsDbSet(new List<BidSubmission>());

        var command = new SubmitBidCommand
        {
            TenderId = tenderId,
            BidderId = bidderId,
            BidValidityDays = 90
        };

        // Act
        var act = async () => await _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<InvalidOperationException>()
            .WithMessage("*not invited*");
    }

    [Fact]
    public async Task Handle_WithMissingRequiredDocuments_ThrowsInvalidOperationException()
    {
        // Arrange
        var tenderId = Guid.NewGuid();
        var bidderId = Guid.NewGuid();
        var bidSubmissionId = Guid.NewGuid();

        var tender = CreateTestTender(tenderId, TenderStatus.Active);
        var bidder = CreateTestBidder(bidderId);
        var tenderBidder = CreateTestTenderBidder(tenderId, bidderId);

        // Create bid with only partial documents (missing required ones)
        var incompleteDocuments = new List<BidDocument>
        {
            new BidDocument
            {
                Id = Guid.NewGuid(),
                BidSubmissionId = bidSubmissionId,
                DocumentType = BidDocumentType.PricedBOQ,
                FileName = "boq.xlsx",
                FilePath = "/uploads/boq.xlsx",
                FileSizeBytes = 1024,
                ContentType = "application/xlsx",
                UploadedAt = DateTime.UtcNow,
                CreatedAt = DateTime.UtcNow
            }
            // Missing: Methodology, TeamCVs, Program, HSEPlan
        };

        var pendingBid = new BidSubmission
        {
            Id = bidSubmissionId,
            TenderId = tenderId,
            BidderId = bidderId,
            ReceiptNumber = string.Empty,
            BidDocuments = incompleteDocuments,
            CreatedAt = DateTime.UtcNow
        };

        SetupTendersDbSet(new List<Tender> { tender });
        SetupBiddersDbSet(new List<Bidder> { bidder });
        SetupTenderBiddersDbSet(new List<TenderBidder> { tenderBidder });
        SetupBidSubmissionsDbSet(new List<BidSubmission> { pendingBid });

        var command = new SubmitBidCommand
        {
            TenderId = tenderId,
            BidderId = bidderId,
            BidValidityDays = 90
        };

        // Act
        var act = async () => await _handler.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<InvalidOperationException>()
            .WithMessage("*Missing required documents*");
    }

    #region Helper Methods

    private static Tender CreateTestTender(Guid tenderId, TenderStatus status, DateTime? submissionDeadline = null)
    {
        return new Tender
        {
            Id = tenderId,
            Title = "Test Tender for Bidding",
            Reference = "TND-BID-001",
            ClientId = Guid.NewGuid(),
            Status = status,
            SubmissionDeadline = submissionDeadline ?? new DateTime(2025, 7, 1, 23, 59, 59, DateTimeKind.Utc),
            BaseCurrency = "AED",
            CreatedAt = DateTime.UtcNow
        };
    }

    private static Bidder CreateTestBidder(Guid bidderId)
    {
        return new Bidder
        {
            Id = bidderId,
            CompanyName = "Test Bidding Company",
            ContactPerson = "John Doe",
            Email = "bidder@testcompany.com",
            Phone = "+971501234567",
            IsActive = true,
            CreatedAt = DateTime.UtcNow
        };
    }

    private static TenderBidder CreateTestTenderBidder(Guid tenderId, Guid bidderId)
    {
        return new TenderBidder
        {
            Id = Guid.NewGuid(),
            TenderId = tenderId,
            BidderId = bidderId,
            CreatedAt = DateTime.UtcNow
        };
    }

    private static List<BidDocument> CreateRequiredDocuments(Guid? bidSubmissionId = null)
    {
        var subId = bidSubmissionId ?? Guid.NewGuid();
        return new List<BidDocument>
        {
            new BidDocument
            {
                Id = Guid.NewGuid(),
                BidSubmissionId = subId,
                DocumentType = BidDocumentType.PricedBOQ,
                FileName = "priced-boq.xlsx",
                FilePath = "/uploads/priced-boq.xlsx",
                FileSizeBytes = 2048,
                ContentType = "application/xlsx",
                UploadedAt = DateTime.UtcNow,
                CreatedAt = DateTime.UtcNow
            },
            new BidDocument
            {
                Id = Guid.NewGuid(),
                BidSubmissionId = subId,
                DocumentType = BidDocumentType.Methodology,
                FileName = "methodology.pdf",
                FilePath = "/uploads/methodology.pdf",
                FileSizeBytes = 4096,
                ContentType = "application/pdf",
                UploadedAt = DateTime.UtcNow,
                CreatedAt = DateTime.UtcNow
            },
            new BidDocument
            {
                Id = Guid.NewGuid(),
                BidSubmissionId = subId,
                DocumentType = BidDocumentType.TeamCVs,
                FileName = "team-cvs.pdf",
                FilePath = "/uploads/team-cvs.pdf",
                FileSizeBytes = 8192,
                ContentType = "application/pdf",
                UploadedAt = DateTime.UtcNow,
                CreatedAt = DateTime.UtcNow
            },
            new BidDocument
            {
                Id = Guid.NewGuid(),
                BidSubmissionId = subId,
                DocumentType = BidDocumentType.Program,
                FileName = "program.pdf",
                FilePath = "/uploads/program.pdf",
                FileSizeBytes = 3072,
                ContentType = "application/pdf",
                UploadedAt = DateTime.UtcNow,
                CreatedAt = DateTime.UtcNow
            },
            new BidDocument
            {
                Id = Guid.NewGuid(),
                BidSubmissionId = subId,
                DocumentType = BidDocumentType.HSEPlan,
                FileName = "hse-plan.pdf",
                FilePath = "/uploads/hse-plan.pdf",
                FileSizeBytes = 5120,
                ContentType = "application/pdf",
                UploadedAt = DateTime.UtcNow,
                CreatedAt = DateTime.UtcNow
            }
        };
    }

    private static BidSubmission CreateTestBidSubmission(Guid bidSubmissionId, Guid tenderId, Guid bidderId)
    {
        var docs = CreateRequiredDocuments(bidSubmissionId);
        return new BidSubmission
        {
            Id = bidSubmissionId,
            TenderId = tenderId,
            BidderId = bidderId,
            ReceiptNumber = string.Empty, // Pending
            BidDocuments = docs,
            CreatedAt = DateTime.UtcNow
        };
    }

    /// <summary>
    /// Sets up a complete valid scenario for bid submission and returns the pending BidSubmission entity.
    /// </summary>
    private BidSubmission SetupValidSubmissionScenario(
        Guid tenderId,
        Guid bidderId,
        DateTime? submissionDeadline = null)
    {
        var tender = CreateTestTender(tenderId, TenderStatus.Active, submissionDeadline);
        var bidder = CreateTestBidder(bidderId);
        var tenderBidder = CreateTestTenderBidder(tenderId, bidderId);
        var bidSubmissionId = Guid.NewGuid();
        var pendingBid = CreateTestBidSubmission(bidSubmissionId, tenderId, bidderId);

        SetupTendersDbSet(new List<Tender> { tender });
        SetupBiddersDbSet(new List<Bidder> { bidder });
        SetupTenderBiddersDbSet(new List<TenderBidder> { tenderBidder });
        SetupBidSubmissionsDbSet(new List<BidSubmission> { pendingBid });

        return pendingBid;
    }

    private void SetupTendersDbSet(List<Tender> tenders)
    {
        var mockDbSet = tenders.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.Tenders).Returns(mockDbSet.Object);
    }

    private void SetupBiddersDbSet(List<Bidder> bidders)
    {
        var mockDbSet = bidders.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.Bidders).Returns(mockDbSet.Object);
    }

    private void SetupTenderBiddersDbSet(List<TenderBidder> tenderBidders)
    {
        var mockDbSet = tenderBidders.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.TenderBidders).Returns(mockDbSet.Object);
    }

    private void SetupBidSubmissionsDbSet(List<BidSubmission> bidSubmissions)
    {
        var mockDbSet = bidSubmissions.AsQueryable().BuildMockDbSet();
        _contextMock.Setup(x => x.BidSubmissions).Returns(mockDbSet.Object);
    }

    #endregion
}
