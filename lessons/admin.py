# ========================================
# Imports
# ========================================

from django.contrib import admin
from django.db.models.aggregates import Count
from django.urls import reverse
from django.utils.html import format_html, urlencode

from .models import Collection, Lesson, MediaUpload


# ========================================
# Inline Admins
# ========================================
class MediaUploadInline(admin.TabularInline):
    """Inline admin for MediaUpload under Lesson (only video files)."""

    model = MediaUpload
    extra = 0
    fields = (
        "file",
        "file_url",
        "file_type",
        "status",
        "created_at",
    )
    readonly_fields = ("created_at",)
    show_change_link = True

    def get_queryset(self, request):
        """Limit inline to video files only."""
        qs = super().get_queryset(request)
        return qs.filter(file_type__startswith="video/")


# ========================================
# Lesson Admin
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
        "collection_title",
        "created_at",
    )

    # Filters and search
    list_filter = ("difficulty", "is_published", "teacher", "collection")
    search_fields = ("title", "description", "teacher__user__username", "tags")

    # Slug, readonly, ordering
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "thumbnail_preview")
    ordering = ("-created_at",)

    # Inline
    inlines = [MediaUploadInline]

    # Admin actions
    actions = ["make_published", "make_unpublished"]
    list_select_related = ["teacher", "collection"]

    # Field grouping
    fieldsets = (
        (None, {"fields": ("title", "slug", "description", "collection")}),
        (
            "Media & Duration",
            {
                "fields": (
                    "video",
                    "video_url",
                    "thumbnail",
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
        """Show clickable thumbnail image in admin."""
        if obj.thumbnail:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" width="100" style="object-fit: cover; border-radius: 5px;" />'
                "</a>",
                obj.thumbnail.url,
                obj.thumbnail.url,
            )
        return "-"

    thumbnail_preview.short_description = "Thumbnail"

    @admin.display(description="Collection")
    def collection_title(self, obj):
        return obj.collection.title if obj.collection else "-"

    def teacher_name(self, obj):
        """Display teacher's username."""
        return obj.teacher.user.username if obj.teacher else "-"

    teacher_name.short_description = "Teacher"

    # ===============================
    # Admin actions
    # ===============================
    @admin.action(description="Publish selected lessons")
    def make_published(self, request, queryset):
        queryset.update(is_published=True)

    @admin.action(description="Unpublish selected lessons")
    def make_unpublished(self, request, queryset):
        queryset.update(is_published=False)


# ========================================
# MediaUpload Admin
# ========================================
@admin.register(MediaUpload)
class MediaUploadAdmin(admin.ModelAdmin):
    """Admin for MediaUpload model."""

    list_display = (
        "file_url",
        "file_type",
        "status",
        "uploader_name",
        "created_at",
    )
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


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("title", "lessons_count_link")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "description")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            lessons_count=Count("lessons")
        )  # 'lessons' = related_name in Lesson

    @admin.display(ordering="lessons_count", description="Number of Lessons")
    def lessons_count_link(self, obj):
        count = obj.lessons_count
        url = (
            reverse("admin:lessons_lesson_changelist")
            + "?"
            + urlencode({"collection__id": obj.id})
        )
        return format_html('<a href="{}">{}</a>', url, count)
