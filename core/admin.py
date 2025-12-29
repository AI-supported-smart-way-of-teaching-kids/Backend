from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin configuration for security and system audit logs."""

    # Columns to display in the list view
    list_display = (
        "created_at",
        "user",
        "action",
        "resource_id",
        "meta_summary",
    )

    # Filters to easily narrow down logs
    list_filter = (
        "action",
        "user",
        "created_at",
    )

    # Search fields for quick lookup
    search_fields = (
        "user__username",
        "action",
        "resource_id",
        "meta",
    )

    # Fields that are read-only (logs should not be editable)
    readonly_fields = (
        "user",
        "action",
        "resource_id",
        "meta",
        "created_at",
    )

    # Default ordering
    ordering = ("-created_at",)

    # Field grouping in detail view
    fieldsets = (
        (None, {"fields": ("user", "action", "resource_id")}),
        ("Details", {"fields": ("meta",)}),
        ("Timestamps", {"fields": ("created_at",)}),
    )

    # ================================
    # Helper methods
    # ================================
    def meta_summary(self, obj):
        """Show a brief summary of the meta JSON field in list display."""
        if obj.meta:
            # Limit to 50 characters for compact display
            return str(obj.meta)[:50] + ("..." if len(str(obj.meta)) > 50 else "")
        return "-"

    meta_summary.short_description = "Meta"
