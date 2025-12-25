from django.db import models
from django.utils.text import slugify
from django.conf import settings

from profiles.models import TeacherProfile


# Create your models here.
class lesson(models.Model):
    """Lesson metadata & media URL"""

    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    title = models.CharField(max_length=200, help_text="Lesson title")
    slug = models.SlugField(
        max_length=200, unique=True, help_text="URL-friendly identifier"
    )
    description = models.TextField(help_text="Detailed lesson description")
    video_url = models.URLField(
        max_length=500, help_text="S3/CDN URL for video content"
    )
    thumbnail_url = models.URLField(
        max_length=500, null=True, blank=True, help_text="URL for lesson thumbnail"
    )
    duration_seconds = models.IntegerField(
        null=True, blank=True, help_text="Lesson duration in seconds"
    )
    difficulty = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.EASY,
        help_text="Lesson difficulty level",
    )
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.PROTECT,
        related_name="lessons",
        help_text="Teacher who created the lesson",
    )
    tags = models.JSONField(
        default=list, blank=True, help_text="List of tags for categorization"
    )
    is_published = models.BooleanField(
        default=False, help_text="Whether lesson is publicly available"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "lessons_lesson"
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["difficulty"]),
            models.Index(fields=["is_published", "created_at"]),
        ]
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} by {self.teacher.user.username}"


class MediaUpload(models.Model):
    """Upload / transcoding tracker"""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    class FileType(models.TextChoices):
        VIDEO_MP4 = "video/mp4", "MP4 Video"
        VIDEO_WEBM = "video/webm", "WebM Video"
        IMAGE_PNG = "image/png", "PNG Image"
        IMAGE_JPG = "image/jpg", "JPG Image"

    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="media_uploads",
        help_text="User who uploaded the file",
    )
    file_url = models.URLField(max_length=500, help_text="URL of uploaded file")
    file_type = models.CharField(
        max_length=50, choices=FileType.choices, help_text="MIME type of the file"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Current processing status",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "lessons_mediaupload"
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"{self.file_type} - {self.status}"
