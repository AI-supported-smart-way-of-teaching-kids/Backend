import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Progress, Badge, ChildBadge

# Set up logging to track achievements without using 'print'
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Progress)
def handle_lesson_completion(sender, instance, **kwargs):
    """
    Signal receiver that triggers rewards when a child completes a lesson.
    """
    if instance.status == Progress.Status.COMPLETED:
        award_first_star_badge(instance)


def award_first_star_badge(progress_instance):
    """
    Logic to award the 'First Star' badge if the child hasn't earned it yet.
    """
    child = progress_instance.child

    # 1. Define or retrieve the badge
    badge, created = Badge.objects.get_or_create(
        name="First Star",
        defaults={"description": "Congratulations on finishing your first lesson!"},
    )

    # 2. Assign the badge safely using get_or_create to prevent duplicates
    child_badge, awarded = ChildBadge.objects.get_or_create(child=child, badge=badge)

    if awarded:
        logger.info(f"Badge 'First Star' awarded to Child ID: {child.id}")
