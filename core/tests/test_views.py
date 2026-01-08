import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from profiles.models import User
from core.models import AuditLog
# from django.utils import timezone


@pytest.mark.django_db
def test_healthcheck_view_public_access():
    client = APIClient()
    url = reverse("health")  # <-- fixed name
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"status": "healthy", "service": "Learnify Backend API"}


@pytest.mark.django_db
def test_auditlog_viewset_admin_access():
    admin = User.objects.create_superuser(
        username="admin", email="admin@test.com", password="pass123"
    )
    client = APIClient()
    client.force_authenticate(admin)

    # Create some audit logs
    log1 = AuditLog.objects.create(action="LOGIN_SUCCESS")
    log2 = AuditLog.objects.create(action="PASSWORD_CHANGE")

    url = reverse("audit-log-list")
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK

    # Support paginated response
    if "results" in response.data:
        results = response.data["results"]
    else:
        results = response.data

    returned_ids = [item["id"] for item in results]
    # Audit logs are ordered descending by created_at
    expected_ids = (
        [log2.id, log1.id] if log2.created_at > log1.created_at else [log1.id, log2.id]
    )
    assert returned_ids == expected_ids


@pytest.mark.django_db
def test_auditlog_viewset_non_admin_denied():
    user = User.objects.create_user(
        username="user1", email="user1@test.com", password="pass123"
    )
    client = APIClient()
    client.force_authenticate(user)

    url = reverse("audit-log-list")  # <-- fixed name
    response = client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
