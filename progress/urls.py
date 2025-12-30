# progress/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BadgeViewSet, ChildBadgeViewSet, ProgressViewSet

router = DefaultRouter()
router.register(r"progress", ProgressViewSet, basename="progress")
router.register(r"badges", BadgeViewSet, basename="badge")
router.register(r"child-badges", ChildBadgeViewSet, basename="child-badge")

urlpatterns = [
    path("", include(router.urls)),
]
