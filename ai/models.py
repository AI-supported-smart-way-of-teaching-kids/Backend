"""
Machine Learning Pipeline Models for Educational Platform.

This module implements a complete ETL pipeline for ML-driven educational
recommendations. Follows PEP8 standards with consistent stacked structure.
"""

import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from profiles.models import ChildProfile


# ==============================================================================
# 1. SYSTEM CONFIGURATION & MAPPING
# ==============================================================================


class MLModel(models.Model):
    """Metadata for AI model versions
               and artifact locations."""

    name = models.CharField(
        max_length=100,
        help_text="Model name"
    )
    version = models.CharField(
        max_length=50,
        help_text="Model version"
    )
    file_path = models.CharField(
        max_length=500,
        help_text="Artifact location"
    )
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Model metadata")
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "ml_mlmodel"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "version"], name="unique_model_version"
            )
        ]
        indexes = [
            models.Index(fields=["name", "version"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        """String representation of the model."""
        return f"{self.name} v{self.version}"


class MLStudentMap(models.Model):
    """Bridge table mapping ML internal IDs to backend ChildProfiles."""

    ml_student_id = models.IntegerField(
        primary_key=True,
        help_text="ML team's internal student ID"
    )
    student_uuid = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="UUID from User model (accounts.User.uuid)",
    )
    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ml_mappings",
        help_text="Django ChildProfile reference",
    )
    mapped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_mlstudentmap"
        indexes = [
            models.Index(fields=["student_uuid"]),
            models.Index(fields=["child"]),
            models.Index(fields=["mapped_at"]),
        ]

    def save(self, *args, **kwargs):
        """Populate student_uuid from related User or generate a new one."""
        if not self.student_uuid:
            # Prefer the ChildProfile's user.uuid if it exists
            if self.child and getattr(self.child, "user", None):
                user_uuid = getattr(self.child.user, "uuid", None)
                if user_uuid:
                    # Accepts either a UUID object or a string
                    self.student_uuid = user_uuid
                else:
                    # child.user exists but doesn't have uuid attribute
                    self.student_uuid = uuid.uuid4()
            else:
                # No child/user — generate an ML-side UUID
                self.student_uuid = uuid.uuid4()
        super().save(*args, **kwargs)

    def __str__(self):
        """String representation of the mapping."""
        if self.child and hasattr(self.child, "user"):
            return f"ML{self.ml_student_id} -> {self.child.user.username}"
        return f"ML{self.ml_student_id} -> No mapping"


# ==============================================================================
# 2. DATA PIPELINE (RAW EVENTS)
# ==============================================================================


class BaseInteractionModel(models.Model):
    """Abstract base to keep shared ML fields consistent."""

    ml_student_id = models.IntegerField(
        help_text="ML team's internal student ID"
    )
    student_uuid = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        help_text="UUID from accounts.User"
    )
    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="Django ChildProfile reference",
    )

    class Meta:
        abstract = True


class LessonInteractionsRaw(BaseInteractionModel):
    """Append-only raw interaction events."""

    lesson_id = models.IntegerField(
        help_text="Lesson ID from lessons_lesson table"
    )
    time_spent = models.FloatField(
        help_text="Time spent on lesson (minutes)"
    )
    video_watch_percentage = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(150)],
        help_text="Raw video watch percentage (0-150)",
    )
    number_of_clicks = models.IntegerField(
        help_text="Number of clicks/interactions"
    )
    completion_status = models.BooleanField(
        help_text="Whether lesson was completed"
    )
    received_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "ml_lesson_interactions_raw"
        indexes = [
            models.Index(fields=["ml_student_id", "received_at"]),
            models.Index(fields=["lesson_id", "received_at"]),
            models.Index(fields=["received_at"]),
        ]

    def __str__(self):
        """String representation of raw lesson interactions."""
        return (
            f"LessonInteractionsRaw {self.id}: "
            f"ML{self.ml_student_id} - Lesson {self.lesson_id}"
        )


class QuizAttemptsRaw(BaseInteractionModel):
    """Unprocessed quiz scores and behaviors."""

    lesson_id = models.IntegerField(
        help_text="Lesson ID linked to this quiz"
    )
    attempt_number = models.IntegerField(
        help_text="Ordinal attempt count (1st, 2nd, etc.)"
    )
    score = models.FloatField(
        help_text="Raw numerical score achieved"
    )
    wrong_questions = models.IntegerField(
        help_text="Count of incorrect answers"
    )
    response_time = models.FloatField(
        help_text="Total time taken in seconds"
    )
    received_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "ml_quiz_attempts_raw"
        indexes = [
            models.Index(fields=["ml_student_id", "lesson_id"]),
            models.Index(fields=["received_at"]),
            models.Index(fields=["lesson_id", "attempt_number"]),
        ]

    def __str__(self):
        """String representation of raw quiz attempts."""
        return (
            f"QuizAttemptsRaw {self.id}: "
            f"ML{self.ml_student_id} - Attempt {self.attempt_number}"
        )


