from django.contrib import admin
from django.utils.timezone import localtime

from .models import Badge, ChildBadge, Progress

# ==============================================================================
# Progress Admin
# ==============================================================================


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = (
        "child",
        "lesson",
        "status",
        "points_earned",
        "last_accessed_display",
        "completion_date_display",
    )

    list_filter = (
        "status",
        "lesson",
    )

    search_fields = (
        "child__nickname",
        "lesson__title",
    )

    ordering = (
        "child",
        "lesson",
    )

    readonly_fields = (
        "child",
        "lesson",
        "last_accessed",
        "completion_date",
    )

    fieldsets = (
        (
            "Progress Info",
            {
                "fields": (
                    "child",
                    "lesson",
                    "status",
                    "points_earned",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "last_accessed",
                    "completion_date",
                )
            },
        ),
    )

    def last_accessed_display(self, obj):
        return localtime(obj.last_accessed) if obj.last_accessed else "—"

    last_accessed_display.short_description = "Last Accessed"

    def completion_date_display(self, obj):
        return localtime(obj.completion_date) if obj.completion_date else "—"

    completion_date_display.short_description = "Completed At"


# ==============================================================================
# Badge Admin
# ==============================================================================


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "created_at",
        "awarded_count",
    )

    search_fields = ("name",)
    ordering = ("name",)

    def awarded_count(self, obj):
        return obj.awarded_to.count()

    awarded_count.short_description = "Times Awarded"


# ==============================================================================
# ChildBadge Admin (Read-only Award History)
# ==============================================================================


@admin.register(ChildBadge)
class ChildBadgeAdmin(admin.ModelAdmin):
    list_display = (
        "child",
        "badge",
        "awarded_at",
    )

    list_filter = (
        "badge",
        "awarded_at",
    )

    search_fields = (
        "child__nickname",
        "badge__name",
    )

    ordering = ("-awarded_at",)

    readonly_fields = (
        "child",
        "badge",
        "awarded_at",
    )

    fieldsets = (
        (
            "Badge Award",
            {
                "fields": (
                    "child",
                    "badge",
                )
            },
        ),
        (
            "Award Metadata",
            {
                "fields": ("awarded_at",),
            },
        ),
    )

    def has_add_permission(self, request):
        """
        Prevent manual badge awards from admin.
        Badges should be granted by business logic.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Prevent deletion of historical badge data.
        """
        return False
