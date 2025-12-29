from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import AuditLog


@receiver(post_save, sender=User)
def log_password_change(sender, instance, **kwargs):
    """
    This 'tripwire' triggers every time a User is saved.
    We check if the password was the thing that changed.
    """
    # In a real scenario, you'd check if the password field was updated
    # For this simple example, we log the update event
    AuditLog.objects.create(
        user=instance,
        action="USER_UPDATE",
        resource_id=str(instance.id),
        meta={"info": "User profile or password was updated", "status": "Success"},
    )
