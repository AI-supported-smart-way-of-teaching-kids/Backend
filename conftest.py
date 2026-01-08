import secrets
import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

# =============================================================================
# GENERAL UTILITIES
# =============================================================================


@pytest.fixture
def api_client():
    """Basic REST Framework test client."""
    return APIClient()


@pytest.fixture
def factory():
    """Returns model_bakery baker for easy instance creation."""
    return baker


# =============================================================================
# USER & AUTHENTICATION FIXTURES
# =============================================================================


@pytest.fixture
def user(db):
    """Generic user fixture to fix 'fixture user not found' error."""
    return baker.make(User, email="user@test.com", username="user")


@pytest.fixture
def revealed_user(teacher_user):
    """Alias for teacher_user to fix 'fixture revealed_user not found' error."""
    return teacher_user


@pytest.fixture
def parent_user(db):
    password = secrets.token_urlsafe(12)
    user = User.objects.create_user(
        email="parent@test.com",
        username="parent",
        password=password,
        role=User.Role.PARENT,
    )
    user.raw_password = password
    return user


@pytest.fixture
def teacher_user(db):
    password = secrets.token_urlsafe(12)
    user = User.objects.create_user(
        email="teacher@test.com",
        username="teacher",
        password=password,
        role=User.Role.TEACHER,
    )
    user.raw_password = password
    return user


@pytest.fixture
def admin_user(db):
    password = secrets.token_urlsafe(12)
    user = User.objects.create_superuser(
        email="admin@test.com",
        username="admin",
        password=password,
    )
    user.raw_password = password
    return user


@pytest.fixture
def auth_client(api_client):
    """
    Helper to authenticate a client using JWT.

    IMPORTANT USAGE IN TESTS:
    The fixture returns a function. You must call it:
    >>> client = auth_client(user_instance)
    >>> response = client.get(url)
    """

    def _auth(user_instance):
        token = RefreshToken.for_user(user_instance)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        return api_client

    return _auth
