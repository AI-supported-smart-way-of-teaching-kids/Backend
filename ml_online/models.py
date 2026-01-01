"""
Online ML model: Single aggregate table for real-time inference.
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from profiles.models import ChildProfile


# ==============================================================================
# Student realtime aggregate
# ==============================================================================
class StudentRealtimeAggregate(models.Model):
    """
    Single-row-per-student snapshot used for real-time inference.

    This table is intentionally denormalized and kept small so the backend can
    fetch features for a single student quickly. The ML pipeline (offline)
    is responsible for updating these values via UPSERTs.
    """

    ml_student_id = models.IntegerField(
        primary_key=True,
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
        help_text="Django ChildProfile reference"
    )

    # --------------------------------------------------------------------------
    # Aggregated features (precomputed by offline pipeline)
    # --------------------------------------------------------------------------
    avg_time_spent = models.FloatField(
        default=0.0,
        help_text="Average time spent per lesson (minutes)"
    )
    avg_video_watch = models.FloatField(
        default=0.0,
        help_text="Average video watch percentage (0-100)"
    )
    avg_clicks = models.FloatField(
        default=0.0,
        help_text="Average number of clicks per lesson"
    )
    completion_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Lesson completion rate (0-1)"
    )

    avg_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Average quiz score (0-100)"
    )
    avg_wrong_questions = models.FloatField(
        default=0.0,
        help_text="Average wrong questions per quiz"
    )
    avg_response_time = models.FloatField(
        default=0.0,
        help_text="Average response time per question (seconds)"
    )
    avg_attempt_number = models.FloatField(
        default=0.0,
        help_text="Average attempt number per quiz"
    )

    lessons_completed = models.IntegerField(
        default=0,
        help_text="Number of lessons completed"
    )
    badges_earned = models.IntegerField(
        default=0,
        help_text="Number of badges earned"
    )
    streak_days = models.IntegerField(
        default=0,
        help_text="Current login streak in days"
    )
    topic_mastery = models.FloatField(
        default=0.0,
        help_text="Topic mastery score (0-100)"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update timestamp for the aggregate row"
    )

    class Meta:
        db_table = "ml_student_realtime_aggregate"
        indexes = [
            models.Index(fields=["ml_student_id"]),
            models.Index(fields=["updated_at"])
        ]

    def __str__(self):
        return (
            f"StudentRealtimeAggregate: ML{self.ml_student_id} - "
            f"{self.updated_at.date()}"
        )
