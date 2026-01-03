import secrets

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError

from profiles.models import ChildProfile, TeacherProfile

# Standardizing User model retrieval
User = get_user_model()
TEST_PASSWORD = secrets.token_urlsafe(12)


@pytest.fixture
def parent_user(db):
    """Returns a saved user with the Parent role"""
    return User.objects.create_user(
        email="parent_fixture@test.com",
        username="parent_fixture",
        password=TEST_PASSWORD,
        role=User.Role.PARENT,
    )


@pytest.mark.django_db
class TestUserModel:
    """Tests for the Custom User model and its Manager"""

    def test_create_user_with_email_successful(self):
        """Test creating a regular user with email as username field"""
        user = User.objects.create_user(
            email="parent@example.com", username="parentuser", password=TEST_PASSWORD
        )
        if user.email != "parent@example.com":
            raise AssertionError("Expected user.email to be 'parent@example.com'")
        if user.is_active is not True:
            raise AssertionError("Expected user.is_active to be True")
        if user.role != User.Role.PARENT:
            raise AssertionError(f"Expected user.role to be {User.Role.PARENT!r}")
        if not user.check_password(TEST_PASSWORD):
            raise AssertionError("Password mismatch for created user")
        if user.is_parent is not True:
            raise AssertionError("Expected user.is_parent to be True")

    # --- NEGATIVE TESTS TO ADDRESS "MISSES" ---

    def test_create_user_no_email_raises_error(self):
        """Triggers: raise ValueError('The Email field must be set')"""
        with pytest.raises(ValueError, match="The Email field must be set"):
            User.objects.create_user(
                email=None, username="test", password=TEST_PASSWORD
            )

    def test_create_user_no_password_raises_error(self):
        """Triggers: raise ValueError('The password must be set')"""
        with pytest.raises(ValueError, match="The password must be set"):
            User.objects.create_user(
                email="test@example.com", username="test", password=""
            )

    def test_create_superuser_invalid_staff_raises_error(self):
        """Triggers: raise ValueError('Superuser must have is_staff=True.')"""
        with pytest.raises(ValueError, match="Superuser must have is_staff=True."):
            User.objects.create_superuser(
                email="admin@test.com",
                username="admin",
                password=TEST_PASSWORD,
                is_staff=False,
            )

    def test_create_superuser_invalid_superuser_status_raises_error(self):
        """Triggers: raise ValueError('Superuser must have is_superuser=True.')"""
        with pytest.raises(ValueError, match="Superuser must have is_superuser=True."):
            User.objects.create_superuser(
                email="admin@test.com",
                username="admin",
                password=TEST_PASSWORD,
                is_superuser=False,
            )

    # --- END NEGATIVE TESTS ---

    def test_create_superuser_successful(self):
        """Test valid superuser creation and role assignment"""
        admin = User.objects.create_superuser(
            email="admin@example.com", username="adminuser", password=TEST_PASSWORD
        )
        if not admin.is_staff:
            raise AssertionError("Expected admin.is_staff to be True")
        if not admin.is_superuser:
            raise AssertionError("Expected admin.is_superuser to be True")
        if admin.role != User.Role.ADMIN:
            raise AssertionError(f"Expected admin.role to be {User.Role.ADMIN!r}")
        if not admin.is_admin:
            raise AssertionError("Expected admin.is_admin to be True")

    def test_role_helper_properties(self):
        """Test the @property helpers for is_parent, is_teacher, is_admin"""
        teacher = User(role=User.Role.TEACHER)
        if teacher.is_teacher is not True:
            pytest.fail("Expected teacher.is_teacher to be True")
        if teacher.is_parent is not False:
            pytest.fail("Expected teacher.is_parent to be False")


@pytest.mark.django_db
class TestChildProfileModel:
    """Tests for ChildProfile constraints and relationships"""

    def test_child_profile_creation(self, parent_user):
        """Test creating a valid child profile linked to a parent"""
        child = ChildProfile.objects.create(
            parent=parent_user,
            nickname="Little Star",
            age=5,
            learning_level=ChildProfile.LearningLevel.BEGINNER,
        )
        if child.nickname != "Little Star":
            pytest.fail("Expected child.nickname to be 'Little Star'")
        if child.uuid is None:
            pytest.fail("Expected child.uuid to be set")
        if child.parent != parent_user:
            pytest.fail("Expected child.parent to be the parent_user")

    def test_age_validators(self, parent_user):
        """Test age must be between 4 and 6"""
        child = ChildProfile(parent=parent_user, nickname="Kid", age=3)
        with pytest.raises(ValidationError):
            child.full_clean()  # Age 3 is too young

        child.age = 7
        with pytest.raises(ValidationError):
            child.full_clean()  # Age 7 is too old

    def test_protect_parent_deletion(self, parent_user):
        """Ensure parent cannot be deleted if they have a child profile"""
        ChildProfile.objects.create(parent=parent_user, nickname="Son", age=5)
        with pytest.raises(ProtectedError):
            parent_user.delete()


@pytest.mark.django_db
class TestTeacherProfileModel:
    """Tests for TeacherProfile metadata"""

    def test_teacher_profile_one_to_one(self):
        """Test linking a teacher profile to a user"""
        user = User.objects.create_user(
            email="teacher@school.com",
            username="teacher1",
            password=TEST_PASSWORD,
            role=User.Role.TEACHER,
        )
        profile = TeacherProfile.objects.create(user=user, bio="Expert in AI for kids")

        if profile.user.email != "teacher@school.com":
            pytest.fail("Expected profile.user.email to be 'teacher@school.com'")
        if user.teacher_profile != profile:
            pytest.fail("Expected user.teacher_profile to be profile")
        if profile.uploaded_count != 0:
            pytest.fail(
                f"Expected profile.uploaded_count to be 0, got {profile.uploaded_count}"
            )
