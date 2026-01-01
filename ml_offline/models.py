"""
Offline ML models: Raw, Cleaned, Features, and Dataset for training/EDA.
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from ai.models import BaseInteractionModel


# ==============================================================================
# 1. RAW EVENTS
# ==============================================================================

class LessonInteractionsRaw(BaseInteractionModel):
    """Append-only raw lesson interaction events."""

    lesson_id = models.IntegerField(help_text="Lesson ID from lessons_lesson table")
    time_spent = models.FloatField(help_text="Time spent on lesson (minutes)")
    video_watch_percentage = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(150)],
        help_text="Raw video watch percentage (0-150)"
    )
    number_of_clicks = models.IntegerField(help_text="Number of clicks/interactions")
    completion_status = models.BooleanField(help_text="Whether lesson was completed")
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_lesson_interactions_raw"
        indexes = [
            models.Index(fields=["ml_student_id", "received_at"]),
            models.Index(fields=["lesson_id", "received_at"]),
            models.Index(fields=["received_at"])
        ]


class QuizAttemptsRaw(BaseInteractionModel):
    """Unprocessed quiz attempts with raw scores and behavior."""

    lesson_id = models.IntegerField(help_text="Lesson ID linked to this quiz")
    attempt_number = models.IntegerField(help_text="Attempt number (1st, 2nd, etc.)")
    score = models.FloatField(help_text="Raw numerical score")
    wrong_questions = models.IntegerField(help_text="Count of incorrect answers")
    response_time = models.FloatField(help_text="Total time in seconds")
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_quiz_attempts_raw"
        indexes = [
            models.Index(fields=["ml_student_id", "lesson_id"]),
            models.Index(fields=["received_at"]),
            models.Index(fields=["lesson_id", "attempt_number"])
        ]


class ProgressRaw(BaseInteractionModel):
    """Daily snapshots of student progress before cleaning."""

    lessons_completed = models.IntegerField(help_text="Lessons completed today")
    badges_earned = models.IntegerField(help_text="Badges earned today")
    streak_days = models.IntegerField(help_text="Current login streak")
    topic_mastery = models.FloatField(help_text="Raw topic mastery score")
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_progress_raw"
        indexes = [
            models.Index(fields=["ml_student_id", "received_at"]),
            models.Index(fields=["received_at"])
        ]


# ==============================================================================
# 2. CLEANED DATA
# ==============================================================================

class LessonInteractionsClean(BaseInteractionModel):
    """Normalized and clipped lesson interaction data for ML training."""

    lesson_id = models.IntegerField(help_text="Lesson ID from lessons_lesson table")
    time_spent = models.FloatField(
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text="Clipped time spent (1-30 minutes)"
    )
    video_watch_percentage = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Clipped video watch percentage (0-100)"
    )
    number_of_clicks = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of clicks (>=0)"
    )
    completion_status = models.BooleanField(help_text="Completion status")
    cleaned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_lesson_interactions_clean"
        indexes = [
            models.Index(fields=["child", "lesson_id"]),
            models.Index(fields=["cleaned_at"])
        ]


class QuizAttemptsClean(BaseInteractionModel):
    """Sanitized quiz attempts for ML training."""

    lesson_id = models.IntegerField(help_text="Lesson ID from lessons_lesson table")
    attempt_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="Attempt number clipped (max 3)"
    )
    score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Normalized score (0-100)"
    )
    wrong_questions = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="Validated wrong questions (0-4)"
    )
    response_time = models.FloatField(
        validators=[MinValueValidator(5), MaxValueValidator(150)],
        help_text="Response time clipped (5-150s)"
    )
    cleaned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_quiz_attempts_clean"
        indexes = [
            models.Index(fields=["child", "lesson_id"]),
            models.Index(fields=["cleaned_at"])
        ]


class ProgressClean(BaseInteractionModel):
    """Sanitized student progress data."""

    lessons_completed = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Validated lesson count"
    )
    badges_earned = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(12)],
        help_text="Badges clipped to max system limit (0-12)"
    )
    streak_days = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Login streak clipped (0-50)"
    )
    topic_mastery = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Mastery score normalized (0-100)"
    )
    cleaned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_progress_clean"
        indexes = [
            models.Index(fields=["cleaned_at"])
        ]


# ==============================================================================
# 3. FEATURES
# ==============================================================================

class LessonFeatures(BaseInteractionModel):
    """Aggregated lesson-level features per student."""

    avg_time_spent = models.FloatField(help_text="Average time spent per lesson")
    avg_video_watch = models.FloatField(help_text="Average video watch percentage")
    avg_clicks = models.FloatField(help_text="Average clicks per lesson")
    completion_rate = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Lesson completion rate (0-1)"
    )
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_lesson_features"
        verbose_name_plural = "Lesson Features"
        indexes = [
            models.Index(fields=["computed_at"])
        ]


class QuizFeatures(BaseInteractionModel):
    """Aggregated quiz-level features per student."""

    avg_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Average quiz score"
    )
    avg_wrong_questions = models.FloatField(help_text="Average wrong questions per quiz")
    avg_response_time = models.FloatField(help_text="Average response time per quiz")
    avg_attempt_number = models.FloatField(help_text="Average attempt number per quiz")
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_quiz_features"
        verbose_name_plural = "Quiz Features"
        indexes = [
            models.Index(fields=["computed_at"])
        ]


class ProgressLabeled(BaseInteractionModel):
    """Labeled student progress (target for supervised learning)."""

    class MasteryLevel(models.TextChoices):
        LOW = "Low", "Low"
        MEDIUM = "Medium", "Medium"
        HIGH = "High", "High"

    lessons_completed = models.IntegerField(help_text="Number of lessons completed")
    badges_earned = models.IntegerField(help_text="Number of badges earned")
    streak_days = models.IntegerField(help_text="Current streak")
    topic_mastery = models.FloatField(help_text="Topic mastery score (0-100)")
    mastery_level = models.CharField(
        max_length=10,
        choices=MasteryLevel.choices,
        help_text="Mastery level classification"
    )
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_progress_labeled"
        verbose_name_plural = "Progress labeled"
        indexes = [
            models.Index(fields=["mastery_level", "computed_at"])
        ]


# ==============================================================================
# 4. FINAL ML DATASET
# ==============================================================================

class StudentMLDataset(models.Model):
    """Final aggregated dataset for ML training."""

    student_id = models.IntegerField(primary_key=True, help_text="ML internal student ID")
    child = models.ForeignKey(
        "profiles.ChildProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Backend Child reference"
    )

    # Lesson features
    avg_time_spent = models.FloatField(help_text="Average time spent per lesson")
    avg_video_watch = models.FloatField(help_text="Average video watch percentage")
    avg_clicks = models.FloatField(help_text="Average clicks per lesson")
    completion_rate = models.FloatField(help_text="Lesson completion rate (0-1)")

    # Quiz features
    avg_score = models.FloatField(help_text="Average quiz score")
    avg_wrong_questions = models.FloatField(help_text="Average wrong questions")
    avg_response_time = models.FloatField(help_text="Average response time")
    avg_attempt_number = models.FloatField(help_text="Average attempt number")

    # Progress features
    lessons_completed = models.IntegerField(help_text="Lessons completed")
    badges_earned = models.IntegerField(help_text="Badges earned")
    streak_days = models.IntegerField(help_text="Current streak days")
    topic_mastery = models.FloatField(help_text="Topic mastery score (0-100)")

    # Target
    MASTERY_LEVEL_CHOICES = [("Low", "Low"), ("Medium", "Medium"), ("High", "High")]
    mastery_level = models.CharField(max_length=10, choices=MASTERY_LEVEL_CHOICES, help_text="Target classification")
    snapshot_date = models.DateField(auto_now_add=True, help_text="Snapshot creation date")

    class Meta:
        db_table = "ml_student_ml_dataset"
        indexes = [
            models.Index(fields=["snapshot_date"]),
            models.Index(fields=["mastery_level"])
        ]
