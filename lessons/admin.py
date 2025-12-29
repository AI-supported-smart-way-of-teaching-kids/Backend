# ========================================
# Imports
# ========================================
from django.contrib import admin
from django.utils.html import format_html
from .models import Lesson, MediaUpload


# ========================================
# Inline Admins
# ========================================
class MediaUploadInline(admin.TabularInline):
    """Inline admin for MediaUpload under Lesson."""

    model = MediaUpload
    extra = 0
    fields = ("file_url", "file_type", "status", "created_at")
    readonly_fields = ("created_at",)
    show_change_link = True


# ========================================
# Main Admin Classes
# ========================================
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Admin configuration for Lesson model."""

    # Columns in list view
    list_display = (
        "title",
        "teacher_name",
        "difficulty",
        "is_published",
        "thumbnail_preview",
        "created_at",
    )
    list_filter = ("difficulty", "is_published", "teacher")
    search_fields = ("title", "description", "teacher__user__username", "tags")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "thumbnail_preview")
    ordering = ("-created_at",)
    inlines = [MediaUploadInline]

    # Field grouping
    fieldsets = (
        (None, {"fields": ("title", "slug", "description")}),
        (
            "Media & Duration",
            {
                "fields": (
                    "video_url",
                    "thumbnail_url",
                    "thumbnail_preview",
                    "duration_seconds",
                )
            },
        ),
        ("Classification", {"fields": ("difficulty", "tags", "is_published")}),
        ("Teacher", {"fields": ("teacher",)}),
        ("Timestamps", {"fields": ("created_at",)}),
    )

    # ===============================
    # Custom methods
    # ===============================
    def thumbnail_preview(self, obj):
        """Show thumbnail image in admin."""
        if obj.thumbnail_url:
            return format_html(
                '<img src="{}" width="100" style="object-fit: cover; border-radius: 5px;" />',
                obj.thumbnail_url,
            )
        return "-"

    thumbnail_preview.short_description = "Thumbnail"

    def teacher_name(self, obj):
        """Display teacher's username."""
        return obj.teacher.user.username if obj.teacher else "-"

    teacher_name.short_description = "Teacher"


@admin.register(MediaUpload)
class MediaUploadAdmin(admin.ModelAdmin):
    """Admin for MediaUpload model."""

    list_display = ("file_url", "file_type", "status", "uploader_name", "created_at")
    list_filter = ("status", "file_type")
    search_fields = ("file_url", "uploader__username")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    # ===============================
    # Custom methods
    # ===============================
    def uploader_name(self, obj):
        """Show uploader's username."""
        return obj.uploader.username if obj.uploader else "-"

    uploader_name.short_description = "Uploader"
