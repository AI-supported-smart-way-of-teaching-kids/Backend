from django.db import models

from profiles.models import User


class AuditLog(models.Model):
    """
    Immutable log of security-sensitive events and system changes.
    Used for compliance and debugging.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        help_text="The user account that triggered this event.",
    )
    action = models.CharField(
        max_length=100,
        help_text="The category of action (e.g., 'LOGIN_SUCCESS', 'PASSWORD_CHANGE').",
    )
    resource_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The ID of the object being modified (e.g., ML_MODEL_ID).",
    )
    meta = models.JSONField(
        null=True,
        blank=True,
        help_text="Detailed payload (IP address, Browser agent, old vs new values).",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The exact moment the action was recorded."
    )

    class Meta:
        db_table = "core_auditlog"
        # Ordered so the newest logs always appear at the top of the list
        ordering = ["-created_at"]
        # Composite indexes optimize filtering by user actions over time
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self):
        username = self.user.username if self.user else "System"
        return f"{username} - {self.action} at {self.created_at}"
