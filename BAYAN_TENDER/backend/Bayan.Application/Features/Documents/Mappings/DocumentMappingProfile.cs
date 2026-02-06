using AutoMapper;
using Bayan.Application.Features.Documents.DTOs;
using Bayan.Domain.Entities;

namespace Bayan.Application.Features.Documents.Mappings;

/// <summary>
/// AutoMapper profile for Document entity mappings.
/// </summary>
public class DocumentMappingProfile : Profile
{
    public DocumentMappingProfile()
    {
        CreateMap<Document, DocumentDto>()
            .ForMember(dest => dest.Name, opt => opt.MapFrom(src => src.FileName))
            .ForMember(dest => dest.Folder, opt => opt.MapFrom(src => src.FolderPath))
            .ForMember(dest => dest.Size, opt => opt.MapFrom(src => src.FileSizeBytes))
            .ForMember(dest => dest.SizeFormatted, opt => opt.MapFrom(src => FormatFileSize(src.FileSizeBytes)))
            .ForMember(dest => dest.UploadedAt, opt => opt.MapFrom(src => src.CreatedAt))
            .ForMember(dest => dest.UploadedByName, opt => opt.MapFrom(src =>
                src.Uploader != null ? $"{src.Uploader.FirstName} {src.Uploader.LastName}" : "Unknown"));
    }

    /// <summary>
    /// Formats file size in human-readable format.
    /// </summary>
    private static string FormatFileSize(long bytes)
    {
        string[] sizes = { "B", "KB", "MB", "GB", "TB" };
        int order = 0;
        double size = bytes;

        while (size >= 1024 && order < sizes.Length - 1)
        {
            order++;
            size /= 1024;
        }

        return $"{size:0.##} {sizes[order]}";
    }
}
