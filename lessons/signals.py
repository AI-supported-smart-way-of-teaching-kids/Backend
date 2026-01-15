from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from lessons.models import Lesson
from profiles.models import TeacherProfile


@receiver(post_save, sender=Lesson)
def lesson_created_increase_count(sender, instance, created, **kwargs):
    if created and instance.teacher_id:
        TeacherProfile.objects.filter(id=instance.teacher_id).update(
            uploaded_count=models.F("uploaded_count") + 1
        )


@receiver(post_delete, sender=Lesson)
def lesson_deleted_decrease_count(sender, instance, **kwargs):
    if instance.teacher_id:
        TeacherProfile.objects.filter(
            id=instance.teacher_id, uploaded_count__gt=0
        ).update(uploaded_count=models.F("uploaded_count") - 1)
