from django.contrib import admin

# from django.utils.html import format_html
from django.db.models.aggregates import Count

from .models import Question, Quiz, QuizAttempt

# ==============================================================================
# Question Inline (inside Quiz)
# ==============================================================================


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    ordering = ("order",)
    fields = (
        "order",
        "question_type",
        "question_text",
        "media_url",
        "options",
        "correct_option_index",
    )


# ==============================================================================
# Quiz Admin
# ==============================================================================


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "lesson",
        "question_count",
        "time_limit_seconds",
        "created_at",
    )
    list_filter = ("lesson", "created_at")
    search_fields = ("title", "lesson__title")
    ordering = ("-created_at",)
    inlines = [QuestionInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(question_count=Count("questions"))

    @admin.display(ordering="question_count", description="Questions")
    def question_count(self, obj):
        return obj.question_count

    question_count.short_description = "Questions"


# ==============================================================================
# Question Admin
# ==============================================================================


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "quiz",
        "media_url",
        "question_type",
        "short_question",
        "correct_option_index",
    )
    list_filter = ("quiz", "question_type")
    search_fields = ("question_text",)
    ordering = ("quiz", "order")

    @admin.display(description="Question")
    def short_question(self, obj):
        return obj.question_text[:60]

    short_question.short_description = "Question"


# ==============================================================================
# Quiz Attempt Admin (Read-only)
# ==============================================================================


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "child",
        "quiz",
        "score",
        "status",
        "correct_count",
        "total_questions",
        "created_at",
        "completed_at",
    )
    list_filter = (
        "status",
        "quiz",
        "created_at",
    )
    search_fields = (
        "child__nickname",
        "quiz__title",
    )
    ordering = ("-created_at",)

    readonly_fields = (
        "child",
        "quiz",
        "answers",
        "score",
        "status",
        "duration_seconds",
        "correct_count",
        "total_questions",
        "created_at",
        "completed_at",
    )

    fieldsets = (
        (
            "Attempt Info",
            {
                "fields": (
                    "child",
                    "quiz",
                    "status",
                    "score",
                )
            },
        ),
        (
            "Results",
            {
                "fields": (
                    "correct_count",
                    "total_questions",
                    "duration_seconds",
                )
            },
        ),
        (
            "Answers",
            {
                "fields": ("answers",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "completed_at",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of attempts."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of attempt history."""
        return False
