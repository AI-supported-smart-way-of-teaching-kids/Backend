# profiles/serializers.py
import logging

from rest_framework import serializers

from .models import ChildProfile, TeacherProfile, User

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    """Full user serializer used for responses."""

    class Meta:
        model = User
        # pick the fields you want exposed — __all__ is easy for demo but consider narrowing in prod
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
    """Serializer used for user registration (create only)."""

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
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        logger.info("New user created: %s (role=%s)", user.email, user.role)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for login (used only to describe input for Swagger)."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ChildProfileSerializer(serializers.ModelSerializer):
    """Serializer for reading child profiles (parents/admins)."""

    parent_username = serializers.CharField(source="parent.username", read_only=True)
    parent_email = serializers.EmailField(source="parent.email", read_only=True)

    class Meta:
        model = ChildProfile
        fields = [
            "id",
            "uuid",
            "nickname",
            "avatar_url",
            "age",
            "parent_phone",
            "learning_level",
            "parent",
            "parent_username",
            "parent_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "uuid", "created_at", "updated_at"]

    def validate_age(self, value):
        if value < 4 or value > 6:
            raise serializers.ValidationError("Age must be between 4 and 6.")
        return value


class ChildProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer used when a parent creates a child profile (parent set from request)."""

    class Meta:
        model = ChildProfile
        fields = ("nickname", "avatar_url", "age", "parent_phone", "learning_level")


class TeacherProfileSerializer(serializers.ModelSerializer):
    """Read-only teacher profile serializer with nested user info."""

    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = TeacherProfile
        fields = [
            "id",
            "user",
            "username",
            "email",
            "bio",
            "uploaded_count",
            "created_at",
        ]
        read_only_fields = ["id", "uploaded_count", "created_at"]
