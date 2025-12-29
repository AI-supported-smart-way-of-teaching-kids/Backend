from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, ChildProfile, TeacherProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # What shows in the user list
    list_display = (
        "email",
        "username",
        "role",
        "is_active",
        "is_staff",
    )

    # Filters on the right side
    list_filter = ("role", "is_active", "is_staff")

    # Search box
    search_fields = ("email", "username")

    ordering = ("email",)

    # User edit page layout
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Role & Profile", {"fields": ("role", "profile_picture_url")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    # User creation form layout
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2", "role"),
            },
        ),
    )

    filter_horizontal = ("groups", "user_permissions")


@admin.register(ChildProfile)
class ChildProfileAdmin(admin.ModelAdmin):
    list_display = (
        "nickname",
        "parent",
        "age",
        "learning_level",
        "created_at",
    )

    list_filter = ("learning_level", "age")

    search_fields = (
        "nickname",
        "parent__email",
        "parent__username",
    )

    readonly_fields = ("uuid", "created_at", "updated_at")


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "uploaded_count",
        "created_at",
    )

    search_fields = (
        "user__email",
        "user__username",
    )

    readonly_fields = ("created_at",)
