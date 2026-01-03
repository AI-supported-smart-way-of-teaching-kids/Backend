# tests/conftest.py
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import secrets

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


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
    def _auth(user):
        token = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        return api_client

    return _auth