class ProgressRaw(BaseInteractionModel):
    """Daily snapshots of a student's standing before sanitization."""

    lessons_completed = models.IntegerField(
        help_text="Total lessons finished recorded today"
    )
    badges_earned = models.IntegerField(
        help_text="Total badges unlocked recorded today"
    )
    streak_days = models.IntegerField(
        help_text="Current login streak in days"
    )
    topic_mastery = models.FloatField(
        help_text="Raw mastery score (unclipped)"
    )
    received_at = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp of log entry"
    )

    class Meta:
        db_table = "ml_progress_raw"
        indexes = [
            models.Index(fields=["ml_student_id", "received_at"]),
            models.Index(fields=["received_at"]),
        ]

    def __str__(self):
        """String representation of raw progress."""
        return (
            f"ProgressRaw {self.id}: "
            f"ML{self.ml_student_id} - {self.received_at.date()}"
        )


# ==============================================================================
# 3. DATA PIPELINE (CLEANED & AGGREGATED)
# ==============================================================================


class LessonInteractionsClean(BaseInteractionModel):
    """Clipped and normalized lesson data for ML training."""

    lesson_id = models.IntegerField(
        help_text="Lesson ID from lessons_lesson table"
    )
    time_spent = models.FloatField(
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text="Clipped time spent (1-30 minutes)",
    )
    video_watch_percentage = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Clipped watch percentage (0-100)",
    )
    number_of_clicks = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of clicks (>=0)"
    )
    completion_status = models.BooleanField(
        help_text="Completion status"
    )
    cleaned_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "ml_lesson_interactions_clean"
        indexes = [
            models.Index(fields=["child", "lesson_id"]),
            models.Index(fields=["cleaned_at"]),
        ]

    def __str__(self):
        """String representation of cleaned lesson interactions."""
        return (
            f"LessonInteractionsClean {self.id}: "
            f"ML{self.ml_student_id} - Lesson {self.lesson_id}"
        )


class QuizAttemptsClean(BaseInteractionModel):
    """
    Sanitized quiz attempts with physiological and logical limits applied.
    """

    lesson_id = models.IntegerField(
        help_text="Lesson ID from lessons_lesson table"
    )
    attempt_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="Attempt count clipped (max 3 for statistical use)",
    )
    score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score normalized to 0-100 range",
    )
    wrong_questions = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="Validated count (0-4)",
    )
    response_time = models.FloatField(
        validators=[MinValueValidator(5), MaxValueValidator(150)],
        help_text="Response time clipped (5s to 150s)",
    )
    cleaned_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp of sanitization"
    )

    class Meta:
        db_table = "ml_quiz_attempts_clean"
        indexes = [
            models.Index(fields=["child", "lesson_id"]),
            models.Index(fields=["cleaned_at"]),
        ]

    def __str__(self):
        """String representation of cleaned quiz attempts."""
        return (
            f"QuizAttemptsClean {self.id}: "
            f"ML{self.ml_student_id} - Lesson {self.lesson_id}"
        )


class ProgressClean(BaseInteractionModel):
    """Sanitized progress metrics clipped to realistic limits."""

    lessons_completed = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Validated non-negative lesson count",
    )
    badges_earned = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(12)],
        help_text="Badges clipped to max system limit (0-12)",
    )
    streak_days = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Streak clipped to a yearly limit (0-50)",
    )
    topic_mastery = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Mastery score normalized (0-100%)",
    )
    cleaned_at = models.DateTimeField(
        auto_now_add=True, help_text="When the raw data was sanitized"
    )

    class Meta:
        db_table = "ml_progress_clean"
        indexes = [
            models.Index(fields=["cleaned_at"]),
        ]

    def __str__(self):
        """String representation of cleaned progress."""
        return f"ProgressClean {self.id}: ML{self.ml_student_id}"


# ==============================================================================
# 4. FEATURE TABLES (AGGREGATED)
# ==============================================================================


class LessonFeatures(BaseInteractionModel):
    """Aggregated lesson features per student."""

    avg_time_spent = models.FloatField(
        help_text="Average time spent per lesson (minutes)"
    )
    avg_video_watch = models.FloatField(
        help_text="Average video watch percentage (0-100)"
    )
    avg_clicks = models.FloatField(
        help_text="Average number of clicks per lesson"
    )
    completion_rate = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Lesson completion rate (0-1)",
    )
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_lesson_features"
        indexes = [
            models.Index(fields=["computed_at"]),
        ]

    def __str__(self):
        """String representation of lesson features."""
        return f"LessonFeatures {self.id}: ML{self.ml_student_id}"


