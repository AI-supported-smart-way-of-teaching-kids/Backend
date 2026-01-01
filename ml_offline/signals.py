"""from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LessonInteractionsRaw
from ml_online.models import StudentRealtimeAggregate

@receiver(post_save, sender=LessonInteractionsRaw)
def update_online_aggregate(sender, instance, created, **kwargs):
    if created:
        # Update or Create the ONE aggregate record for this student
        obj, created_new = StudentRealtimeAggregate.objects.update_or_create(
            ml_student_id=instance.ml_student_id,
            defaults={
                'child': instance.child,
                'student_uuid': instance.student_uuid,
                # Example: simple logic to update mastery or completion
                'completion_rate': 1.0 if instance.completion_status else 0.0
            }
        )"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import LessonInteractionsRaw
from ml_online.models import StudentRealtimeAggregate


@receiver(post_save, sender=LessonInteractionsRaw)
def sync_to_online_feature_store(sender, instance, created, **kwargs):
    if created:
        ml_id = instance.ml_student_id

        # 1. Calculate ALL stats at once
        stats = LessonInteractionsRaw.objects.filter(ml_student_id=ml_id).aggregate(
            avg_time=Avg("time_spent"), total_count=Count("id")
        )

        avg_time = stats["avg_time"] or 0.0
        total_lessons = stats["total_count"] or 0

        # 2. Simple Mastery Logic for the AI
        # You can add a 'mastery_label' field to your Online model if you want to store this

        # 3. Update the Online Table
        StudentRealtimeAggregate.objects.update_or_create(
            ml_student_id=ml_id,
            defaults={
                "avg_time_spent": avg_time,
                "lessons_completed": total_lessons,  # Fixes the '0' issue
                "updated_at": instance.received_at,
            },
        )
