from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from lessons.models import lesson
from profiles.models import ChildProfile


class MLModel(models.Model):
    """Model metadata"""

    name = models.CharField(max_length=100, help_text="Model name")
    version = models.CharField(max_length=50, help_text="Model version")
    file_path = models.CharField(max_length=500, help_text="Artifact location")
    metadata = models.JSONField(null=True, blank=True, help_text="Model metadata")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_mlmodel"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "version"], name="unique_model_version"
            )
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"


class MLStudentMap(models.Model):
    """Map ML ID → backend child"""

    ml_student_id = models.IntegerField(
        primary_key=True, help_text="ML team's internal student ID"
    )
    student_uuid = models.CharField(
        max_length=36, null=True, blank=True, help_text="UUID from accounts.User"
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
        ]

    def __str__(self):
        return f"ML{self.ml_student_id} -> {self.child.user.username if self.child else 'No mapping'}"


class BaseInteractionModel(models.Model):
    """Base model for ML interaction data"""

    ml_student_id = models.IntegerField(help_text="ML team's internal student ID")
    student_uuid = models.CharField(
        max_length=36, null=True, blank=True, help_text="UUID from accounts.User"
    )
    child = models.ForeignKey(
        'profiles.ChildProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="Django ChildProfile reference",
    )

    class Meta:
        abstract = True


class LessonInteractionsRaw(BaseInteractionModel):
    """Append-only raw events"""

    lesson_id = models.IntegerField(help_text="Lesson ID from lessons_lesson")
    time_spent = models.FloatField(help_text="Time spent on lesson (minutes)")
    video_watch_percentage = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(150)],
        help_text="Raw video watch percentage (0-150)",
    )
    number_of_clicks = models.IntegerField(help_text="Number of clicks/interactions")
    completion_status = models.BooleanField(help_text="Whether lesson was completed")
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_lesson_interactions_raw"
        indexes = [
            models.Index(fields=["ml_student_id", "received_at"]),
            models.Index(fields=["student_uuid", "received_at"]),
        ]

    def __str__(self):
        return f"Lesson {self.lesson_id} - Student {self.ml_student_id}"


class QuizAttemptsRaw(BaseInteractionModel):
    """Raw quiz rows"""

    lesson_id = models.IntegerField(help_text="Lesson ID from lessons_lesson")
    attempt_number = models.IntegerField(help_text="Attempt number (1, 2, 3...)")
    score = models.FloatField(help_text="Raw score")
    wrong_questions = models.IntegerField(help_text="Number of wrong questions")
    response_time = models.FloatField(help_text="Response time in seconds")
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_quiz_attempts_raw"
        indexes = [
            models.Index(fields=["ml_student_id", "lesson_id"]),
        ]

    def __str__(self):
        return f"Quiz {self.lesson_id} - Attempt {self.attempt_number}"


class ProgressRaw(BaseInteractionModel):
    """Raw progress summary"""

    lessons_completed = models.IntegerField(help_text="Number of lessons completed")
    badges_earned = models.IntegerField(help_text="Number of badges earned")
    streak_days = models.IntegerField(help_text="Current streak in days")
    topic_mastery = models.FloatField(
        validators=[MinValueValidator(-5), MaxValueValidator(110)],
        help_text="Raw topic mastery (-5 to 110)",
    )
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_progress_raw"

    def __str__(self):
        return f"Progress Raw - Student {self.ml_student_id}"


class LessonInteractionsClean(BaseInteractionModel):
    """Cleaned & clipped lesson interactions"""

    lesson_id = models.IntegerField(help_text="Lesson ID from lessons_lesson")
    time_spent = models.FloatField(
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text="Clipped time spent (1-30 minutes)",
    )
    video_watch_percentage = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Clipped watch percentage (0-100)",
    )
    number_of_clicks = models.IntegerField(
        validators=[MinValueValidator(0)], help_text="Number of clicks (>=0)"
    )
    completion_status = models.BooleanField(help_text="Whether lesson was completed")
    cleaned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_lesson_interactions_clean"
        indexes = [
            models.Index(fields=["child", "lesson_id"]),
        ]

    def __str__(self):
        return f"Clean Lesson {self.lesson_id} - Student {self.ml_student_id}"


class QuizAttemptsClean(BaseInteractionModel):
    """Cleaned quiz data"""

    lesson_id = models.IntegerField(help_text="Lesson ID from lessons_lesson")
    attempt_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="Attempt number (1-3)",
    )
    score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score (0-100)",
    )
    wrong_questions = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="Wrong questions (0-4)",
    )
    response_time = models.FloatField(
        validators=[MinValueValidator(5), MaxValueValidator(150)],
        help_text="Response time (5-150 seconds)",
    )
    cleaned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_quiz_attempts_clean"

    def __str__(self):
        return f"Clean Quiz {self.lesson_id} - Attempt {self.attempt_number}"


