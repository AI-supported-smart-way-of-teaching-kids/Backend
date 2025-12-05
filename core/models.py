from django.db import models
from django.utils import timezone

class TimeStampModel(models.Model):
    """
    abstract provides the created_at and updated_at.
    
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        abstract = True
        
class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)
    
    def dead(self):
        return self.filter(deleted_at__isnull=False)
    
class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model,using=self._db).filter(delete_at__isnull=True)
    
class SoftDeleteModel(models.Model):
    """
    Optional mixin to support soft-delete semantics.
    Use objects (default) to get alive rows; all_objects to access all.
    """
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    class Meta:
        abstract = True
        
class Role(models.TextChoices):
    KID = "kid", "Kid"
    PARENT = "parent", "Parent"
    TEACHER = "teacher", "Teacher"
    ADMIN = "admin", "Admin"