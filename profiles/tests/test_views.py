import secrets

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from profiles.models import ChildProfile, TeacherProfile

User = get_user_model()

# -----------------------
# Helpers / Fixtures
# -----------------------


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_password():
    return secrets.token_urlsafe(12)


def auth_client(client, user):
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


@pytest.fixture
def parent_user(db, test_password):
    return User.objects.create_user(
        email="parent@test.com",
        username="parent_user",
        password=test_password,
        role=User.Role.PARENT,
    )


@pytest.fixture
def teacher_user(db, test_password):
    return User.objects.create_user(
        email="teacher@test.com",
        username="teacher_user",
        password=test_password,
        role=User.Role.TEACHER,
    )


@pytest.fixture
def admin_user(db, test_password):
    return User.objects.create_superuser(
        email="admin@test.com",
        username="admin_user",
        password=test_password,
    )


# -----------------------
# Register & Login
# -----------------------


@pytest.mark.django_db
def test_register_creates_user_and_returns_tokens(api_client):
    payload = {
        "email": "new@test.com",
        "username": "newuser",
        "password": "StrongPass123",
    }

    res = api_client.post("/api/profiles/auth/register/", payload, format="json")

    assert res.status_code == 201
    assert "access" in res.data
    assert "refresh" in res.data
    if not User.objects.filter(email="new@test.com").exists():
        pytest.fail("User with email new@test.com was not created")


@pytest.mark.django_db
def test_login_success(api_client, parent_user, test_password):
    res = api_client.post(
        "/api/profiles/auth/login/",
        {"email": parent_user.email, "password": test_password},
        format="json",
    )

    assert res.status_code == 200
    assert "access" in res.data


@pytest.mark.django_db
def test_login_invalid_credentials(api_client):
    res = api_client.post(
        "/api/profiles/auth/login/",
        {"email": "x@test.com", "password": "wrong"},
        format="json",
    )

    assert res.status_code == 401


# -----------------------
# UserViewSet
# -----------------------


@pytest.mark.django_db
def test_user_can_view_own_profile(api_client, parent_user):
    client = auth_client(api_client, parent_user)
    res = client.get("/api/profiles/users/profile/")

    assert res.status_code == 200
    assert res.data["email"] == parent_user.email


@pytest.mark.django_db
def test_user_can_update_own_profile(api_client, parent_user):
    client = auth_client(api_client, parent_user)
    res = client.put(
        "/api/profiles/users/profile/", {"username": "updated_name"}, format="json"
    )

    assert res.status_code == 200
    parent_user.refresh_from_db()
    assert parent_user.username == "updated_name"


@pytest.mark.django_db
def test_admin_can_list_all_users(api_client, admin_user, parent_user):
    client = auth_client(api_client, admin_user)
    res = client.get("/api/profiles/users/")

    assert res.status_code == 200
    assert len(res.data) >= 2


# -----------------------
# ChildProfileViewSet
# -----------------------


@pytest.mark.django_db
def test_parent_can_create_child(api_client, parent_user):
    client = auth_client(api_client, parent_user)
    res = client.post(
        "/api/profiles/children/", {"nickname": "Kid One", "age": 5}, format="json"
    )

    assert res.status_code == 201
    assert ChildProfile.objects.filter(parent=parent_user).exists()


@pytest.mark.django_db
def test_teacher_cannot_create_child(api_client, teacher_user):
    client = auth_client(api_client, teacher_user)
    res = client.post(
        "/api/profiles/children/", {"nickname": "Kid", "age": 5}, format="json"
    )
    assert res.status_code == 403


@pytest.mark.django_db
def test_parent_sees_only_own_children(api_client, parent_user):
    ChildProfile.objects.create(parent=parent_user, nickname="Kid", age=5)
    client = auth_client(api_client, parent_user)
    res = client.get("/api/profiles/children/")

    assert res.status_code == 200
    assert len(res.data["results"]) == 1


@pytest.mark.django_db
def test_teacher_can_read_children(api_client, teacher_user, parent_user):
    ChildProfile.objects.create(parent=parent_user, nickname="Kid", age=5)
    client = auth_client(api_client, teacher_user)
    res = client.get("/api/profiles/children/")

    assert res.status_code == 200
    assert len(res.data["results"]) == 1


@pytest.mark.django_db
def test_parent_cannot_access_other_parent_child_progress(api_client, parent_user):
    other_password = secrets.token_urlsafe(12)
    other_parent = User.objects.create_user(
        email="other@test.com",
        username="other_user",
        password=other_password,
        role=User.Role.PARENT,
    )
    child = ChildProfile.objects.create(parent=other_parent, nickname="Kid", age=5)
    client = auth_client(api_client, parent_user)

    res = client.get(f"/api/profiles/children/{child.uuid}/progress/")

    assert res.status_code == 403


# -----------------------
# TeacherProfileViewSet
# -----------------------


@pytest.mark.django_db
def test_teacher_profile_read_only(api_client, teacher_user):
    TeacherProfile.objects.get_or_create(user=teacher_user)
    client = auth_client(api_client, teacher_user)
    res = client.get("/api/profiles/teachers/")

    assert res.status_code == 200


@pytest.mark.django_db
def test_teacher_profile_cannot_be_created(api_client, teacher_user):
    client = auth_client(api_client, teacher_user)
    res = client.post("/api/profiles/teachers/", {})

    assert res.status_code in [403, 405]