class ProgressClean(models.Model):
    """Cleaned progress per student"""

    ml_student_id = models.IntegerField(
        primary_key=True, help_text="ML team's internal student ID"
    )
    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="progress_clean",
        help_text="Django ChildProfile reference",
    )
    lessons_completed = models.IntegerField(
        validators=[MinValueValidator(0)], help_text="Lessons completed (>=0)"
    )
    badges_earned = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(12)],
        help_text="Badges earned (0-12)",
    )
    streak_days = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Streak days (0-50)",
    )
    topic_mastery = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Topic mastery (0-100)",
    )
    cleaned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_progress_clean"

    def __str__(self):
        return f"Clean Progress - Student {self.ml_student_id}"


class LessonFeatures(models.Model):
    """Aggregated lesson features per student"""

    student_id = models.IntegerField(help_text="ML team's internal student ID")
    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lesson_features",
        help_text="Django ChildProfile reference",
    )
    avg_time_spent = models.FloatField(help_text="Average time spent per lesson")
    avg_video_watch = models.FloatField(help_text="Average video watch percentage")
    avg_clicks = models.FloatField(help_text="Average number of clicks per lesson")
    completion_rate = models.FloatField(help_text="Lesson completion rate")
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_lesson_features"

    def __str__(self):
        return f"Lesson Features - Student {self.student_id}"


class QuizFeatures(models.Model):
    """Aggregated quiz features per student"""

    student_id = models.IntegerField(help_text="ML team's internal student ID")
    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quiz_features",
        help_text="Django ChildProfile reference",
    )
    avg_score = models.FloatField(help_text="Average quiz score")
    avg_wrong_questions = models.FloatField(help_text="Average wrong questions")
    avg_response_time = models.FloatField(help_text="Average response time")
    avg_attempt_number = models.FloatField(help_text="Average attempt number")
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_quiz_features"

    def __str__(self):
        return f"Quiz Features - Student {self.student_id}"


class ProgressLabeled(models.Model):
    """Labeled progress (target)"""

    class MasteryLevel(models.TextChoices):
        LOW = "Low", "Low"
        MEDIUM = "Medium", "Medium"
        HIGH = "High", "High"

    student_id = models.IntegerField(help_text="ML team's internal student ID")
    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="progress_labeled",
        help_text="Django ChildProfile reference",
    )
    lessons_completed = models.IntegerField(help_text="Number of lessons completed")
    badges_earned = models.IntegerField(help_text="Number of badges earned")
    streak_days = models.IntegerField(help_text="Current streak in days")
    topic_mastery = models.FloatField(help_text="Topic mastery score")
    mastery_level = models.CharField(
        max_length=10,
        choices=MasteryLevel.choices,
        help_text="Mastery level classification",
    )
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_progress_labeled"

    def __str__(self):
        return f"Progress Labeled - Student {self.student_id} ({self.mastery_level})"


class StudentMLDataset(models.Model):
    """Final merged ML dataset"""

    student_id = models.IntegerField(
        primary_key=True, help_text="ML team's internal student ID"
    )
    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ml_dataset",
        help_text="Django ChildProfile reference",
    )

    # Lesson features
    avg_time_spent = models.FloatField(help_text="Average time spent per lesson")
    avg_video_watch = models.FloatField(help_text="Average video watch percentage")
    avg_clicks = models.FloatField(help_text="Average number of clicks per lesson")
    completion_rate = models.FloatField(help_text="Lesson completion rate")

    # Quiz features
    avg_score = models.FloatField(help_text="Average quiz score")
    avg_wrong_questions = models.FloatField(help_text="Average wrong questions")
    avg_response_time = models.FloatField(help_text="Average response time")
    avg_attempt_number = models.FloatField(help_text="Average attempt number")

    # Progress features
    lessons_completed = models.IntegerField(help_text="Number of lessons completed")
    badges_earned = models.IntegerField(help_text="Number of badges earned")
    streak_days = models.IntegerField(help_text="Current streak in days")
    topic_mastery = models.FloatField(help_text="Topic mastery score")

    # Target
    mastery_level = models.CharField(
        max_length=10,
        choices=ProgressLabeled.MasteryLevel.choices,
        help_text="Mastery level classification",
    )

    snapshot_date = models.DateField(help_text="Date of data snapshot")

    class Meta:
        db_table = "ml_student_ml_dataset"
        indexes = [
            models.Index(fields=["snapshot_date", "mastery_level"]),
        ]

    def __str__(self):
        return f"ML Dataset - Student {self.student_id}"


class Recommendation(models.Model):
    """AI output used by backend"""

    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.PROTECT,
        related_name="recommendations",
        help_text="Child receiving recommendation",
    )
    lesson = models.ForeignKey(
        lesson,
        on_delete=models.PROTECT,
        related_name="recommendations",
        help_text="Recommended lesson",
    )
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Confidence score (0-1)",
    )
    reason = models.TextField(
        null=True, blank=True, help_text="Explanation for recommendation"
    )
    model = models.ForeignKey(
        MLModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendations",
        help_text="ML model that generated recommendation",
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ml_recommendation"
        indexes = [
            models.Index(fields=["child", "-confidence_score"]),
            models.Index(fields=["generated_at"]),
        ]
        ordering = ["-confidence_score"]

    def __str__(self):
        return f"Recommend {self.lesson.title} for {self.child.user.username}"
