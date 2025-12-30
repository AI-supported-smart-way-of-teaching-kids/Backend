# core/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuditLogViewSet, HealthCheckView

router = DefaultRouter()
router.register(r"audit-logs", AuditLogViewSet, basename="audit-log")

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("", include(router.urls)),
]
