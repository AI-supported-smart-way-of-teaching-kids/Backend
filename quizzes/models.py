# =========================
# Imports
# =========================
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from lessons.models import Lesson
from profiles.models import ChildProfile


# =========================
# Quiz
# =========================
class Quiz(models.Model):
    """Group of questions for a lesson"""

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.PROTECT,
        related_name="quizzes",
    )

    title = models.CharField(max_length=200)

    time_limit_seconds = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(30)],
        help_text="Optional time limit in seconds",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "quizzes_quiz"
        ordering = ["created_at"]
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return f"{self.title} ({self.lesson.title})"


# =========================
# Question
# =========================
class Question(models.Model):
    """Single quiz question (text / image / audio)"""

    class QuestionType(models.TextChoices):
        TEXT = "text", "Text"
        IMAGE = "image", "Image"
        AUDIO = "audio", "Audio"

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    question_type = models.CharField(
        max_length=10,
        choices=QuestionType.choices,
        default=QuestionType.TEXT,
    )

    question_text = models.TextField()

    media_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
    )

    options = models.JSONField(
        default=list,
        help_text="List of answer choices",
    )

    correct_option_index = models.SmallIntegerField(
        validators=[MinValueValidator(0)],
    )

    explanation = models.TextField(
        null=True,
        blank=True,
    )

    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "quizzes_question"
        ordering = ["order"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(correct_option_index__gte=0),
                name="correct_option_index_non_negative",
            )
        ]

    def __str__(self):
        preview = self.question_text[:40]
        return f"Q{self.order}: {preview}"

    # -------------------------
    # Validation
    # -------------------------
    def clean(self):
        from django.core.exceptions import ValidationError

        if not isinstance(self.options, (list, tuple)):
            raise ValidationError("Options must be a list.")

        option_count = len(self.options)

        if option_count < 2:
            raise ValidationError("At least 2 options required.")

        if option_count > 4:
            raise ValidationError("Maximum 4 options allowed.")

        if self.correct_option_index >= option_count:
            raise ValidationError("Correct option index is out of range.")

        if (
            self.question_type in {self.QuestionType.IMAGE, self.QuestionType.AUDIO}
            and not self.media_url
        ):
            raise ValidationError("Media URL is required for this question type.")


# =========================
# Quiz Attempt
# =========================
class QuizAttempt(models.Model):
    """One quiz attempt by a child"""

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        ABANDONED = "abandoned", "Abandoned"

    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.PROTECT,
        related_name="quiz_attempts",
    )

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.PROTECT,
        related_name="attempts",
    )

    answers = models.JSONField(default=list)

    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )

    duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
    )

    correct_count = models.PositiveSmallIntegerField(default=0)
    total_questions = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "quizzes_quizattempt"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["child", "created_at"]),
            models.Index(fields=["quiz", "created_at"]),
        ]

    def __str__(self):
        nickname = getattr(self.child, "nickname", "Child")
        return f"{nickname} – {self.quiz.title} – {self.score}%"

    # -------------------------
    # Scoring Logic
    # -------------------------
    def calculate_score(self) -> Decimal:
        if not self.answers:
            return Decimal("0.00")

        question_map = {q.id: q for q in self.quiz.questions.all()}

        earned = 0
        total = 0

        for answer in self.answers:
            question = question_map.get(answer.get("question_id"))
            if not question:
                continue

            total += 1
            selected = answer.get("selected_indices", [])

            if len(selected) == 1 and int(selected[0]) == question.correct_option_index:
                earned += 1

        self.correct_count = earned
        self.total_questions = total

        if total == 0:
            return Decimal("0.00")

        percent = (Decimal(earned) / Decimal(total)) * 100
        return percent.quantize(Decimal("0.01"))

    # -------------------------
    # Finalization
    # -------------------------
    def complete_attempt(self):
        if self.status == self.Status.COMPLETED:
            return

        self.score = self.calculate_score()
        self.completed_at = timezone.now()

        if self.created_at:
            self.duration_seconds = int(
                (self.completed_at - self.created_at).total_seconds()
            )

        if self.total_questions == 0:
            self.status = self.Status.ABANDONED
        else:
            self.status = self.Status.COMPLETED

        self.save()
