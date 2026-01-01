from django.contrib import admin
from .models import (
    LessonInteractionsRaw,
    LessonInteractionsClean,
    QuizAttemptsRaw,
    QuizAttemptsClean,
    ProgressRaw,
    ProgressClean,
    LessonFeatures,
    QuizFeatures,
    ProgressLabeled,
    StudentMLDataset,
)

# --- 1. RAW DATA (The Ingested Logs) ---


@admin.register(LessonInteractionsRaw)
class LessonInteractionsRawAdmin(admin.ModelAdmin):
    list_display = ("ml_student_id", "lesson_id", "time_spent", "received_at")
    list_filter = ("received_at", "completion_status")
    search_fields = ("ml_student_id", "lesson_id")
    readonly_fields = ("received_at",)


@admin.register(QuizAttemptsRaw)
class QuizAttemptsRawAdmin(admin.ModelAdmin):
    list_display = (
        "ml_student_id",
        "lesson_id",
        "score",
        "attempt_number",
        "received_at",
    )
    list_filter = ("received_at", "attempt_number")
    readonly_fields = ("received_at",)


@admin.register(ProgressRaw)
class ProgressRawAdmin(admin.ModelAdmin):
    list_display = ("ml_student_id", "streak_days", "lessons_completed", "received_at")
    readonly_fields = ("received_at",)


# --- 2. CLEANED DATA (The Sanitized Records) ---


@admin.register(LessonInteractionsClean)
class LessonInteractionsCleanAdmin(admin.ModelAdmin):
    list_display = ("ml_student_id", "lesson_id", "cleaned_at")
    list_filter = ("cleaned_at",)
    readonly_fields = ("cleaned_at",)


@admin.register(QuizAttemptsClean)
class QuizAttemptsCleanAdmin(admin.ModelAdmin):
    list_display = ("ml_student_id", "score", "cleaned_at")
    readonly_fields = ("cleaned_at",)


@admin.register(ProgressClean)
class ProgressCleanAdmin(admin.ModelAdmin):
    list_display = ("ml_student_id", "topic_mastery", "cleaned_at")
    readonly_fields = ("cleaned_at",)


# --- 3. FEATURES (The Pre-computed Math) ---


@admin.register(LessonFeatures)
class LessonFeaturesAdmin(admin.ModelAdmin):
    list_display = ("ml_student_id", "avg_time_spent", "completion_rate", "computed_at")
    readonly_fields = ("computed_at",)


@admin.register(QuizFeatures)
class QuizFeaturesAdmin(admin.ModelAdmin):
    list_display = ("ml_student_id", "avg_score", "avg_response_time", "computed_at")
    readonly_fields = ("computed_at",)


# --- 4. TARGETS & DATASETS (Final Training Prep) ---


@admin.register(ProgressLabeled)
class ProgressLabeledAdmin(admin.ModelAdmin):
    list_display = ("ml_student_id", "mastery_level", "computed_at")
    list_filter = ("mastery_level", "computed_at")
    readonly_fields = ("computed_at",)


@admin.register(StudentMLDataset)
class StudentMLDatasetAdmin(admin.ModelAdmin):
    list_display = ("student_id", "mastery_level", "snapshot_date")
    list_filter = ("mastery_level", "snapshot_date")
    search_fields = ("student_id",)
    readonly_fields = ("snapshot_date",)
