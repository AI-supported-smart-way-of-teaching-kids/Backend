from django.contrib import admin
# from django.utils.timezone import localtime

from .models import (
    MLModel,
    MLStudentMap,
    LessonInteractionsRaw,
    QuizAttemptsRaw,
    ProgressRaw,
    LessonInteractionsClean,
    QuizAttemptsClean,
    ProgressClean,
    LessonFeatures,
    QuizFeatures,
    ProgressLabeled,
    StudentMLDataset,
    Recommendation,
)

# ==============================================================================
# 1. MODEL CONFIGURATION
# ==============================================================================


@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "version",
        "file_path",
        "created_at",
    )
    list_filter = ("name",)
    search_fields = ("name", "version")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)


@admin.register(MLStudentMap)
class MLStudentMapAdmin(admin.ModelAdmin):
    list_display = (
        "ml_student_id",
        "child",
        "student_uuid",
        "mapped_at",
    )
    search_fields = (
        "ml_student_id",
        "student_uuid",
        "child__nickname",
    )
    ordering = ("-mapped_at",)
    readonly_fields = ("mapped_at",)


# ==============================================================================
# 2. RAW DATA (READ-ONLY)
# ==============================================================================


class ReadOnlyAdmin(admin.ModelAdmin):
    """Base admin class for append-only ML tables."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LessonInteractionsRaw)
class LessonInteractionsRawAdmin(ReadOnlyAdmin):
    list_display = (
        "id",
        "ml_student_id",
        "lesson_id",
        "time_spent",
        "video_watch_percentage",
        "completion_status",
        "received_at",
    )
    list_filter = ("completion_status",)
    search_fields = ("ml_student_id", "lesson_id")
    ordering = ("-received_at",)


@admin.register(QuizAttemptsRaw)
class QuizAttemptsRawAdmin(ReadOnlyAdmin):
    list_display = (
        "id",
        "ml_student_id",
        "lesson_id",
        "attempt_number",
        "score",
        "received_at",
    )
    search_fields = ("ml_student_id", "lesson_id")
    ordering = ("-received_at",)


@admin.register(ProgressRaw)
class ProgressRawAdmin(ReadOnlyAdmin):
    list_display = (
        "id",
        "ml_student_id",
        "lessons_completed",
        "badges_earned",
        "streak_days",
        "received_at",
    )
    ordering = ("-received_at",)


# ==============================================================================
# 3. CLEANED DATA (READ-ONLY)
# ==============================================================================


@admin.register(LessonInteractionsClean)
class LessonInteractionsCleanAdmin(ReadOnlyAdmin):
    list_display = (
        "id",
        "ml_student_id",
        "lesson_id",
        "time_spent",
        "video_watch_percentage",
        "completion_status",
        "cleaned_at",
    )
    ordering = ("-cleaned_at",)


@admin.register(QuizAttemptsClean)
class QuizAttemptsCleanAdmin(ReadOnlyAdmin):
    list_display = (
        "id",
        "ml_student_id",
        "lesson_id",
        "attempt_number",
        "score",
        "cleaned_at",
    )
    ordering = ("-cleaned_at",)


@admin.register(ProgressClean)
class ProgressCleanAdmin(ReadOnlyAdmin):
    list_display = (
        "id",
        "ml_student_id",
        "lessons_completed",
        "badges_earned",
        "streak_days",
        "topic_mastery",
        "cleaned_at",
    )
    ordering = ("-cleaned_at",)


# ==============================================================================
# 4. FEATURE TABLES
# ==============================================================================


@admin.register(LessonFeatures)
class LessonFeaturesAdmin(ReadOnlyAdmin):
    list_display = (
        "id",
        "ml_student_id",
        "avg_time_spent",
        "avg_video_watch",
        "completion_rate",
        "computed_at",
    )
    ordering = ("-computed_at",)


@admin.register(QuizFeatures)
class QuizFeaturesAdmin(ReadOnlyAdmin):
    list_display = (
        "id",
        "ml_student_id",
        "avg_score",
        "avg_wrong_questions",
        "avg_response_time",
        "computed_at",
    )
    ordering = ("-computed_at",)


@admin.register(ProgressLabeled)
class ProgressLabeledAdmin(ReadOnlyAdmin):
    list_display = (
        "id",
        "ml_student_id",
        "topic_mastery",
        "mastery_level",
        "computed_at",
    )
    list_filter = ("mastery_level",)
    ordering = ("-computed_at",)


@admin.register(StudentMLDataset)
class StudentMLDatasetAdmin(ReadOnlyAdmin):
    list_display = (
        "student_id",
        "child",
        "mastery_level",
        "snapshot_date",
    )
    list_filter = ("mastery_level", "snapshot_date")
    search_fields = ("student_id", "child__nickname")
    ordering = ("-snapshot_date",)


# ==============================================================================
# 5. AI OUTPUTS
# ==============================================================================


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = (
        "child",
        "lesson",
        "confidence_score",
        "model",
        "generated_at",
    )
    list_filter = ("model",)
    search_fields = (
        "child__nickname",
        "lesson__title",
    )
    ordering = ("-confidence_score",)
    readonly_fields = ("generated_at",)
