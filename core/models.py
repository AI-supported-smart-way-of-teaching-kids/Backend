from django.db import models

from profiles.models import User


class AuditLog(models.Model):
    """Security events"""

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        help_text="User who performed the action",
    )
    action = models.CharField(max_length=100, help_text="Action performed")
    meta = models.JSONField(null=True, blank=True, help_text="Additional metadata")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_auditlog"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["action", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        username = self.user.username if self.user else "System"
        return f"{username} - {self.action} at {self.created_at}"
