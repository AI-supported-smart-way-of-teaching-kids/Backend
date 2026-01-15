import pytest
from profiles.models import User, ChildProfile, TeacherProfile
from profiles.serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    LoginSerializer,
    ChildProfileCreateSerializer,
    ChildProfileParentSerializer,
    ChildProfilePublicSerializer,
    TeacherProfileSerializer,
)

# -----------------------
# Fixtures
# -----------------------


@pytest.fixture
def parent_user(db):
    return User.objects.create_user(
        email="parent@test.com",
        username="parent",
        password="password123",
        role=User.Role.PARENT,
    )


@pytest.fixture
def teacher_user(db):
    return User.objects.create_user(
        email="teacher@test.com",
        username="teacher",
        password="password123",
        role=User.Role.TEACHER,
    )


@pytest.fixture
def teacher_profile(teacher_user):
    # Delete any existing profile to avoid unique constraint errors
    TeacherProfile.objects.filter(user=teacher_user).delete()
    return TeacherProfile.objects.create(
        user=teacher_user,
        bio="Math teacher",
        uploaded_count=3,
    )


@pytest.fixture
def child(parent_user):
    return ChildProfile.objects.create(
        parent=parent_user,
        nickname="Kid One",
        age=5,
        learning_level=ChildProfile.LearningLevel.BEGINNER,
    )


# -----------------------
# User Serializers
# -----------------------


@pytest.mark.django_db
def test_user_serializer(parent_user):
    serializer = UserSerializer(parent_user)
    data = serializer.data

    assert data["email"] == parent_user.email  # nosec
    assert data["username"] == parent_user.username  # nosec
    assert data["role"] == User.Role.PARENT  # nosec


@pytest.mark.django_db
def test_user_registration_serializer_creates_user():
    payload = {
        "email": "new@test.com",
        "username": "newuser",
        "password": "strongpass",
        "role": User.Role.PARENT,
    }

    serializer = UserRegistrationSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors  # nosec

    user = serializer.save()
    assert user.email == payload["email"]  # nosec
    assert user.check_password(payload["password"])  # nosec


@pytest.mark.django_db
def test_user_registration_duplicate_email(parent_user):
    payload = {
        "email": parent_user.email,
        "username": "another",
        "password": "password123",
        "role": User.Role.PARENT,
    }

    serializer = UserRegistrationSerializer(data=payload)
    assert not serializer.is_valid()  # nosec
    assert "email" in serializer.errors  # nosec


def test_login_serializer_valid():
    payload = {"email": "test@test.com", "password": "secret"}
    serializer = LoginSerializer(data=payload)

    assert serializer.is_valid()  # nosec


# -----------------------
# Child Serializers
# -----------------------


@pytest.mark.django_db
def test_child_profile_create_serializer_valid():
    payload = {
        "nickname": "Kid",
        "age": 5,
        "learning_level": ChildProfile.LearningLevel.BEGINNER,
    }

    serializer = ChildProfileCreateSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors  # nosec


@pytest.mark.django_db
def test_child_profile_create_serializer_invalid_age():
    payload = {"nickname": "Kid", "age": 10}

    serializer = ChildProfileCreateSerializer(data=payload)
    assert not serializer.is_valid()  # nosec
    assert "age" in serializer.errors  # nosec


@pytest.mark.django_db
def test_child_profile_parent_serializer(child):
    serializer = ChildProfileParentSerializer(child)
    data = serializer.data

    assert data["nickname"] == child.nickname  # nosec
    assert data["parent_username"] == child.parent.username  # nosec
    assert data["parent_email"] == child.parent.email  # nosec


@pytest.mark.django_db
def test_child_profile_public_serializer(child):
    serializer = ChildProfilePublicSerializer(child)
    data = serializer.data

    assert set(data.keys()) == {"uuid", "nickname", "learning_level"}  # nosec


# -----------------------
# Teacher Serializer
# -----------------------


@pytest.mark.django_db
def test_teacher_profile_serializer(teacher_profile):
    serializer = TeacherProfileSerializer(teacher_profile)
    data = serializer.data

    assert data["username"] == teacher_profile.user.username  # nosec
    assert data["email"] == teacher_profile.user.email  # nosec
    assert data["uploaded_count"] == teacher_profile.uploaded_count  # nosec
