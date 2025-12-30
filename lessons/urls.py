# lessons/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CollectionViewSet, LessonViewSet, MediaUploadViewSet

router = DefaultRouter()
router.register(r"lessons", LessonViewSet, basename="lesson")
router.register(r"collections", CollectionViewSet, basename="collection")
router.register(r"media-uploads", MediaUploadViewSet, basename="mediaupload")

urlpatterns = [
    path("", include(router.urls)),
]
