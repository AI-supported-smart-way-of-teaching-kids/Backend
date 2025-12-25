from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from lessons.models import lesson


class Quiz(models.Model):
    """Group of questions for a lesson"""

    lesson = models.ForeignKey(
        lesson,
        on_delete=models.PROTECT,
        related_name="quizzes",
        help_text="Associated lesson",
    )
    title = models.CharField(max_length=200, help_text="Quiz title")
    time_limit_seconds = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(30)],
        help_text="Time limit in seconds (optional)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "quizzes_quiz"
        verbose_name_plural = "Quizzes"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.title} - {self.lesson.title}"


class Question(models.Model):
    """One question + options"""

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
        help_text="Parent quiz",
    )
    question_text = models.TextField(help_text="The question text")
    options = models.JSONField(default=list, help_text="List of answer options")
    correct_option_index = models.SmallIntegerField(
        validators=[MinValueValidator(0)],
        help_text="Index of correct option in options list",
    )
    explanation = models.TextField(
        null=True, blank=True, help_text="Explanation of correct answer"
    )
    order = models.SmallIntegerField(default=0, help_text="Display order within quiz")

    class Meta:
        db_table = "quizzes_question"
        ordering = ["order"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(correct_option_index__gte=0),
                name="correct_option_index_non_negative",
            )
        ]

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."


class QuizAttempt(models.Model):
    """Child's attempt (append-only)"""

    child = models.ForeignKey(
        "profiles.ChildProfile",
        on_delete=models.PROTECT,
        related_name="quiz_attempts",
        help_text="Child who attempted the quiz",
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.PROTECT,
        related_name="attempts",
        help_text="Quiz attempted",
    )
    answers = models.JSONField(
        default=list, help_text="Selected indices for each question"
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Score achieved",
    )
    max_score = models.IntegerField(default=100, help_text="Maximum possible score")
    duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Time taken to complete (seconds)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True, blank=True, help_text="When the attempt was completed"
    )

    class Meta:
        db_table = "quizzes_quizattempt"
        indexes = [
            models.Index(fields=["child", "created_at"]),
            models.Index(fields=["quiz", "created_at"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.child.user.username} - {self.quiz.title} - {self.score}"
