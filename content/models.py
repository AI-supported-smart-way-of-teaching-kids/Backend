from django.db import models
from core.models import TimeStampedModel


class Video(TimeStampedModel):
    title = models.CharField(max_length=255, blank=True)
    storage_key = models.CharField(
        max_length=1024, blank=True, null=True
    )  # S3 key or similar
    url = models.CharField(max_length=2048)  # playback URL or signed URL
    uploaded_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_videos",
    )
    upload_date = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    thumbnail_url = models.CharField(max_length=2048, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["uploaded_by"]),
            models.Index(fields=["upload_date"]),
        ]

    def __str__(self):
        return f"Video {self.id}: {self.title or self.storage_key}"


class Lesson(TimeStampedModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    teacher = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lessons",
    )
    # lesson may reference a primary video; additional videos can be added via a join table if needed
    video = models.ForeignKey(
        "content.Video",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lessons",
    )
    topic_tag = models.CharField(max_length=128, blank=True, null=True)
    lesson_metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["teacher"]),
            models.Index(fields=["topic_tag"]),
        ]

    def __str__(self):
        return self.title


class Quiz(TimeStampedModel):
    lesson = models.ForeignKey(
        "content.Lesson", on_delete=models.CASCADE, related_name="quizzes"
    )
    title = models.CharField(max_length=255, blank=True, null=True)
    passing_score = models.IntegerField(default=70)
    difficulty = models.CharField(max_length=16, blank=True, null=True)
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["lesson"]),
        ]

    def __str__(self):
        return self.title or f"Quiz {self.id}"


class Question(models.Model):
    QUESTION_TYPE_CHOICES = (
        ("mcq", "MCQ"),
        ("multi", "Multiple Choice"),
        ("input", "Input"),
        ("drag", "Drag"),
    )
    quiz = models.ForeignKey(
        "content.Quiz", on_delete=models.CASCADE, related_name="questions"
    )
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=16, choices=QUESTION_TYPE_CHOICES, default="mcq"
    )
    metadata = models.JSONField(default=dict, blank=True)  # images, hints, timers, etc.

    def __str__(self):
        return f"Q{self.id}: {self.question_text[:60]}"


class Choice(models.Model):
    question = models.ForeignKey(
        "content.Question", on_delete=models.CASCADE, related_name="choices"
    )
    option_text = models.TextField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["question"])]

    def __str__(self):
        return f"Choice {self.id} (correct={self.is_correct})"
