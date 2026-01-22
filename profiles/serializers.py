import logging
from rest_framework import serializers
from .models import ChildProfile, TeacherProfile, User

logger = logging.getLogger(__name__)


# -----------------------
# User Serializers
# -----------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "profile_picture_url",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "is_active", "date_joined"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ("email", "username", "password", "role")

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        logger.info("New user created: %s (role=%s)", user.email, user.role)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


# -----------------------
# Child Serializers
# -----------------------
class ChildProfileCreateSerializer(serializers.ModelSerializer):
    """Used when a parent creates or updates a child. Parent is set by backend."""

    class Meta:
        model = ChildProfile
        fields = (
            "uuid",
            "nickname",
            "avatar_url",
            "age",
            "parent_phone",
            "learning_level",
        )
        read_only_fields = [
            "uuid",
        ]

    def validate_age(self, value):
        if not 4 <= value <= 6:
            raise serializers.ValidationError("Age must be between 4 and 6.")
        return value


class ChildProfileParentSerializer(serializers.ModelSerializer):
    """Full child info for parents/admins (read-only parent info)."""

    parent_username = serializers.CharField(source="parent.username", read_only=True)
    parent_email = serializers.EmailField(source="parent.email", read_only=True)

    class Meta:
        model = ChildProfile
        fields = [
            "uuid",
            "nickname",
            "avatar_url",
            "age",
            "parent_phone",
            "learning_level",
            "parent_username",
            "parent_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["uuid", "created_at", "updated_at"]


class ChildProfilePublicSerializer(serializers.ModelSerializer):
    """Limited info for teachers (privacy-safe)."""

    class Meta:
        model = ChildProfile
        fields = ["uuid", "nickname", "learning_level"]


# -----------------------
# Teacher Serializer
# -----------------------


class TeacherProfileSerializer(serializers.ModelSerializer):
    # These grab data from the linked User model
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    class Meta:
        model = TeacherProfile
        fields = [
            "id",  # This is the TeacherProfile ID (the one that causes 404 if missing)
            "user_id",  # This is the Auth User ID (25 in your logs)
            "username",
            "email",
            "bio",
            "uploaded_count",
            "created_at",
        ]
        read_only_fields = ["id", "user_id", "uploaded_count", "created_at"]
