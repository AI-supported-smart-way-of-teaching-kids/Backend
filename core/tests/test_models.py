import pytest
from django.utils import timezone
from profiles.models import User
from core.models import AuditLog  # adjust import path if your app is named differently


@pytest.mark.django_db
def test_auditlog_create_with_user():
    user = User.objects.create_user(
        username="testuser", email="user@test.com", password="pass1234"
    )

    log = AuditLog.objects.create(
        user=user,
        action="LOGIN_SUCCESS",
        resource_id="123",
        meta={"ip": "127.0.0.1", "browser": "chrome"},
    )

    # Check that the log was created
    assert AuditLog.objects.count() == 1
    assert log.user == user
    assert log.action == "LOGIN_SUCCESS"
    assert log.resource_id == "123"
    assert log.meta["ip"] == "127.0.0.1"
    assert isinstance(log.created_at, timezone.datetime)


@pytest.mark.django_db
def test_auditlog_create_without_user():
    # Create a system log (user=None)
    log = AuditLog.objects.create(
        user=None,
        action="SYSTEM_UPDATE",
        resource_id="sys_001",
        meta={"version": "1.0.0"},
    )

    assert AuditLog.objects.count() == 1
    assert log.user is None
    assert log.action == "SYSTEM_UPDATE"
    assert log.resource_id == "sys_001"
    assert log.meta["version"] == "1.0.0"


@pytest.mark.django_db
def test_auditlog_str_method_with_user():
    user = User.objects.create_user(
        username="alice", email="alice@test.com", password="pass1234"
    )
    log = AuditLog.objects.create(user=user, action="PASSWORD_CHANGE")

    expected_str_start = "alice - PASSWORD_CHANGE at"
    assert str(log).startswith(expected_str_start)


@pytest.mark.django_db
def test_auditlog_str_method_without_user():
    log = AuditLog.objects.create(user=None, action="SYSTEM_MAINTENANCE")

    expected_str_start = "System - SYSTEM_MAINTENANCE at"
    assert str(log).startswith(expected_str_start)
