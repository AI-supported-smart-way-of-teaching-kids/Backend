from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import TeacherProfile, User


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automates profile creation only for Teachers.
    Parents will add ChildProfiles manually through the app.
    """
    if created:
        if instance.role == User.Role.TEACHER:
            TeacherProfile.objects.create(user=instance)
