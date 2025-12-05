
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from core.models import TimeStampedModel, Role

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Role.ADMIN)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        return self._create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """
    AUTH_USER_MODEL: central user record for all roles.
    Use email as username field.
    """
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=16, choices=Role.choices, db_index=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.role})"

class KidProfile(TimeStampedModel):
    """
    1:1 profile for kids (linked to User with role='kid').
    """
    user = models.OneToOneField("users.User", on_delete=models.CASCADE, related_name="kid_profile")
    date_of_birth = models.DateField(null=True, blank=True)
    preferred_language = models.CharField(max_length=32, null=True, blank=True)
    level_estimate = models.CharField(max_length=64, null=True, blank=True)
    parent_primary = models.ForeignKey("users.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="primary_children")

    def __str__(self):
        return f"KidProfile: {self.user.email}"

class TeacherProfile(TimeStampedModel):
    """
    1:1 profile for teachers.
    """
    user = models.OneToOneField("users.User", on_delete=models.CASCADE, related_name="teacher_profile")
    bio = models.TextField(blank=True, null=True)
    institution = models.CharField(max_length=255, blank=True, null=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return f"TeacherProfile: {self.user.email}"

class ParentChildLink(models.Model):
    """
    Many-to-many join table (parent User) <-> (KidProfile).
    Unique constraint prevents duplicate links.
    """
    parent = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="parent_links")
    kid = models.ForeignKey("users.KidProfile", on_delete=models.CASCADE, related_name="parent_links")
    relationship = models.CharField(max_length=64, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["parent", "kid"], name="unique_parent_kid")
        ]
        indexes = [
            models.Index(fields=["parent", "kid"]),
        ]

    def __str__(self):
        return f"ParentChildLink parent={self.parent_id} kid={self.kid_id}"

