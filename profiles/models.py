import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# =========================
# Custom User Manager
# =========================
class UserManager(BaseUserManager):
    """Custom manager for User model with email as username"""

    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        if not password:
            raise ValueError("The password must be set")

        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)

        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, username, password, **extra_fields)


# =========================
# User Model (Adults)
# =========================
class User(AbstractUser):
    """Central authentication table for all account owners (Adults)"""

    class Role(models.TextChoices):
        PARENT = "parent", "Parent"
        TEACHER = "teacher", "Teacher"
        ADMIN = "admin", "Admin"

    email = models.EmailField(
        unique=True, help_text="User's email address (used for login)"
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PARENT,
        help_text="User role in the system",
    )

    profile_picture_url = models.URLField(
        max_length=500, null=True, blank=True, help_text="URL to profile picture"
    )

    # Override username to keep it unique
    username = models.CharField(max_length=150, unique=True)

    # Use email for authentication
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    class Meta:
        db_table = "profiles_user"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.username} ({self.email})"

    # Convenience helpers
    @property
    def is_parent(self):
        return self.role == self.Role.PARENT

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN


# =========================
# Child Profile
# =========================
class ChildProfile(models.Model):
    """Child-specific data for ML tracking and learning"""

    class LearningLevel(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Stable external ID for ML pipeline tracking",
    )

    parent = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="children",
        help_text="Associated parent account (Protected from deletion)",
    )

    nickname = models.CharField(max_length=50, help_text="Child's display name")

    avatar_url = models.URLField(
        max_length=500, null=True, blank=True, help_text="URL to child's avatar icon"
    )

    age = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(4), MaxValueValidator(6)],
        help_text="Child's age (4-6 years)",
    )

    parent_phone = models.CharField(
        max_length=20, null=True, blank=True, help_text="Emergency contact phone number"
    )

    learning_level = models.CharField(
        max_length=20,
        choices=LearningLevel.choices,
        default=LearningLevel.BEGINNER,
        help_text="Current learning level",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "profiles_childprofile"
        indexes = [
            models.Index(fields=["uuid"]),
        ]

    def __str__(self):
        return f"Child: {self.nickname} (ML-ID: {str(self.uuid)[:8]})"


# =========================
# Teacher Profile
# =========================
class TeacherProfile(models.Model):
    """Teacher metadata"""

    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name="teacher_profile",
        help_text="Associated teacher account",
    )

    bio = models.TextField(null=True, blank=True, help_text="Teacher biography")

    uploaded_count = models.PositiveIntegerField(
        default=0, help_text="Cached count of uploaded lessons"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "profiles_teacherprofile"

    def __str__(self):
        return f"Teacher: {self.user.username}"
