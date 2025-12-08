# core/models.py
from django.db import models


class TimeStampedModel(models.Model):
    """
    Simple abstract base model adding created/updated timestamps.
    Other models can inherit from this.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Role(models.TextChoices):
    """
    Simple Role enum. If your users.models expects a Role class,
    this will provide name choices like 'ADMIN' and 'USER'.
    Replace/extend values to match your project.
    """

    ADMIN = "ADMIN", "Admin"
    USER = "USER", "User"
    MANAGER = "MANAGER", "Manager"
