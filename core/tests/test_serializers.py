import pytest

# from rest_framework.serializers import ValidationError
from core.serializers import AuditLogSerializer
from core.models import AuditLog
from profiles.models import User


@pytest.mark.django_db
def test_auditlog_serializer_with_user():
    # Create a user
    user = User.objects.create(
        username="user1", email="user1@test.com", password="pass123"
    )

    # Create an AuditLog with a user
    log = AuditLog.objects.create(
        user=user, action="LOGIN_SUCCESS", resource_id="123", meta={"ip": "127.0.0.1"}
    )

    serializer = AuditLogSerializer(log)
    data = serializer.data

    # Check all fields
    assert data["id"] == log.id
    assert data["user"] == user.id
    assert data["user_name"] == user.username
    assert data["action"] == "LOGIN_SUCCESS"
    assert data["resource_id"] == "123"
    assert data["meta"] == {"ip": "127.0.0.1"}
    assert "created_at" in data


@pytest.mark.django_db
def test_auditlog_serializer_system_user():
    # AuditLog with no user
    log = AuditLog.objects.create(
        action="SYSTEM_MAINTENANCE", resource_id=None, meta=None
    )

    serializer = AuditLogSerializer(log)
    data = serializer.data

    assert data["user"] is None
    assert data["user_name"] is None  # read_only user_name is None if no user
    assert data["action"] == "SYSTEM_MAINTENANCE"
    assert data["resource_id"] is None
    assert data["meta"] is None


@pytest.mark.django_db
def test_auditlog_serializer_write_fields_readonly():
    user = User.objects.create(
        username="user2", email="user2@test.com", password="pass123"
    )
    # Attempt to provide read_only field should be ignored
    data = {
        "user": user.id,
        "action": "LOGIN_SUCCESS",
        "created_at": "2020-01-01T00:00:00Z",  # read-only
    }
    serializer = AuditLogSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    validated = serializer.validated_data

    assert "created_at" not in validated  # read-only field is ignored
    assert validated["user"] == user
    assert validated["action"] == "LOGIN_SUCCESS"
