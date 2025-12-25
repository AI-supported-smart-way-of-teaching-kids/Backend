from django.db import models

from lessons.models import lesson
from profiles.models import ChildProfile


class Progress(models.Model):
    """Per-child per-lesson status"""

    class Status(models.TextChoices):
        NOT_STARTED = "not-started", "Not Started"
        IN_PROGRESS = "in-progress", "In Progress"
        COMPLETED = "completed", "Completed"

    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.PROTECT,
        related_name="progress",
        help_text="Child's progress",
    )
    lesson = models.ForeignKey(
        lesson,
        on_delete=models.PROTECT,
        related_name="progress",
        help_text="Lesson being tracked",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
        help_text="Current completion status",
    )
    points_earned = models.IntegerField(
        default=0, help_text="Points earned from this lesson"
    )
    last_accessed = models.DateTimeField(
        null=True, blank=True, help_text="Last time child accessed this lesson"
    )
    completion_date = models.DateTimeField(
        null=True, blank=True, help_text="When lesson was completed"
    )

    class Meta:
        db_table = "progress_progress"
        constraints = [
            models.UniqueConstraint(
                fields=["child", "lesson"], name="unique_child_lesson_progress"
            )
        ]
        indexes = [
            models.Index(fields=["child", "last_accessed"]),
            models.Index(fields=["status", "completion_date"]),
        ]

    def __str__(self):
        return f"{self.child.user.username} - {self.lesson.title} - {self.status}"


class Badge(models.Model):
    """Badge definition"""

    name = models.CharField(max_length=100, unique=True, help_text="Badge name")
    description = models.TextField(null=True, blank=True, help_text="Badge description")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "progress_badge"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ChildBadge(models.Model):
    """Awarded badge for a child"""

    child = models.ForeignKey(
        ChildProfile,
        on_delete=models.PROTECT,
        related_name="badges",
        help_text="Child who earned the badge",
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.PROTECT,
        related_name="awarded_to",
        help_text="Badge that was awarded",
    )
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "progress_childbadge"
        constraints = [
            models.UniqueConstraint(
                fields=["child", "badge"], name="unique_child_badge"
            )
        ]
        indexes = [
            models.Index(fields=["child", "awarded_at"]),
        ]
        ordering = ["-awarded_at"]

    def __str__(self):
        return f"{self.child.user.username} - {self.badge.name}"
