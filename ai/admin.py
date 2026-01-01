from django.contrib import admin
from .models import MLModel, MLStudentMap, Recommendation


@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = ("name", "version", "created_at", "file_path")
    search_fields = ("name", "version")
    readonly_fields = ("created_at",)


@admin.register(MLStudentMap)
class MLStudentMapAdmin(admin.ModelAdmin):
    list_display = ("ml_student_id", "child", "student_uuid", "mapped_at")
    search_fields = ("ml_student_id", "student_uuid")
    readonly_fields = ("mapped_at",)


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("child", "lesson", "confidence_score", "model", "generated_at")
    list_filter = ("model", "generated_at")
    search_fields = ("child__user__username", "lesson__title")
    readonly_fields = ("generated_at",)