class QuizFeatures(BaseInteractionModel):
    """Aggregated quiz features per student."""

    avg_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Average quiz score (0-100)",
    )
    avg_wrong_questions = models.FloatField(
        help_text="Average wrong questions per quiz"
    )
    avg_response_time = models.FloatField(
        help_text="Average response time per question (seconds)"
    )
    avg_attempt_number = models.FloatField(
        help_text="Average attempt number per quiz"
    )
    computed_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "ml_quiz_features"
        indexes = [
            models.Index(fields=["computed_at"]),
        ]

    def __str__(self):
        """String representation of quiz features."""
        return f"QuizFeatures {self.id}: ML{self.ml_student_id}"


class ProgressLabeled(BaseInteractionModel):
    """Labeled progress (target)."""

    class MasteryLevel(models.TextChoices):
        """Mastery level choices."""

        LOW = "Low", "Low"
        MEDIUM = "Medium", "Medium"
        HIGH = "High", "High"

    lessons_completed = models.IntegerField(
        help_text="Number of lessons completed"
    )
    badges_earned = models.IntegerField(
        help_text="Number of badges earned"
    )
    streak_days = models.IntegerField(
        help_text="Current streak in days"
    )
    topic_mastery = models.FloatField(
        help_text="Topic mastery score (0-100)"
    )
    mastery_level = models.CharField(
        max_length=10,
        choices=MasteryLevel.choices,
        help_text="Mastery level classification",
    )
    computed_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "ml_progress_labeled"
        indexes = [
            models.Index(fields=["mastery_level", "computed_at"]),
        ]

    def __str__(self):
        """String representation of labeled progress."""
        return (
            f"ProgressLabeled {self.id}: "
            f"ML{self.ml_student_id} ({self.mastery_level})"
        )


class StudentMLDataset(models.Model):
    """Final merged ML dataset for training."""

    student_id = models.IntegerField(
        primary_key=True, help_text="ML Internal Student ID"
    )
    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Backend Child Reference",
    )

    # Lesson features (4)
    avg_time_spent = models.FloatField(
        help_text="Average time spent per lesson (minutes)"
    )
    avg_video_watch = models.FloatField(
        help_text="Average video watch percentage (0-100)"
    )
    avg_clicks = models.FloatField(
        help_text="Average number of clicks per lesson"
    )
    completion_rate = models.FloatField(
        help_text="Lesson completion rate (0-1)"
    )

    # Quiz features (4)
    avg_score = models.FloatField(
        help_text="Average quiz score (0-100)"
    )
    avg_wrong_questions = models.FloatField(
        help_text="Average wrong questions per quiz"
    )
    avg_response_time = models.FloatField(
        help_text="Average response time per question (seconds)"
    )
    avg_attempt_number = models.FloatField(
        help_text="Average attempt number per quiz"
    )

    # Progress features (3)
    lessons_completed = models.IntegerField(
        help_text="Number of lessons completed"
    )
    badges_earned = models.IntegerField(
        help_text="Number of badges earned"
    )
    streak_days = models.IntegerField(
        help_text="Current streak in days"
    )
    topic_mastery = models.FloatField(
        help_text="Topic mastery score (0-100)"
    )

    # Target (1)
    MASTERY_LEVEL_CHOICES = [("Low", "Low"), ("Medium", "Medium"), ("High", "High")]
    mastery_level = models.CharField(
        max_length=10,
        choices=MASTERY_LEVEL_CHOICES,
        help_text="Target classification"
    )
    snapshot_date = models.DateField(
        auto_now_add=True,
        help_text="Date of snapshot creation"
    )

    class Meta:
        db_table = "ml_student_ml_dataset"
        indexes = [
            models.Index(fields=["snapshot_date"]),
            models.Index(fields=["mastery_level"]),
        ]

    def __str__(self):
        """String representation of ML dataset."""
        return f"StudentMLDataset: ML{self.student_id} - {self.snapshot_date}"


# ==============================================================================
# 5. AI INSIGHTS & OUTPUTS
# ==============================================================================


class Recommendation(models.Model):
    """Actionable insights generated by the AI for the user."""

    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.PROTECT,
        related_name="recommendations",
        help_text="Target child",
    )
    lesson = models.ForeignKey(
        "lessons.Lesson",
        on_delete=models.PROTECT,
        related_name="recommendations",
        help_text="Recommended lesson",
    )
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="AI confidence (0-1)",
    )
    reason = models.TextField(
        null=True, blank=True, help_text="Why this was recommended"
    )
    model = models.ForeignKey(
        MLModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendations",
        help_text="Model used for prediction",
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_recommendation"
        ordering = ["-confidence_score"]
        indexes = [
            models.Index(fields=["child", "-confidence_score"]),
            models.Index(fields=["generated_at"]),
        ]

    def __str__(self):
        """String representation of recommendation."""
        child_name = (
            self.child.user.username if self.child and self.child.user else "Unknown"
        )
        return (
            f"Recommendation {self.id}: "
            f"{self.lesson.title} for {child_name} "
            f"(confidence: {self.confidence_score:.2f})"
        )
