import os
from django.conf import settings
from django.db import models
from django.utils.text import slugify

from profiles.models import TeacherProfile


class Collection(models.Model):
    title = models.CharField(max_length=100)
    slug = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """Lesson metadata & media URL"""

    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    collection = models.ForeignKey(
        Collection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lessons",
    )

    title = models.CharField(max_length=200, help_text="Lesson title")
    slug = models.SlugField(
        max_length=200, unique=True, help_text="URL-friendly identifier"
    )
    description = models.TextField(help_text="Detailed lesson description")
    video = models.FileField(
        upload_to="videos/", null=True, blank=True, help_text="Uploaded video file"
    )
    video_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Optional: External URL if not uploading file",
    )
    thumbnail = models.ImageField(
        upload_to="thumbnails/",
        null=True,
        blank=True,
        help_text="Thumbnail image for lesson",
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
        # ordering = ["title"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} by {self.teacher.user.username}"


def get_media_upload_path(instance, filename):
    """
    Groups files into 'videos/', 'images/', or 'audios/'
    based on the file_type attribute.
    """
    # 1. Map MIME types to your desired folder names
    folder_map = {"video": "videos", "image": "images", "audio": "audios"}

    # 2. Extract the category (e.g., 'video' from 'video/mp4')
    # If file_type is unknown, default to 'others'
    file_category = instance.file_type.split("/")[0] if instance.file_type else "others"
    subfolder = folder_map.get(file_category, "others")

    # 3. Return the relative path from MEDIA_ROOT
    # Note: Do NOT include 'media/' here; Django prepends MEDIA_ROOT automatically.
    return os.path.join(subfolder, filename)


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
        AUDIO_MP3 = "audio/mpeg", "MP3 Audio"  # Added for your audios folder

    lesson = models.ForeignKey(
        "Lesson", on_delete=models.CASCADE, related_name="media_uploads"
    )
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="media_uploads",
        help_text="User who uploaded the file",
    )

    # Updated: Now uses the dynamic function
    file = models.FileField(
        upload_to=get_media_upload_path,
        null=True,
        blank=True,
        help_text="The actual video/image/audio file being uploaded",
    )

    file_url = models.URLField(
        max_length=500, blank=True, help_text="S3/CDN URL if applicable"
    )
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
