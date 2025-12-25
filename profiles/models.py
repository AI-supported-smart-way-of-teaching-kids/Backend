import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models


# Create your models here.
class UserManager(BaseUserManager):
    """Custom manager for User model with email as username"""

    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        return self.create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    """
    central authentication tablefor all user

    """

    class Role(models.TextChoices):
        CHILD = "child", "CHILD"
        TEACHER = "TEACHER", "teacher"
        ADMIN = "ADMIN", "admin"

    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Stable external ID for ML pipeline",
    )
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True, help_text="User's email address (unique)")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CHILD)
    profile_picture_url = models.URLField(
        max_length=500, null=True, blank=True, help_text="URL to profile picture"
    )

    # Override AbstractUser fields
    username = models.CharField(max_length=150, unique=True)

    # Custom fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "accounts_user"
        indexes = [
            models.Index(fields=["uuid"]),
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.username} ({self.email})"


class ChildProfile(models.Model):
    """Child-specific data"""

    # This regex ensures the number starts with + and has 9-15 digits
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    )

    class LearningLevel(models.TextChoices):
        BEGINNER = "beginner", "BEGINNER"
        INTERMIDATE = "INTERMIDATE", "intermidate"
        ADVANCED = "ADVANCED", "advanced"

    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name="child_profile",
        help_text="Associated user account",
    )
    age = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(4), MaxValueValidator(6)],
        help_text="Child's age (4-6 years)",
    )
    parent_phone_no = models.CharField(
        validators=[phone_regex], max_length=15, blank=True
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
        db_table = "accounts_childprofile"

    def __str__(self):
        return f"Child: {self.user.username}"


class TeacherProfile(models.Model):
    """Teacher metadata"""

    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name="teacher_profile",
        help_text="Associated user account",
    )
    bio = models.TextField(null=True, blank=True, help_text="Teacher biography")
    upload_count = models.IntegerField(
        default=0, help_text="Cached count of uploaded lessons"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Mate:
        db_table = "accounts_teacherprofile"

    def __str__(self):
        return f"Teacher: {self.user.username}"
