from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import TeacherProfile


@receiver(post_save, sender=User)
def create_teacher_profile(sender, instance, created, **kwargs):
    if created:
        # This automatically creates the profile when a user signs up
        TeacherProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_teacher_profile(sender, instance, **kwargs):
    # This ensures the profile is saved if the user is updated
    if hasattr(instance, "teacherprofile"):
        instance.teacherprofile.save()
